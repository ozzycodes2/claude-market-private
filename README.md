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
| [repo-improv](./repo-improv) | Restructures bloated agent-instructions files (CLAUDE.md/AGENTS.md) via progressive disclosure and turns their deterministic CLI-policy rules into enforced PreToolUse hooks. Provides the `agent-docs-improv` skill. |

Install an individual plugin with:

```
/plugin install review@claude-market-private
/plugin install session-improv@claude-market-private
/plugin install repo-improv@claude-market-private
```

## License

MIT — see [LICENSE](./LICENSE).
