export type Card = {
  bullets: string[]
  warmedAt: number
  pings: number
  // Why warming ended; absent while it runs.
  stopped?: string
}

declare module 'claude-code' {
  interface PluginState {
    ember: { card: Card | null }
  }
}
