# Scatter Plot

**Best for:** correlation and distribution — two continuous variables plotted against each other. Use when the relationship (or lack of one) between variables is the message, or when you need to identify clusters, outliers, and high/low performers.

## Layout conventions

- **Plot area:** inside a `0 0 1000 500` viewBox; X axis rule at `y=432`, Y axis rule at `x=144` in the shipped example, both outside the data so no point touches its axis.
- **Point count:** 5–30 points is the sweet spot. Fewer → just describe the relationship in prose. More is allowed up to a hard cap of **300**; past that, bin into a density contour or hand the crowd to the **beeswarm variant**, which packs instead of jittering.
- **Range-frame axes.** Each axis rule spans only the data: the x rule from the smallest to the largest x, the y rule from the smallest to the largest y. Tick labels (`sublabel` mono, 8px) sit at the two ends of each rule plus evenly between; the ends calibrate the rest. The ends of the rule are the data's range, which is information a full-width box throws away. No frame around the plot.
- **No full grid.** Horizontal and vertical rules together turn the plot into graph paper. Use the axes and the labelled reference lines; if a wide plot genuinely needs help reading across, at most four rules in one direction at `ink @ 0.08`.
- **Axis titles:** sentence case, horizontal, mono 8px `muted`. The y title sits above the top of the y axis, left-aligned to it (`x=144`, `y=84`); the x title sits under the tick labels, left-aligned to the start of the x rule. No rotated text.
- **Optional rug marks.** A short `soft` 1px tick on each axis at every point's x (or y) shows the marginal distribution for the ink of a single stroke per point. Put them outside the axis rule, unbound, and draw them only when the marginals are part of the story.
- **Point shape:** `<circle>` r=5 for standard points, r=6 for focal. Focal point in `accent`. Others in `muted @ 0.20` fill + `muted` stroke.
- **Direct labels first.** Label a point in place (the focal point and at most 2–3 outliers a reader will look for), name in `sublabel` mono 8px, sentence case, `ink`, on a paper-fill mask sized from the width budget in style-guide.md. A legend appears only for an encoding that cannot be written in place; a plain scatter has none, so the shipped example has no legend strip at all.
- **Trend line only when it is a computed fit.** A trend is `<line data-trend="ols">` between the smallest and largest x of the data, solid `soft` 1.2px, with a direct label and a source line naming the method ("Solid line: least squares fit to all 12 points"). The endpoints are the ordinary least squares prediction at those x values, recomputed from the points whenever a point changes; a line drawn by eye is refused by `scripts/verify-scatter.py`. Omit it when the data is genuinely scattered; a forced fit is dishonest.
- **Comparison line.** Draw at least one comparison the data supports: the median or average of one variable, or a target. A `soft` 1px line dashed `4,3`, under the points, with a sentence-case direct label (`data-ref`, `data-value`; a `median` or `mean` must equal that statistic of the bound points). Quadrant dividers are this same line at both medians; label each quadrant only if the quadrants carry a name.
- **Source line:** one `data-role="source"` text under the plot, sentence case: who measured it, over what, how many, and what each line is.

### Point pattern

```svg
<!-- Non-focal point: paper mask + circle; data-x / data-y state the value -->
<circle cx="X" cy="Y" r="5" fill="{paper}"/>
<circle data-x="4" data-y="18" cx="X" cy="Y" r="5" fill="{muted @ 0.20}" stroke="{muted}" stroke-width="1"/>

<!-- Focal point, named so its label can be bound to it -->
<circle cx="X" cy="Y" r="6" fill="{paper}"/>
<circle data-x="18" data-y="3" data-name="Platform" cx="X" cy="Y" r="6" fill="{accent @ 0.15}" stroke="{accent}" stroke-width="1.2"/>
<text data-name="Platform" data-role="label" x="830" y="357" fill="{ink}" font-size="8" font-family="{sublabel}" text-anchor="middle">Platform</text>

<!-- A range-frame axis and its end tick -->
<line data-axis="y" x1="144" y1="103.3" x2="144" y2="388.3" stroke="{soft}" stroke-width="1"/>
<text data-tick="y" data-value="20" x="136" y="106.3" fill="{muted}" font-size="8" font-family="{sublabel}" text-anchor="end">20</text>

<!-- Comparison and fit -->
<line data-ref="median" data-value="10" x1="168" y1="261.7" x2="960" y2="261.7" stroke="{soft}" stroke-width="1" stroke-dasharray="4,3"/>
<line data-trend="ols" x1="168" y1="132.4" x2="960" y2="414.3" stroke="{soft}" stroke-width="1.2"/>
```

`data-x` and `data-y` on a `<circle>` are this contract's vocabulary, and only a circle carrying neither `data-size` (bubble) nor `data-value` (beeswarm) claims a file for `scripts/verify-scatter.py`, so the three checkers never claim one another's files. It holds every point to two shared linear scales; holds ticks, the range-frame rules and reference lines to the same scales; recomputes the least squares line from the bound points and compares both trend endpoints; requires a `median` or `mean` reference to equal that statistic; requires every named point to carry exactly one label bound to it and refuses a legend, a LEGEND heading, a key that repeats a direct label, a full grid, rotated text, any transform, and more than 300 points. `scripts/test-verify-scatter.py` proves each check in both polarities. Its `--all` globs `example-scatter*.html` and filters on the detection rule, so the bubble and beeswarm variants below are left to their own checkers.

## Anti-patterns

- More than 300 points (jitter/mush) — when the crowd itself is the story, hand it to the **beeswarm variant** below, which packs instead of jittering.
- A trend line that is not a computed fit: drawn by eye, with no named method, or running past the data.
- Forced trend line when the data is genuinely scattered — dishonest.
- A full horizontal-and-vertical grid, or a frame around the plot.
- A legend that repeats what direct labels already say.
- Rotated axis titles, or axis titles in caps with tracking.
- Point labels on every point (label the focal and 1–2 notable outliers only).
- Ad-hoc bubble size encoding on a plain scatter. Size perception is unreliable enough that it earns its own contract: when the third value genuinely matters, use the **bubble variant** below, which pins area to the value and gates it with `scripts/verify-bubble.py`; when it doesn't, a third axis label or a focal choice says it cheaper.
- No comparison: a cloud with no median, average or target beside it.
- Axes that don't include zero when the absolute position matters; axes that do include zero when the range is tiny and far from zero.

### Bubble

**Best for:** three quantities per item — x, y, and a magnitude — where the *joint* reading is the story: which items combine a bad position with a big footprint. The shipped example plots services by p95 latency and error rate with area as request volume, and the point of the figure is exactly the multiplication a two-variable scatter cannot do — the slowest service barely matters and the risky one is not the slowest.

Not for: a third value that is really a category (use the focal accent or facet it); two variables (that is the parent scatter — size on everything is decoration); or magnitudes spanning several orders (the small bubbles vanish; bin, or plot the magnitude on an axis of its own).

#### Layout conventions

- **Plot frame:** inside `0 0 1000 500`, the x scale `x = 80 + 1.76·ms` and y scale `y = 420 − 95·pct`. **Range-frame axes:** each rule spans only the data's own min to max, not the plot box (the shipped example runs the y rule from 0.5 % to 2.8 % and the x rule from 85 to 460 ms), in `soft`. **No grid** — the bound ticks carry the scale. **Axis titles are horizontal and sentence case**: the y title sits above its axis, left-aligned to it (`Error rate, %`); the x title sits under the axis (`p95 latency, ms`). No rotated text anywhere.
- **Item count:** 5–15. Below 5 the leave-one-out scale check has nothing to hold onto and a table says it better; above 15 the areas start stacking and the reading degrades to a density cloud — which is the parent's contour territory, not this.
- **Radius from area:** `r = K·√value` for one constant K across the figure, sized so the largest bubble stays inside the plot (the shipped example uses `K = 1.4` on requests-per-second, giving 10.8–42px). State the area scale in the source line.
- **Bound axis ticks:** every tick carries `data-tick` (axis) and `data-value` (the number it prints). 4–6 per axis at equal intervals, `arrow-label` role 8px, same placement as the parent.
- **Paper underlay per bubble**, same radius, painted immediately beneath — the translucent fill must not show the comparison line or a neighbour through itself, because the fill's job is to read as one solid area.
- **Draw order: largest first.** A small bubble painted early is buried under a later giant and its area is unreadable. `verify-bubble.py` checks paint order on every overlapping pair.
- **Size key, not a legend.** Two or three reference circles (`data-key-size`, here 100, 400 and 800 requests per second) drawn on the bubbles' own K, each with its value printed beneath (`<text data-key-size>`), under a sentence-case header (`Bubble area, requests per second`). No `LEGEND` heading. The key circles are outline-only `muted` strokes — a key is a ruler, not data.
- **Source line states K.** `<text data-role="source">` carries the area rule and its constant in visible text (`Area = π·K²·requests per second, K = 1.4 px per √(req/s)`), plus the axis units and the scale note. A reader cannot turn an area back into a value without K.
- **A comparison line.** One horizontal `<line data-ref data-value>` at a target the reader judges against (the shipped example draws the 1.5 % error budget), `soft`, 1px, dashed `4,3`, with a direct sentence-case label at its end (`Error budget, 1.5%`).
- **Labels:** the focal bubble plus at most 2–3 outliers a reader will look for, `arrow-label` role 8px, sentence case, each bound to its bubble with `data-name` and printing exactly that string. No letter-spacing, no mask. Never all of them.
- **4px grid** applies to the designed constants — axis rules, tick baselines, key rows. Bubble centres and radii are data-scaled and exempt; snapping them would move the data.

#### Colour

- **One accent bubble, and one uniform `ink` fill for everything else** (`ink` at 0.14 in the shipped example) — never a hue per item, and never a tone that changes with size. Every labelled bubble is named where it sits, so hue would re-encode what the labels already carry.
- **The accent marks the editorially focal item, not the biggest or the worst single number.** In the shipped example it marks the service whose *combination* is the risk: near-peak volume on the worst error rate.
- **No opacity ramp.** A fill that fades as area grows is a second encoding of a value the area already shows, and it makes the reader weigh ink that no value asked for. Overlap is solved by paint order (largest first) and the `muted` stroke, not by tone. `verify-bubble.py` requires every non-focal bubble to declare the identical fill.
- **Every bubble keeps a `muted` stroke** (6.11:1 on light paper, 7.07:1 on dark) — the fill sits at an opacity well under 3:1, so the stroke is what carries WCAG 1.4.11 for the mark's edge. The focal bubble's accent stroke measures 4.71:1 on light paper with the default skin and may measure less on an onboarded one; as with the focal bar, line and slopegraph, its data is carried redundantly — position and label — and the accent adds only *which bubble is focal*.
- **Labels stay `ink` or `muted`**, including the focal one. Accent text at 8px misses AA on light paper.

#### Honest-data rule

**Area encodes the third value — never radius.** Radius-proportional sizing squares the claim: a 6× value reads as 36× the ink. `scripts/verify-bubble.py` gates it, along with the two axis scales.

- **One finite, nonzero linear scale per axis, every bubble on it.** A bubble nudged aside because two crowd each other reads as a different number; crowded bubbles are data, and the honest fixes are a hairline of separation (which the largest-first rule provides) or fewer items — never a moved centre.
- **Axes include zero, or the source line states the bounds.** A bubble's position is read against the origin in a way a slopegraph's is not. No log scale without saying so — and area next to a log axis is a reading most audiences get wrong, so prefer not at all.
- **K and the axis bounds are stated in the visible source line.** Omitted items are counted there too.
- **Omitted items are counted in the footnote.** A bubble chart with the inconvenient giant quietly missing is the same lie as a truncated axis.
- **A non-positive magnitude cannot be a bubble.** Area has no sign; omit the item and say so.
- **Round once, then draw from the rounded number**, so the declared value and the drawn geometry are two statements of one number rather than two chances to disagree.

#### Declaring the values

**Every drawn quantity is bound to an attribute stating the value it encodes.** A zero-slope value axis collapses distinct values to one position and is rejected, including in the beeswarm variant. The data circle carries all three values; the paper underlay is scenery and carries nothing.

```svg
<!-- A bubble: position from two shared linear scales, area from the size.
     x = 80 + 1.76·ms, y = 420 - 95·pct, r = 1.4·√(req/s) -->
<circle cx="537.6" cy="154" r="38.6" fill="{paper}"/>
<circle data-name="Payments" data-x="260" data-y="2.8" data-size="760"
        cx="537.6" cy="154" r="38.6"
        fill="{accent @ 0.15}" stroke="{accent}" stroke-width="1.2"/>

<!-- Its label, bound to the bubble it names -->
<text data-name="Payments" data-role="label" x="538" y="108" fill="{ink}" font-size="8" font-family="{arrow-label}" text-anchor="middle">Payments</text>

<!-- An axis tick, bound to the number it prints -->
<text data-tick="x" data-value="300" x="608" y="440" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="middle">300</text>

<!-- A size-key circle on the same K, its printed value, and the source line -->
<circle data-key-size="400" cx="844" cy="116" r="28" fill="none" stroke="{muted}" stroke-width="1"/>
<text data-key-size="400" x="844" y="160" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="middle">400</text>
<text data-role="source" x="40" y="488" fill="{muted}" font-size="8" font-family="{arrow-label}">Area = π·K²·requests per second, K = 1.4 px per √(req/s). …</text>

<!-- The comparison line and its direct label -->
<line data-ref="budget" data-value="1.5" x1="172" y1="277.5" x2="960" y2="277.5" stroke="{soft}" stroke-width="1" stroke-dasharray="4,3"/>
<text data-ref="budget" data-role="label" x="960" y="271.5" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="end">Error budget, 1.5%</text>
```

What each binding buys, and what it costs to omit:

| Binding | Without it |
|---|---|
| `data-x` / `data-y` on the circle | A nudged centre could not be caught — the drawn position would be the only statement of the value. |
| `data-size` on the circle | Nothing pins area to the value, and radius-proportional sizing renders identically plausible. |
| `data-name` on the circle | An unnamed bubble cannot be labelled or cross-checked, and drops out of every comparison silently. |
| `data-name` on a label | Two labels could be exchanged between bubbles, renaming both, with every number still correct in isolation. |
| `data-tick` / `data-value` on a tick | The printed axis could be relabelled wholesale — every bubble honestly placed on a scale the axis lies about. |
| `data-key-size` on a key circle and its text | A key drawn on a different K than the bubbles teaches the reader the wrong scale, and a key with no printed value is a circle with no meaning. |
| `data-role="source"` stating `K = n` | The area constant lives only in the geometry; nobody can convert an area back into a value. |
| `data-ref` / `data-value` on a line, and `data-ref` on its label | The comparison line could sit anywhere, or float with no name. |

`scripts/verify-bubble.py` derives both axis scales and the area constant from the set itself (Theil–Sen, leave-one-out, so one dishonest bubble cannot drag the line it is measured against), requires at most one accent bubble, checks paint order on overlaps, and holds every bound label and tick against the mark it describes. The Tufte pass adds five checks: one uniform non-focal fill; a size key of two or three `data-key-size` circles drawn on the bubbles' own K, each with a printed value; a source line whose `K = n` matches the K the bubbles draw (within 2 %); at least one `data-ref` line that is horizontal, on the y scale, dashed `4,3` and directly labelled; and no rotated text and no `LEGEND` heading. Labels must match their binding exactly — sentence case, not small-caps. Deliberately **not** `data-series`: that attribute is the slopegraph contract, and using it here would put every bubble file inside `verify-slopegraph.py`'s scope.

**No `transform` on any of it.** The checker reads raw `cx`/`cy`/`r` and `x`/`y` attributes, so a transform on a bubble, a bound label, an ancestor `<g>`, or in a CSS rule moves the rendered mark away from the number that was verified. Bake the offset into the coordinates. Nothing is rotated, so there is no exception to carve out.

#### Anti-patterns

- Radius proportional to the value — the type's one unforgivable error.
- Moving a bubble to stop it overlapping a neighbour, or drawing a small bubble under a large one.
- A hue per item instead of one uniform ink fill plus a single accent, or any fill that varies with size.
- A legend heading, a rotated axis title, a full grid, or small-caps labels.
- A size key drawn on a different K than the bubbles, or a source line that never states K.
- A log axis the source line never states, or a truncated axis with no stated bounds.
- Labelling every bubble (the focal plus 2–3 outliers, no more).
- A `transform` on a bubble, a bound label, an ancestor group, or in CSS.
- An unbound visible string: a label or an axis tick with no attribute stating the same thing.
- Size on a value nobody will read — if the areas do not change the story, this is the parent scatter wearing a costume.

### Beeswarm

**Best for:** a full distribution where every unit deserves its own mark — one dot per item on a single shared value axis, dodged perpendicular so nothing overlaps. Use when the *shape* of the crowd and its outliers are the story a summary number would hide: the shipped example plots 138 per-request latency samples for one endpoint, and the point of the figure is that a healthy median and an ugly p99 are the same dataset.

Not for: two variables (that is the parent scatter); comparing distributions across many groups (facet, or reach for a ridgeline); more than ~300 items (the packing outgrows the band — bin into a histogram); or a handful of values (below 20 there is no distribution to swarm, and a table says it shorter).

#### Layout conventions

- **One value axis, horizontal, at the parent's baseline** (`y=420` inside `0 0 1000 500`, plot margins left 80, right 40), drawn as a **range frame** in `soft` that spans only the first to the last dot, with 4–6 bound ticks at equal intervals in the `arrow-label` role at 8px and **no gridlines** — the swarm axis has no scale to grid, a horizontal rule through the band would invite reading the packing offsets as values, and the two reference lines below do the job a grid would. The axis title is horizontal, sentence case and left-aligned to the axis (`Per-request latency, ms`).
- **Median and p99 lines.** The title argues about the tail, so draw the statistics it argues with: `<line data-ref="median">` and `<line data-ref="p99">`, vertical, `soft`, 1px, dashed `4,3`, painted behind the dots, each with a direct sentence-case label above it that prints the number (`Median 122.5 ms`, `p99 396.8 ms`). The median line is always required; the p99 line is required whenever the title or description mentions the tail or p99. Title, description and lines must say one thing: the shipped example's three requests past 380 ms are the tail, its median is 122.5 ms and its linear-interpolation p99 is 396.8 ms.
- **Dot count: 20–300**, one dot per item, all at one radius (the shipped example uses `r=4`). Both ends of the budget are enforced by `scripts/verify-beeswarm.py`.
- **Greedy dodge around a midline** (`y=230` in the shipped example): each dot takes the first free slot alternating above/below at a fixed pitch of `2r+2`. The dodge is packing, not data — any collision-free arrangement is legitimate, and the algorithm is not part of the contract.
- **Labels: the focal dot plus the outliers a reader will look for, at most 6.** `arrow-label` role 8px, sentence case, printing exactly the `data-name`, on a paper mask sized to the text, one tier per label, alternating sides of the band, each tied to its dot by an unbound `soft` leader and bound to it with `data-name`.
- **4px grid** applies to the designed constants — the axis rule, tick baselines, source line. Dot positions are data-scaled on the value axis and packing-scaled on the swarm axis, and both are exempt; snapping them would move the data.

#### Colour

- **One ink fill for every non-focal dot** (`ink` at 0.55 in the shipped example) plus a `muted` stroke for the mark's edge, and **at most one accent dot**. Density must read as swarm *thickness*, never as tone: opacity as a value encoding while also dodging says one thing twice in two different lies, so `verify-beeswarm.py` requires the non-focal fill to be literally identical across the swarm.
- **The accent marks the editorially focal item** — in the shipped example the single slowest request, the one the title is about — never a hue per group. Groups are a facet decision, not a palette decision.
- **The focal dot keeps the shared radius.** Its cues are the accent fill and stroke, and its label; a bigger focal dot is a second encoding and breaks the packing.

#### Honest-data rule

**The value axis is exact and shared; the swarm axis carries no meaning — and says so.** The source line (`<text data-role="source">`) states the unit (`Latency in ms`), that one dot is one request, that the vertical spread is packing, the axis scale, how the p99 was computed, and counts anything omitted. There is no `LEGEND` heading. `scripts/verify-beeswarm.py` gates the geometry half.

- **No dot is dropped, binned, or jittered off its true value.** One dot = one item at exactly its value on one linear scale derived from the set itself (Theil-Sen, leave-one-out, so one dishonest dot cannot drag the line it is measured against).
- **Overlap is resolved by the perpendicular dodge, never by moving a dot along the value axis.** Two items with one value share a position and dodge apart; crowding is data, and the honest rendering of a crowd is thickness.
- **No two dots overprint.** A dot painted over another turns density into darkness, which the eye reads as a value nobody declared.
- **Linear scale only in the shipped grammar.** A log axis needs its own declaration before the checker could hold it to anything, so it is refused rather than half-trusted; if the spread demands log, say so in the source line and expect the gate to disagree until the grammar grows the declaration.

#### Declaring the values

**Every dot is bound to the value it encodes.** `data-value` on a `<circle>` is the beeswarm contract — deliberately not `data-series` (slopegraph), `data-ranks` (bump) or `data-size` (bubble), so no sibling checker claims a beeswarm file and this one claims none of theirs. Detection is element-scoped: `data-value` also appears on `<text>` axis ticks in the bubble contract, so only a `<circle>` binding it puts a file inside this gate. The paper underlay beneath each dot is scenery and carries nothing.

```svg
<!-- A dot: position on the shared value scale, x = 80 + 2·ms. The cy is
     packing only. -->
<circle data-value="90" cx="260" cy="250" r="4" fill="{ink @ 0.55}" stroke="{muted}" stroke-width="0.75"/>

<!-- The focal dot — named, accented, same radius as everyone -->
<circle data-value="431" data-name="req-4c1f" cx="942" cy="230" r="4" fill="{accent @ 0.55}" stroke="{accent}" stroke-width="1.2"/>

<!-- Its label, bound to the dot it names -->
<text data-name="req-4c1f" data-role="label" x="942" y="120" fill="{ink}" font-size="8" font-family="{arrow-label}" text-anchor="middle">req-4c1f</text>

<!-- An axis tick, bound to the number it prints -->
<text data-tick="x" data-value="200" x="480" y="440" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="middle">200</text>

<!-- A comparison line, drawn behind the dots, and its direct label -->
<line data-ref="median" data-value="122.5" x1="325" y1="64" x2="325" y2="420" stroke="{soft}" stroke-width="1" stroke-dasharray="4,3"/>
<text data-ref="median" data-role="label" x="325" y="52" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="middle">Median 122.5 ms</text>
```

What each binding buys, and what it costs to omit:

| Binding | Without it |
|---|---|
| `data-value` on the circle | A dot nudged along the value axis could not be caught — the drawn position would be the only statement of the value. |
| `data-name` on the focal/outlier circles | An unnamed outlier cannot be labelled or cross-checked, and two swapped labels rename both dots silently. The name must be non-empty and unique to one dot: two dots sharing a name collapse into one entry, so a single label satisfies both. |
| `data-name` on a label | The label floats free — it could name a dot that is not there, or drift to a neighbour. |
| `data-tick` / `data-value` on a tick | The printed axis could be relabelled wholesale — every dot honestly placed on a scale the axis lies about. |
| `data-ref` / `data-value` on a line, and `data-ref` on its label | A title can say "median" over a line drawn anywhere. The checker recomputes the median and the p99 from the dots and holds the line, the declared value and the printed number to it. |

`scripts/verify-beeswarm.py` derives the value scale from the dots themselves, requires dots sharing a value to share a position, refuses any overprinted pair, holds every dot to one radius and every non-focal dot to one fill, caps the accent at one dot and the labels at six, requires every `data-name` to be non-empty and unique, checks every bound label and tick against the mark it describes, requires the median line (and the p99 line when the title argues the tail) to match the statistic the dots compute, sit on the dots' scale, be dashed `4,3` and be directly labelled, requires a `data-role="source"` line that names a unit, and refuses rotated text and a `LEGEND` heading. Labels match their binding exactly (sentence case); `scripts/test-verify-beeswarm.py` proves each check in both polarities and pins the sibling scope treaty in both directions.

**Nothing may position a mark except its own attributes.** The checker reads raw `cx`/`cy`/`r` and `x`/`y`, so anything applied afterwards invalidates the check that passed. Every carrier is refused — the `transform` attribute, an inline `style="…"`, and a rule in a `<style>` block — on a dot, on a bound label or tick, or on an ancestor `<g>`/`<svg>`. So is every positioning property, not just `transform`: the Level 2 individual properties `translate`/`rotate`/`scale`, the SVG geometry properties `cx`/`cy`/`r`/`x`/`y` (CSS beats the presentation attribute), and CSS motion path. Bake the offset into the coordinates. `line-height`, `color` and font declarations are untouched — they do not move anything.

#### Anti-patterns

- Moving a dot along the value axis to open up space — the type's one unforgivable error.
- Binning or averaging before plotting (that is a histogram wearing a costume), or quietly dropping the inconvenient outlier.
- Dot size as a second encoding (that is the **bubble variant**), or opacity as a value encoding while also dodging.
- Meaning smuggled into the swarm axis: sorting the dodge by a second variable, or a midline drawn as if it were a scale.
- A hue per group instead of one ink plus a single accent.
- A title about the median or the tail with no line drawn for it, or a line that does not match the data.
- A full grid, a `LEGEND` heading, a rotated axis title, or small-caps labels.
- Labelling more than the focal dot and a handful of outliers.
- Positioning a dot, a bound label, a tick or an ancestor group from CSS — `transform`, `translate`, `rotate`, `scale`, a geometry property (`cx`/`cy`/`r`/`x`/`y`) or a motion path — whether as an attribute, an inline `style`, or a rule in a `<style>` block.
- Two dots wearing the same `data-name`, or an empty one: a name that identifies two marks identifies neither.
- An unbound visible string: a label or an axis tick with no attribute stating the same thing.

## Examples

- `assets/example-scatter.html` — minimal light
- `assets/example-scatter-dark.html` — minimal dark
- `assets/example-scatter-full.html` — full editorial
- `assets/example-bubble.html` — bubble, minimal light
- `assets/example-bubble-dark.html` — bubble, minimal dark
- `assets/example-bubble-full.html` — bubble, full editorial
- `assets/example-beeswarm.html` — beeswarm, minimal light
- `assets/example-beeswarm-dark.html` — beeswarm, minimal dark
- `assets/example-beeswarm-full.html` — beeswarm, full editorial
