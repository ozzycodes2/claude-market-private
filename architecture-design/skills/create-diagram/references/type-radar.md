# Radar / Spider

**Best for:** the profile of one or two entities, or at most four compared on a shared panel, across 3–5 quantitative criteria on a single normalized 0–N scale. Capability matrices, product or backend evaluations, framework/team scorecards. Where a comparison table starts running out of horizontal room, radar makes the shape of each option legible at a glance.

## Layout conventions

- **N axes (3-5).** Equally spaced on a regular polygon-N. First axis at the top (`-90°`), going clockwise. **Above 5 → split or use a comparison table.**
- **Axis order is a stated rule, not an accident.** Polygon shape changes with axis order, so group axes by a rule the reader can check (here: data path, then operations, then ecosystem) and print that rule in the source line. Same order on every radar in a set.
- **Grid rings: at most 4**, at fractions `0.25 / 0.5 / 0.75 / 1.0` of the scale, drawn as closed polygons. Inner rings are `ink @ 0.08`. The outer ring is the traced maximum, so it takes `soft`; spokes are not traced and stay `ink @ 0.08`. If the reader must trace a spoke to a value, promote that spoke to `soft`.
- **Axis spokes** from center to each outer vertex. **No arrowheads.**
- **Axis labels:** one or two words per spoke, sentence case. `node-name` role 11px weight 600. Place 16px outside the outer ring along the axis vector. Top/bottom = `text-anchor="middle"`; right side = `start`; left side = `end`.
- **Scale ticks** (e.g. `2.5 5 7.5 10`) only on the **first (top) axis**. Mono tick-label role 8px, `muted`, anchored end at `cx − 6`.
- **Series strokes follow the [style-guide series table](style-guide.md#series-palette-multi-series-chart-types-only) exactly.** The focal series is `accent` stroke, `accent-tint` fill, solid. Non-focal series, at most 3, are `ink` solid, `muted` dashed `6,3`, and `soft` dotted `2,3`, each with its own colour at 0.06 fill. Stroke 1.5px; 1.8px on the focal series. There are no hues beyond the accent.
- **Vertex dots:** **only on the focal series**, `r=4` filled `accent`. Non-focal series are stroke-and-fill only.
- **Direct-label every series; no legend.** Put the series name (Inter 11px, weight 500, `ink`, never accent) near that series' most distinctive vertex, outside the polygons, joined by a 0.8px `soft` leader. The dash pattern identifies the line; the name sits beside it.
- **Source line** (`data-role="source"`, sentence case, `muted`, bottom-left, starting `Source: `): origin and period first (`illustrative storage review scores, Q3 2026`), then units and scale, then the axis-order rule and "read vertices, not area". A second line is a `<tspan x dy="12">` child.
- **Title is the claim**, under about 60 characters, true of the scores (`MinIO leads on three of five capabilities`); `<desc>` opens with it. Any -full card quoting an average or a count recomputes it from the vertices and states its span.
- **Drawing order:** grid rings → axis spokes → axis labels → scale ticks → non-focal series (smallest area first) → focal series → focal vertex dots → series labels → source line.

## Read the vertices, never the area

Polygon area grows with r², so doubling every score quadruples the area, and a radar overstates differences in proportion to how large the scores already are. Area and shape also change with axis order: the same data on a different order gives a different polygon. Never describe one entity as "bigger" because its polygon is. Read each vertex against its own axis.

- **3 or more entities → prefer small multiples**: one radar per entity, identical axes, identical order, identical scale, a direct title per panel. Or skip radar: a dot plot (one row per axis, one dot per entity) or a table reads values more precisely.
- Radar earns its place only when the question is the *profile* of one or two entities (spiky versus even), not a score comparison.
- Context rule exception: the series on the chart are already each other's comparison; no extra reference line is drawn.

## Math

For axis `i` (0-indexed) of `N`, value `v` on scale `S`, center `(cx, cy)`, outer radius `R`:

```
angle = -π/2 + 2π · i / N
x = cx + (v / S) · R · cos(angle)
y = cy + (v / S) · R · sin(angle)
```

A series with values `[v0, v1, ..., v(N-1)]` becomes a `<polygon>` with `points="x0,y0 x1,y1 ..."`.

### Pre-computed reference (N=5, cx=500, cy=240, R=160, S=10, integer-rounded)

Rows are the offsets for fifths of the radius; the grid rings use `0.25 / 0.5 / 0.75`, so compute those from the formula above.

| Fraction `f` | i=0 (top) | i=1 | i=2 | i=3 | i=4 |
|---|---|---|---|---|---|
| 0.2 | 500,208 | 530,230 | 519,266 | 481,266 | 470,230 |
| 0.4 | 500,176 | 561,220 | 538,292 | 462,292 | 439,220 |
| 0.6 | 500,144 | 591,211 | 556,317 | 444,317 | 409,211 |
| 0.8 | 500,112 | 622,201 | 575,343 | 425,343 | 378,201 |
| 1.0 | 500,80  | 652,191 | 594,369 | 406,369 | 348,191 |

For an arbitrary value `v` on axis `i`, take the unit offset from the row above for that axis (e.g. axis 1: offset `(152, -49)` from center) and scale by `v/S`. **Drop coords as integers — fractional pixels in SVG render fine, but integers keep the file scannable.**

### Worked example (N=5)

Series `[9, 8, 9, 9, 9]` on a 0–10 scale becomes:

```svg
<polygon points="500,96 622,201 585,356 415,356 363,196"
         fill="{accent-tint}" stroke="{accent}" stroke-width="1.8"/>
```

Each vertex: `center + (v/10) · (outer_i − center)`, rounded to the nearest pixel.

## Series palette

There is no series palette. `accent` is reserved for the focal series, and the others separate by stroke pattern on one ink, per the [style-guide series table](style-guide.md#series-palette-multi-series-chart-types-only):

| Slot | Stroke | Fill | Dash |
|---|---|---|---|
| Focal (1 only) | `accent` | `accent-tint` | solid |
| 1 | `ink` | `ink @ 0.06` | solid |
| 2 | `muted` | `muted @ 0.06` | `6,3` |
| 3 | `soft` | `soft @ 0.06` | `2,3` |

Three non-focal series is the ceiling. A fifth entity means two radars, small multiples, or a table.

## Anti-patterns

- **More than 4 series (focal + 3)** → mush. Split into small multiples or switch to a comparison table.
- **Axes on inconsistent native scales** (one 0–100, another 0–1) without normalization. **Always normalize to 0–N first** — radar polygons compare *shapes*, not absolute values.
- **Zero-baseline tricks** — starting the inner ring at v=5 to amplify differences. The grid starts at 0; if differences look small, that's the truthful reading.
- **Dots on every series.** Only the focal carries dots. Adding them to every series turns the chart into a bead curtain.
- **Radar with 2 series** — a comparison bar chart or a 2-row table is clearer.
- **Non-quantitative axes.** All axes must be measurable on the same normalized scale. "Speed" + "color" + "year" mixes don't belong on a radar.
- **Mono-font axis labels.** Names go in the `node-name` sans family (the global rule). Mono is for technical sublabels only.
- **All-caps or rotated axis labels.** Sentence case, horizontal.
- **Hue-coded series, or a legend strip.** Hue is not available; name the series on the chart.
- **Reading area as a total.** See [Read the vertices](#read-the-vertices-never-the-area).

## Examples

- `assets/example-radar.html` — minimal light. 4 storage backends × 5 workload dimensions, MinIO focal, direct series labels.
- `assets/example-radar-dark.html` — minimal dark, same data.
- `assets/example-radar-full.html` — full editorial: container framing + 4 cards (one per backend) with varied widths + footer.
