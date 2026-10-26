---
name: write-doc
description: Use when the user asks to write or draft a README, ADR, runbook, tutorial, how-to, explanation, or reference doc, or a caller passes "type ADR" or "type README". Picks the type, fills a template, adds diagrams. RFCs and design docs belong to writing-design-docs.
---

# Writing Docs

Generate stage of generate, review, fix. Draft one doc from a template, then hand it to `review-doc`.

Supported types: README, ADR, runbook, tutorial, how-to, explanation, reference. RFCs and design docs are out of scope: use `writing-design-docs`.

References, relative to this skill:

- `../../references/common-doc-guidelines.md`: structure, naming, style, and Markdown formatting.
- `../../references/diagrams.md`: when and how to produce a diagram, tool choice, placement.

## Types

Templates live in `templates/`. The Diataxis types differ by what the reader needs, so do not mix them in one doc.

| Type | Template | Reader need |
|---|---|---|
| README | `templates/readme.md` | Orientation: what this is, how to start, where to go next |
| ADR | `templates/adr.md` | A recorded decision and why it was made |
| Runbook | `templates/runbook.md` | Operational steps under pressure, with checks and rollback |
| Tutorial | `templates/tutorial.md` | Learning-oriented: a newcomer gains skill by doing |
| How-to | `templates/how-to.md` | Task-oriented: a competent user reaching a goal |
| Explanation | `templates/explanation.md` | Understanding-oriented: why and context |
| Reference | `templates/reference.md` | Information-oriented: accurate lookup |

## Steps

1. **Pick the type.** If the caller supplied one (for example "type ADR"), use it and skip this question. Otherwise infer it from the request and ask only if two types fit. If the request is an RFC or design doc, switch to `writing-design-docs`.
2. **Follow the repo's existing doc layout and naming.** Look for a `docs/` directory, sibling docs of the same type, and filename conventions before choosing a path. ADRs default to `docs/adr/NNNN-slug.md`, numbered by scanning the directory for the highest number and adding one. Create the directory only when the first doc needs it.
3. **Fill the template** per `../../references/common-doc-guidelines.md`. Gather facts from the code, config, and conversation. Delete sections that add nothing; never invent a fact to fill one. Ask for what is missing.
4. **Add diagrams** per `../../references/diagrams.md` when the doc describes structure, flow, or state.
5. **Produce Markdown.** Write to Notion only on explicit request, after confirming.
6. **End with** "Run `review-doc` on it?"
