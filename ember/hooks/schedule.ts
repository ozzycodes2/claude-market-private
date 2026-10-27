export type Ttl = '5m' | '1h'

const MINUTE = 60_000

const TTL_MS: Readonly<Record<Ttl, number>> = { '5m': 5 * MINUTE, '1h': 60 * MINUTE }

// Pings land this far before expiry, leaving room for retries of a busy API.
const MARGIN_MS: Readonly<Record<Ttl, number>> = { '5m': MINUTE, '1h': 5 * MINUTE }

// Cache-write price per token as a multiple of a cache read (0.1x base input):
// 1.25x base for the 5-minute tier, 2x for the hour. Past this many pings,
// warming has cost more than letting it go cold and rewriting it once.
const BREAK_EVEN_PINGS: Readonly<Record<Ttl, number>> = { '5m': 12, '1h': 20 }

export type Plan = { intervalMs: number; retryMs: number; maxPings: number }

export const plan = (ttl: Ttl, maxHours: number): Plan => {
  const intervalMs = TTL_MS[ttl] - MARGIN_MS[ttl]
  const byHours = Math.floor((Math.max(0, maxHours) * 60 * MINUTE) / intervalMs)

  return { intervalMs, retryMs: MARGIN_MS[ttl] / 3, maxPings: Math.min(byHours, BREAK_EVEN_PINGS[ttl]) }
}

export const isTtl = (value: unknown): value is Ttl => value === '5m' || value === '1h'

// The included-usage windows; a gateway's `spend_limit` says nothing about the plan.
const SUBSCRIPTION_WINDOWS = new Set(['five_hour', 'seven_day'])

// Unset `promptCacheTtl` defaults to an hour on subscription usage, five minutes elsewhere.
export const defaultTtl = (rateLimitKinds: readonly string[]): Ttl =>
  rateLimitKinds.some(kind => SUBSCRIPTION_WINDOWS.has(kind)) ? '1h' : '5m'

// A ping that reads nothing found the cache cold; one that writes a tenth of what
// it reads found the prefix changed. Either way more pings buy nothing.
export const coldReason = (usage: { cache_read_input_tokens: number; cache_creation_input_tokens: number }): string | undefined => {
  if (usage.cache_read_input_tokens === 0) {
    return 'the cache was already cold'
  }

  if (usage.cache_creation_input_tokens * 10 >= usage.cache_read_input_tokens) {
    return 'the cached prefix changed'
  }

  return undefined
}

export const isRetryable = (status: number | undefined): boolean => status === 429 || (status !== undefined && status >= 500)

const BULLET = /^\s*(?:[-*•‣▪]|\d+[.)])\s+/

export const parseBullets = (text: string): string[] => {
  const lines = text.split('\n').map(line => line.trim()).filter(line => line !== '')
  const bullets = lines.filter(line => BULLET.test(line)).map(line => line.replace(BULLET, ''))

  return bullets.length > 0 ? bullets : lines
}

export const clockTime = (ms: number): string => {
  const at = new Date(ms)

  return `${String(at.getHours()).padStart(2, '0')}:${String(at.getMinutes()).padStart(2, '0')}`
}
