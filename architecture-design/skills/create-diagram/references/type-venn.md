# Venn / Set Overlap

**Best for:** intersection of concepts/domains, shared attributes between categories, "where A meets B", ikigai-style frames (desirable × feasible × viable).

## Layout conventions
- **Prefer 2 or 3 circles.** Avoid 4+ (unreadable — use a matrix instead).
- Circle stroke: 1px hairline, color per-set (ink, muted, soft).
- Circle fill: very low-opacity tint — `ink @ 0.04` for the ink set, `muted @ 0.05` for the muted one. Tints compound naturally in overlap regions.
- **Area is either data or not, and the source line says which.** Concept Venns (desirable x feasible x viable) use equal radii, encode no counts, and the source line says "areas and overlaps are not to scale". Data Venns (set sizes or overlaps are counts) scale circle AREA to the count (`r = k * sqrt(n)`), draw overlaps to match where geometry allows, print each count in its region, and state the unit in the source line. Never fake equal sizes for aesthetics when the sets are counts.
- **Set labels** placed outside the circle, NEVER crossing the stroke. `node-name` role 12–14px 600 for the set name, optional `sublabel` role 9px in sentence case ("People want it"), no tracking.
- **Intersection labels** placed inside the overlap region, `node-name` role 12px 600, centered. For small overlaps, use a leader line to a label in clear space.
- **The accent** on the ONE focal intersection — the "sweet spot". Either an `accent` label stroke OR a clipPath-bounded `accent @ 0.10` fill tint.
- Circle centers and radii divisible by 4 (a data Venn's radii are data-scaled and exempt).
- **No legend.** Every region is named in place; a key would repeat the labels. A sentence-case `muted` source line (`data-role="source"`, starting `Source: `) sits bottom-left: origin and period first (`illustrative design framework, 2026`), then whether area is to scale. The `<title>` is the claim (`A product ships only where all three tests overlap`, under about 60 characters) and `<desc>` opens with it.
- **Context rule exception:** a Venn shows set membership, not a measured quantity series, so no reference line is drawn.

## Anti-patterns
- Unlabeled regions — reader can't tell which set is which.
- Circles that don't overlap when overlap is the point.
- Equal-sized circles when the sets are counts of different size (the area lies), or a source line that claims scale for equal circles.
- The accent on multiple overlap regions (focal signal dies).
- Labels sitting on top of circle strokes (illegible).
- 4+ circles where 2–3 would do.

## Examples
- `assets/example-venn.html` — minimal light
- `assets/example-venn-dark.html` — minimal dark
- `assets/example-venn-full.html` — full editorial
