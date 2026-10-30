# Tree / Hierarchy

**Best for:** org charts, dependency trees, taxonomy, file trees, decision breakdowns, skill trees. For hierarchical, ID-addressable block decomposition with per-block I/O, constraints, and implementation traceability, load [`semantic-patterns.md`](semantic-patterns.md) § Traceable block decomposition first — it specializes this layout without changing it.

## Layout conventions
- Root at top, children fan out below (or root at left, children to right).
- Nodes are small labeled rectangles (`rx=6`), `node-name` role 12px 600 name + optional `sublabel` role 9px. Width 120–180px, height 40–52px.
- **Connectors are orthogonal (elbow-style), never diagonal.** Parent drops a short vertical line, then a horizontal bus connects siblings, then each child has a short vertical drop into its top edge. 1px muted stroke.
- Leaf indicator: thinner stroke (0.8) or different fill — OR let terminal position do the work.
- Max depth: 4 (root + 3 tiers). Max breadth per level: 5.
- The accent on **one** node: root OR critical leaf. Not both.
- Draw connectors before nodes.
- Tier captions in the left margin are sentence case, no tracking (`Tier 0 · root`, `Tier 1`).
- Type tags inside a node (`ROOT`, `CATEGORY`) are the one caps exception: 7px, uppercase, tracked. Spell the word out and widen the tag box on the 4px grid to fit (≈4.9px per character plus 8px) rather than truncating (`CAT`). ID tags (`PAY-001`) are literal and keep their case.
- Legend strip has no `Legend` heading; its keys (node treatments) stay.

## Anti-patterns
- Tree 5+ levels deep on a single page (illegible — split).
- Nodes of wildly varying widths — pick 2 widths max.
- Diagonal connector lines.
- Skipped levels (parent connected to grandchild with no middle).
- The accent on root AND a leaf.

## Examples
- `assets/example-tree.html` — minimal light
- `assets/example-tree-dark.html` — minimal dark
- `assets/example-tree-full.html` — full editorial
