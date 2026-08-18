# claude-market-private

Private Claude Code plugin marketplace for [@ozzycodes2](https://github.com/ozzycodes2).

## Install

```
/plugin marketplace add ozzycodes2/claude-market-private
```

## Plugins

| Plugin | Description |
| --- | --- |
| [review](./review) | Comprehensive multi-phase PR review — change analysis, 3-pass deep code review, security scanning, test analysis, and documentation-drift checks, posted as one unified GitHub review. |
| [session-improv](./session-improv) | Query Claude Code session history and conversation data with SQL (DuckDB) via cc-query. Provides the `reflect` skill for session analysis, token usage, tool patterns, and agent activity. |
| [agent-authoring](./agent-authoring) | Author and improve agent-facing instructions and skills — restructure CLAUDE.md/AGENTS.md via progressive disclosure with enforced PreToolUse hooks (`agent-docs-improv`), and write effective skills and agent docs (`writing-for-agents`). |
| [architecture-design](./architecture-design) | Design deep modules and sharpen a project's domain model — architecture vocabulary (`codebase-design`), domain terminology and ADRs (`domain-modeling`), a codebase deepening scan with an HTML report (`improve-codebase-architecture`), and one-time repo setup (`setup-matt-pocock-skills`). |
| [grilling](./grilling) | Relentless interviews to stress-test a plan, decision, or design — `grilling`, `grill-me`, `grill-with-docs` (grilling that produces ADRs + a glossary), and `wayfinder` (plan work too large for one session as a map of decision tickets). |
| [session-mgmt](./session-mgmt) | Manage the full lifecycle of a working session. `start-session` opens a task in a fresh, isolated git worktree (via EnterWorktree) named after the argument and loads the JIRA story when it's an issue key; `exit-session` tears down the ephemeral resources a session created — background processes, Docker/compose stacks, local Tilt/Kubernetes, git worktrees, temp files — with a plan-confirm-execute flow that never destroys data or deletes branches without confirmation. |

Install an individual plugin with:

```
/plugin install review@claude-market-private
/plugin install session-improv@claude-market-private
/plugin install agent-authoring@claude-market-private
/plugin install architecture-design@claude-market-private
/plugin install grilling@claude-market-private
/plugin install session-mgmt@claude-market-private
```

## License

MIT — see [LICENSE](./LICENSE).
