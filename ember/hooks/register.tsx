import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, Timer } from 'claude-code'

import type { Card } from '../types'
import { clockTime, coldReason, defaultTtl, isRetryable, isTtl, parseBullets, plan } from './schedule'
import type { Plan, Ttl } from './schedule'

const card = atom({ plugin: 'ember', key: 'card' } as const, null)

const CARD_PROMPT = [
  '[ember] The user stepped away; this is an automatic keep-warm request, not a message from them.',
  'Write the card they will read on return: 4 to 6 bullets, each a terse fragment under 15 words.',
  'Cover the goal, what is done, what is in progress, what waits on them, and the next step.',
  'No prose, no headers, no tools. Output only the bullets.',
].join(' ')

const PING_PROMPT = '[ember] Automatic keep-warm request. Reply with exactly: ok'

const MAX_RETRIES = 3

type Warmer = {
  maxHours: number
  isOff: boolean
  timer?: Timer
  // Bumped whenever the person is back, so a fork still in flight lands nowhere.
  epoch: number
}

function stopTimer(w: Warmer) {
  w.timer?.cancel()
  w.timer = undefined
}

async function resolveTtl($: EngineInterface): Promise<Ttl> {
  const configured = await $.settings.read({ key: 'promptCacheTtl' })

  if (isTtl(configured)) {
    return configured
  }

  const { rateLimits } = await $.session.usage()

  return defaultTtl(rateLimits.map(limit => limit.kind))
}

async function reset($: EngineInterface, w: Warmer) {
  stopTimer(w)
  w.epoch += 1
  await update($, card, () => null)
}

async function stop($: EngineInterface, w: Warmer, reason: string) {
  stopTimer(w)
  await update($, card, current => (current === null ? current : { ...current, stopped: reason }))
}

async function ping($: EngineInterface, w: Warmer, at: number, schedule: Plan, pings: number, retries: number): Promise<void> {
  if (at !== w.epoch) {
    return
  }

  if (pings >= schedule.maxPings) {
    await stop($, w, `stopped after ${pings} pings: more would cost more than a cold rewrite`)

    return
  }

  const current = await read($, card)
  const reply = await $.model.fork({ prompt: current === null ? CARD_PROMPT : PING_PROMPT })

  if (at !== w.epoch) {
    return
  }

  if (!reply.isAnswered) {
    const status = 'status' in reply ? (reply.status ?? undefined) : undefined

    if (reply.reason === 'api-error' && isRetryable(status) && retries < MAX_RETRIES) {
      w.timer = $.clock.after(schedule.retryMs, () => void ping($, w, at, schedule, pings, retries + 1))

      return
    }

    await stop($, w, reply.reason === 'nothing-to-fork' ? 'nothing to keep warm' : `ping failed: ${reply.reason}${status === undefined ? '' : ` ${status}`}`)

    return
  }

  const cold = coldReason(reply.usage)

  if (cold !== undefined) {
    await stop($, w, cold)

    return
  }

  const warmedAt = await $.clock.now()
  const next: Card = current === null ? { bullets: parseBullets(reply.text), warmedAt, pings: 1 } : { ...current, warmedAt, pings: current.pings + 1 }
  await update($, card, () => next)
  w.timer = $.clock.after(schedule.intervalMs, () => void ping($, w, at, schedule, pings + 1, 0))
}

async function arm($: EngineInterface, w: Warmer) {
  await reset($, w)

  if (w.isOff || (await $.env.get('DISABLE_PROMPT_CACHING')) !== undefined) {
    return
  }

  const at = w.epoch
  const schedule = plan(await resolveTtl($), w.maxHours)
  w.timer = $.clock.after(schedule.intervalMs, () => void ping($, w, at, schedule, 0, 0))
}

export const register: Register = (on, options) => {
  const w: Warmer = { maxHours: typeof options.maxHours === 'number' ? options.maxHours : 8, isOff: false, epoch: 0 }

  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'ember', description: 'Prompt-cache warming: status, or `off` / `on` for this session', argumentHint: '[off|on]' })

    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    await reset($, w)

    return next(e)
  })

  // Subagents finish turns of their own; only the main thread's end starts the idle clock.
  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined) {
      await arm($, w)
    }

    return next(e)
  })

  on('command.run', { command: 'ember' }, async ($, e) => {
    const arg = e.args.trim()

    if (arg === 'off') {
      w.isOff = true
      await reset($, w)

      return { text: 'ember: off for this session.' }
    }

    if (arg === 'on') {
      w.isOff = false

      return { text: 'ember: on; warming starts when this turn ends.' }
    }

    if (w.isOff) {
      return { text: 'ember: off for this session.' }
    }

    const ttl = await resolveTtl($)
    const { intervalMs, maxPings } = plan(ttl, w.maxHours)

    return { text: `ember: ${ttl} cache, pinging every ${Math.round(intervalMs / 60_000)}m while idle, at most ${maxPings} pings.` }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const shown = await read($, card)

    if (shown === null || e.props.hasSurvey) {
      return next(e)
    }

    const { Box, Text } = $.ui.resolve(e)
    const status =
      shown.stopped === undefined
        ? `warm · kept at ${clockTime(shown.warmedAt)} · ${shown.pings} ping${shown.pings === 1 ? '' : 's'}`
        : `cooling · ${shown.stopped}`

    return (
      <Box flexDirection="column">
        <Box flexDirection="column" borderStyle="round" paddingX={1}>
          <Text dimColor>ember · {status}</Text>
          {shown.bullets.map(bullet => (
            <Text>• {bullet}</Text>
          ))}
        </Box>
        {await next(e)}
      </Box>
    )
  })
}
