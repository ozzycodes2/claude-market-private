import { expect, mock, test } from 'claude-code/testing'
import type { On } from 'claude-code'
import type { Engine } from 'claude-code/testing'

import { coldReason, defaultTtl, isRetryable, isTtl, parseBullets, plan } from '../hooks/schedule'

const MINUTE = 60_000

const BAND = {
  plugin: 'ember',
  component: 'AbovePrompt',
  requestId: 'above',
  props: { hasSurvey: false, isWorking: false, maxRows: 20, bodyColumns: 80, scroll: { offset: 0, bodyRows: 19 }, view: {} },
} as const

type Fork = { isAnswered: true; text: string; usage: Usage } | { isAnswered: false; reason: string; status?: number | null; usage?: Usage }
type Usage = { input_tokens: number; output_tokens: number; cache_read_input_tokens: number; cache_creation_input_tokens: number }

const WARM: Usage = { input_tokens: 20, output_tokens: 40, cache_read_input_tokens: 150_000, cache_creation_input_tokens: 0 }

const answered = (text: string, usage = WARM): Fork => ({ isAnswered: true, text, usage })

function stubEngine(on: On, opts: { engine?: string; ttl?: string; rateLimits?: string[]; env?: Record<string, string>; forks?: Fork[] } = {}) {
  const clock = mock.clock(on, { now: 0 })
  mock.env(on, opts.env ?? {})
  const prompts: string[] = []
  const forks = [...(opts.forks ?? [])]

  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)

    return <Text>{opts.engine ?? ''}</Text>
  })
  on('command.register', () => ({ value: { command: 'ember' } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('prompt.submit', (_, e) => ({ text: e.text }))
  on('turn.complete', (_, e) => ({ text: e.answer }))
  on('settings.read', () => ({ value: opts.ttl === undefined ? {} : { promptCacheTtl: opts.ttl } }) as never)
  on('session.usage', () => ({ value: { startedAt: 0, context: {}, rateLimits: (opts.rateLimits ?? []).map(kind => ({ kind, percentUsed: 1 })) } }) as never)
  on('model.fork', (_, e) => {
    prompts.push(e.prompt)

    return { value: forks.shift() ?? answered('ok') } as never
  })

  return { clock, prompts }
}

const turn = (agentId?: string) => ({ durationMs: 1000, isAborted: false, reason: 'answer', turnId: 't', answer: 'done', ...(agentId === undefined ? {} : { agentId }) }) as const

async function bandText($: Engine, surface: 'terminal' | 'desktop' = 'terminal') {
  const ui = await $.ui.mount({ ...BAND, surface })
  const texts = ((await ui.findAll({ type: 'Text' })) as { text?: string }[]).map(el => el.text ?? '')
  await ui.unmount()

  return texts.join('\n')
}

test('plan pings just before expiry and stops at the break-even or the hour cap', () => {
  expect(plan('1h', 8)).toEqual({ intervalMs: 55 * MINUTE, retryMs: (5 * MINUTE) / 3, maxPings: 8 })
  expect(plan('1h', 48).maxPings, 'twenty hour-tier reads cost one rewrite').toBe(20)
  expect(plan('5m', 8)).toEqual({ intervalMs: 4 * MINUTE, retryMs: MINUTE / 3, maxPings: 12 })
  expect(plan('5m', 0.25).maxPings).toBe(3)
  expect(plan('1h', -1).maxPings).toBe(0)
})

test('the TTL defaults by billing path and only known values count as set', () => {
  expect(defaultTtl(['five_hour', 'seven_day'])).toBe('1h')
  expect(defaultTtl(['spend_limit']), 'a gateway limit is no subscription').toBe('5m')
  expect(defaultTtl([])).toBe('5m')
  expect([isTtl('1h'), isTtl('5m'), isTtl('30m'), isTtl(undefined)]).toEqual([true, true, false, false])
})

test('cold and changed prefixes end warming; busy APIs are retried', () => {
  expect(coldReason(WARM)).toBeUndefined()
  expect(coldReason({ ...WARM, cache_read_input_tokens: 0 })).toBe('the cache was already cold')
  expect(coldReason({ ...WARM, cache_creation_input_tokens: 15_000 })).toBe('the cached prefix changed')
  expect([429, 500, 529, 400, undefined].map(isRetryable)).toEqual([true, true, true, false, false])
})

test('bullets are read from any list marker, or every line when there is none', () => {
  expect(parseBullets('- goal: ship ember\n* done: tests\n• next: PR\n2) wait: name')).toEqual(['goal: ship ember', 'done: tests', 'next: PR', 'wait: name'])
  expect(parseBullets('first\n\n second ')).toEqual(['first', 'second'])
})

test('an idle hour-cache session gets a card at 55 minutes, then cheap pings that keep it', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { ttl: '1h', forks: [answered('- goal: ship ember\n- next: open PR')] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())

  await clock.advance(54 * MINUTE)
  expect(prompts, 'nothing before the ping is due').toEqual([])

  await clock.advance(MINUTE)
  expect(prompts).toHaveLength(1)
  expect(prompts[0]).toContain('4 to 6 bullets')

  for (const surface of ['terminal', 'desktop'] as const) {
    const text = await bandText($, surface)
    expect(text).toContain('• goal: ship ember')
    expect(text).toContain('• next: open PR')
    expect(text).toContain('1 ping')
  }

  await clock.advance(55 * MINUTE)
  expect(prompts[1]).toContain('Reply with exactly: ok')
  const text = await bandText($)
  expect(text, 'the card stays').toContain('• goal: ship ember')
  expect(text).toContain('2 pings')
})

test('typing again clears the card and stops the pings', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { ttl: '1h', forks: [answered('- a')] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(55 * MINUTE)
  expect(await bandText($)).toContain('• a')

  await $.prompt.submit({ text: 'back', wait: false, origin: { kind: 'composer' } } as never)
  expect(await bandText($)).not.toContain('ember')

  await clock.advance(120 * MINUTE)
  expect(prompts).toHaveLength(1)
})

test('a subagent finishing does not start the idle clock', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { ttl: '1h' })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn('a1'))
  await clock.advance(120 * MINUTE)
  expect(prompts).toEqual([])
})

test('with no setting, a subscription warms hourly and anything else every 4 minutes', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { rateLimits: [] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(4 * MINUTE)
  expect(prompts).toHaveLength(1)
})

test('a subscription with no setting waits for the hour tier', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { rateLimits: ['five_hour'] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(54 * MINUTE)
  expect(prompts).toEqual([])
  await clock.advance(MINUTE)
  expect(prompts).toHaveLength(1)
})

test('a ping that finds the cache cold stops and says so on the card', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { ttl: '5m', forks: [answered('- a'), answered('ok', { ...WARM, cache_read_input_tokens: 0 })] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(8 * MINUTE)
  expect(await bandText($)).toContain('cooling · the cache was already cold')

  await clock.advance(60 * MINUTE)
  expect(prompts).toHaveLength(2)
})

test('warming stops at the break-even count', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { ttl: '5m', forks: [answered('- a')] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(13 * 4 * MINUTE)
  expect(prompts).toHaveLength(12)
  expect(await bandText($)).toContain('stopped after 12 pings')
})

test('a busy API is retried before the cache lapses; other failures stop', async ($, on) => {
  const busy: Fork = { isAnswered: false, reason: 'api-error', status: 529, usage: WARM }
  const bad: Fork = { isAnswered: false, reason: 'api-error', status: 400, usage: WARM }
  const { clock, prompts } = stubEngine(on, { ttl: '5m', forks: [busy, answered('- a'), bad] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(4 * MINUTE)
  expect(prompts).toHaveLength(1)
  await clock.advance(20_000)
  expect(prompts, 'retried after a third of the margin').toHaveLength(2)
  expect(await bandText($)).toContain('• a')

  await clock.advance(4 * MINUTE)
  expect(await bandText($)).toContain('ping failed: api-error 400')
})

test('nothing to fork leaves no card', async ($, on) => {
  const { clock } = stubEngine(on, { ttl: '1h', forks: [{ isAnswered: false, reason: 'nothing-to-fork' }] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(55 * MINUTE)
  expect(await bandText($)).not.toContain('ember')
})

test('DISABLE_PROMPT_CACHING turns warming off', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { ttl: '1h', env: { DISABLE_PROMPT_CACHING: '1' } })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(120 * MINUTE)
  expect(prompts).toEqual([])
})

test('/ember reports the schedule, and off holds until on', async ($, on) => {
  const { clock, prompts } = stubEngine(on, { ttl: '1h' })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  const run = async (args: string) => ((await $.command.run({ command: 'ember', args, origin: { kind: 'composer' } } as never)) as { text: string }).text

  expect(await run('')).toBe('ember: 1h cache, pinging every 55m while idle, at most 8 pings.')
  expect(await run('off')).toBe('ember: off for this session.')
  expect(await run('')).toBe('ember: off for this session.')
  await $.turn.complete(turn())
  await clock.advance(120 * MINUTE)
  expect(prompts).toEqual([])

  expect(await run('on')).toBe('ember: on; warming starts when this turn ends.')
  await $.turn.complete(turn())
  await clock.advance(55 * MINUTE)
  expect(prompts).toHaveLength(1)
})

test('a survey keeps the band', async ($, on) => {
  const { clock } = stubEngine(on, { ttl: '1h', engine: 'engine', forks: [answered('- a')] })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })
  await $.turn.complete(turn())
  await clock.advance(55 * MINUTE)

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal', props: { ...BAND.props, hasSurvey: true } })
  expect(await ui.find({ type: 'Text', text: /ember/ })).toBeUndefined()
  await ui.unmount()

  expect(await bandText($), 'the card sits above what the band already drew').toMatch(/• a[\s\S]*engine/)
})
