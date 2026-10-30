# Gantt Chart

**Best for:** project plans and roadmaps — tasks with explicit start and end dates, grouped into phases. Use when the reader needs to see temporal overlap, parallel tracks, and milestone sequencing at a glance.

## Layout conventions

- **Left label column:** x=20–200 (180px). Each task is named here, once, in the `node-name` role at 11px 600 (10px in the shipped examples). Phase labels in sentence case above each group, `eyebrow` role 7px `soft`, no tracking.
- **Name each task once.** The left column carries the name; the bar carries none. In-bar text may hold only a duration ("2 wk"), and only if the duration is shown nowhere else. A callout beside a bar ("Critical gate") describes the bar and does not repeat the task name.
- **Timeline area:** x=200–956 (756px). Time axis runs left→right.
- **Row height:** 40px per task. Each bar occupies h=24px centered in the row (8px top padding).
- **Task cap:** 24 tasks. Past that, split into small multiples — identical frame, identical time scale, one panel per phase, a direct title on each.
- **Time axis:** period labels (months) in the `node-name` role 9px 600 at the period centre, y=52. A `soft` hairline at y=60 under them.
- **Time gridlines are sparse.** One line per period boundary at most, `ink @ 0.08` 0.8px, solid; never a line per week. They are labelled by the period names above, not by their own tick text.
- **Phase grouping:** a band behind each phase's rows only when the band encodes the phase. Fill `ink @ 0.04`, no stroke, no frame. If every band would look the same and the phase is already named in the left column, omit them.
- **Focal task bar:** 1 bar in accent fill/stroke (the key deliverable or critical path task). All others: muted fill @ 0.15, muted stroke. Say why it is focal with a direct callout to the right of the bar (italic `ink`, 9px), not a legend key. There is no legend strip.
- **Today marker:** a vertical line in `soft` 1px dashed `4,3` from the header rule to the plot bottom, with the direct label "Today" below the plot in `arrow-label` role 8px `muted`. It is the chart's comparison: what is done sits left of it, what remains to its right.
- **Source line:** sentence case, `Inter` 8.5px `muted` at x=40, y=478. State the unit of the time axis and what the bars span.

### Data binding

The plot declares its time scale and every bar its dates, so `scripts/verify-gantt.py` can hold the drawing to the plan (see `type-line.md` for the same pattern on a slopegraph).

```svg
<g data-plot="gantt" data-domain="0 12" data-range="200 956">
  <line x1="452" y1="36" x2="452" y2="416" data-at="4" data-kind="period" .../>
  <rect x="389" y="192" width="126" height="24" data-name="Wireframes" data-start="3" data-end="5" .../>
  <line x1="515" y1="60" x2="515" y2="416" data-at="5" data-kind="today" .../>
</g>
```

`x = x0 + (t − t0) ÷ (t1 − t0) × (x1 − x0)` for every bar edge and every `data-at` line, to within 0.75px of rounding. No bound mark, and not the group, carries a `transform`. `scripts/verify-gantt.py` fails on: a bar off the shared time scale, a task name printed other than once, in-bar text that is not a duration, more than 24 tasks, a today or period line off the scale or a second today marker, rotated text, any transform, and a file that claims to be a Gantt chart but yields no parseable task. `scripts/test-verify-gantt.py` proves each in both polarities.

### Task bar pattern

```svg
<!-- Task name, left column, once -->
<text x="20" y="ROW_Y+24" fill="{ink}" font-size="10" font-weight="600"
      font-family="{node-name}">Task name</text>

<!-- Non-focal task: no text inside -->
<rect x="X_start" y="ROW_Y+8" width="DURATION_PX" height="24" rx="4"
      fill="{muted @ 0.15}" stroke="{muted}" stroke-width="1"
      data-name="Task name" data-start="3" data-end="5"/>

<!-- Focal task -->
<rect x="X_start" y="ROW_Y+8" width="DURATION_PX" height="24" rx="4"
      fill="{accent @ 0.12}" stroke="{accent}" stroke-width="1"
      data-name="Key task" data-start="7" data-end="8"/>
```

Duration in pixels: `(end − start) × pitch`. Pitch = timeline_width / total periods.

## Anti-patterns

- More than 24 tasks (split into small multiples on one time scale).
- A task name printed twice — in the column and again in its bar.
- A gridline per week; a legend strip whose keys can be labelled in place.
- More than 5 parallel tracks per phase (illegible overlap).
- Dependency arrows between tasks in v1 (add only when essential; use the annotation primitive for labels).
- Start/end dates in the bar label (put them in the x-axis or tooltip comment instead).
- Equal visual weight for all bars (the focal task must stand out).

## Examples

- `assets/example-gantt.html` — minimal light
- `assets/example-gantt-dark.html` — minimal dark
- `assets/example-gantt-full.html` — full editorial

All three are checked by `scripts/verify-gantt.py --all`.
