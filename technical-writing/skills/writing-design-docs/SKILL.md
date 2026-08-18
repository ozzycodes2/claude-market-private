---
name: writing-design-docs
description: Use when the user wants to write a problem-statement design doc, says "let's plan a feature properly" / "write a design doc" / "I'm thinking about how to do X" for a non-trivial X, or before committing to a non-obvious technical direction
---

# Writing Design Docs

Helps draft a problem-statement design doc — the kind whose value comes from the writing process itself, not the artifact. The act of writing exposes knowledge gaps and forces you to articulate values; readers then have something concrete to push back on.

**Core principle:** lead with the problem, not the solution. A doc that opens with "we'll use Tool X" has skipped the work that makes the rest of the doc trustworthy.

Source: <https://blog.ceejbot.com/posts/design-docs/>.

## When to use

- Non-trivial technical direction needs choosing.
- More than one person (or the user with their future self) needs to share understanding.
- Tradeoffs are not obvious and would otherwise devolve into a preference argument.
- Before committing to a path you'd be reluctant to walk back.

**Skip if:** the work is small enough that "just do it" is the right answer, or the path is genuinely obvious.

## The six components

Walk these in order. Don't skip ahead.

### 1. Problem statement
- What's broken or missing in the current system?
- What behaviour change is wanted?
- What does success look like — measurable, ideally?
- Explicitly: what are we **not** addressing?

### 2. Background and research
- How does the existing system actually work today?
- What did investigation turn up — quantifiable where possible (scale, growth rate, failure mode, constraint)?
- Written so a reader unfamiliar with this corner of the system can follow the rest of the doc.

### 3. Project values
- The rubric. Resilience, delivery speed, privacy, cost, simplicity, maintainability, blast radius — pick the few that matter for this decision.
- Without stated values, the options-comparison section becomes "I prefer X" vs "I prefer Y".

### 4. Options considered
- 2–3 serious alternatives.
- For each: how it works, what it costs, how it scores against the values from §3.
- If only one option exists, explain why — what was ruled out, on what grounds.
- Honest tradeoffs. If an option has a real downside, name it.

### 5. Recommended solution with rationale
- The choice, plus reasoning that traces back to the values.
- A reader with **different** value priorities should see how their conclusion would differ. Make the reasoning legible enough to be argued with.

### 6. Open questions
- Known unknowns.
- Decisions deferred and why.
- Areas needing more research.
- Surfacing these is a strength, not a weakness — they're where readers can help most.

## Process

Move through stages, not all at once:

1. **Personal research** — fill in §1, §2, §3 alone. Get the problem clear before talking to anyone.
2. **1–2 trusted advisors** — pressure-test the framing and values before going wider.
3. **Domain expert review** — for areas you don't own.
4. **Stakeholder preview** — people whose work this affects.
5. **Wider audience** — only after the doc has survived the prior stages.

Each stage finds different gaps. Skipping stages means you find them all at once, in front of the wrong audience.

## Pitfalls

| Pitfall | What goes wrong | What to do instead |
|---|---|---|
| Solution-first writing | Doc opens with "use Tool X" without evaluation criteria. Reviewers can only nod or push back without ammunition. | Write §1–§3 *before* allowing yourself to name a tool. |
| Missing reasoning | States the choice but not *why* it follows from the values. Reads as opinion. | Every recommendation traces back to a value in §3. |
| Unstated values | §3 is skipped or vague. Tradeoff debates become preference fights. | Write values explicitly. If reviewers disagree on values, surface that *first*. |
| Approval-seeking | Polishing until the doc looks confident. Open questions disappear. | Keep §6 honest. A doc with open questions invites help; a doc without them invites rubber-stamping. |

## Output

Use the template at `template.md` in this skill directory. Drop it into the project as `docs/design/<topic>.md` (or wherever the project keeps design docs) and fill it in stage by stage.

When drafting interactively with the user, work one section at a time — don't generate the whole doc in one shot. The shared understanding *is* the value, and it only forms through the conversation.

## Anti-patterns when drafting

| Don't | Why |
|---|---|
| Generate all six sections at once | The writing process is the point. Draft §1, confirm, then §2, etc. |
| Hand-wave §3 (values) | Without values, §4 and §5 collapse into preference. |
| Hide the recommendation in §1 | "We're going to do X" before §2–§4 means everything after is post-hoc rationalization. |
| Skip §6 to look confident | Honest open questions invite help. Polished docs invite rubber-stamping. |
| Use "we should" without saying *why we should* | The why is the doc's whole reason for existing. |
