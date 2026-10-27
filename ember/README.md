# ember

Keeps the prompt cache warm while you are away from a Claude Code session, and
leaves a status card for when you come back.

## How it works

When a main-thread turn ends, ember starts an idle timer that fires just before
the cache expires. Each firing is one tool-less fork over the session's own
transcript (`$.model.fork`), which reads the cached prefix and resets its
lifetime. The fork adds nothing to the conversation.

The first fork after your last turn asks for 4 to 6 terse bullets: goal, done,
in progress, waiting on you, next step. They are drawn in a card above the
prompt. Later forks ask only for `ok` and update the card's `kept at HH:MM`
line. Typing anything clears the card and stops the timer.

| Cache lifetime | Ping every | Stops after |
| --- | --- | --- |
| 1h | 55m | 20 pings, or `maxHours` |
| 5m | 4m | 12 pings, or `maxHours` |

The lifetime is read at runtime. `promptCacheTtl` in settings wins. Unset, a
subscription session (one reporting `five_hour` or `seven_day` rate limits)
uses 1h, and anything else uses 5m. `DISABLE_PROMPT_CACHING` turns ember off.

The ping caps are the break-even points. A cache read costs 0.1x base input. A
rewrite costs 2x on the hour tier and 1.25x on the five-minute tier. Past 20 or
12 pings, warming has cost more than one cold rewrite. On a 5-minute cache that
is under an hour away.

Warming also stops, and the card says why, when a ping:

- reads nothing from the cache (it was already cold)
- writes a tenth or more of what it reads (the prefix changed)
- fails with a non-retryable error; 429 and 5xx are retried 3 times inside the
  margin before expiry

## Commands and settings

- `/ember`: the current lifetime, interval and ping cap
- `/ember off` / `/ember on`: pause or resume for this session
- `maxHours` (plugin option, default 8): the longest time away to keep warm

## Developing

```sh
claude plugin validate ./ember
claude plugin test ./ember
claude --plugin-dir ./ember
```

## License

MIT — see [LICENSE](./LICENSE).
