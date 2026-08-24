---
name: setup-matt-pocock-skills
description: Configure this repo for the engineering skills — set up its issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other engineering skills.
---

# Setup Matt Pocock's Skills

Scaffold per-repo config the engineering skills assume:

- **Issue tracker** — where issues live (GitHub by default; local markdown also supported)
- **Triage labels** — strings for the five canonical triage roles
- **Domain docs** — where `CONTEXT.md` and ADRs live, plus consumer rules for reading them

Prompt-driven, not a deterministic script. Explore, present findings, confirm with user, then write.

## Process

### 1. Explore

Inspect current repo state. Read what exists; don't assume:

- `git remote -v` and `.git/config` — GitHub repo? Which one?
- `AGENTS.md` and `CLAUDE.md` at repo root — either exist? Already an `## Agent skills` section in either?
- `CONTEXT.md` and `CONTEXT-MAP.md` at repo root
- `docs/adr/` and any `src/*/docs/adr/` dirs
- `docs/agents/` — this skill's prior output already there?
- `.scratch/` — sign a local-markdown issue tracker convention is in use
- Is `triage` skill installed? (a `triage` skill folder alongside this one, or `triage` in available skills.) Decides whether Section B runs.
- Monorepo signals — `pnpm-workspace.yaml`, a `workspaces` field in `package.json`, or populated `packages/*` with own `src/`. Present only in a genuinely large multi-package repo; absence means single-context, almost every repo.

### 2. Present findings and ask

Summarise present vs missing. Take sections in order — one section, one answer, then next.

Lead each section with recommended answer so user accepts in a word. One-line explainer only when choice genuinely branches; skip section when exploration settled it (Section B when `triage` not installed, Section C when no monorepo).

**Section A — Issue tracker.**

> Explainer: The "issue tracker" is where issues live for this repo. Skills like `to-tickets`, `triage`, and `to-spec` read/write it — they need to know whether to call `gh issue create`, write a markdown file under `.scratch/`, or follow another workflow you describe. Pick where you actually track work.

Default posture: designed for GitHub. If a `git remote` points at GitHub, propose that. If at GitLab (`gitlab.com` or self-hosted), propose GitLab. Otherwise (or if user prefers), offer:

- **GitHub** — issues in repo's GitHub Issues (uses `gh` CLI)
- **GitLab** — issues in repo's GitLab Issues (uses [`glab`](https://gitlab.com/gitlab-org/cli) CLI)
- **Local markdown** — issues as files under `.scratch/<feature>/` (good for solo projects or repos without a remote)
- **Other** (Jira, Linear, etc.) — ask user to describe workflow in one paragraph; recorded as freeform prose

Record choice in `docs/agents/issue-tracker.md`. GitHub and GitLab templates carry a "PRs as a request surface" flag, defaulted **off** — leave it off and don't raise it; user can flip the flag in the file later.

**Section B — Triage label vocabulary.** Skip entirely if `triage` skill not installed — an uninstalled skill needs no labels.

If installed, ask exactly one question:

> Keep default triage labels? (recommended: **yes**)

Defaults are the five canonical roles, each label string equal to its name: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. On **yes**, write as-is. Only if user says no — usually because their tracker uses other names (e.g. `bug:triage` for `needs-triage`) — collect overrides so `triage` applies existing labels instead of creating duplicates.

**Section C — Domain docs.** Default **single-context** — one `CONTEXT.md` + `docs/adr/` at repo root. Fits almost every repo; write without asking.

Offer **multi-context** — a root `CONTEXT-MAP.md` pointing to per-context `CONTEXT.md` files — only when exploration found monorepo signals. Then confirm which layout they want.

### 3. Confirm and edit

Show user a draft of:

- The `## Agent skills` block to add to whichever of `CLAUDE.md` / `AGENTS.md` is edited (see step 4 for selection rules)
- Contents of `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, and `docs/agents/triage-labels.md` (last only when `triage` installed)

Let them edit before writing.

### 4. Write

**Pick the file to edit:**

- If `CLAUDE.md` exists, edit it.
- Else if `AGENTS.md` exists, edit it.
- If neither exists, ask user which to create — don't pick for them.

Never create `AGENTS.md` when `CLAUDE.md` already exists (or vice versa) — always edit the one already there.

If an `## Agent skills` block already exists in the chosen file, update its contents in-place rather than appending a duplicate. Don't overwrite user edits to surrounding sections.

The block:

```markdown
## Agent skills

### Issue tracker

[one-line summary of where issues are tracked]. See `docs/agents/issue-tracker.md`.

### Triage labels

[one-line summary of the label vocabulary]. See `docs/agents/triage-labels.md`.

### Domain docs

[one-line summary of layout — "single-context" or "multi-context"]. See `docs/agents/domain.md`.
```

Include the `### Triage labels` sub-block, and write `docs/agents/triage-labels.md`, only when `triage` installed and Section B ran. Otherwise both omitted.

Then write the docs files using the seed templates in this skill folder as a starting point:

- [issue-tracker-github.md](./issue-tracker-github.md) — GitHub issue tracker
- [issue-tracker-gitlab.md](./issue-tracker-gitlab.md) — GitLab issue tracker
- [issue-tracker-local.md](./issue-tracker-local.md) — local-markdown issue tracker
- [triage-labels.md](./triage-labels.md) — label mapping (only if `triage` installed)
- [domain.md](./domain.md) — domain doc consumer rules + layout

For "other" issue trackers, write `docs/agents/issue-tracker.md` from scratch using the user's description.

### 5. Done

Tell user setup is complete and which engineering skills now read these files. Mention they can edit `docs/agents/*.md` directly later — re-running this skill is only necessary to switch issue trackers or restart from scratch.
