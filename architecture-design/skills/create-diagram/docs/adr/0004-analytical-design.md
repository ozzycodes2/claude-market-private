# ADR 0004 — Apply Tufte's analytical-design principles to chart examples, inside the Fabric skin

**Status:** accepted

## Context

[ADR 0003](0003-tufte-alignment.md) applied *The Visual Display of Quantitative Information*: how a chart is drawn. Its sequel, *Beautiful Evidence*, asks what a chart is for: content counts most, establish credibility, show causality, integrate words, numbers and images, and use multivariate data. The examples met none of these. Titles named a topic, not a claim. No chart said where its data came from. Cards explained why a number moved while the chart showed no trace of the cause, and card prose quoted numbers nobody had checked against the data.

## Decision

The skin is unchanged: no new hue, family or size. Accent never paints text or the new marks.

- **R1, source line.** Every chart example carries exactly one `<text data-role="source">`, bottom-left, `muted`, 8px mono, starting `Source: `. Sentences in fixed order: origin and period, units, then encoding notes only where not obvious. Invented data says so; judged positions say so. The first sentence contains a period token (a year, `FY`, a quarter, `W<digit>`, a unit of time, or `judgement` / `judged`). A second line is a `<tspan>` child, never a second element.
- **R2, one-sentence takeaway.** The `<title>` states the claim when it fits, under about 60 characters, and the `<desc>` opens with that sentence. The topic moves to the `-full` page eyebrow. The claim must be true of the data in the file.
- **R3, causes marked on the chart.** When a card, caption or callout explains why a change happened, an event marker (`data-event` group: vertical `soft` 1px line dashed `2,3`, plus an italic `ink` callout naming the cause) sits at that category on the shared scale. Heatmaps outline the cell or column instead. Event markers count toward the cap of four chart callouts. If the data does not show the effect, change the claim, not the data, unless the data is illustrative and the story is the point.
- **R4, cards cite marks and numbers match data.** Each card names at least one mark visible in the diagram. Every `X → Y` pair in card prose appears in the bound data or the SVG text. Derived numbers state their span. At most one card is "What the chart doesn't show".
- **R5, multivariate.** Ask which second variable explains the first; if one does, route to small multiples, bubble or slopegraph. One small-multiples line example (`example-line-small-multiples.html`) shows the pattern.

## Enforcement

- `lint-skin.py` gains a `source-line` check on `example-<prefix>*` files for the chart prefixes in R1: exactly one source element inside the diagram SVG, text starting `Source: `, first sentence with a period token. Files in the lint baseline are exempt, as for every other skin check.
- `verify-cards.py` checks the mark citation and number-pair membership parts of R4 on every `example-*-full.html` with cards. It does not check derived arithmetic (percent change, averages) or whether a claimed cause is marked; those are review items in the §9 checklist.
- Title-as-claim, desc-opens-with-claim and event-marker placement are checklist items, not linted: whether a title states a claim is a judgement.

## Deliberate non-adoption

- **Sparklines in running text.** Tufte's word-sized graphics need a prose host the single-diagram output does not have.
- **Free-form annotation of every point.** The four-callout cap from ADR 0003 stands; event markers spend from it.

## Consequences

- Chart examples, in all three variants, migrate to the new rules; `lint-skin.py --all --baseline` and `verify-cards.py --all` show what has not moved.
- Existing per-type verifiers that read source text keep their strictness; only wording they hard-coded may need updating.
- A chart without a source line, or a card whose numbers are not in the data, is incomplete under §9.
