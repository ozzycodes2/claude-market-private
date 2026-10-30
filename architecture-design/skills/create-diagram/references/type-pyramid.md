# Pyramid / Funnel

**Best for:** hierarchy of needs, prioritization ranks, value pyramids, conversion funnels, content importance stacks.

## Two orientations — pick one
- **Pyramid** (point up) — narrow apex = most important / rarest / most valuable. Base is broadest / foundational.
- **Funnel** (point down) — narrow end = conversion (smallest group). Top is widest / audience.

Don't mix orientations on one diagram.

## Layout conventions
- 4–6 layers. Each layer is a trapezoid built from an SVG `<polygon>` with 4 points.
- Consistent layer height (56–72px).
- **Conceptual pyramid** (ranks, needs, stacks): widths step in by equal linear amounts. Width is rank, not quantity. Never claim proportionality, never call the widths "honest", and never let trapezoid area stand for counts. Print any figures as labels and say in the source line that width is rank only.
- **Data funnel** (conversion, pipeline): width is proportional to the value (count or percentage of the first stage), starting at zero. If the range is too wide for linear widths (a 240-to-1 drop), use a log width and say "log width" in the source line. Print the value on every layer.
- Decide which kind it is before drawing. A diagram with printed counts that span orders of magnitude and equal-step widths is a conceptual pyramid; say so in the source line.
- Each layer has:
  - **Name label** centered inside the trapezoid — `node-name` role, 12–14px 600.
  - **Sublabel** below or beside the name — `sublabel` role, 9–10px.
  - **Side annotation** (right or left) — optional. For funnels: drop-off percentage here (`−40%`).
- Fill: subtle graded tints OR all paper-2 with hairline dividers (cleaner). Pick one.
- Stroke: 1px hairline between layers; outer silhouette 1px muted or ink.
- **The accent on ONE layer only**: apex of pyramid, conversion layer of funnel, or critical bottleneck.
- Optional left-margin axis arrow + label in sentence case (`Rarer, fewer`, `Drop-off`), set horizontally above the arrow's tip, left-aligned to the arrow. No rotated text.
- No legend: layers are named in place. The source line (sentence case) states the data source and whether width is rank only, proportional, or log.

## Anti-patterns
- 7+ layers (illegible — compress or split).
- Pyramid for non-hierarchical data (use a tree or bar chart).
- Equal-step widths on a data funnel, or any caption claiming that equal-step widths are "honest" or proportional.
- The accent on the base layer (dilutes the "apex = rare" signal).

## Examples
- `assets/example-pyramid.html` — minimal light
- `assets/example-pyramid-dark.html` — minimal dark
- `assets/example-pyramid-full.html` — full editorial
