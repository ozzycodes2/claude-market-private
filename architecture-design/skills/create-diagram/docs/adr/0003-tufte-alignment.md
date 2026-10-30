# ADR 0003 — Align the skill with Tufte's data-ink and graphical-integrity rules, inside the Fabric skin

**Status:** accepted

## Context

The skill's philosophy ("the highest-quality move is usually deletion") is Tufte's data-ink principle in spirit, but the rules beneath it had drifted: arrow labels and axis captions were all caps and tracked, legends carried a "LEGEND" heading and repeated what direct labels already said, charts printed gridlines and value labels for the same marks, decorative watermark numerals were exempt from the type ramp, rotated axis titles were common, and nothing asked a chart to state units or show a comparison. Tufte's *The Visual Display of Quantitative Information* gives named, checkable rules for each.

## Decision

Adopt Tufte's rules as house rules, without changing the Fabric skin (no new hue, no new family, no new size, contrast values untouched).

- **Upper-and-lower case.** Arrow labels, axis titles, tick-unit captions, source lines, legend text, callouts, and quadrant or axis captions are sentence case with no letter-spacing; acronyms keep their case. Arrow labels allow 24 characters (was 14). Uppercase with tracking survives only on the 7px node type tag and the HTML page eyebrow. No rotated text: y-axis titles are horizontal above the axis.
- **Data-ink.** Each value is encoded once: value labels or gridlines and axis, not both. Unlabelled charts use sparse ticks and a range frame, with at most four gridlines at `ink @ 0.08`. No frames around plots, no watermark numerals, no "LEGEND" heading. The watermark font-size exemption in `output-spec.md` is removed.
- **Direct labels first.** Series and categories are labelled in place. A legend remains only for node treatments, edge styles, and size keys.
- **Graphical integrity.** Lie factor near 1; zero baseline or a drawn and stated break; area encodings scale area, with a size key; graphic dimensions never exceed data dimensions; units stated, and money across periods marked nominal or real (base year).
- **Context.** Quantitative charts show a comparison the data supports (target, average or median, prior period) as a `soft` 1px line dashed `4,3` with a direct label, except types whose reference forbids it (ridgeline, streamgraph).
- **Density.** Chart budgets rise to bar 16, line 6 series, scatter and beeswarm 300 points, Gantt 24 tasks, heatmap 12 x 12. The 9-node schematic budget is unchanged. Past a chart cap, split into small multiples (identical frame and scales). Charts may shrink to the type-ramp floor before splitting (Tufte's shrink principle); schematics still split into overview and detail. Summary cards become optional.
- **Aspect.** Charts are wider than tall; line charts bank their dominant slopes to about 45 degrees within the preset's viewBox.
- **Annotations.** Callouts may sit beside the data they explain, joined by a leader line and never covering marks. Two per schematic, up to four short ones per chart.
- **Icons** must encode something the label does not.

`lint-skin.py` enforces two of these mechanically: no `<text>` with a `rotate` transform, and no text reading `LEGEND`. There is deliberately no sentence-case linter: acronyms and proper nouns make the signal too noisy.

## Deliberate non-adoption

- **Serif type.** Tufte favours a serif face for text. The skin forbids serif (see `style-guide.md` § No serif), and Inter plus the SF Mono stack is what the source design system declares. Case, weight and size carry the hierarchy instead.
- **More than one chroma.** Tufte's data maps use color freely; the skin has one signal chroma, with series separated by dash pattern. That stays, and the three-dash-series cap on radar stays with it.

## Consequences

- Every example, type reference, and generator shipped before this decision was written to the old rules; they migrate shard by shard, and `lint-skin.py --all` is the gate that shows what has not moved.
- Mask rectangles behind arrow labels shrink or grow with the new text, using the existing 0.62em-per-character budget and rounding up to a multiple of 4.
- A chart that cannot show a comparison or state its units is incomplete under §9, not merely plain.
