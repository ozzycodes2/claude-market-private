# session-improv

Turn your own Claude Code session history into signal — query it with SQL, and use
what you find to prune your setup with confidence.

## Skills

| Skill | What it does |
|-------|--------------|
| `reflect` | Query Claude Code conversation history and session data with SQL (DuckDB via cc-query) — token usage, tool patterns, agent activity, and insights from past session logs. |
| `plugin-curation` | An evidence-based audit of your installed plugins, skills, and MCP servers. Pulls real usage counts and recency, then produces keep / consolidate / prune recommendations — it recommends, it never edits `settings.json`. |

## Usage

```
> how many tokens did I burn this week?
> which tools do I call most across my sessions?
> audit my plugins — I think I have too many
```

Each skill can also be invoked explicitly, e.g. `/session-improv:reflect`.

## Requirements

Both skills lean on `cc-query` (DuckDB over your session transcripts). `plugin-curation`
also reads `~/.claude.json` and `~/.claude/settings.json` for usage counters and the
enabled-plugin map.

## License

MIT — see the marketplace [LICENSE](../LICENSE).
