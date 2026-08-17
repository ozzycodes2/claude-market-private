---
name: agent-docs-improv
description: Use when a repo's agent-instructions file (CLAUDE.md, AGENTS.md, GEMINI.md) has grown large, duplicative, or hard to navigate, or when the user asks to restructure/refactor/clean up agent docs, apply progressive disclosure, split a monolithic instructions file into topic files, or turn written policy into deterministic enforcement. Also use when asked to "turn these instructions into hooks," "enforce this automatically," or "stop the agent from running X" — the CLI-policy half of this skill converts must-use-this-not-that and disallowed-command rules into Claude Code PreToolUse hooks. Trigger even if the user doesn't name the skill or the file explicitly.
license: MIT
---

# Improving agent instructions files

Two independent phases. Run Phase 1 first if the instructions file is
disorganized; run Phase 2 whenever there's CLI-policy prose worth enforcing.
A repo may only need one phase — don't force the other.

## Non-negotiable: superpowers paths are never project docs

Regardless of phase, never read `docs/superpowers/`, `.superpowers/`, or any
other directory owned by the `superpowers` plugin (its own `.gitignore` is
authoritative — currently `.worktrees/`, `.private-journal/`, `.claude/`,
`.superpowers/`, `triage/`, `evals/`) as if it were this repo's:

- **Domain docs** (`CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`) — these are
  the superpowers plugin's own planning/journal files, not the project's.
- **Issue tracker** — a `docs/superpowers/plans/*.md` file is not the
  local-markdown `.scratch/<feature>/` convention, even though both are
  markdown-under-docs.
- **Triage label vocabulary** — never infer label strings from anything
  under a superpowers path.

Don't just skip these paths in-session — check that they're actually
gitignored in the repo being worked on, and add them to `.gitignore` if
they're missing. This applies to every exploration step below, including the
`setup-matt-pocock-skills` delegation's own exploration in step 5.

## Phase 1: Progressive disclosure restructure

Goal: a root file short enough to read in one glance, with detail pushed into
linked topic files loaded only when relevant.

1. **Identify the file.** If more than one instructions file exists (root
   `CLAUDE.md` vs. a nested one, or `AGENTS.md` vs `CLAUDE.md`), ask the user
   which one via AskUserQuestion rather than guessing — these files are easy
   to conflate and picking wrong wastes the whole restructure.
2. **Scan for contradictions first, before restructuring anything.** Read the
   full file and look for instructions that conflict (two build commands, two
   commit formats, etc.). For each contradiction found, ask the user which
   version to keep — don't silently pick one. Report explicitly if you found
   none; don't skip this step just because nothing turned up.
3. **Extract the essentials for the root file.** Only:
   - One-sentence project description.
   - Package manager / build tool, if non-standard for the language.
   - Non-standard build/lint/test commands (e.g. "always go through `just`,
     never bare `cargo fmt`").
   - Anything relevant to literally every task (the one irreversible rule, a
     safety invariant, etc.).
4. **Group everything else into topic files.** One file per logical category
   (e.g. testing, error handling, PR conventions, code style) under
   `docs/agents/` (or wherever the project already keeps this kind of doc —
   check for an existing convention before defaulting to `docs/agents/`).
   Keep section headers and wording verbatim where possible; this is a split,
   not a rewrite. Note any wording changes you make (e.g. a cross-reference
   replacing a repeated paragraph) so you can call them out in the summary.
5. **Delegate issue tracker / domain docs / triage labels — don't hand-roll
   them.** These three topics have a purpose-built setup flow; don't
   hand-author `docs/agents/issue-tracker.md`, `docs/agents/domain.md`,
   `docs/agents/triage-labels.md`, or the `## Agent skills` block yourself
   when a better tool exists for it.

   Check whether `/mattpocock-skills:setup-matt-pocock-skills` is available
   (look for it among your available skills). If it is, run it now. Hand it
   what you already learned in steps 1-2 — which file is authoritative,
   any existing `## Agent skills` content you found — so it doesn't re-ask
   what you already know, and let it own the actual file selection, the
   in-place-update-vs-duplicate logic, and the writes.

   **If it isn't installed**, do the equivalent by hand (remember the
   non-negotiable above while exploring):
   1. Explore: `git remote -v` (GitHub vs. GitLab), whether `CLAUDE.md` or
      `AGENTS.md` already exists, `CONTEXT.md`/`CONTEXT-MAP.md`,
      `docs/adr/`, `.scratch/`, whether a `triage` skill is installed, and
      monorepo signals (`pnpm-workspace.yaml`, a `workspaces` field, or
      populated `packages/*`).
   2. Ask, one topic at a time, leading with the recommended default:
      - **Issue tracker**: GitHub (if the remote points there) / GitLab (if
        the remote points there) / local markdown under
        `.scratch/<feature>/` / other (record as freeform prose).
      - **Triage labels** (only if a `triage` skill is installed): keep the
        five canonical defaults — `needs-triage`, `needs-info`,
        `ready-for-agent`, `ready-for-human`, `wontfix` — unless the user's
        tracker already uses different names.
      - **Domain docs**: default to single-context (`CONTEXT.md` +
        `docs/adr/` at the repo root); offer multi-context
        (`CONTEXT-MAP.md` + per-context `CONTEXT.md`) only if monorepo
        signals were found.
   3. Draft `docs/agents/issue-tracker.md`, `docs/agents/domain.md`, and
      (if applicable) `docs/agents/triage-labels.md`, plus the `## Agent
      skills` block for whichever root file already exists — never create
      the other one if one exists, and update an existing `## Agent
      skills` block in place rather than duplicating it. Show the drafts,
      let the user edit, then write.
6. **Rewrite the root file as an index**: essentials from step 3, plus a
   `## Guides` section linking every topic file with a one-line description
   of what's in it. Keep it short enough that a reader doesn't need to
   scroll.
7. **Flag, don't delete.** Instructions that read as redundant (the agent
   already knows this), too vague to act on, or generically obvious ("write
   clean code") get flagged in your final report as deletion candidates —
   leave them in the file. Deleting someone else's authored guidance isn't
   yours to decide; let the user choose.
8. **Verify zero content loss.** Run `git diff --stat` on the split and spot
   check with `grep` for a handful of distinctive phrases from the original
   to confirm they landed in the new files. Report the before/after line
   count of the root file.

## Phase 2: convert deterministic rules into PreToolUse hooks

Goal: policy that's phrased as "always use X, never bare Y" or "never run Z"
gets enforced automatically instead of relying on the agent remembering it
every session.

**Scope check — not everything is hookable.** Only convert rules that are:
- CLI-command shaped: "use `just fmt`, not bare `cargo fmt`"; "PR titles must
  match `<type>: [TICKET] description`"; "never run `terraform apply` without
  `-var-file=...`".

Do **not** try to hook rules that require judgment or reading file *content*
to evaluate (e.g. "never `unwrap()` outside tests", "member number must never
be logged"). A `Bash` PreToolUse hook only sees the command string being
run — it can't statically analyze what a diff does. Leave those as documented
policy the agent self-polices, or as file-path-based Edit/Write "ask" hooks
that prompt for review rather than trying to fully re-implement the rule (see
`references/hook-patterns.md` for that softer pattern).

Steps:

1. **List candidates.** Go through the (now-split, if Phase 1 ran) docs and
   pull out every CLI-policy rule that fits the scope check above.
2. **Confirm scope with the user before writing anything.** Present the
   candidate list via AskUserQuestion (multi-select) and implement only what
   they pick. Don't assume "convert everything" — some rules are deliberately
   left to judgment.
3. **Implement.** For each confirmed rule:
   - Add one script under `.claude/hooks/<rule-name>.sh`.
   - Register it in `.claude/settings.json` under
     `hooks.PreToolUse`, matcher `"Bash"`, pointing at
     `${CLAUDE_PROJECT_DIR}/.claude/hooks/<rule-name>.sh`. Multiple hooks can
     share one matcher block — append to the `hooks` array rather than adding
     a new matcher block per rule.
   - Read `references/hook-patterns.md` before writing the script — it has
     the exact stdin/exit-code contract, the BSD-grep portability rules
     (macOS's default `grep` doesn't support `\s`/`\b`), and the two script
     templates in `scripts/` to start from.
4. **Test exhaustively before calling it done**, per rule:
   - True positive: the exact command the rule bans → hook must exit 2 with
     a clear stderr message naming the allowed alternative.
   - True negative: the allowed alternative, and unrelated commands → hook
     must exit 0.
   - Dynamic-value edge case: if the rule inspects a flag value (e.g. a PR
     title) and the command builds that value via `$(...)`/backticks/a shell
     variable rather than a literal string, the hook can't know the real
     runtime value — it must pass (exit 0) rather than guess, since a false
     block on unparseable input is worse than a missed enforcement.
   - Build the test JSON with `jq -n --arg c "$COMMAND" '{tool_input:{command:$c}}'`,
     not string-interpolated literals — embedded quotes in the test command
     otherwise produce silently-malformed JSON and every test "passes" for
     the wrong reason.
5. **Report what got blocked vs. what still relies on judgment**, and give
   the user the one-line restart instruction (hooks load at session start,
   so an already-running session needs a restart to pick up new/edited
   hooks).

## Reference

- `references/hook-patterns.md` — the PreToolUse JSON contract, exit-code
  semantics, the softer "ask" pattern for Edit/Write hooks, and the BSD-grep
  gotchas. Read before writing a new hook script.
- `scripts/block-command-template.sh` — starting point for a hard-block rule
  ("always X, never Y").
- `scripts/enforce-format-template.sh` — starting point for a rule that
  validates a flag's *value* against a format (e.g. a title convention),
  including the dynamic-value skip logic from step 4 above.
