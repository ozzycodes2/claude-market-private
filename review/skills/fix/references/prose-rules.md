# Prose rules — documentation, and code comments

Two audiences, two sets of rules. §1 and §2 govern prose a reader chooses to
read: README sections, guides, ADRs, runbooks, doc comments. §3 governs comments
embedded in code, where the default action is **deletion**, not improvement.

## 1. Clarity — after Zinsser, *On Writing Well*

Ordered by yield. Each one is checkable: you can point at the words.

1. **Clutter.** Every word must do work. If removing a word does not change the
   claim, remove it. `at this point in time` → `now`. `in the event that` → `if`.
   `has the ability to` → `can`.
2. **Qualifiers.** Cut `very`, `rather`, `quite`, `pretty much`, `sort of`,
   `a bit`, `really`, `somewhat`. They dilute the sentence; they never
   strengthen it.
3. **Adverbs that repeat the verb.** `completely destroy`, `effectively
   prevents`, `tightly clenched`. The verb already said it.
4. **Passive to active.** Name the actor. `The token is validated by the
   handler` → `The handler validates the token`. Keep the passive only when the
   actor is genuinely unknown or irrelevant.
5. **Nominalizations back to verbs.** A noun ending in `-ion`, `-ment`, or
   `-ance` that carries the sentence's action belongs as a verb: `perform
   validation of` → `validate`; `make a determination` → `determine`; `provide
   assistance` → `help`.
6. **Short, concrete words over long Latinate ones.** `use` not `utilize`,
   `start` not `initiate`, `about` not `approximately`, `before` not `prior to`,
   `help` not `facilitate`.
7. **One thought per paragraph.** When a paragraph turns, start a new one.
8. **The lead is the most important sentence.** State the point first; a reader
   who stops after one sentence should still have the gist.
9. **Do not announce what you are about to say.** Delete `This section
   describes…`, `It is worth noting that…`, `In order to understand X, we must
   first…`. Say the thing.
10. **Rewriting is the essence.** The first draft of the replacement is not the
    replacement. Read it back and cut again.

## 2. House voice

Adapted from the `laconic` output style in the `technical-writing` plugin (MIT).
Inlined rather than read across plugins, so this skill works in any repository
with no other plugin installed.

- **Length tracks decision content, not effort.** Keep a fact only if a reader
  would otherwise ask about it, if it asks something of them, or if it answers a
  question the code cannot.
- **Strip leaked frames.** Prose that describes the conversation rather than the
  subject: `as discussed`, `per the ask`, `the task said`, `Phase 2`, `Option C`,
  run IDs, `correcting my earlier note`. They do not merely fail to inform — the
  reader tries to resolve a reference they cannot reach and cannot tell whether
  they are missing something that matters. They are invisible from the inside,
  so check for them deliberately.
- **The reader was not in the room.** Write the conclusion, not the path to it.

| Leaked frame | Write instead |
|---|---|
| "As discussed, we chose X" | Why X. |
| "The review flagged this" | The constraint itself. |
| "Correcting the above…" | The final position, once. |

## 3. Code comments

**Delete by default.** A comment the code already demonstrates is noise: it
duplicates the code, and it rots independently of it. Deleting it is the fix.
Shortening it is not.

Keep a comment only when it says something the code cannot:

- **Why** a non-obvious choice was made, where the obvious alternative looks
  better at a glance.
- An **external constraint** — a vendor bug, a protocol quirk, a spec section, a
  wire-format requirement.
- A **measured fact** — a benchmark result, an empirical limit, a tuned value.
- A **security or concurrency invariant** a caller must preserve.
- A **non-obvious algorithm's** invariant, or its citation.
- A **tracked** `TODO(<TICKET>)` — with a real ticket, not a bare `TODO`.
- License headers, codegen markers, lint pragmas.

### Rules

- **Never narrate the next line.** `// increment counter` above `n += 1` is pure
  noise. Comment the decision or the trap, not the mechanics.
- **Doc comments say what the signature cannot.** Do not restate the name, the
  parameters, or the return type. Answer the caller's real questions: when to
  call it, what it mutates, how it fails and what to do about that, the usual
  call sequence.
- **Correct a stale comment from the code it describes** — never from the file
  name, the function name, or the variable names. Those are what went stale.
- **Never silently delete a comment that names an unfixed defect.** If the defect
  is in scope, fix it and route the finding as a repair. If it is not, leave the
  comment and defer. This skill does not file tickets.
- **Never comment your own change.** No `// fixed`, no `// now handles the edge
  case`, no address to a reviewer. That is the commit message's job.
- **Match the file's comment density.** A sparse file stays sparse. Do not
  introduce a house style the surrounding code does not have.
- **Delete commented-out code.** Do not leave it, and do not re-comment it.
- Markdown files are §1 and §2's business, not §3's.

## 4. Scope of a prose edit

**Rewrite the flagged line and the paragraph containing it. No further.**

One finding becomes one commit, so the diff has to map to the finding. Clutter
elsewhere in the same file that the review did not flag stays — it is not this
commit's business, and sweeping it in makes the commit unreviewable.

### Preserve the claim

The sharpest risk in this whole strategy. "Every word must work" invites deleting
a qualifier that was load-bearing: `usually`, `on the primary path`, `only when
the cache is cold`, `for self-hosted installs`. Cutting one of those does not
tighten the sentence — it makes it false.

- Preserve the paragraph's **proposition**. Shorter, not different.
- **Exception:** for a drift finding, the proposition is *supposed* to change —
  anchor the new one to `extra.code_says`, which is what the code actually does.
- Report the before and after claim, one line each. If the meaning changed and
  the finding was not a drift finding, that is a deferral, not a commit.

## 5. Out of scope

- **Spelling and dead links.** Repositories that care about these mechanize them
  in CI, and re-litigating them by hand fights the configuration and produces
  churn. Out of scope whether or not such a check exists here.
- **Generated artifacts.** Anything whose `drift_class` is `rendered-lag` must be
  **regenerated**, never hand-edited — the next generator run would revert the
  edit. Route it to the regenerate strategy; if no regeneration command can be
  found, defer and say so.
- **Reflowing or reformatting** a file the finding did not flag.
