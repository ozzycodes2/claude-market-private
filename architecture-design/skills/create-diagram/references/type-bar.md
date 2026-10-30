# Bar / Column Chart

**Best for:** comparing discrete quantities across categories or time intervals — sprint velocity, monthly revenue, feature adoption, cohort counts. Use when each category has a single numeric value and the comparison between bars is the primary message — or, in the dumbbell variant below, exactly two values whose difference is the message.

## Layout conventions

- **Orientation:** Vertical bars (columns) are default. Horizontal bars are appropriate when category labels are long or you have more than 8 categories.
- **Plot area margins:** left 80px, bottom 60px (category labels), top 40px, right 40px — inside a `0 0 1000 500` viewBox.
- **Bar count cap:** 4–16 categories. Past 16 → sorted horizontal bars (longest first, one row per category), or small multiples: identical frame, identical scales, one panel per category group, a direct title on each panel.
- **Bar width:** ≥ 50% of the column pitch (the gap should never exceed the bar). Typical: pitch=110px, bar=72px.
- **Each value is encoded once.** Every bar prints its value, so the chart carries no gridlines, no value-axis line and no tick labels — they would draw the same number a second time. The only rule is the zero baseline at `soft`, 1px: the baseline is what the bars are read against, so it is not a hairline. A bar chart that omits per-bar value labels instead takes sparse tick labels and a range frame (axis line spanning only the data's min → max), with at most 4 gridlines at `ink @ 0.08`.
- **Axis title:** one horizontal line above the plot, left-aligned to the plot at x=80, y=28, `eyebrow` role 7px `muted`, sentence case with no tracking ("Story points per sprint"). Never rotated.
- **Category labels:** centered below each bar, `node-name` role 11px 600 for category names.
- **Value labels:** `arrow-label` role 8px above each bar (baseline `top − 8`). Focal bar label in `ink` at weight 600; others in `muted`.
- **Focal bar:** 1 bar max in accent fill/stroke. All others in `muted @ 0.15` fill + `muted` stroke. Say what makes it focal in place, with an event marker (below) rather than a legend key.
- **Comparison line:** every bar chart shows the comparison its data supports (target, average, prior period): a `soft` 1px line dashed `4,3` across the plot, declared `data-reference="<value>"`, with a direct sentence-case label at its right end, `arrow-label` role 8px `muted`, set clear of the value labels. Drawn after the bars so it reads across them.
- **Direct labels first.** Name things where they are. A legend strip is kept only for encodings that cannot be labelled in place; when the keys all name a bar (focal, "other"), drop the strip. There is no "LEGEND" heading in any case.
- **Event markers:** when a card or caption explains why a bar changed, mark the cause on the chart: `<g data-event="S4" data-event-label="API shipped late">` holding a `soft` 1px rule dashed `2,3` at the bar's centre and an italic `ink` callout that says the cause, not the mark ("Record high" says nothing). `data-event` equals the category label; `scripts/verify-bar.py` fails a marker that is more than 0.5px off that bar's centre or names no bar. The rule stops above the value label so it never strikes through a number.
- **Source line:** one `<text data-role="source">` at x=40, y=478, 8px mono `muted`. Fixed order: origin and period, then units, then encoding notes ("Source: team sprint tracker, 8 two-week sprints to Oct 2026. Story points. Bars start at zero.").

### Data binding

The plot declares its scale and every bar its value, so `scripts/verify-bar.py` can hold the drawing to the data (see `type-line.md` for the same pattern on a slopegraph).

```svg
<g data-plot="bar" data-orient="vertical" data-domain="0 120" data-baseline="420" data-top="40">
  <rect x="99" y="192" width="72" height="228" data-name="S1" data-value="72" .../>
  <text x="135" y="184" data-for="S1">72</text>
  <line x1="80" y1="103.3" x2="960" y2="103.3" data-reference="100" .../>
</g>
```

`data-domain` is `lo hi` and `lo` must be 0; `data-baseline` is the pixel position of `lo` and `data-top` of `hi` (for `data-orient="horizontal"`, an x position). Bar length = (value ÷ hi) × (baseline − top), rounded to the pixel; the checker allows 0.75px. The group carries no `transform`, and no bound mark does. `scripts/verify-bar.py` fails on: a domain that does not start at zero, a bar not proportional to its value or off the baseline, a label that does not equal its bound value (or a bar with none), a gridline, value-axis line or tick label beside labelled bars, a reference line off the scale, rotated text, any transform, more than 16 bars, and a file that claims to be a bar chart but yields no parseable bar. `scripts/test-verify-bar.py` proves each in both polarities.

### Bar element pattern

```svg
<!-- Opaque paper mask prevents bleed from background -->
<rect x="X" y="Y" width="W" height="H" fill="{paper}"/>
<!-- Bar body -->
<rect x="X" y="Y" width="W" height="H" fill="{muted @ 0.15}" stroke="{muted}" stroke-width="1"
      data-name="Category" data-value="VALUE"/>
<!-- Value label above bar -->
<text x="X+W/2" y="Y-8" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="middle" data-for="Category">VALUE</text>
```

Focal bar: replace fill with `accent @ 0.12` and stroke with `accent`; the label stays `ink` at weight 600 (the accent paints objects, never type).

## Anti-patterns

- More than 16 bars (past the cap, sorted horizontal bars or small multiples).
- Gridlines, a value-axis line or tick labels on a chart that prints every value — the same number encoded twice.
- A rotated axis title; a legend whose keys name things that can be labelled in place.
- Truncated y-axis (not starting at 0) — distorts the magnitude comparison.
- Accent on more than 1 bar ("everything is important" = nothing is).
- 3-D bar extrusion — no shadows, no depth.
- Category labels rotated more than 45°; prefer short labels or horizontal chart instead.

## Variants

- **Grouped bars:** two bars per category, side by side. Use `accent` for the primary series and `series-1` for the secondary. Max 2 groups.
- **Stacked bars:** segments stacked to total. Use `accent` for the focal segment; muted tints for others. Document the total at the top of each stack.
- **Dumbbell:** one row per category, two dots on a single shared horizontal scale joined by a hairline. Use it for a two-state comparison where the *distance* between the ends is the message — before/after, two cohorts, target vs actual. Two series only; a third dot makes the connector meaningless and the figure is a dot plot.

### Dumbbell layout

- **Orientation:** horizontal only. Rows stack downward and the value axis runs left → right; a vertical dumbbell forces rotated category labels.
- **Plot area:** left margin 200px for row labels — this replaces the 80px margin above — so `x` 200→960, `y` 40→420 inside `0 0 1000 500`. Row labels right-aligned at x=188, `node-name` role 11px 600 `ink` (the category-label size this type already uses).
- **Rows:** the table below covers 4–8 rows; the chart cap is 16 rows (see below). Pitch and origin are fixed per row count so the block stays inside the plot band — a 64px pitch from y=96 overflows y=420 at seven rows:

  | rows | pitch | first row `y` | last row `y` |
  | --- | --- | --- | --- |
  | 4 | 88 | 96 | 360 |
  | 5 | 64 | 96 | 352 |
  | 6 | 64 | 76 | 396 |
  | 7 | 52 | 72 | 384 |
  | 8 | 48 | 68 | 404 |

- **No gridlines, no tick labels.** Both dots of every row print their value (see below), so the value axis is encoded once, by the labels. The only rule is the axis line at the domain floor: `soft` 1px, y 40→420.
- **Axis title:** the value axis carries the family's axis label — `eyebrow` role 7px `muted`, sentence case with no tracking ("Share of accounts, percent"), left-aligned at x=200, y=28, above the plot. Never rotated. The category axis needs no title: the row labels name themselves.
- **Dots:** r=6, positioned by value. Style by *series*: the reference end hollow (paper fill, `muted` stroke 1.5px), the focal end solid `accent` with a 1px `ink` stroke. Both marks therefore have a boundary above 3:1 even though the accent fill is not — see below. Fill weight, not hue, carries the pairing.
- **Accent marks the series, not a focal row.** The solid dot repeats on every row — the one place this variant departs from the one-accent rule above, because the two ends must be told apart in each pair. Do not additionally accent a "most changed" row; the sort order already carries rank.
- **Connector:** `ink @ 0.55` 1px (`rgba(23,23,23,0.55)` under the default light skin, the value `scripts/verify-dumbbell.py` checks), declared before both dots so the dots cap it. The connector is what says *these two dots are one row*, so it has to clear the 3:1 an object needs: 0.55 composites to 3.93:1 on light paper. It is not a hairline — but it is not the brighter mark either, since the axis takes `soft` at 5.83:1. Position and role separate the two, not weight: the axis runs the frame at the domain floor, the connector sits inside a row.
- **Endpoint positions round, they never snap.** `x = 200 + (v − floor) ÷ (ceil − floor) × 760`, with `floor` and `ceil` set by the axis rule below, rounded to the nearest integer pixel — at most 0.5px, below one rendered pixel. Data coordinates are exempt from the 4px grid; snapping them moves the data.
- **Value labels sit outside the pair, placed by geometry rather than by series.** A focal value *below* its reference reverses the dots, so derive `x_left = min(x_ref, x_focal)` and `x_right = max(x_ref, x_focal)`: left label right-anchored at `x_left − 12`, right label left-anchored at `x_right + 12`, both baseline `y + 4`, `arrow-label` role 8px `muted`, each still carrying its own series' value. Keying the offsets to start/end instead puts both labels *inside* the pair on every decreasing row.
- **Floor exception.** A value sitting on the domain floor lands its label at x=188, right-anchored on baseline `y + 4` — exactly the category label's anchor and baseline, so the two texts overlap. When `x_left − 12 < 200`, centre that label above its dot at baseline `y − 10` instead.
- **Series names are direct labels.** Name both series on the first row, above its dots: sentence-case `arrow-label` role 8px `muted`, centred over each dot at baseline `y − 12`. There is no legend strip and no "LEGEND" heading; the hollow/solid shape difference carries the pairing on every other row. The row order goes in the source line.
- **Row cap:** 16 rows. Past 8, divide the 336px row band evenly (pitch ≥ 20px) and shrink both dots to r=4 below a 28px pitch; past 16, sorted rows in small multiples with identical frame and scales.

**Why the dots differ by fill, not hue.** The focal bar pattern above (12% tint + accent stroke) does not transfer to a 6px dot: the 12% tint across a 6px-radius disc contributes roughly 14 square pixels of colour, so the mark reads as its stroke alone and the pair separates by hue only. A solid accent dot against a hollow one separates by shape, survives greyscale and colour-vision deficiency, and leaves hue as redundant encoding.

**Non-text contrast: the boundary carries it, not the fill.** The default accent clears the 3:1 WCAG 1.4.11 asks of a graphical object (4.71:1 on light paper, 5.21:1 on dark), but an onboarded accent may not, and shape redundancy does not waive that floor, because the reader still has to see the mark's edge and the line joining the pair. So neither is left to the accent: the solid endpoint takes a 1px `ink` stroke (11.82:1 against paper) and the connector takes 55% ink on light, 40% on dark (3.19:1 and 3.24:1). The hollow end already cleared it via its `muted` stroke at 6.11:1 light and 7.07:1 dark. `scripts/verify-dumbbell.py` asserts all four, so a later tint change cannot quietly drop one under the line. The hollow/solid shape difference stays as redundant encoding for greyscale and colour-vision deficiency — do not collapse the two dots to a single fill.

**Minimum drawn gap — never clamp it.** Both dots carry `r="6"`; the hollow one paints out to 6.75 because its 1.5px stroke straddles the path, so the marks touch at 12.75px of centre separation and below about 16px the pair reads as one blob — on a 0–100 domain across 760px, a data gap of 2.1 units. Do **not** widen the separation to clear it: moving a dot off its scaled position breaks the shared-scale rule below. Keep the true positions and shrink both marks (r=4 touches at 8.75px), or print the two values and mark the row as too close to resolve.

### Dumbbell element pattern

```svg
<!-- One row. Connector first so the dots cap it; labels outside the pair. -->
<line x1="458" y1="96" x2="740" y2="96" stroke="{ink @ 0.55}" stroke-width="1"/>
<circle cx="458" cy="96" r="6" fill="{paper}" stroke="{muted}" stroke-width="1.5"/>
<circle cx="740" cy="96" r="6" fill="{accent}" stroke="{ink}" stroke-width="1"/>
<text x="446" y="100" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="end">34</text>
<text x="752" y="100" fill="{muted}" font-size="8" font-family="{arrow-label}">71</text>
<text x="188" y="100" fill="{ink}" font-size="11" font-weight="600" font-family="{node-name}" text-anchor="end">Platform</text>
```

Values 34 and 71 on a 0–100 domain compute to 458.4 and 739.6, rounded to 458 and 740. Had this row fallen instead, the accent dot would sit on the left; the two anchors stay tied to left and right, and each label carries its own series' value.

**Dark theme.** Dots and labels keep their roles and take the dark column of [`style-guide.md`](style-guide.md): hollow `paper` fill with a `muted` stroke, solid `accent` with an `ink` stroke, labels `muted`. **The connector opacity changes too:** connector `ink @ 0.40` (`rgba(247,248,248,0.40)` under the default dark skin), which composites to 3.52:1 and clears 3:1 for the same reason as on light paper. The axis is not on this ramp at all — it takes `soft` (`#8a8f98`, 6.42:1), as `example-bar-dark.html` ships it. Resolve `ink` against the dark column, never the light one: in the default skin light `ink` *is* dark `paper`, so a connector, gridline, or axis carried over from light composites to exactly 1.000:1 and the gap encoding and the scale both vanish.

### Dumbbell honesty rules

- **Never truncate the value axis.** `floor` and `ceil` follow the data's range, never its observed extremes — taking `min` and `max` as the bounds *is* the truncation. With `lo` and `hi` the smallest and largest values, the four cases are exhaustive: `lo >= 0` anchors `floor = 0` and rounds `ceil` up past `hi` (including fractional data smaller than a fixed absolute tolerance); `hi <= 0` anchors `ceil = 0` and rounds `floor` down past `lo`; `lo < 0 < hi` brackets both sides, and zero then falls inside the plot — give it a line at its scaled position in the axis-line weight, since it is what every gap is read against. The fourth case is the one a sign-based rule drops: **when every value is zero**, `lo == hi == 0` would make `ceil - floor` zero and the position formula divide by zero, so take a finite fallback span (`floor = 0`, `ceil = 1` in the data's unit) and let every dot sit on the floor, which is the truth. Data that merely *touches* zero is covered by the first two cases, not a special one. `scripts/verify-dumbbell.py` implements this and proves finite coordinates for all four. The plot width is fixed, so narrowing the domain raises px-per-unit and draws every gap wider: across the same 760px, an 8-point gap is 61px on a 0–100 axis and 152px on a 40–80 axis. Ratios *between* rows survive the zoom — what inflates is each gap's size against the frame, which is how a reader judges whether a gap is large. The gap is the entire claim, which makes this the most common way a dumbbell lies.
- **Both dots share one scale and one unit.** Label both endpoints with their real values. Labelling only the focal end asks the reader to take the geometry on trust.
- **The connector is a gap, not a trajectory.** It encodes the distance between two values and nothing about what lies between them — no intermediate points, no rate, no guarantee the change was monotonic. Do not narrate it as movement.
- **State the row order** in the source line: by one endpoint, by signed change, by absolute change, or by an order the subject supplies (chronological, geographic, ordinal). "By gap" alone is ambiguous — say signed or absolute. What is not allowed is an unstated order, which reads as arbitrary.
- **A row missing an endpoint is disclosed, never imputed and never silently dropped.** Removing incomplete categories without saying so changes the population being compared. Either draw the known end and name the missing value, or drop the row *and* record which rows went and why — a lone dot is otherwise indistinguishable from two coincident dots, which is to say from a genuine zero gap.

Two of these rules live in a formula rather than a drawing, so they are executable: `scripts/verify-dumbbell.py` resolves the domain over every sign case and asserts finite coordinates and 3:1 marks, and `scripts/test-verify-dumbbell.py` exercises both polarities — including all-zero and zero-touching data, and the sub-3:1 treatments this replaced. The checker reads the tokens out of this file, so prose and thresholds cannot drift apart. A shipped dumbbell example would additionally owe a check of drawn positions against the values printed at them.

## Examples

- `assets/example-bar.html` — minimal light
- `assets/example-bar-dark.html` — minimal dark
- `assets/example-bar-full.html` — full editorial

All three are checked by `scripts/verify-bar.py --all`.

Dumbbell domain resolution retains finite bounds for representable subnormal and extreme values. If the next nice ladder step would overflow, the finite extreme is used; opposite-sign extreme domains are scaled without overflowing their span.
