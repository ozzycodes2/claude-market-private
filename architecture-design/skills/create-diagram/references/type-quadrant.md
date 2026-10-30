# Quadrant

**Best for:** prioritization (Impact × Effort), positioning (Reach × Frequency), portfolio maps, 2×2 decision frames.

## Layout conventions
- 2×2 grid. Axis lines: 1px ink cross through the center.
- **Axis labels: Jobs-minimal.** One single word at each arrow tip — no glyphs baked into the label (no `↑` / `→` / `←` / `↓`), no parentheticals, no "high / low" modifiers. `eyebrow` role at 9px regular weight, sentence case, no tracking ("Effort", "Impact"). The word sits at the tip where the quantity rises; the source line says which way it rises. Flank the arrow tips — never sit labels on top of the axis line. Shorten the arrow enough (~60–80px inside the viewBox edge) to leave breathing room for the labels beyond the tips.
- Never label at the midpoint.
- **Quadrant names** (corner labels) are sentence case, 9px mono, no tracking ("Do first", "Quick wins").
- **Positions are judged or measured, and the source line says which.** Judged: origin and period first (`Source: team judgement, Q3 2026 content planning.`), then "Positions are team estimates, not measurements." Measured: name the metric, its unit and the period. Without that line the reader takes a point cloud for data.
- **Title is the claim** (`Start with Schematic skill v4: high impact, low effort`, under about 60 characters); `<desc>` opens with it. The source line is `data-role="source"`, starting `Source: `, with a second line as a `<tspan x dy="12">` for axis direction. The consultant variant carries the same one-line source and claim title.
- **No legend.** Name the focal item in place (a short `muted` mono label beside it, e.g. "Start tomorrow"); ordinary dots need no key. A sentence-case `muted` source line sits bottom-left and states the direction of each axis and how positions were set.
- **Context rule exception:** a quadrant's axis cross is its own comparison (quadrant versus quadrant); no extra reference line is drawn.
- Items: small labeled dots (`r=4`) positioned in the quadrants. Labels 8–10px away; don't let labels cross axis lines.
- The accent on the "do first" item (typically top-right).
- Limit to ~12 items; cluster or split beyond that.

## Anti-patterns
- Four filled quadrants in different colors — position + label does the work; color noise weakens it.
- Items placed on axis lines (ambiguous quadrant).
- Missing axis names.

## Examples
- `assets/example-quadrant.html` — minimal light
- `assets/example-quadrant-dark.html` — minimal dark
- `assets/example-quadrant-full.html` — full editorial
- `assets/example-quadrant-consultant.html` — consultant special (see below)

---

## Consultant special (2×2 scenario matrix)

A **layout variant** of the standard quadrant — same house skin (near-white paper, `title` at a larger Inter step, mono `eyebrow`s, one accent focal). The grammar shifts: axes hold a **range** rather than a measurement; cells hold **named scenarios** rather than positioned items.

**Use when:** you're framing four futures, archetypes, or strategic options across two independent drivers — classic scenario planning, positioning frames, or 2×2 strategy decks (BCG/McKinsey territory). The reader should come away with four named bets, not a point cloud.

**Do not use** for prioritization, density maps, or anything where the *position inside* a cell carries meaning — that's the standard quadrant above.

### What makes it the consultant variant

| Move | Standard quadrant | Consultant special |
|---|---|---|
| Axis arrows | single-ended | **double-ended** — both axes have `marker-start` + `marker-end` |
| Cell content | small dots with labels | **named scenario + 1–3 line description** |
| Quadrant corner | short tag (e.g. Do first) | **numbered tag + axis combination** (`01 · Dimension-a / dimension-b`) |
| Focal accent | accent on one *item* | accent on one *quadrant* — tinted bg + accent stroke + ink corner tag, its label still ink |
| Axes | 1px muted ink | **1.2px ink** (slightly heavier — the axes carry more of the figure) |

Both variants use the same Jobs-minimal axis labels: one word at each arrow tip, no glyphs, no parentheticals. The only axis difference is that the consultant variant uses double-ended arrows instead of single-ended.

Everything else — paper, typography, legend strip, 4px grid, complexity budget — is the house default. Don't invent new colors or fonts for this variant.

### Style tokens (in-house)

- **Paper / bg**: `paper` from `style-guide.md`, solid across the full viewBox.
- **Axis lines**: `ink`, `stroke-width: 1.2`, `marker-start` + `marker-end` both pointing outward.
- **Focal quadrant tint**: `accent @ 0.04` full rect behind the focal cell.
- **Focal cell**: `accent-tint` fill, `accent` stroke at 1.2px. Corner tag in `ink`, weight 600 (accent paints objects, never text).
- **Non-focal cells**: `store` treatment (`ink @ 0.04` fill, `muted @ 0.28` stroke).
- **Cell title**: `node-name` role, 16px, weight 600, `ink`.
- **Cell description**: `node-name` role, 11px, `muted`, 1–3 lines, left-aligned inside the cell.
- **Corner tag**: `eyebrow` role, 8px, sentence case, no tracking, `muted` (or `ink` on focal). Format: `NN · Remote / human` — the two axis-dimension words must match the axis labels exactly, case included.
- **Axis labels**: `eyebrow` role 9px **regular weight** (not bold), sentence case, no tracking, `ink`. **One word per tip.** No arrow glyphs in the label, no `HIGH / LOW` parentheticals, no multi-line sublabels. The word itself *is* the label. Position labels *beyond* the arrow tips (not on the axis line):
  - Top tip: `text-anchor="middle"`, ~12px above the arrow tip
  - Bottom tip: `text-anchor="middle"`, ~20px below the arrow tip
  - Left tip: `text-anchor="end"`, ~12px left of the arrow tip, `dominant-baseline="middle"`
  - Right tip: `text-anchor="start"`, ~12px right of the arrow tip, `dominant-baseline="middle"`

### Layout conventions

- Four cells, equal size (240×160 or 280×180 are good defaults), arranged with a 40–60px gap from the axis cross.
- Axis cross passes *between* the cells, not through them.
- Arrow tips live ~20–40px outside the outermost cell edge; single-word axis labels sit ~12px beyond each tip (see Axis labels above).
- Exactly one focal cell. Picking none makes it a placeholder template; picking two erases the signal.
- Keep the legend strip + horizontal rule at the bottom — same as the standard quadrant. Legend swatches should show both "headline bet" (accent) and "candidate future" (neutral).

### Anti-patterns (variant-specific)

- Pure `#fff` background — the near-white paper is load-bearing across the skill, and the figure's own `paper-2` surfaces stop separating from it.
- A second hue to tell the four cells apart — the cells are named, and position already distinguishes them. One accent, on the focal cell only.
- Unnamed cells ("Scenario 1/2/3/4") in a shipped diagram — OK as a blank template; not OK as a finished artifact.
- The accent on more than one cell — same focal rule as everywhere else in the skill.
- 3×3 or 2×3 grids — those are different diagrams, not this variant.
- Positioning dots *inside* the cells — if position matters, use the standard quadrant.
- Bolded axis labels, arrow glyphs in the text (`↑ Driver`), or "high / low" parentheticals — all forbidden. Jobs-minimal is non-negotiable on this variant.
- Corner tags that disagree with the axis labels (e.g. axis says `Remote / In-person` but the tag reads `High remote / low AI`). Reader parses this as a bug in three seconds.
