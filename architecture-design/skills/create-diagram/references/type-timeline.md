# Timeline

**Best for:** release history, project milestones, incident timelines, roadmaps, changelog visualizations.

## Layout conventions
- Horizontal hairline baseline across the middle (`stroke-width=1`).
- Tick marks at time boundaries (quarters, months, sprints) with date labels below in the `arrow-label` role, in sentence case ("Feb 2025", "Jan 2026") with no letter-spacing — tracking is for caps only.
- Events: small filled circles (`r=4`) on the baseline. Labels alternate above and below to prevent collision, connected to the circle with a 1px `soft` drop — the drop is what binds a label to its event, so it takes the same role as the baseline rather than a hairline.
- Major milestones: `accent` circle (`r=6`) + bold `node-name`-role label.
- Time scale must be honest: if intervals are non-equal, space the circles non-equally. Don't fake linear spacing for aesthetics. Break the axis visibly if a region is too dense.
- No watermark numerals: a year is named by the tick label at its boundary, not by a large faint year behind the axis.
- Legend: only for encodings that cannot be labelled in place (event versus major milestone). No "LEGEND" heading; keys stay where they were.

## Anti-patterns
- Equal-spacing events that aren't equally spaced in time.
- Missing axis labels ("what unit is this?").
- Crowded labels without vertical offset — illegible.
- Decorative year watermarks behind the axis.

## Examples
- `assets/example-timeline.html` — minimal light
- `assets/example-timeline-dark.html` — minimal dark
- `assets/example-timeline-full.html` — full editorial
