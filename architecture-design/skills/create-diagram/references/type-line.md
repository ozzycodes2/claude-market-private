# Line Chart

**Best for:** continuous trends over time or a sequential index — signups over weeks, revenue by month, latency over releases. Use when the direction and rate of change between points is the primary message.

## Layout conventions

- **Plot area:** inside a `0 0 1000 500` viewBox. The plot is as wide as the story needs, not as wide as the canvas: leave room right of the last point for the end labels. The shipped example runs x 80 → 472 at a 56px pitch, y 80 → 410 on `y = 500 − 2·value`.
- **Points:** 4–12 per series. Fewer → consider a summary stat; more → aggregate into periods.
- **Range-frame axes.** Each axis rule spans only the data: the y rule runs from the data minimum to the data maximum, the x rule from the first point to the last. The rules sit just outside the data (y at `x=64`, x at `y=428` in the example), `soft`, 1px. Tick labels sit at the two ends of each rule (the data min and max) plus at most one round value between; the ends are the only numbers a reader needs to calibrate the rest. A rule that runs past the data measures nothing.
- **Say when the axis does not start at zero.** A range frame starts at the data minimum, so the source line states it ("Y axis spans 45 to 210, not from zero"). A line is read for direction and rate, which survive a moved origin; a magnitude story (how many, not how fast) keeps zero in the frame.
- **No gridlines by default.** The direct end labels and the sparse ticks carry the scale. Keep gridlines only when reading a value across a wide plot genuinely needs them, then at most four, `ink @ 0.08`, and justify them in the source line's neighbourhood or the card copy.
- **Axis title:** sentence case, horizontal, at the top of the y axis and left-aligned to it (`x=64`, `y=60` in the example). No rotated text anywhere; a rotated title forces the reader to tilt their head for the one string that names the unit.
- **X-axis labels:** evenly spaced period labels under the x rule, `sublabel` mono at 9px, centred on each point's x.
- **Lines:** `<polyline>` with `fill="none"`. Focal series `stroke-width="1.8"`, others `"1.2"`.
- **Vertex dots:** one dot, on the focal series' last point (`r=4`, filled), anchoring its end label. No dots on the other series, and no dot per vertex: the polyline's bends already mark each measurement.
- **Area fill is not decoration.** Series are one-dimensional (a value per period), so no polygon under them. Fill the area only when the area itself is a quantity, the cumulative total or an accumulated amount, and then mark the polygon `data-area="cumulative"`.
- **Direct labels at the last point.** Every series is named at its own last vertex, 16px to its right and on its row: the name in `node-name` (Inter 11px; `ink` at 600 for the focal series, `muted` at 500 for the rest). The names are the identifier; a legend strip is dropped whenever every series carries one. A key is only for an encoding that cannot be written in place, and a line chart has none.
- **Comparison line.** Draw at least one comparison the data supports: a target, an average, or the prior period. A `soft` 1px line dashed `4,3`, under the data, with a sentence-case label at its right end (`arrow-label` role, 8px, `muted`). Bind it with `data-ref` and `data-value` so its y is held to the same scale as the series.
- **Banking.** Choose the plot's proportions so the dominant slopes average about 45° (Cleveland's banking): flatter than about 15° hides rate changes, steeper than about 70° exaggerates them. Compute the median absolute segment angle of the focal series, then change the plot's width-to-height ratio, never the data scale, until it nears 45°. The shipped example averages about 28° on its focal series, with a 56px pitch against 2px per signup; the zero-based reading would flatten it further. Banking tunes proportion; it never licenses a truncated axis without the statement above.
- **Source line:** one `data-role="source"` text under the plot, sentence case, stating the data source, the period, units, and anything the frame leaves out (the axis bounds when not from zero, what a dashed line is). Money across periods says "nominal" or "real (base year)".
- **Series cap: six.** The limit is end-label collisions, not the lines: two end labels closer than 10px mean the series are too close to name in place. Past six, or when labels collide, split into small multiples: identical frame, identical scales, one panel per series, a direct title per panel.

### Telling series apart, honestly

The skin has one chroma, so series cannot be told apart by hue. The identifier is the end label; everything below is a secondary cue to help trace one line through a crossing.

| Series | Stroke | Dash |
|---|---|---|
| focal (1 only) | `accent`, 1.8px | solid |
| 1 | `ink` | solid |
| 2 | `muted` | `6,3` |
| 3 | `soft` | `2,3` |
| 4–5 | `ink` at 0.74, then 0.62 | solid |

- The three dash patterns are the style guide's series table; a fourth pattern is not distinguishable from them at 1.2px. A chart that needs more than four patterned lines is not distinguished by pattern at all: series 4 and 5 take an ink-opacity ramp, the slopegraph's (`0.80 → 0.62`, **floor 0.53**, where an `ink` stroke crosses 3:1 on light paper).
- The cap of six is therefore the accent focal, three patterned series, and two ramp series. **That is only legitimate because every series is labelled at its end**: the dash and the opacity are never the only way to tell two lines apart, so a reader who cannot resolve them loses a convenience, not the data. If a series cannot be end-labelled, the chart is over its cap.
- The accent marks the editorially focal series, not the biggest. At 3.06:1 on light paper it clears the 3:1 floor for a mark and misses the 4.5:1 floor for a word, so it never sets text: end labels stay `ink` or `muted` on every series including the focal one.
- Focus is carried by stroke weight (1.8px against 1.2px) as well as by the accent, so it survives greyscale.

### Polyline pattern

```svg
<!-- Comparison, under the data -->
<line data-ref="target" data-value="150" x1="80" y1="200" x2="472" y2="200"
      stroke="{soft}" stroke-width="1" stroke-dasharray="4,3"/>
<text data-ref="target" data-role="label" x="488" y="203" fill="{muted}" font-size="8" font-family="{sublabel}">Target: 150 a week</text>

<!-- A series: values bound on the line, y = 500 - 2*value, x on one shared grid -->
<polyline data-line="Organic" data-values="120,135,148,162,155,178,195,210"
          points="80,260 136,230 192,204 248,176 304,190 360,144 416,110 472,80"
          fill="none" stroke="{accent}" stroke-width="1.8" stroke-linejoin="round"/>
<circle cx="472" cy="80" r="4" fill="{accent}"/>
<!-- Its end label, bound to the series and placed at its last point -->
<text data-line="Organic" data-role="name" x="488" y="84" fill="{ink}" font-size="11" font-weight="600" font-family="{node-name}">Organic</text>

<!-- A y tick, bound to the number it prints, at the data max -->
<text data-tick="y" data-value="210" x="56" y="83" fill="{muted}" font-size="8" font-family="{sublabel}" text-anchor="end">210</text>
```

`data-line` is this contract's own series attribute, deliberately not `data-series` (slopegraph, bump), `data-layer` (streamgraph) or `data-bins` (ridgeline), so no sibling checker claims a line file. `scripts/verify-line.py` binds `data-values` on every polyline and holds every vertex to one linear y scale and one x grid; holds each y tick, the range-frame rules and the comparison line to the same scale; requires each series' end label to name it, sit right of its last point on its row, and stay 10px clear of its neighbours; refuses a legend once every series is labelled, any rotated text or transform, a filled area under a series, more than six series, more than four gridlines, and a series fainter than the 0.53 ink floor. `scripts/test-verify-line.py` proves each check in both polarities and pins the scope treaty. Its `--all` globs `example-line*.html` only, so the variant files below belong to their own checkers.

## Anti-patterns

- A legend strip when every series can be named at its end.
- More than six series, or end labels closer than 10px (visual mush: split into small multiples).
- Hue to tell series apart, or a dash pattern as the only identifier.
- An axis rule that runs past the data, a frame around the plot, or a grid in every direction.
- A rotated axis title, or an axis title in caps with tracking.
- An area fill under a one-dimensional series.
- A dot on every vertex.
- No comparison: a trend with no target, average or prior period beside it.
- A truncated y axis that the source line does not state.
- Smoothed or spline curves when the underlying data is sampled; a polyline is honest.
- Connecting discontinuous data segments without a visual gap.

## Variants

- **Slopegraph:** exactly two states, several series, read as slope and rank change. Full spec below. Its shared quantitative scale must be finite and nonzero; a flat value axis cannot encode distinct values.
- **Ridgeline:** one distribution per series, stacked with deliberate overlap on one shared amplitude. Full spec below.
- **Streamgraph:** many periods, few layers, read as a total and its composition breathing. Full spec below.
- **Bump chart:** rank movement across 3–6 ordered snapshots, position only. Full spec below.

### Slopegraph

**Best for:** change between exactly **two** comparable states across several series — two years, before and after, two cohorts, two scenarios. The reading is threefold and no other type gives all three at once: direction (up or down), steepness (how fast), and **crossings** (who overtook whom). Tufte's original (*The Visual Display of Quantitative Information*, 1983) is a table whose rows have been given an angle — every number is still printed, which is why both endpoints keep their labels here.

Not for: three or more states (that is the **line chart** above, or a bump chart); a single series (write the sentence instead); ranking at one moment with no change (use a **bar chart**); or two variables measured in different units (use a **scatter plot** — a slope between unlike units means nothing).

#### Layout conventions

- **Two vertical axis rules**, `y` 40 → 420 inside a `0 0 1000 500` viewBox, at `x` 320 and `x` 680. The plot sits inside `x` 40 → 956. The value-axis caption is horizontal, sentence case, 8px, set at `y=28` and left-aligned to the left axis rule (`x=320`); no text is rotated. The source line sits at `y=478` from `x=40`, sentence case with no tracking and no `LEGEND` heading word, above the rule at `y=462`; the one key that survives sits at `492` with its text at `496`.
- **Keep the run narrower than the plot is tall.** The 360px run against a 380px height puts the steepest shipped slope at 35° and the flattest at 4° — the spread you need before "halved" and "barely moved" look like different claims. Widening the run flattens every slope toward horizontal and throws away the comparison the type exists to make; the leftover width belongs to the label gutters, which need it.
- **Label gutters:** on the left, names right-aligned ending at `x=272` and values right-aligned ending at `x=304`; mirrored on the right from `x=696` (values) and `x=728` (names). Size the gutter to the longest name — a name that collides with the axis is the one thing here you cannot fix by moving a coordinate.
- **State captions** in sentence case (`Before`, `After`) at 9px mono, centred under each axis at `y=440`, untracked. The tracked-caps `eyebrow` register is for type tags only.
- **Series count:** 4–10 — deliberately more than the parent chart's cap of 6. That cap exists because eight-vertex polylines tangle in mid-plot and their end labels collide; a slopegraph has no mid-plot, so what sets the ceiling here is endpoint labels colliding, not the lines. Below 4 a sentence or a pair of bars says it better.
- **No gridlines.** Every endpoint prints its own value, so a gridline carries nothing the figure has not already said; the two axis rules *are* the scale. The parent line chart also drops gridlines by default; here the rule is absolute, because two printed endpoints per series leave nothing for a grid to read.
- **Domain:** pick round bounds that contain the data and state them in the source line. The shipped example runs 100–550ms over `y` 420 → 40, i.e. 0.84px per millisecond. The parent chart's "say when the axis does not start at zero" rule is met by stating the bounds, and the origin does not matter here: a slope is unchanged by moving the origin, provided *both* axes move together. What a tight domain does do is magnify every slope equally, so state the bounds and let the reader calibrate.
- **Legend keys only for what cannot be labelled in place.** Every series is named at both ends, so no key repeats a series name. The two keys that remain explain encodings: the accent heavier line ("the only regression") and the ink-tone ramp. Each is a 24px line plus its dot, because the key has to show stroke weight. No key names a series.
- **No comparison line, by exception to the house rule 5.** A slopegraph already is the comparison (before against after, on one scale). A median or target line across two states would be a third reference the two-state design cannot place: it would add ink that repeats the slope's own question. If a target exists, state it in the source line.
- **Dots at both endpoints** — `r=3` non-focal, `r=4` focal. Also a departure: the line chart puts dots on the focal series only, because it has eight vertices per series and dots everywhere would be mush. A slopegraph has exactly two per series and both are where a value is read.
- **4px grid** applies to the designed constants — axis positions, gutter edges, state-caption baselines. Endpoint `y` values are data-scaled and exempt; snapping them would move the data. Two inherited constants are also off-grid and stay that way: the legend rule at `y=462` and the source baseline at `478`, which every chart type in `assets/` shares. Matching the house rhythm beats matching the grid here — moving them 4px would misalign this variant against the other chart types to satisfy a rule none of them satisfies either.

#### Colour

- **One accent, and an `ink` opacity ramp for everything else.** The skin has no series palette; the parent line chart separates series by direct end labels, dash and the same ramp. Here every series is named at both ends, so the ramp is a tracing aid and nothing more, and a second encoding of something the labels already carry would spend the accent for nothing.
- **The ramp runs 0.80 → 0.62**, ordered by the left-hand value. The hard floor is **0.53** — that is where an `ink` stroke crosses 3:1 against light paper (0.53 measures 3.03:1, 0.52 measures 2.95:1), and every line in this figure is data, not decoration. The shipped ramp bottoms out at 0.62 (3.84:1) rather than hugging the floor, because a ramp whose lightest member is only just legible has no room left to add a series.
- **Note what the ramp does not buy you.** It separates the ends of the range, not adjacent members — 0.80 and 0.74 are not distinguishable at 1.2px, as the shipped example shows. It is there to help trace one line through a crossing. It must never be the only way to tell two series apart; that is the labels' job.
- **The accent marks the editorially focal series, not the best or the biggest.** In the shipped example it marks the one service that got *worse*.
- **Focus is carried by stroke weight, not tone** — 2.4px focal against 1.2px. The skin's `accent` measures **3.06:1 on light paper** and 6.42:1 on dark, below the top of the ink ramp it is meant to dominate, so weight is the only cue that survives both skins and greyscale.
- **Be honest about what that leaves.** 3.06:1 clears WCAG 1.4.11's 3:1 floor for a graphical object by a thin margin, and a heavier stroke does not raise a contrast ratio — it only makes the mark easier to find. The focal line therefore clears the bar on redundancy as well as contrast: its position and its endpoint labels (`ink` and `muted`, both above 4.5:1) carry the data, and its accent adds only *which series is focal*, which the key states in words and the stroke weight repeats. Nothing here rests on the accent alone.
- **Labels stay `ink` (names) and `muted` (values) on every series, including the focal one.** The accent never sets type: it misses 4.5:1 on light paper, and a focal value label in accent is the most common way to make a slopegraph fail contrast while looking deliberate.
- **Legend wording must be skin-neutral: "strongest tone", never "darkest".** The ramp is ink-at-opacity, so the top of it is the darkest line on light paper and the *lightest* on dark. A legend that says "darker is higher" ships false in one of the two variants — and it renders perfectly in both, so only reading the dark file catches it.

#### Honest-data rule

**Both axes must carry the same scale and the same units.** That is the entire claim of the type: if the scales differ, the angle of every line is fiction. `scripts/verify-slopegraph.py` gates it.

- **The two axes must never differ from each other** — not in scale, not in origin, not in transform. A shared *origin* matters as much as a shared scale: shifting one axis tilts every slope by the same amount, so the series still rank correctly against each other while every rate is wrong. That is the harder version to spot by eye, which is why the checker tests slope and origin separately.
- **A domain tighter than zero is fine; an undisclosed one is not.** Both axes sharing a 100–550 window is legitimate, because moving the origin leaves every slope unchanged when both axes move together — this is exactly where a slopegraph differs from a bar chart, whose truncated baseline distorts the ratio between bars. What a tight window does do is magnify all slopes equally, so the bounds go in the source line and the reader calibrates. Log-scaling is a different matter and stays out: it makes the angle mean nothing.
- **Label both endpoints with actual values.** A slope with no magnitudes is a mood.
- **Round once, then draw from the rounded number**, so the printed label, the declared metadata and the drawn `y` are three statements of one number rather than three chances to disagree.
- **If a series is missing an endpoint, drop it and say so.** Never interpolate to complete a line.
- **Crowded endpoint labels are data.** When two series sit a few tenths apart their labels crowd *because the values are close*. Moving a point to open up space converts a legibility problem into a false statement — and it is invisible afterwards, because the label you moved it for now sits comfortably beside the wrong position. This is the specific defect the gate exists for.
- **Two series that coincide at both endpoints cannot be separated at all.** Merge them into one labelled line, or drop one and name the omission in the source line. What you must not do is nudge them apart, which is the same defect as above wearing a better excuse.
- **The straight line is a connector, not a trajectory.** Two endpoints say nothing about the path between them: the underlying series may have dipped, spiked, or crossed three times. So never read an intermediate value off a slope, and never annotate a crossing with a date. In the shipped example one service regresses while four improve, so its line crosses three others; none of the three crossings is annotated, and the card beside the figure says why.

#### Declaring the values

**Every visible string that carries meaning is bound to an attribute stating the same thing.** That is the whole contract, and it exists because each unbound string is a place the figure can be made to lie while every geometric check stays green.

```svg
<!-- State captions: data-axis names the axis, data-state binds the text -->
<text data-axis="from" data-state="Before" x="320" y="440" fill="{muted}" font-size="9" font-family="{sublabel}" text-anchor="middle">Before</text>
<text data-axis="to" data-state="After" x="680" y="440" fill="{muted}" font-size="9" font-family="{sublabel}" text-anchor="middle">After</text>

<!-- A series: the line declares its two values, and each of its four labels
     declares which series and which end it belongs to -->
<line data-series="Recommender" data-from="238" data-to="431"
      x1="320" y1="303.5" x2="680" y2="140.5" stroke="{accent}" stroke-width="2.4"/>
<circle cx="320" cy="303.5" r="4" fill="{accent}"/>
<circle cx="680" cy="140.5" r="4" fill="{accent}"/>
<text data-series="Recommender" data-end="from" data-role="name" x="272" y="307" fill="{ink}" font-size="11" font-weight="600" font-family="{node-name}" text-anchor="end">Recommender</text>
<text data-series="Recommender" data-end="from" x="304" y="307" fill="{muted}" font-size="9" font-family="{sublabel}" text-anchor="end">238</text>
<text data-series="Recommender" data-end="to" x="696" y="144" fill="{muted}" font-size="9" font-family="{sublabel}">431</text>
<text data-series="Recommender" data-end="to" data-role="name" x="728" y="144" fill="{ink}" font-size="11" font-weight="600" font-family="{node-name}">Recommender</text>
```

Non-focal series: `stroke="{ink @ 0.68}"` at `stroke-width="1.2"`, dots `r=3`, names at `font-weight="500"`.

What each binding buys, and what it costs to omit:

| Binding | Without it |
|---|---|
| `data-from` / `data-to` on the line | The checker would have to read the labels, and a series whose label went missing would drop silently out of the verified set — the exact hole that let a treemap cell ship 50% oversized. |
| `data-end` on a value label | A printed number could not be cross-checked against the value it claims to state. |
| `data-role="name"` on a name label | Two series names could be exchanged between rows, renaming both lines, with every number still correct in isolation. |
| `data-axis` on a state caption | The captions could be swapped, reversing the direction every slope is read in. |
| `data-state` on a state caption | Swapping just the two visible strings leaves both captions in place and reverses the figure anyway. |

`scripts/verify-slopegraph.py` requires all of them, cross-checks each visible string against its binding, and reports any label drawn nearer another series' endpoint than its own — a label on the wrong row renames the line.

**No `transform` on any of it.** The checker reads raw `x`/`y` attributes, so a `transform` on a series line, on a bound label, on an ancestor `<g>`, or in a CSS rule moves the rendered mark away from the number that was verified — `transform="translate(0 80)"` on one line slid its endpoint 80px past every green check. Transforms are rejected rather than resolved: a partial implementation of the SVG transform stack looks like coverage without being it. Bake the offset into the coordinates. The value-axis caption is horizontal and unbound — it is neither verified geometry nor a bound label.

**Print one complete number per value label.** A unit suffix is fine (`208ms`); a thousands separator that changes the value is not, and neither is a second number in the same label. Reading only the first numeric fragment let the label `512,000` agree with metadata that said `512`.

#### Anti-patterns

- Different scales, different units, or different origins on the two axes — the type's one unforgivable error.
- A value axis whose two halves disagree, or a tight domain the source line never states.
- Moving an endpoint to make room for its label.
- More than 10 series (labels collide) or fewer than 4 (a sentence is shorter).
- Three or more state columns — that is the parent line chart, or a bump chart, not this.
- One hue per series instead of the ink ramp plus a single accent.
- A value label in `accent`, or any text in the accent at all.
- A legend key that repeats a series name already printed at both ends.
- Gridlines, or a value axis that repeats numbers the endpoints already print.
- Annotating the crossing with a date, or reading any intermediate value off a slope.
- A `transform` on a series line, a bound label, an ancestor group, or in CSS — it moves the mark away from the checked coordinate.
- An unbound visible string: a name, a value or a state caption with no attribute stating the same thing.
- Curving the connector. There is nothing between the two points to curve through.

### Ridgeline

**Best for:** one **distribution** per series, stacked at a fixed pitch with deliberate overlap, when the shape of each distribution is the story and the series are directly comparable — request latency per service, build duration per pipeline, session length per cohort. The line chart above plots one value per x; a ridgeline plots a whole distribution per row, and the reading is the silhouette: where the mass sits, how tight it is, whether there is a second peak. A p50/p99 pair cannot show a bimodal service, and a box plot flattens it to a rectangle.

Not for: a single distribution (that is a histogram — one ridge is a ridgeline with the comparison removed); series measured in different units or on different x-ranges, which cannot share the one x-scale the type requires; time series, where each row is one value per moment rather than one distribution; or distributions so similar that the ridges are five copies of one shape, which a table of percentiles says shorter.

#### Layout conventions

- **One baseline per ridge at a fixed pitch**, inside the `0 0 1000 500` viewBox the other Line variants use. The shipped example runs five baselines at `y` 152/208/264/320/376, a 56px pitch.
- **The x-run is the slopegraph's**, `x` 320 → 680, sampled at 13 bins 30px apart. The gutters are symmetric about it: names right-aligned ending at `x=304`, ranges starting at `x=696`, both 16px clear of the plot.
- **Name left of the baseline, range right of it**, each on its ridge's own row (`y = baseline + 3.5`). The range is the span of the ridge's nonzero mass in x-axis units, which is the number a silhouette cannot give you.
- **Bin ticks** in the 9px mono `sublabel` role at `y=400`, centred on bin positions and untracked, with the sentence-case x-axis caption at `y=424`. The amplitude caption is horizontal, sentence case, 8px, at `y=28` left-aligned to the first bin column (`x=320`); no text is rotated. The source line is sentence case at `y=478`, with no `LEGEND` heading word.
- **No comparison line, by exception to the house rule 5.** Every ridge is already compared with every other on one shared x-scale and one amplitude; a pooled median or target line drawn through the stack would cross rows it does not belong to and read as a value on a swarm of baselines. Percentiles belong in each ridge's printed range.
- **Ridge count 3–12, bins 8–40.** Below three ridges there is no family of shapes to compare and two distributions are a pair of small multiples; past twelve the stack is taller than a reader can hold one silhouette in mind across. Below eight bins the outline is a histogram wearing a curve's clothes; past forty the bins are narrower than the noise in them.
- **Straight segments between bins, closed with `Z`.** Not splines: the source line states the drawing is unsmoothed, and a curve through binned counts puts extrema between bins that the sample never measured. The draft this variant came from permits Catmull-Rom with vertices on true values; the shipped grammar does not use it, because unsmoothed bins need no footnote about what the curve is allowed to invent.
- **No gridlines.** The baselines are the rules, and every ridge prints its own range.

#### Colour

The slopegraph's colour section holds here unchanged, with one addition for the fill. One accent on the editorially focal ridge (stroke `accent`, fill the accent at `0.16`), an `ink` opacity ramp for the rest (`0.80 → 0.62`, floor `0.53`) ordered top row to bottom, and focus carried by stroke weight — 2.4px against 1.2px — rather than tone. Labels stay `ink` (names) and `muted` (ranges) on every ridge including the focal one.

- **Fill `ink` at `0.12` on every non-focal ridge**, low enough that two overlapping ridges read as depth rather than as a third tone. This is the one place the type needs a fill at all: the outline alone does not say which side of the curve is mass.
- **Legend wording stays skin-neutral** — "strongest tone", never "darkest". The ramp is ink-at-opacity, so its top is the darkest line on light paper and the lightest on dark, and a legend that says "darker" ships false in one of the two skins while rendering perfectly in both.
- **The accent marks the ridge the story is about, not the worst performer.** In the shipped example it marks the service whose *shape* is unusual, not the slowest one.

#### Honest-data rule

**One amplitude on every ridge, stated in the source line.** That is the entire claim of the type: the ridges are stacked so their silhouettes can be compared, and per-ridge normalisation destroys exactly that while rendering beautifully — a rare, flat distribution given its own scale wears the same shape as a tight one. `scripts/verify-ridgeline.py` derives the figure's single amplitude and holds every vertex of every ridge to it.

- **The baseline never lies.** Each ridge declares the row it rises from, and that row must sit on the stack's fixed pitch with its rule drawn across the full bin run. A baseline nudged up to give one ridge headroom is the same falsification as a private amplitude, told with different arithmetic — and it is the harder one to see, because the silhouette above it is untouched.
- **Every ridge shares one x-scale.** A peak at one x means one latency on every row, or the column comparison the type exists for is fiction.
- **State the overlap, and keep it overlap.** Ridges are meant to intrude on the row above — that is how the stack reads as depth. A peak that reaches the row *two* above is occluded by the peaks it passes, and the fix is more pitch, never a smaller amplitude on one ridge. The checker enforces the ceiling; the source line states the amplitude so the reader can convert a height back into a number.
- **A ridge starts and ends on its own baseline.** The first and last bins are zero, so the outline closes along the baseline. A distribution clipped mid-mass draws a cliff, and a cliff reads as data.
- **No smoothing beyond what the footnote states.** The shipped grammar smooths nothing at all. If a figure ever does smooth, the footnote names the method and the vertices stay on true values — a spline that invents a second peak is indistinguishable, on the page, from a service that has one.
- **Height is share, not volume.** Each ridge is normalised to its own series' count before the shared amplitude is applied, so the tallest ridge is the most concentrated, not the busiest. Say so in the source line; a reader who assumes height is traffic reads the figure exactly backwards.

#### Declaring the values

The binding contract is the slopegraph's, applied to areas: the outline declares its bins and its baseline, and every visible string is bound to what it describes.

```svg
<line data-ridge="checkout-api" data-role="baseline" x1="320" y1="320" x2="680" y2="320" stroke="{soft}" stroke-width="1"/>
<path data-ridge="checkout-api" data-baseline="320" data-bins="0,1,6,17,21,14,8,6,7,9,7,4,0" d="M320,320 L350,317.6 L380,305.6 L410,279.2 L440,269.6 L470,286.4 L500,300.8 L530,305.6 L560,303.2 L590,298.4 L620,303.2 L650,310.4 L680,320 Z" fill="{accent @ 0.16}" stroke="{accent}" stroke-width="2.4" stroke-linejoin="round"/>
<text data-ridge="checkout-api" data-role="name" x="304" y="323.5" fill="{ink}" font-size="11" font-weight="600" font-family="{node-name}" text-anchor="end">checkout-api</text>
<text data-ridge="checkout-api" data-role="range" x="696" y="323.5" fill="{muted}" font-size="9" font-family="{sublabel}">40–440 ms</text>
<text data-tick="2" data-bin="240" x="500" y="400" fill="{muted}" font-size="9" font-family="{sublabel}" text-anchor="middle">240</text>
```

`data-bins` is the basis of every geometric check, and it is this contract's own vocabulary: the slopegraph above binds `data-series` on a `<line>`, this variant binds `data-bins` on a `<path>`, and neither gate reads the other's attribute, so neither claims the other's file. Any further Line variant should take its own attribute for the same reason — a shared name means two checkers holding one figure to two contracts, and the one that loses rejects it for lacking elements it never said it had. `data-baseline` is what makes a moved row detectable; without it the checker would have to infer the zero from the drawing, which is the very thing being falsified. The printed range is cross-checked against the first and last nonzero bin through the figure's own tick scale, so a range widened by a word is a finding. `scripts/verify-ridgeline.py` covers the amplitude, the pitch, the baseline rules, the shared bins, the segment grammar, the overlap ceiling, the focus pairing and every label binding; `scripts/test-verify-ridgeline.py` proves each check in both polarities and pins the scope treaty with the sibling gates.

**No `transform` on any of it**, for the reason the slopegraph section gives: the checker reads raw coordinates, so a transform on an outline, a baseline rule, a bound label, an ancestor `<g>` or a CSS rule moves the rendered mark away from the bin that was verified. The horizontal amplitude caption is fine — it is neither verified geometry nor a bound label.

#### Anti-patterns

- Per-ridge normalisation, or any second amplitude anywhere in the figure — the type's one unforgivable error.
- A baseline moved off the pitch to buy one ridge headroom, or a baseline rule drawn somewhere other than the row its ridge declares.
- Ridges sampled on different x-ranges, or an x-scale that is not printed at all.
- Smoothing that puts a peak between two bins, and any spline in a figure whose footnote says the drawing is unsmoothed.
- A ridge clipped mid-mass so the outline closes as a cliff.
- Pitch so tight that peaks hide behind peaks — increase the pitch, never shrink one ridge.
- One hue per ridge instead of the ink ramp plus a single accent.
- A legend that says "darker is faster", which is false on one of the two skins.
- Fewer than 3 ridges (that is a histogram or a pair of small multiples) or more than 12.
- Reading traffic off ridge height, or shipping a figure whose source line lets a reader do so.
### Streamgraph

**Best for:** how a total and its composition breathe across many periods — build minutes by pipeline, traffic by service, error budget by subsystem. The symmetric baseline makes the envelope the hero: the stream's height at any period *is* the total, and each layer keeps its share inside it. No other line form gives both at once — a plain multi-series line loses the total, a 100%-stacked area loses it on purpose.

Not for: exact per-period values (the reader gets shape, not numbers — use a **bar chart** or print a table); two or three periods (that is the parent line chart, or a **slopegraph**); a single series (a plain line chart does this, and the stream's symmetric baseline adds nothing for one layer); or ranking stories (a bump chart reads rank, a stream reads volume).

#### Layout conventions

- **Period columns** evenly spaced across the plot, `x` 80 → 960 inside the `0 0 1000 500` viewBox. The shipped example runs 12 weekly columns at 80px pitch. Budget: **3–24 periods, 2–6 layers**. Below 3 periods there is no flow to show; above 6 layers the ramp runs out of distinguishable tones.
- **Symmetric baseline at `y=230`**, the vertical middle of the 40 → 420 plot. Each period's stack is centred on it: envelope top and bottom always average back to the midline, so the silhouette is the total mirrored about a constant axis. The baseline is a *derived* line, not a drawn one — do not paint it.
- **One shared linear scale** for every layer at every period. The shipped example uses 1.25px per build-minute; state the scale or the bucket size in the source line so the reader can calibrate the envelope.
- **Boundaries are Catmull-Rom smoothed, control points at 1/6 chord, vertices on true values.** Smoothing bends only the *drawing between* periods; every on-curve vertex sits exactly where the stacked value puts it, which is what lets `scripts/verify-streamgraph.py` read the geometry back. Between-vertex overshoot near a sharp change is the honest cost of smoothing — never move a vertex to tame it.
- **Stack order is fixed for the whole figure, largest totals innermost** — the two biggest layers hug the midline, smaller ones ride the outer edges where the curvature is. Order never changes per period.
- **Layer boundaries get a 1px `paper` hairline** so adjacent tones separate where they run thin.
- **Period captions** (`W05`, which are data labels and keep their own case) in 8px mono, centred under each column at `y=440`, untracked. The value caption is horizontal, sentence case, at `y=28` left-aligned to the first period column (`x=80`); no text is rotated.
- **No comparison line, by exception to the house rule 5.** The envelope is the total and each layer is a share of it; a flat average or target line drawn across a silhouette that has no value axis would have nothing to be read against, and the totals are already in the legend.
- **No y-axis ticks and no gridlines.** The form is about the shape of the envelope; per-layer totals are printed in the legend, and a tick grid would invite reading precise values off a curve that cannot deliver them.
- **Annotate at most one landmark period** — a short hairline above the envelope and a mono label, as the shipped example marks the week the focal layer becomes the largest. More than one and the shape stops being the hero.
- **Legend keys are 16×8 rects** (area fills, so the key shows an area), one entry per layer **with its total** — `Unit · 789 min`. The legend is where the numbers live. House rhythm as everywhere: rule at `y=462`, the sentence-case source line at `478` (no `LEGEND` heading word), keys at `488` with text at `496`. These keys stay because the layers carry totals that the stream itself cannot print.
- **4px grid** applies to the designed constants — columns, caption baselines, legend rows. Boundary `y` values are data-scaled and exempt.

#### Colour

- **One accent layer — the editorially focal series — and an `ink` opacity ramp for the rest**, never the series palette. Layers are named in the legend, so hue would re-encode what the labels already say. The shipped ramp runs 0.78 → 0.30, **strongest tone on the largest layer**; adjacent tones in the stack need at least ~0.15 of separation or the hairline is doing all the work.
- Fills may run lighter than a line could: these are areas bounded by `paper` hairlines with no text on them, so the 3:1 stroke floor that binds the slopegraph ramp does not bind here. What does bind: every fill must still be `ink` at opacity (or `accent`), and no text ever sits on a layer.
- **Legend wording must be skin-neutral** — "strongest tone", never "darkest". The ramp inverts on dark paper.
- **Layer names must not contain digits.** The legend prints one number per entry (the total) and the checker refuses a label carrying two numeric tokens — `E2E` fails, `End-to-end` passes.

#### Honest-data rule

**The envelope is a claim about the total, and the layers are a claim about its parts.** Both are enforced by `scripts/verify-streamgraph.py` against the values each layer declares.

- **Zero-sum baseline, stated.** Every period centres on one midline — baseline = −total/2, the classic silhouette. Say so in the source line. A baseline that drifts per period to minimise wiggle re-orders what the eye reads as growth; a baseline pinned to the bottom is a stacked area wearing a costume. Neither is this type.
- **One scale, every layer, every period.** A layer drawn at its own scale makes its share a lie while the envelope stays plausible.
- **Zero periods stay in the domain — the pinch IS data.** The shipped docs pipeline runs nothing in weeks five and six, so its band pinches to zero thickness and reopens. Never bridge, resample, or drop a zero to prettify the flow.
- **No layer dropped silently.** Every drawn layer appears in the legend with its total, and every legend entry has a drawn layer. A stream that quietly loses a small series overstates every share that remains.
- **State the bucket size** (weekly, daily, per release) in the source line. Resampling to a coarser bucket smooths the story; the reader deserves to know which story they got.
- **Totals are sums, not typed numbers.** The legend total must equal the sum of the layer's declared per-period values — one number, three statements (values, geometry, print), zero chances to disagree.

#### Declaring the values

**Each layer's path declares its per-period values, and the drawn geometry must put every vertex where those values stack.** Same contract as the slopegraph: every meaningful visible string is bound to an attribute stating the same thing.

```svg
<!-- A layer: closed region, top boundary left-to-right, then bottom back.
     Absolute M/C/L/Z only; on-curve vertices at every period column. -->
<path data-layer="Docs" data-values="8,9,7,6,0,0,5,7,8,8,9,9"
      d="M 80 297.5 C … L 960 403.8 C … Z"
      fill="{ink @ 0.30}" stroke="{paper}" stroke-width="1"/>

<!-- Period captions: data-index places the column, data-period binds the text -->
<text data-period="W05" data-index="4" x="400" y="440" fill="{muted}" font-size="8" font-family="{arrow-label}" text-anchor="middle">W05</text>

<!-- Legend entries: data-total binds the printed per-layer total. The family is the
     node-name family at regular weight; swap in the active skin's sans stack. -->
<text data-layer="Docs" data-total="76" x="808" y="496" fill="{muted}" font-size="8.5" font-family="'Inter', system-ui, sans-serif">Docs · 76 min · paused</text>
```

What the checker holds against those bindings: every layer's on-curve vertices sit at the shared period columns; per-period thickness matches `data-values` on one shared scale; layers tile with no gap or overlap; the envelope stays centred on one midline; control points sit where Catmull-Rom at 1/6 chord puts them (so the curve between vertices is determined by the vertices, not free to editorialise); each legend entry names its own layer and no other, and its total matches both its printed text and the sum of the declared values; and each period caption sits on its own column reading exactly its `data-period`. Paths must use plain absolute `M`/`C`/`L`/`Z` — anything else is refused rather than half-parsed, and **no `transform`** may touch a layer path, a bound label, or an ancestor group, for the same reason as the slopegraph: the checker reads raw coordinates.

#### Anti-patterns

- A wiggle-minimised baseline that reorders layers per period — the legend stops meaning anything.
- A bottom-pinned baseline presented as a streamgraph — that is a stacked area; the symmetric silhouette is the type.
- One hue per layer instead of the ink ramp plus a single accent.
- Y-axis ticks, or reading a precise value off a layer's thickness — totals live in the legend.
- Bridging or dropping zero periods, or resampling to a bucket the source line does not state.
- More than 6 layers (indistinguishable tones) or fewer than 3 periods (no flow to show).
- Text on a layer fill, or a layer name carrying digits.
- Moving a vertex off its true value to tame smoothing overshoot or open room for an annotation.
- A `transform` on a layer path, a bound label, an ancestor group, or in CSS.
- An unbound visible string: a period caption, a legend name or a legend total with no attribute stating the same thing. An entry printing one layer's name above another's `data-layer` satisfies every number in the figure and still hands the reader the wrong band.

### Bump chart

**Best for:** rank movement across **3–6 ordered snapshots** when position, not magnitude, is the story — package popularity by quarter, team standings by sprint, top queries by month. The slopegraph above shows two moments and keeps magnitude; a bump chart trades magnitude away entirely to show *several* moments of pure position. That trade is the type: the vertical axis is rank, every row is one rank apart, and a flat line means "nothing displaced it", not "nothing changed".

Not for: exactly two snapshots (that is the **slopegraph** above); magnitude stories — a series whose downloads doubled while its rank held draws a flat line, and if that surprise matters the reader needed a **line chart**; fewer than 4 series (a sentence is shorter) or more than 8 (spaghetti with a legend).

#### Layout conventions

- **One vertical axis rule per snapshot**, evenly pitched inside the plot, with the label gutters of the slopegraph: names right-aligned ending at `x=272` and first ranks at `x=304` on the left, mirrored from `x=696` (ranks) and `x=728` (names) on the right. The shipped example runs four axes at `x` 320/440/560/680 — the same 360px run as the slopegraph, spent in three segments instead of one.
- **Rank rows on a fixed pitch.** The shipped grid is `y = 88 + 56 × (rank − 1)`. Rank is ordinal, so — unlike the slopegraph, whose endpoint `y` values are data-scaled and grid-exempt — **every vertex lands exactly on the 4px grid**, and `scripts/verify-bump.py` enforces the row placement with no tolerance at all. There is no honest reason for a vertex to sit off its row.
- **Straight segments between adjacent snapshots, dots at every vertex** (`r=3`, focal `r=4`). Never splines: a curve between two quarterly snapshots draws a trajectory nobody measured. The draft this variant came from calls them subway curves and bans them outright.
- **Labels at first and last appearance** — name and rank (`#1`…`#6`, the sigil keeps a rank from reading as a magnitude) at both ends, each on its own series' row **and in the gutter outboard of the end it names**. Both coordinates are required and both are checked: the row says which series a label belongs to, the column says which *end* of it, and neither implies the other. A first-end label slid along its row into the plot prints every rank correctly and reads against the wrong snapshot.
- **Snapshot captions** (`Q1`…, data labels that keep their own case) in 9px mono, untracked, centred under each axis, bound with `data-axis` / `data-state` exactly as the slopegraph binds its two. The rank caption is horizontal, sentence case, at `y=28` left-aligned to the first axis (`x=320`); no text is rotated. The source line is sentence case at `y=478`, no `LEGEND` heading word; the two remaining keys explain the accent and the ramp, not series names.
- **No comparison line, by exception to the house rule 5.** Rank is ordinal and every row is one rank apart; an average or target rank is not a quantity the figure holds, and a line across the rows would read as a rank between ranks.
- **Series count 4–8, snapshots 3–6.** Two snapshots are a slopegraph; past six the columns compress until rank changes cannot be followed.
- **No gridlines.** The dots are the readable positions and the axis rules are the columns.

#### Colour

Everything the slopegraph's colour section says holds here unchanged: one accent on the editorially focal series, an `ink` opacity ramp (`0.80 → 0.62`, floor 0.53) for the rest — ordered by first-snapshot rank, so the legend can say "strongest tone was highest-ranked", skin-neutrally — focus carried by stroke weight (2.4px against 1.2px) and dot size rather than tone, and labels in `ink`/`muted` on every series including the focal one. The accent marks the series the story is about, never the winner: the shipped example spends it on the package that *fell*.

#### Honest-data rule

**State the ranking key and the tie-break in the source line.** Rank hides magnitude by design, so the footnote is where a reader learns what "first" means and why no two series ever share a row. `scripts/verify-bump.py` gates the geometry half: every snapshot's ranks must be a permutation of 1..N — a duplicated rank is a tie the stated tie-break cannot produce, and a skipped rank is an empty row the reader fills with a series that is not there.

- **If the ranking measure changed definition between snapshots, the chart is invalid** — ranks under different measures are not comparable, and no drawing convention repairs that.
- **A series that enters late or leaves early starts or stops.** A real gap is drawn as absence, never interpolated across. The shipped grammar has no way to *declare* a gap yet, so `verify-bump.py` requires every series to visit every snapshot — a series with fewer vertices than columns is a finding until a gap declaration exists, because widening the rule without one would let a truncated series pass as a deliberate exit.
- **Never smooth a tie into a crossing.** The tie-break decides the order; drawing anything else invents a rank.
- **Never nudge a vertex off its row** to dodge a label collision — it reads as a rank between two ranks, and the checker treats it as the lie it is.

#### Declaring the values

The binding contract is the slopegraph's, one level up: the path declares its ranks, and every visible string is bound to what it describes.

```svg
<path data-series="legacy-http" data-ranks="1,2,4,6" d="M320,88 L440,144 L560,256 L680,368" fill="none" stroke="{accent}" stroke-width="2.4"/>
<text data-series="legacy-http" data-end="first" data-role="name" x="272" y="91.5" fill="{ink}" font-size="11" font-weight="600" font-family="{node-name}" text-anchor="end">legacy-http</text>
<text data-series="legacy-http" data-end="first" data-role="rank" x="304" y="91.5" fill="{muted}" font-size="9" font-family="{sublabel}" text-anchor="end">#1</text>
<text data-axis="0" data-state="Q1" x="320" y="416" fill="{muted}" font-size="9" font-family="{sublabel}" text-anchor="middle">Q1</text>
```

`data-ranks` is the basis of every geometric check, so a series whose labels go missing stays in the verified set and the missing label is itself reported. `scripts/verify-bump.py` covers the grid, the permutations, the segments, the dots, the focus pairing, the label bindings, label placement on both axes and the captions; `scripts/test-verify-bump.py` proves each check in both polarities. The gutter x is read off the figure — every label sharing an end and a role must agree on one column — so a resized plot needs no constant changed here.

## Examples

- `assets/example-line.html` — minimal light
- `assets/example-line-dark.html` — minimal dark
- `assets/example-line-full.html` — full editorial
- `assets/example-slopegraph.html` — slopegraph, minimal light
- `assets/example-slopegraph-dark.html` — slopegraph, minimal dark
- `assets/example-slopegraph-full.html` — slopegraph, full editorial
- `assets/example-ridgeline.html` — ridgeline, minimal light
- `assets/example-ridgeline-dark.html` — ridgeline, minimal dark
- `assets/example-ridgeline-full.html` — ridgeline, full editorial
- `assets/example-streamgraph.html` — streamgraph, minimal light
- `assets/example-streamgraph-dark.html` — streamgraph, minimal dark
- `assets/example-streamgraph-full.html` — streamgraph, full editorial
- `assets/example-bump.html` — bump chart, minimal light
- `assets/example-bump-dark.html` — bump chart, minimal dark
- `assets/example-bump-full.html` — bump chart, full editorial
