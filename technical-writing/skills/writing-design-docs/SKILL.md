---
name: writing-design-docs
description: Use when the user wants to write a problem-statement design doc, says "let's plan a feature properly" / "write a design doc" / "I'm thinking about how to do X" for a non-trivial X, or before committing to a non-obvious technical direction
---

# Writing Design Docs

Draft a problem-statement design doc — value comes from the writing process itself, not the artifact. Writing exposes knowledge gaps and forces you to articulate values; readers then have something concrete to push back on.

**Core principle:** lead with the problem, not the solution. A doc opening with "we'll use Tool X" has skipped the work that makes the rest trustworthy.

Source: <https://blog.ceejbot.com/posts/design-docs/>.

## When to use

- Non-trivial technical direction needs choosing.
- More than one person (or the user with their future self) needs shared understanding.
- Tradeoffs are not obvious and would otherwise devolve into a preference argument.
- Before committing to a path you'd be reluctant to walk back.

**Skip if:** work is small enough that "just do it" is right, or the path is genuinely obvious.

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
- Written so a reader unfamiliar with this corner can follow the rest.

### 3. Project values
- The rubric. Resilience, delivery speed, privacy, cost, simplicity, maintainability, blast radius — pick the few that matter for this decision.
- Without stated values, the options comparison becomes "I prefer X" vs "I prefer Y".

### 4. Options considered
- 2–3 serious alternatives.
- For each: how it works, what it costs, how it scores against §3 values.
- If only one option exists, explain why — what was ruled out, on what grounds.
- Honest tradeoffs. If an option has a real downside, name it.

### 5. Recommended solution with rationale
- The choice, plus reasoning tracing back to the values.
- A reader with **different** value priorities should see how their conclusion would differ. Make the reasoning legible enough to be argued with.

### 6. Open questions
- Known unknowns.
- Decisions deferred and why.
- Areas needing more research.
- Surfacing these is a strength, not a weakness — where readers help most.

## Process

Move through stages, not all at once:

1. **Personal research** — fill in §1, §2, §3 alone. Get the problem clear before talking to anyone.
2. **1–2 trusted advisors** — pressure-test framing and values before going wider.
3. **Domain expert review** — for areas you don't own.
4. **Stakeholder preview** — people whose work this affects.
5. **Wider audience** — only after the doc survives the prior stages.

Each stage finds different gaps. Skipping stages means finding them all at once, in front of the wrong audience.

## Pitfalls

| Pitfall | What goes wrong | What to do instead |
|---|---|---|
| Solution-first writing | Doc opens with "use Tool X", no evaluation criteria. Reviewers can only nod or push back without ammunition. | Write §1–§3 *before* naming a tool. |
| Missing reasoning | States the choice but not *why* it follows from the values. Reads as opinion. | Every recommendation traces back to a §3 value. |
| Unstated values | §3 skipped or vague. Tradeoff debates become preference fights. | Write values explicitly. If reviewers disagree on values, surface that *first*. |
| Approval-seeking | Polishing until the doc looks confident. Open questions disappear. | Keep §6 honest. A doc with open questions invites help; one without invites rubber-stamping. |

## Output

Use the template at `template.md` in this skill directory. Drop it into the project as `docs/design/<topic>.md` (or wherever the project keeps design docs) and fill in stage by stage.

When drafting interactively, work one section at a time — don't generate the whole doc in one shot. The shared understanding *is* the value, and it forms only through the conversation.

## Anti-patterns when drafting

| Don't | Why |
|---|---|
| Generate all six sections at once | The writing process is the point. Draft §1, confirm, then §2, etc. |
| Hand-wave §3 (values) | Without values, §4 and §5 collapse into preference. |
| Hide the recommendation in §1 | "We're going to do X" before §2–§4 makes everything after post-hoc rationalization. |
| Skip §6 to look confident | Honest open questions invite help. Polished docs invite rubber-stamping. |
| Use "we should" without saying *why we should* | The why is the doc's whole reason for existing. |
