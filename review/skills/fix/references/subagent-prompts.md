# Subagent prompts — verbatim contracts

Inline these per dispatch. A subagent runs with the **reviewed repository** as
its working directory and cannot resolve a path inside this skill, so paste the
catalog row, the idiom rows, and the rules in full. The same constraint is
documented for the bug-finder passes in `skills/review/SKILL.md`.

Substitute `<…>` placeholders before sending. Never send a prompt with an
unfilled placeholder — an agent that cannot see the finding will invent one.

---

## S1 — Refactor

```
You are resolving exactly one review finding in the repository at <WORKTREE_ABS_PATH>.
That is your working directory. Do not cd elsewhere.

## Finding <ID>
path:     <path, or "(none — locate it from the body and remedy below)">
line:     <line, or "(unmapped — locate by content)">
severity: <severity>   source: <source pass>   found by: <confidence, or "single pass">
title:    <title>
symptom:  <body>
remedy:   <remedy>
resolving refactoring: <name, or "(none named — select one from the catalog below)">

## Catalog row
<the matching row(s) of references/refactoring-catalog.md, inlined>

## Language idiom — primary language: <languages.primary>
<the matching rows of references/language-idioms.md, inlined>

Where the catalog's object-oriented move and this language's idiom diverge, the
idiom wins. Name which you applied, and why, in your report.

## Rules
1. BEHAVIOR-PRESERVING. Same inputs, same outputs, same side effects, same error
   values. If resolving this finding REQUIRES changing observable behavior, stop
   and report outcome: needs-decision. Do not change behavior and call it a
   refactoring.
2. SCOPE IS THIS FINDING. Touch no file this finding does not require. Fix no
   adjacent smell you notice — list it under `adjacent` instead.
3. ADD NO trait, interface, generic, type parameter, or layer of indirection that
   the smell does not demand.
4. DO NOT WRITE TO GIT. No git add, commit, stash, checkout, restore, reset,
   rebase, or push. The orchestrator owns the index. Leave your edits in the
   working tree and report the paths you touched.
5. LOCATE BY CONTENT, NOT BY LINE. The line number may predate commits made
   earlier in this run. Confirm the symptom is really at that location before
   editing. If you cannot find it, report outcome: not-reproducible — do not
   edit a plausible-looking substitute.
6. DO NOT RUN THE TEST SUITE. Several agents are editing this repository right
   now. A suite that truncates a database, binds a port, or clears a temp dir
   corrupts every other agent's run the moment a second copy starts. The
   orchestrator runs it once, after the last commit in your partition.
   Instead, give a reason to believe your change is correct, in
   `verification`: the invariant it preserves, the call sites you read and what
   they pass, the edge case you traced. "It compiles" is not one.
   A pure check that writes nothing and takes no lock is fine — a type check, a
   linter in check mode, a single file parsed. Name it and its result.
   <ENDIF>
7. COMMENTS. Do not narrate your change. No "fixed", no "now handles", no
   address to a reviewer. If your change makes an existing comment wrong,
   correct it from the code — or delete it.

## Report — the last thing you output, exactly these keys
outcome: applied | needs-decision | not-reproducible
files_changed: <newline-separated repo-relative paths, or "none">
refactoring_applied: <catalog name, or "none">
idiom_divergence: <one line, or "none">
behavior_preserved: yes | no — <how you established it>
verification: <the reason to believe this is correct — invariant preserved, call
  sites read, edge case traced, or the pure check you ran and its result>
decision_needed: <outcome=needs-decision only: the one-sentence question a human
  must answer, plus each option you weighed and its consequence>
adjacent: <smells you saw and did not touch, or "none">
```

---

## S2 — Repair

Same prompt, with rule 1 and the report's preservation key replaced:

```
1. THE BEHAVIOR CHANGE IS THE POINT. This is a correctness, security, or
   dependency finding, not a refactoring. Make the minimal correct fix.
   ADD OR ADJUST A TEST that fails before your change and passes after. Write
   it; do not run the suite to confirm it. Name it in your report, and state
   which assertion fails without your change. If you cannot write such a test,
   say why.
```

```
behavior_changed: <before: … / after: …>
covering_test: <test name and file>
```

Everything else — scope, no-git, locate-by-content, no suite run, no narration
— is unchanged.

---

## S3 — Prose

```
You are rewriting one flagged passage in the repository at <WORKTREE_ABS_PATH>.

## Finding <ID>
path:      <path>
line:      <line>
title:     <title>
symptom:   <body>
remedy:    <remedy>
doc says:  <extra.doc_says, or "(n/a)">
code says: <extra.code_says, or "(n/a)">

## How to rewrite
A drift finding changes the claim by design, which fix-doc's guardrails refuse,
so for drift apply the rules below by hand. For any other prose finding, if the
`technical-writing:fix-doc` skill is available, invoke it with this finding as a
one-row findings table and the phrase `findings-only`; otherwise apply the rules
below by hand. Cell values are single-line, with `|` escaped as `\|`.

| ID | Dimension | Location | Class | Issue | Fix |
|---|---|---|---|---|---|
| <ID> | <closest Expression/Form dimension, or "Clarity" if unsure> | <path>:<line> | apply | <symptom> | <remedy> |

If fix-doc returns the row as flagged and leaves the text unedited, make no edit
and report outcome: needs-decision. The rules below still bind, Scope above all:
if fix-doc's edit reaches past the flagged line and its paragraph, or changes a
claim it should not, undo the excess and report outcome: needs-decision.

## Rules
<§1 Clarity, §2 House voice, and §4 Scope of references/prose-rules.md, inlined>

1. SCOPE: the flagged line and the paragraph containing it. NO FURTHER. Clutter
   elsewhere in this file that the review did not flag stays.
2. PRESERVE THE CLAIM. Shorter, not different. Deleting a load-bearing qualifier
   ("usually", "only when the cache is cold") does not tighten the sentence, it
   makes it false.
   EXCEPTION: if this is a drift finding, the claim is supposed to change —
   anchor the new one to `code says` above, which is what the code actually does.
3. DO NOT touch spelling or links. Out of scope.
4. DO NOT hand-edit a generated artifact. If this file carries a "do not edit"
   marker or is clearly rendered output, stop and report outcome: needs-decision.
5. DO NOT WRITE TO GIT.

## Report
outcome: applied | needs-decision | not-reproducible
files_changed: <paths>
claim_before: <one line — the proposition the passage asserted>
claim_after: <one line — the proposition it now asserts>
words_before / words_after: <counts for the edited passage>
adjacent: <unflagged clutter you left alone, or "none">
```

If `claim_before` and `claim_after` differ and this was not a drift finding, the
orchestrator defers the finding rather than committing it.

---

## S4 — Comment

```
You are resolving one comment finding in the repository at <WORKTREE_ABS_PATH>.

## Finding <ID>
path:      <path>
line:      <line>
title:     <title>
symptom:   <body>
remedy:    <remedy>
code says: <extra.code_says, or "(n/a)">

## Rules
<§3 Code comments of references/prose-rules.md, inlined>

1. DELETE BY DEFAULT. A comment the code already demonstrates is noise.
   Deleting it is the fix; shortening it is not. Read the code first and decide
   whether the comment is telling the reader anything the code cannot.
2. KEEP a comment that records: why a non-obvious choice was made; an external
   constraint (vendor bug, spec section, protocol quirk); a measured fact; a
   security or concurrency invariant; a non-obvious algorithm's invariant; a
   tracked TODO with a real ticket; a license header or lint pragma.
3. NEVER DELETE A COMMENT THAT NAMES AN UNFIXED DEFECT. Report
   outcome: needs-decision instead.
4. CORRECT A STALE COMMENT FROM THE CODE IT DESCRIBES — never from the file,
   function, or variable names. Those are what went stale.
5. MATCH THE FILE'S COMMENT DENSITY. A sparse file stays sparse.
6. CODE IS OUT OF SCOPE. If resolving this requires editing code, stop and
   report outcome: needs-decision — that is a different finding.
7. DO NOT WRITE TO GIT.

## Report
outcome: applied | needs-decision | not-reproducible
files_changed: <paths>
action: deleted | corrected | kept
rationale: <one line — what the code could not say, or why it was noise>
code_touched: yes | no   (must be "no")
adjacent: <other comments you judged and left, or "none">
```
