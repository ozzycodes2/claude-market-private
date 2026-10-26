# technical-writing

Human-facing developer writing, done well: draft a doc, score it, fix it. Four
skills form one pipeline, plus the `laconic` output style.

```
write-doc / writing-design-docs  ->  review-doc  ->  fix-doc
```

## Install

```
/plugin install technical-writing@claude-market-private
```

## Skills

| Skill | Stage | What it does |
|-------|-------|--------------|
| `write-doc` | Write | Drafts a README, ADR, runbook, tutorial, how-to, explanation, or reference doc from a Diataxis template. Edits nothing existing. |
| `writing-design-docs` | Write | Drafts a problem-statement design doc one section at a time, before you commit to a non-obvious technical direction. Covers RFCs and design docs, which `write-doc` leaves out. |
| `review-doc` | Review | Read-only. Scores a doc on the 20 Practical Prose dimensions and emits a Scores table and a Findings table. Each finding is `apply`, `flag`, or `diagram`. |
| `fix-doc` | Fix | Applies the `apply` findings, generates the `diagram` findings, lists the `flag` findings for the author without rewriting them, then runs an AI-tell pass last. |

Each stage ends by offering the next. Skills are also callable alone, for
example `/technical-writing:review-doc docs/runbook.md`.

### write-doc

Picks the doc type (or takes one, such as "type ADR"), follows the repo's
existing doc layout and naming, fills the template from the code and
conversation, and deletes sections that add nothing. It never invents a fact to
fill a section. Output is Markdown; Notion only on explicit request, after
confirming.

### writing-design-docs

Walks six sections in order: problem statement, background, project values,
options, recommendation, open questions. Leads with the problem, not the
solution. Ships `template.md`. Offers `review-doc` when the draft is complete.

### review-doc

Takes a file or pasted text and changes nothing. Every score below 5 cites the
guideline rule missed. Findings are classed `apply` (safe, meaning-preserving),
`flag` (needs the author or new facts), or `diagram` (a figure to add). Refuses
generated files (`DO NOT EDIT`, `@generated`) and names the generator instead.

### fix-doc

Modifies the target. Runs `review-doc` first if no findings are in the
conversation. With `findings-only` (for example from `review:fix`) it applies
only the rows it is given. Leaves code blocks, link targets, citations, and YAML
frontmatter untouched. For pasted text it returns the edited text and writes no
file. Reports counts of applied, generated, and flagged items.

## Diagrams

When a doc describes structure, flow, states, or more than three interacting
components, the skills add a diagram. If `architecture-design` is installed,
`create-diagram` draws it as `.html` plus `.png`. Without it, the diagram is a
fenced Mermaid block. `architecture-design` is optional. The rule lives in
`references/diagrams.md`.

## Output styles

| Style | What it does |
|-------|--------------|
| `technical-writing:laconic` | Terse, salient prose for anything read by someone who was not in the room: comments, PR bodies, review replies, commit messages. Names the "leaked frame" failure mode and what to write instead. |

Select it with `/output-style technical-writing:laconic`, or make it the default
by setting `"outputStyle": "technical-writing:laconic"` in `settings.json`.

## Attribution

Full notices, pinned commits, local edits, and upstream license texts are in
[NOTICE.md](NOTICE.md).

- `writing-design-docs` is adapted from [ceejbot/ceej-skills](https://github.com/ceejbot/ceej-skills)
  by [ceej](https://blog.ceejbot.com), under the MIT license.
- The `laconic` output style is copied verbatim from
  [chrisdickinson/pertinent](https://github.com/chrisdickinson/pertinent)
  (`styles/laconic/style.md`) by Chris Dickinson, under the MIT license.
- The review rubric and guidelines in `references/` derive from
  [jlevy/practical-prose](https://github.com/jlevy/practical-prose) by Joshua Levy
  (prose under CC BY 4.0).
- The AI-tell checklist in `references/ai-tells.md` derives from
  [blader/humanizer](https://github.com/blader/humanizer) by Siqi Chen, merged
  with Practical Prose's AI-prose corrections.

## License

MIT — see the marketplace [LICENSE](../LICENSE).
