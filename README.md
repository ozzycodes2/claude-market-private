# claude-market-private

Private Claude Code plugin marketplace for [@ozzycodes2](https://github.com/ozzycodes2).

## Install

```
/plugin marketplace add ozzycodes2/claude-market-private
```

## Plugins

| Plugin | Description |
| --- | --- |
| [review](./review) | Comprehensive multi-phase PR review — change analysis, 3-pass deep code review, security scanning, test analysis, and documentation-drift checks, posted as one unified GitHub review. Plus `monitor-pr`: continuously watch a PR for CI failures and review comments (drive with `/loop`) and fix them via subagents. |
| [session-improv](./session-improv) | Query Claude Code session history and conversation data with SQL (DuckDB) via cc-query. Provides the `reflect` skill for session analysis, token usage, tool patterns, and agent activity, and `plugin-curation` for evidence-based keep/consolidate/prune audits of installed plugins, skills, and MCP servers. |
| [technical-writing](./technical-writing) | Human-facing developer writing done well — draft, score, and fix docs (`write-doc`, `writing-design-docs`, `review-doc`, `fix-doc`), build minimalist Machinify HTML decks whose diagrams come from `architecture-design` (`create-slides`), and the `laconic` output style (write the conclusion, not the path to it). Adapted from ceej-skills, pertinent, practical-prose, humanizer, and slide-deck-template. |
| [architecture-design](./architecture-design) | Design deep modules and sharpen a project's domain model — architecture vocabulary (`codebase-design`), domain terminology and ADRs (`domain-modeling`), a codebase deepening scan with an HTML report (`improve-codebase-architecture`), and one-time repo setup (`setup-matt-pocock-skills`). |
| [grilling](./grilling) | Relentless interviews to stress-test a plan, decision, or design — `grilling`, `grill-me`, `grill-with-docs` (grilling that produces ADRs + a glossary), and `wayfinder` (plan work too large for one session as a map of decision tickets). |
| [session-mgmt](./session-mgmt) | Manage the full lifecycle of a working session. `start-session` opens a task in a fresh, isolated git worktree (via EnterWorktree) named after the argument and loads the JIRA story when it's an issue key; `exit-session` tears down the ephemeral resources a session created — background processes, Docker/compose stacks, local Tilt/Kubernetes, git worktrees, temp files — with a plan-confirm-execute flow that never destroys data or deletes branches without confirmation. |
| [fabric](./fabric) | Skins for Claude Code in the Fabric palette — one chroma, ink on near-black or paper — plus sixteen upstream themes. A mod that redraws the transcript: tool rows, diff, table, code, math, Mermaid and shell cards, a usage band, `/skin` to swap live. The same tokens draw `architecture-design`'s diagrams. Forked from hellosverre/claude-skins (MIT). |
| [ember](./ember) | Keeps the prompt cache warm while you are away. Forks the session just before the cache expires and leaves a bulleted status card above the prompt; stops once more pings would cost more than a cold rewrite. `/ember` shows the schedule, `/ember off` pauses it. |

Install an individual plugin with:

```
/plugin install review@claude-market-private
/plugin install session-improv@claude-market-private
/plugin install architecture-design@claude-market-private
/plugin install grilling@claude-market-private
/plugin install session-mgmt@claude-market-private
/plugin install technical-writing@claude-market-private
/plugin install fabric@claude-market-private
/plugin install ember@claude-market-private
```

## License

MIT — see [LICENSE](./LICENSE).
