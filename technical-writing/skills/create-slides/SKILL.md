---
name: create-slides
description: Use when the user asks for a slide deck, presentation, talk, or slides from a document, report, PR, notes, or topic. Builds one self-contained Machinify-branded HTML deck in a minimalist style, with headline-plus-visual slides, speaker notes, and every diagram drawn by architecture-design:create-diagram.
---

# Create Slides

Turn content into a minimalist Machinify HTML deck: one claim and one visual
per slide, prose in the speaker notes. The output is a single `index.html`
that opens from disk, navigates with the keyboard, and prints one slide per
page.

References, relative to this skill:

- `references/minimalism.md`: the slide rules. Read it before drafting.
- `references/brand.md`: colors, type, fixed elements, icons.
- `assets/deck-template.html`: the slide catalogue to build from.
- `assets/machinify.diagram-profile.md`: the create-diagram skin for slides.
- `scripts/check_deck.py`: the rule checker.

## Requirement

Diagrams come only from the `architecture-design:create-diagram` skill. If
it is not installed, stop and tell the user to install the
`architecture-design` plugin. Do not hand-draw SVG, build diagrams from HTML
boxes, or fall back to Mermaid.

## Workflow

### 1. Intake

Read the source first: a file, a PR, a report, notes, or a topic. Then ask
only for what the source does not answer:

- **Audience** and what they should do or believe afterwards.
- **Duration.** Plan about one slide per two minutes, plus title and closing.
- **Ground.** Light (default) or dark content slides.
- **Output directory.** Default: a new directory named after the deck, next
  to the source.

### 2. Storyline and outline approval

Write one claim per slide, in the order the argument needs. A claim is a
sentence the audience could disagree with: "Tests own 70% of build time", not
"Build time". Then pick the visual that shows the claim:

| The claim is about | Visual |
|---|---|
| Relationship, flow, structure, sequence, state, time, comparison, distribution, ranking, hierarchy | Diagram via create-diagram, which picks the type |
| One number | `big-number` |
| Three or four numbers | `stat-strip`, one marked `focus` |
| Three parallel concepts | `icon-trio` |
| One idea that needs no picture | `statement` slide |

There is no bullet-list slide. If a claim seems to need bullets, it is a
diagram, several slides, or speaker notes.

Present the outline as a table and wait for approval before building:

| # | Layout | Eyebrow | Headline | Visual |
|---|---|---|---|---|
| 1 | title | CI review | Faster builds by **Q3** | — |
| 2 | content | CI | Tests own 70% of build time | bar chart: stage durations |

Iterate on the table, not on built slides.

### 3. Diagrams

Prepare the profile once per deck:

1. If `~/.diagram-design/profiles/machinify.md` is missing, copy
   `assets/machinify.diagram-profile.md` there. If it exists and differs from
   the bundled copy, show the difference and ask before replacing it.
2. Write `<deck-dir>/.diagram-design` containing exactly `profile: machinify`.
   If the deck directory sits inside a git repository whose root has no
   marker, ask before writing one at the repository root, since it would
   reskin every diagram in that repository. If an existing marker names
   another profile, ask before changing it.

For each diagram slide, invoke the `architecture-design:create-diagram` skill
from the deck directory, one diagram per call, with:

- **The claim** the diagram must show, and the source facts behind it.
- **Size preset `slide-body`**: the viewBox is `0 0 1104 520`, there is no
  title or eyebrow inside the SVG, and there is no footer reserve.
- **Profile `machinify`**, light or dark to match the slide.
- **Detail `simplified`** and **audience `executive`** unless the audience is
  engineers, then `balanced` and `mixed`.
- **Output** `<deck-dir>/diagrams/<slug>.html`, with a slug that describes
  the diagram.

Let create-diagram choose the diagram type and run its own checks. Then
export and inline:

```bash
python3 <create-diagram-dir>/scripts/export_svg.py <deck-dir>/diagrams/<slug>.html --system-fonts
```

Paste the resulting `<svg>` element into the slide's `.visual.dgm` div. Drop
the `<?xml ...?>` line. Keep the diagram HTML next to the deck; it is the
source to edit later.

### 4. Assemble

Copy `assets/deck-template.html` to `<deck-dir>/index.html`. Keep the slide
blocks the outline needs, in outline order, and delete the rest. For each
slide:

- Set the eyebrow (1–3 words) and the headline (7 words or fewer, one
  `<strong>` phrase at most).
- Fill the one visual.
- Put everything else in `<aside class="notes">`: explanation, sources,
  caveats, numbers behind the numbers.
- Add class `dark` to a content slide to put it on teal.

Do not add footers, page numbers, or nav dots; the template's script
generates them. Do not add CSS colors; use the template's variables.

### 5. Check

```bash
python3 <this-skill-dir>/scripts/check_deck.py <deck-dir>/index.html
```

It prints JSON and exits 1 on findings. Fix every finding by cutting, moving
text to notes, or re-requesting the diagram, never by loosening a rule. Then
review what the checker cannot see, from `references/minimalism.md`: one
accent per slide, whitespace left empty, labels that are two to four words.

Report the deck path, the slide count, and the diagram files. Mention that
`N` toggles speaker notes and `F` toggles full screen.

## Revising a deck

Edit the outline first when the change moves the argument. Re-run the
diagram step only for diagrams whose claim changed, then re-export, re-inline,
and re-run the checker.
