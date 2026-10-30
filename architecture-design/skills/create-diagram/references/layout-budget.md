# Layout grid, per-type budgets, page layout, and summary cards

Routed from SKILL.md §7 and §8. SKILL.md keeps the grid rule in one line, the universal complexity limits, and the split rule. This file holds the full grid table, every per-type budget row, the page layout, and the summary card pattern.

## Layout & Spacing

### 4px grid

**Structural geometry, divisible by 4:** node origins, widths, heights, gaps, padding. Off-grid by design: type sizes (role ramp in `references/output-spec.md`), radii, data-derived positions, text baselines, arrow markers, `.5` offsets that keep 1px strokes crisp, stroke widths, opacity, and the 22×22 dot-pattern.

| Category | Allowed values |
|---|---|
| Node width / height | 80, 96, 112, 120, 128, 140, 144, 160, 180, 200, 240, 320 |
| Gap between nodes | 20, 24, 32, 40, 48 |
| Padding inside boxes | 8, 12, 16 |
| Border radius | 4, 6, 8 |

### Complexity budget (per diagram)

These are the per-type limits. The universal rows in SKILL.md §7 (9 nodes, 12 arrows or transitions, 2 accent elements, 2 annotation callouts, and the motion limits) apply to every type on top of these, and a semantic pattern's own budget in [semantic-patterns.md](semantic-patterns.md) can only tighten them.

| Limit | Rule |
|---|---|
| Max unique components / relationships / ledger entries (architecture delta) | 8 / 10 / 8 |
| Max admin bands / traffic scopes / nodes (architecture containment) | 2 / 4 / 8 |
| Max lifelines (sequence) | 5 |
| Max combined fragments (sequence) | 1 (default); 2 only if each is single-region `opt`/`loop` |
| Max `alt` regions (sequence) | 2 |
| Max fragment nesting (sequence) | 1 |
| Max lanes (swimlane) | 5 |
| Max items (quadrant) | 12 |
| Max entities (ER) | 8 |
| Max nesting levels (nested) | 6 |
| Max tree depth | 4 |
| Max org chart depth | 4 |
| Max org chart nodes | 12 |
| Max layers (layer stack) | 6 |
| Max parts / levels / focal parts (exploded axonometric) | 5 / 5 / 1, three detail levels |
| Max tagged rooms or buildings / boxes / focal (axonometric plan) | 8 / 40 / 1 |
| Max circles (venn) | 3 |
| Max layers (pyramid) | 6 |
| Max radar axes | 5 |
| Max radar series | 5 |
| Max focal radar series | 1 |
| Max polar categories | 8 |
| Max polar series | 1 |
| Max focal polar categories | 1 |
| Max bars (bar chart) | 16 |
| Max bars (waterfall) | 8 incl. totals, 1 subtotal |
| Max cells (treemap) | 8 |
| Max series (line chart) | 6 (limited by end-label collisions) |
| Max tasks (Gantt) | 24 |
| Max points (scatter and beeswarm) | 300 |
| Max cells (heatmap) | 12 x 12 |
| Max stages / nodes / flows (sankey) | 3 / 8 / 12 |
| Max categories (fishbone) | 6 bones, 3 sub-causes each |
| Max components / links (wardley) | 9 / 12, 2 movement arrows |
| Max columns / cards (kanban) | 5 / 12 total, 4 per column |
| Max stages / rows (user journey) | 6 / 3, 2 pain markers |
| Max stages / layers (service blueprint) | 6 stages; required customer / frontstage / backstage; optional evidence / support; 1 focal cell |
| Max zones / nodes / paths (deployment) | 3 / 6 / 8, 9 artifacts |
| Max nodes / edges (dependency) | 9 / 14, 4 ranks, 1 cycle |
| Max classes / relationships (UML class) | 7 / 8, 5 members per compartment |
| Max activities / slices / cards (story map) | 5 / 3 / 12 |
| Max tables / columns / FKs (db schema) | 5 / 8 shown / 6 |

The chart rows (bar, line, scatter, Gantt, heatmap) are Tufte's data-density allowance: a chart earns its ink per value, so it can carry more than a schematic. The 9-node schematic budget is unchanged. Charts may shrink down to the type-ramp floor before they split.

If a schematic exceeds, split into two diagrams (overview + detail). If a chart exceeds its row, split it into small multiples.

### Small multiples

The split method for charts. Repeat one small chart per category with an identical frame and identical scales, so panels compare by eye. Each panel gets a direct title (sentence case, in the panel, not a legend); the shared axis is labelled once, on the outer panel. Same marks, same colors, same order in every panel. Schematics split by overview + detail; charts split by small multiples. Also use small multiples when a second variable explains the first (one panel per segment, same scales). Worked example: [`assets/example-line-small-multiples.html`](../assets/example-line-small-multiples.html).

### Page layout

1. **Header** — `eyebrow` role, `title` role, optional subtitle (`node-name` family, `muted`).
2. **Diagram container** — default: **clean, borderless**, no background — the SVG sits directly on the page paper. Optional *framed* variant (for card-heavy layouts or hero placements): `paper-2` bg + 1px `rule` border + 8px radius + `1.5rem` padding + `overflow-x: auto`.
3. **Summary cards** (optional) — 2–3 col grid with *varied* widths (e.g., `1.1fr 1fr 0.9fr`).
4. **Footer** — colophon in the `sublabel` role, `muted`, hairline top border.

## Summary Card Pattern

Cards are optional, not required; add them only when they say something the diagram does not. Don't use 3 identical generic cards. Vary the treatment:

```html
<div class="card">
  <p class="eyebrow">SECTION LABEL</p> <!-- HTML page eyebrow: caps allowed -->
  <div class="card-header">
    <span class="card-dot accent"></span>
    <h3>Card Title</h3>
  </div>
  <ul><li>Item</li></ul>
</div>
```

Rules:

- `background: #ffffff` (not paper — slight lift without shadow)
- `border: 1px solid` the `rule` color
- `border-radius: 18px` (`radius-lg`, the ladder's step for editorial cards), `padding: 1.25rem`
- **No `box-shadow`**
- Card dots: 7px, `border-radius: 50%` — ink / muted / accent / soft variants (no `link`: this skin has one chroma)

Content rules for chart pages (checked by `scripts/verify-cards.py`):

- Each card (`<h3>` plus `<p>`) names at least one mark visible in the diagram: a string equal, ignoring case, to the full text of an SVG `<text>` of 2 or more characters (a tick label like `S4`, a node name, a series end label).
- Every number pair written `X → Y`, `X→Y`, `X to Y` or `from X to Y` (plain numbers, not percentages) has both numbers in the bound data (`data-value`, `data-values`, `data-x`, `data-y`, `data-size`, `data-start`, `data-end`, `data-domain`) or as SVG text.
- Derived numbers (percent change, averages) are right against the data and state their span: "+75% over 8 weeks", never "75% week-over-week" for a total. The script does not check this arithmetic; check it by hand.
- At most one card is "What the chart doesn't show", the limits of the measure. Encourage it on chart pages.
- A cause a card names is marked on the chart with an [event marker](primitives-core.md#event-marker).
