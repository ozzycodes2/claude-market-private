# repo-improv

Cleans up a repo's agent-instructions file (`CLAUDE.md`, `AGENTS.md`, etc.) in two
independent phases: restructure it with progressive disclosure, then convert its
deterministic CLI-policy rules into enforced Claude Code hooks.

## Usage

```
> clean up my CLAUDE.md, it's grown into one giant file
> turn the "always use just, never bare cargo fmt" rule into a hook
```

Or invoke the skill explicitly:

```
/repo-improv:agent-docs-improv
```

## Skills

| Skill | What it does |
|-------|--------------|
| `agent-docs-improv` | Phase 1: finds contradictions, extracts root-file essentials, splits the rest into topic files under `docs/agents/`, flags (doesn't delete) redundant/vague instructions. Phase 2: identifies which of those rules are CLI-command-shaped, confirms scope with the user, then writes `.claude/hooks/*.sh` scripts wired into `.claude/settings.json`'s `PreToolUse` — deterministically blocking the banned invocation instead of relying on the agent remembering the rule every session. |

## How it works

```
Phase 1 (progressive disclosure)
  contradiction scan → ask user to resolve
  → extract root essentials
  → split the rest into docs/agents/*.md
  → delegate issue-tracker/domain-docs/triage-labels to
    /mattpocock-skills:setup-matt-pocock-skills (prose fallback if not installed)
  → rewrite root as a slim index + links
  → flag deletion candidates (leave them in place)
  → verify zero content loss (git diff --stat + spot-check grep)

Phase 2 (deterministic enforcement) — only for CLI-shaped rules
  list candidates → confirm scope with user (AskUserQuestion)
  → write .claude/hooks/<rule>.sh + register in .claude/settings.json
  → test: banned command blocks, allowed command passes, dynamic values pass unjudged
  → report what's enforced vs. what still relies on judgment
```

Judgment-based rules (anything requiring reading file *content*, not just a
command string — e.g. "never log the member number") are explicitly out of
scope for Phase 2's `Bash` hooks; the skill leaves those as documented policy
rather than faking enforcement with a check that can't see what it needs to.

## Requirements

- `jq` — hook scripts parse the `PreToolUse` stdin JSON with it.
- macOS's BSD `grep` is the tested baseline for hook regexes (no `\s`/`\b`
  support) — see `skills/agent-docs-improv/references/hook-patterns.md`.
- Optional: the `mattpocock-skills` plugin (`setup-matt-pocock-skills`) — used
  to scaffold issue-tracker/domain-docs/triage-labels conventions in Phase 1.
  Not required; the skill falls back to doing the equivalent by hand.

## Notes

- Never deletes existing instructions on its own initiative — flags
  candidates and leaves the removal decision to the user.
- Hooks only take effect in new sessions; restart Claude Code after Phase 2
  to pick up newly registered hooks.
- Never treats `docs/superpowers/`, `.superpowers/`, or any other
  superpowers-plugin-owned path as this repo's domain docs, issue tracker, or
  triage label source — and makes sure those paths are gitignored.
