# Minimalism rules

A slide is read in three seconds while someone is talking. It carries one
claim and one picture of that claim; everything else is said aloud or lives
in the speaker notes. `scripts/check_deck.py` enforces the numbered rules.

## Rules

1. **Headline: seven words or fewer, and a claim.** "CI got 3× faster", not
   "CI performance". A topic label makes the audience guess the point.
2. **Eyebrow: one to three words.** It names the topic, so the headline can
   state the claim.
3. **No third text layer.** No sub-headline, no `<p>`, no `<ul>` or `<ol>`,
   no caption under the headline.
4. **Exactly one visual per content slide**, marked with class `visual`:
   a diagram from `architecture-design:create-diagram`, a big number, a stat
   strip, an icon trio, or a statement.
5. **At most 25 visible words per slide**, counting eyebrow, headline, and
   visual labels. Text inside a diagram SVG does not count; the diagram's
   own detail dial governs it.
6. **Brand colors only.** Any hex value outside `references/brand.md` and
   the Machinify diagram profile fails.
7. **Diagrams come from create-diagram.** An inline `<svg>` without a
   `<title>`, a `<desc>`, and a slug-scoped root `id` was drawn by hand.

## Judgment the checker cannot make

- **Prose goes to the notes.** Explanation, caveats, sources, and the
  sentence you would have put under the headline go into
  `<aside class="notes">`. The presenter presses `N` to read them.
- **Infographic over text.** When a slide has a relationship, sequence,
  structure, timeline, comparison, or distribution, draw it. Three
  bullet points about a flow are a flow diagram.
- **One accent per slide.** One focal number in a stat strip, one
  highlighted node in a diagram. Two accents mean neither is the point.
- **Whitespace is the layout.** Do not fill the body because it is empty.
  A single number in 520px of space reads as important.
- **Numbers carry their unit and nothing else.** `3×`, `42%`, `7 min`.
  The label under them is two to four uppercase words.
- **Cut, don't shrink.** If content does not fit, split the slide or move
  the detail to notes. Never drop type below the template's sizes.
- **Bullets are banned, not restyled.** A checklist, a row of cards with a
  sentence each, and a two-column comparison of sentences are bullet
  lists. Pick a visual or a statement.

## Rewrite examples

| Before | After |
|---|---|
| Eyebrow `CI PIPELINE`, `h2` "Wall-clock analysis of the voice-connect pipeline", `.sub` "We measured 40 runs over two weeks…", five bullets | Eyebrow `CI`, `h2` "Tests own 70% of build time", diagram: bar chart of stage durations, measurement method in notes |
| Three cards, each with an icon, a title, and two sentences | Icon trio: icon plus two to four words each; the sentences go to notes |
| "Key takeaways" slide with four bullets | One statement slide per takeaway that matters; drop the rest |
