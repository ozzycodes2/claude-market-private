# Style Guide

**The single source of truth for colors, typography, and tokens.** Every diagram draws from this — not from hex values inlined in other reference files. If you want to change the visual skin of Diagram Design, change this file.

The skin is **Mine Final** — two polarities of one token vocabulary, carried over
from `systems/DESIGN-mine-final.md` in this repository's parent. Near-black
ground or off-white ground, the same eleven diagram roles at two sets of values,
and one shared signal orange across both. Swap these values (or run
[`onboarding.md`](onboarding.md)) and every new diagram inherits the new skin
without touching any type-specific logic.

Three rules from the source system override what this skill shipped by default.
They are not preferences; the rest of the file is written assuming them:

1. **The accent never sets type.** It is a fill, an edge, and a ring. At 3.06:1
   on the light paper it clears the 3:1 floor for an object and misses the
   4.5:1 floor for a word.
2. **There is no second chroma**, so the `link` role is gone. External and HTTP
   arrows are distinguished by stroke weight, not by hue.
3. **One family, two cuts.** Inter and SF Mono. No serif.

To generate your own from a website URL, see [`onboarding.md`](onboarding.md).

---

## Tokens

### Semantic roles

Every token is referred to by **semantic role**, not by its hex value. Type references (`type-*.md`) and SKILL.md say `accent`, not `#ef6306`.

| Role | Purpose | Source token | Light (`#f8f8f8` ground) | Dark (`#010102` ground) |
|---|---|---|---|---|
| `paper` | Page background, default node fill | `{colors.canvas}` | `#f8f8f8` | `#010102` |
| `paper-2` | Diagram container bg, secondary fill | `{colors.surface-1}` | `#ffffff` | `#0f1011` |
| `ink` | Primary text, primary stroke | `{colors.ink}` | `#171717` | `#f7f8f8` |
| `ink-strong` | Text on the accent fill | `{colors.on-primary}` | `#171717` | `#171717` |
| `muted` | Secondary text, default arrow stroke | `{colors.ink-muted}` | `#4d4d4d` | `#d0d6e0` |
| `soft` | Sublabels, boundary labels, axes | `{colors.ink-subtle}` | `#616161` | `#8a8f98` |
| `rule` | Hairline borders | `{colors.hairline}` | `#d9d9d9` | `#23252a` |
| `rule-solid` | Stronger borders | `{colors.hairline-strong}` | `#c6c6c6` | `#34343a` |
| `accent` | Focal / 1–2 max per diagram — **never text** | `{colors.primary}` | `#ef6306` | `#ef6306` |
| `accent-tint` | Fill for accent-bordered boxes | derived | `rgba(239,99,6,0.10)` | `rgba(239,99,6,0.14)` |
| `accent-deep` | Focus rings only | `{colors.primary-focus}` | `#d65905` | `#d65905` |

> **Source system:** every value above except `accent-tint` is a literal from
> `DESIGN-mine-final.md`, at the role its name implies. The source declares
> seventeen color roles against a component vocabulary; eleven of them map onto
> diagram roles, and the six that don't (`primary-hover`, `surface-2` through
> `-4`, `hairline-tertiary`, `inverse-canvas`/`inverse-ink`) describe pressed
> states, a tile ladder and a polarity-inverting button — none of which a
> schematic has. `accent-tint` is the one derived value: the accent composited
> over its own paper at 0.10 light, 0.14 dark, chosen so an accent-bordered box
> reads as filled without the border losing its edge.

> **`link` is deleted, not remapped.** The source system's standing rule is one
> chroma and no semantic palette, so a blue for HTTP arrows has nowhere to come
> from. External and HTTP calls are drawn in `ink` at `stroke-strong`; internal
> calls in `muted` at `stroke-default`. The distinction survives as weight.
>
> Two types keep `link` as an edge-*style* key (`type-data-flow.md`,
> `type-it-state.md`). There it names a topology — the edge leaves the system —
> and resolves to `ink` at 1.2. There is no `link` color to look up.

> **Note:** The example HTML files in `assets/` carry this palette. Their
> geometry is the upstream skill's, unchanged — no coordinate moved in the
> reskin — so they document the layout grammar and the skin at once. Where a
> figure could not keep a convention under one chroma, the figure says so in a
> comment rather than faking it; the retired series palette is the usual case.
> The terminal examples are the exception and keep the upstream palette by
> design.

### Contrast contract

Every token must clear the threshold for each role it plays, against the background it actually sits on, in both skins. `scripts/verify-contrast.py` computes the WCAG 2.x ratio for every row above against the `paper` of its skin (`ink-strong` against the 0.85 `accent` fill it labels) and fails CI when one falls short.

| Use | Minimum vs. its actual background |
|---|---|
| Regular text — `ink`, `muted`, `soft`, `ink-strong` | 4.5:1 |
| Large text (24px+, or 18.7px+ at weight 600+) | 3:1 |
| Essential non-text marks: arrows, node borders, focus outlines, data points, chart axes and baselines | 3:1 against the adjacent color |
| Decorative rules and translucent tints (`rule`, `rule-solid`, `paper-2`, `accent-tint`, fills at opacity) | No minimum, but never the only carrier of meaning |

- **`accent` is exempt from the text row because it may not be text.** The
  shipped skin held it to 4.5:1 so it could label its own arrow; this one
  forbids the use instead. An accent arrow's label is `ink`. An accent node's
  name is `ink`. Nothing is written in `#ef6306`, in either theme, at any size.
- **Translucent colors are composited first.** An `rgba()` fill or stroke is blended over `paper` before its ratio is measured. A value that clears the bar at full strength can fail at 0.5 opacity.
- **Surfaces other than `paper` cost contrast.** Inside an `accent-tint` box or on `paper-2` every ratio drops. Measure text placed there against that surface, not against `paper`.
- **An essential mark may not be a hairline.** `rule` reads 1.33:1 light and
  1.36:1 dark, `rule-solid` 1.61:1 and 1.69:1 — all four are far under the 3:1
  an essential mark needs. They are correct for a node border that merely
  encloses a label the reader can already see, and wrong for a chart axis, a
  baseline, a lifeline, or a boundary the reader has to trace. Those take
  `soft`, which clears 5.83:1 light and 6.42:1 dark.
- **Current values:** light `ink` 16.88:1, `muted` 7.96:1, `soft` 5.83:1,
  `accent` 3.06:1 on `#f8f8f8`; dark `ink` 19.61:1, `muted` 14.28:1, `soft`
  6.42:1, `accent` 6.42:1 on `#010102`. `ink-strong` on the accent fill is
  5.51:1 in both. Inside `accent-tint`, `ink` holds 15.10:1 light and 17.35:1
  dark; `accent` drops to 2.74:1 light, which is the second reason it is not a
  label.

### The two polarities are not an inversion

The shipped skin derived dark from light by flipping RGB at fixed opacities.
This one does not: both themes are declared in full, because the source system
declares them in full and the asymmetry is deliberate. `paper-2` is a lift
above `paper` on both grounds — `#ffffff` over `#f8f8f8`, `#0f1011` over
`#010102` — but the light ground's remaining surfaces step *down* into the
canvas while the dark ground's step up, so a value interpolated between the two
is in neither system.

The accent does not shift between them. One hue, `#ef6306`, at one value, on
both grounds. That costs the dark theme more separation than a fill needs
(6.42:1) and leaves the light theme the least it can have (3.06:1); the source
system argues the trade at length and the diagrams inherit it, because a brand
hue that changes with the reader's OS setting is not one brand.

### Series palette (multi-series chart types only)

**There is no series palette.** The source system's standing rule is one chroma,
and five desaturated hues is five chromas. Chart types that need to tell
overlapping entities apart (currently: **radar**) distinguish them by stroke
pattern on one ink, not by hue.

| Series | Stroke | Fill | Dash |
|---|---|---|---|
| focal (1 only) | `accent` | `accent-tint` | solid |
| `series-1` | `ink` | `ink @ 0.06` | solid |
| `series-2` | `muted` | `muted @ 0.06` | `6,3` |
| `series-3` | `soft` | `soft @ 0.06` | `2,3` |

**Three non-focal series, not five.** A fourth dash pattern is not reliably
distinguishable from the three above at a 1px stroke, and stacking a fourth
translucent fill over the other three stops reading as separable at all. If a
radar needs five entities, it is two radars or a table — which is the answer
the complexity budget would have reached anyway.

**Don't backfill these to non-chart types** — architecture, swimlane, and the
rest continue to use ink-ramp variants with no dash vocabulary, because a dashed
connector already means optional/async there and a second meaning for the same
mark erases both.

### Terminal skin (opt-in alternate)

A self-contained palette for the terminal-window primitive (see [primitive-terminal.md](primitive-terminal.md)) — a CLI-chrome register for dev-tool posts and technical social cards. It does not replace the default skin above and isn't affected by onboarding; it's a second, fixed skin you opt into per-diagram.

| Token | Hex | Purpose |
|---|---|---|
| `terminal-page` | `#0a0a0a` | Page background behind the window |
| `terminal-paper` | `#141414` | Window body, node fill |
| `terminal-bar` | `#1b1b1b` | Titlebar strip |
| `terminal-border` | `#2b2b2b` | Window border, hairlines |
| `terminal-ink` | `#f5f5f5` | Primary text, primary stroke (same white-smoke as default `ink`) |
| `terminal-muted` | `#9a9a9a` | Secondary text, sublabels, ring stroke |
| `terminal-soft` | `#5c5c5c` | Tertiary — inactive dots, spokes |
| `terminal-accent` | `#ff5a36` | The one accent — focal station, prompt sign, active dot |
| `terminal-accent-tint` | `rgba(255,90,54,0.12)` | Fill for accent-bordered boxes |

**1-accent rule still holds.** Everything that isn't `terminal-ink` or `terminal-muted`/`terminal-soft` should be `terminal-accent` — never introduce a second hue.

---

## Typography

| Role | Family | Size | Weight | Usage |
|---|---|---|---|---|
| `title` | Inter | 32px | 600, tracked -0.8px | Page H1 |
| `node-name` | Inter | 12px | 600 | Human-readable labels |
| `sublabel` | SF Mono | 9px | 400 | Port, protocol, URL, field type |
| `eyebrow` | SF Mono | 8px | 500, tracked 0.14em, uppercase | Type tags, axis labels |
| `arrow-label` | SF Mono | 8px | 400, tracked 0.08em, uppercase | Arrow annotations |
| `callout` | Inter *italic* | 14px | 400 | Editorial asides only |

### No serif

The shipped skin called the serif/sans contrast load-bearing and told a
brand with all-sans typography to keep Instrument Serif anyway. The source
system has eight type steps and a monospace, all on Inter, and a standing rule
that one family change is allowed and it is the monospace. The serif loses: a
page title in a face the system does not declare is the diagram advertising a
different design system from the page around it.

What replaces the register change is weight and tracking. `title` is
`{typography.headline}` — 32px/600 at -0.8px — against a 12px/600 node name, so
the two are the same face at a 2.7× size step and the same weight. Italic Inter
carries the callout, which is a weaker signal than italic Instrument Serif was;
callouts therefore lean harder on `primitive-annotation.md`'s leader line to
mark themselves as asides.

### The type scale does not survive, and says so

Diagram labels run 8–12px. The source system's smallest declared step is the
12px eyebrow, so `node-name` is the only role that lands on the scale at all,
and it lands there at 600 rather than the 500 that step declares. `sublabel`,
`eyebrow`, and `arrow-label` are below every declared step.

This is not fixable by moving the sizes — a 14px sublabel inside a 64px node box
leaves no room for the name above it. What carries over is the *rules* rather
than the ladder: one family and one monospace, weight never below 400, tracking
positive only in the eyebrow register. The tracking values are the exception:
the source system's eyebrow tracks +0.5px, which at 8px is 0.0625em and far too
tight for uppercase mono. These roles track 0.14em and 0.08em instead — the
source system's *direction*, at the value the size needs. Recorded in Known Gaps
rather than resolved.

### Font stack

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,400;0,500;0,600;1,400&family=Noto+Sans+KR:wght@400;500;600&family=Noto+Sans+TC:wght@400;500;600&display=swap" rel="stylesheet">
```

SF Mono is not on Google Fonts and is not redistributable. It resolves natively
on macOS and falls through `ui-monospace` elsewhere, which is what the source
system already specifies — so the mono stack is
`'SF Mono', ui-monospace, SFMono-Regular, Menlo, monospace` and no mono family
is requested over the network. The Noto faces stay for non-Latin labels; the
Noto *serif* faces are gone with the serif they backed.

### Font source

The font source decides whether a diagram makes any network request. It is a skin setting, so a saved profile carries it too.

Font source: `web`

| Value | What ships | Network |
|---|---|---|
| `web` (default) | The Google Fonts `<link>` above; text renders in Inter, with the mono resolving locally | One stylesheet request to `fonts.googleapis.com`, plus the font files |
| `system` | No font `<link>`; both family stacks fall through to the platform's own sans and monospace faces | None |

Use `system` when the user asks for offline output, system fonts, or no Google Fonts, or when this line says `system`. In `system` mode:

- Omit the font `<link>` (and the export `@import`) entirely. Keep every `font-family` stack as written: each one already ends in a generic family (`system-ui, sans-serif`, `ui-monospace, monospace`), so a viewer who has Inter installed still gets it and everyone else gets their system face.
- Fallback faces have different metrics from Inter, so keep the 8px label padding intact rather than trimming boxes to the Inter measurement.
- Export with `python3 scripts/export_svg.py <file> --system-fonts`, and verify with `python3 scripts/self_check.py --offline <file>`, which fails if the Google Fonts link is still present.

The render linter's default run (`lint-render.py` with network blocked) measures exactly this fallback rendering, so every shipped template and example is already checked in system-font mode.

To render with no network at all, install Inter locally (SIL Open Font License) and use `system`: the sans stack resolves to the installed face first. The mono never travels the network in either mode — SF Mono is not redistributable, so a non-Apple host always draws the label in a substitute, and the 8px label budget is the contract rather than a fallback allowance.

### Korean labels

Inter carries no Hangul. Google Fonts serves it in seven subsets — `cyrillic-ext`, `cyrillic`, `greek-ext`, `greek`, `vietnamese`, `latin-ext`, `latin` — and none of them is Korean. A Korean `<text>` element extends its own family — never swap the skin:

```svg
<text font-family="'Inter', 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif">결제 서비스</text>
```

`Noto Sans KR` ships in the font link above, so the web font resolves before any locally installed one and the same file renders identically on macOS, Windows, and a reviewer's browser. The local families follow it for offline viewing. Google's `css2` endpoint slices Korean by unicode-range, so a diagram with a handful of Korean labels downloads only the slices it touches.

There is no serif line to extend. A page title is `'Inter', 'Noto Sans KR', …` at 32px/600, the same two faces as a node name at a 2.7× size step, so a mixed Latin/Korean title cannot split across families the way the shipped skin's `'Instrument Serif', 'Noto Serif KR', serif` was built to stop it splitting.

**The link is not the stack.** All four templates and all 210 shipped examples request `Noto Sans KR` and `Noto Sans TC` in the `css2` link, but only `template.html` and `template-dark.html` name those faces in a sans variable; every other file resolves its own to `'Inter', system-ui, sans-serif`. A file in the second group draws Hangul from whatever `system-ui` resolves to on the viewer's machine and never touches the face it already downloaded. When one of them gains a Korean label, either add the Noto faces to that variable or set `font-family` on the `<text>` element as above.

**Width budget.** Measure per character, not per script: **every Unicode wide or full-width character costs 1em, every other character costs its face's Latin advance** (0.60em sans, 0.62em mono), and nonspacing/enclosing marks cost nothing. Sum over the string and multiply by the font size for the text width, then add padding and round the box up to the next multiple of 4. `verify-treemap.py` enforces exactly this text width for treemap cell labels; the padding and rounding are authoring convention, and no other type carries an automatic check, so on those the budget is yours to hold.

The two Latin advances are the shipped skin's constants, kept because they measure conservative against the faces this skin uses rather than because they were recalibrated. Read from the variable font Google Fonts serves (Inter v20, `latin` subset) at the 600 that `node-name` sets, Inter averages 0.579em across printable ASCII and 0.524em across ten realistic node names, so 0.60em over-budgets a Latin sans label and sizes the box large. `'SF Mono'` resolves on macOS to `.SF NS Mono`, monospaced at 0.618em; `Menlo` is monospaced at 0.602em. 0.62em is therefore exact on the first and conservative on the second. Both errors push the box outward, which is the safe direction. None of these are browser measurements and none of them include kerning.

Counting by script is the trap. `주문 v2.1` is two full-width syllables and five narrow characters; a formula that tallies Hangul, Latin letters, and spaces silently drops `2`, `.`, and `1` and sizes the box for four of its seven characters. Every rendered character costs something — measure per character, never per script.

Three rules follow from Hangul metrics:

- **Sublabels stay Latin.** Ports, protocols, field types, and URLs are Latin anyway — keep the mono there and don't translate them. Hangul in a 9px mono sublabel is unreadable, and no face in the mono stack has a glyph for it: `.SF NS Mono` and `Menlo` both lack Hangul entirely, and no mono family is requested over the network to supply it.
- **Floor of 12px.** Hangul goes muddy below 12px. If a Korean name doesn't fit at 12px, cut the name — don't shrink the type.
- **Arrow labels, eyebrows, and legend text switch register.** Those slots are 8px mono, uppercase and tracked, which Hangul has neither a face nor legibility for. A Korean label in one of those slots becomes 12px sans at weight 500 with no tracking and no uppercase transform, and its mask rect grows to match (16px tall, width from the budget above, still rounded to a multiple of 4). Latin labels in the same diagram keep the mono treatment. The general rule this follows from is derived under [Cyrillic labels](#cyrillic-labels).

**Load-bearing rule:** Mono is for *technical* content (ports, commands, URLs, field types). Names go in Inter. So does the page title: there is no serif to change register with, so the title is carried by size and tracking instead (see [No serif](#no-serif)). Italic Inter is reserved for annotation callouts (see [primitive-annotation.md](primitive-annotation.md)). **Never JetBrains Mono** as a blanket "dev" font.

### Traditional Chinese labels

Inter carries no Han either — the seven subsets listed under [Korean labels](#korean-labels) are the whole of its coverage. A Traditional Chinese `<text>` element extends its own family — never swap the skin:

```svg
<text font-family="'Inter', 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif">請求項比對</text>
```

`Noto Sans TC` ships in the font link above, so the web font resolves before any locally installed one and the same file renders identically on macOS, Windows, and a reviewer's browser. The local families follow it for offline viewing. Google's `css2` endpoint slices Chinese by unicode-range, so a diagram with a handful of Chinese labels downloads only the slices it touches. The link-is-not-the-stack caveat under [Korean labels](#korean-labels) applies verbatim: only `template.html` and `template-dark.html` name `Noto Sans TC` in a sans variable.

A page title takes the same stack as a node name, at 32px/600. There is no serif equivalent to reach for, so a mixed Latin/Han title has nothing to split across.

**Width budget.** The per-character contract above is unchanged: every Unicode wide or full-width character costs 1em, every other character costs its face's Latin advance, and nonspacing marks cost nothing. Full-width punctuation — `（）「」，。：` — is wide and costs 1em as well, which is the part most often dropped.

Counting by script is the trap. `請求項 v2.1` is three full-width characters and five narrow ones; a formula that tallies Han and Latin letters silently drops `2`, `.`, and `1` and sizes the box for six of its nine characters.

Three rules follow from Han metrics, mirroring the Hangul ones:

- **Sublabels stay Latin.** Ports, protocols, field types, and URLs are Latin anyway — keep the mono there and don't translate them. Han in a 9px mono sublabel is unreadable, and `.SF NS Mono` and `Menlo` have no Han glyphs at all. A sublabel that is prose rather than a value may be Chinese, but it then switches register by the third rule below.
- **Floor of 12px.** Han packs more strokes than Hangul into the same em box, so the 12px floor binds at least as hard here. If a Chinese name doesn't fit at 12px, cut the name — don't shrink the type.
- **Arrow labels, eyebrows, and legend text switch register.** Those slots are 8px mono, uppercase and tracked, which Han has neither a face nor legibility for. A Chinese label in one of those slots becomes 12px sans at weight 500 with no tracking and no uppercase transform, and its mask rect grows to match (16px tall, width from the budget above, still rounded to a multiple of 4). Latin labels in the same diagram keep the mono treatment.

Simplified Chinese takes the same three rules with the Simplified stack (`'Noto Sans SC'`, `'PingFang SC'`, `'Microsoft YaHei'`). That face does not ship in the link, so Simplified labels still resolve through whatever the viewer has locally.

### Cyrillic labels

Inter ships Cyrillic — Google Fonts serves it in a `cyrillic` subset (U+0301, U+0400–045F, U+0490–0491, U+04B0–04B1, U+2116) and a `cyrillic-ext` subset — so names, titles, and callouts in Bulgarian, Russian, Ukrainian, or Serbian need no stack extension at all. Greek is the same: `greek` and `greek-ext` ship too. Sublabels, arrow labels, eyebrows, and legend text keep the Latin treatment as well — same faces, sizes, tracking, and uppercase — because `.SF NS Mono` and `Menlo` both carry Cyrillic and Greek. There is no register switch for either script.

**The register switch is a coverage test, not a face fact.** The shipped skin could settle it by citing a subset list: Geist Mono came over the network from Google Fonts, its Cyrillic coverage was published, and Hangul and Han switched register because that same list showed no face for them. This skin requests no mono over the network. The author therefore cannot ask what the mono *is*; the rule has to be stated over what the stack can be shown to cover. **A script keeps the mono treatment only when every named face in the mono stack carries it; otherwise it switches to 12px sans at weight 500, untracked and un-uppercased.** The stack's two named faces are `'SF Mono'` — `.SF NS Mono` on macOS — and `Menlo`. Read off the font files, both carry Latin, Greek, and Cyrillic, and neither carries a single Hangul syllable or Han character. That lands Cyrillic and Greek on the Latin treatment and Hangul and Han on the register switch: the same two outcomes as the shipped skin, reached from the glyph tables instead of from a subset list.

Past those two faces the stack is `ui-monospace`, `SFMono-Regular`, and the `monospace` generic, which resolve to whatever the viewer's platform supplies. Nothing in this skill can know what that is, so a viewer whose generic mono lacks Cyrillic draws it from a proportional substitute at a width the budget does not predict. That tail is unverified and recorded in Known Gaps rather than assumed covered. Extending a mono stack is not the escape: appending `'Noto Sans KR'` to it puts a proportional face in a monospaced slot, which is the register switch with none of its compensating size.

**Inter leads the sans stack, and that is what keeps the CJK slices out of the way.** Google Fonts slices Cyrillic into `Noto Sans KR` and `Noto Sans TC` as well, so a sans stack reaching one of them before a Cyrillic-covering face would set Cyrillic in a Korean or Chinese design. The shipped skin had exactly that problem, because Instrument Serif has no Cyrillic and was transparent to it; that is what the serif-order rule existed to patch. Here `'Inter'` leads every sans stack in the asset tree — all four templates and every example — and Inter's own `cyrillic` subset answers before any Noto face is consulted. The ordering is an invariant to hold rather than a rule to remember — demote Inter below a Noto face and the trap returns.

**Width budget.** The per-character contract above is unchanged: every character costs its face's Latin advance (0.60em sans, 0.62em mono). It fits the mono exactly and Inter only on average. `.SF NS Mono` and `Menlo` are monospaced, so a Cyrillic glyph advances exactly as far as a Latin one — `А`, `Ж`, and `A` all measure 0.618em in the first — and sublabels, arrow labels, eyebrows, legend text, and their mask rects are sized as for Latin. Inter is proportional, and its wide Cyrillic letters run well past the 0.60em average, capitals and lowercase alike. At the 600 that `node-name` sets, `Ж` and `Ю` measure 1.03em, `Щ` 1.00em, `Ш` 0.98em, and `Ы` 0.91em, while `ж ш щ ы ю` fall between 0.78em and 0.87em. `Шкаф ODF-2` at 12px is budgeted at 72px and sums to 75px of advance. Rounding the box up to a multiple of 4 recovers at most 3px, so it is not the remedy. Leave the overshoot in the box padding and measure a Cyrillic sans name in the browser: these are advance widths with no kerning in them, and `verify-treemap.py` holds the budget rather than the drawn width, so neither it nor the figure above catches what the renderer actually does.

Counting by script is still the trap. `Шкаф ODF-2` is four Cyrillic letters, a space, three Latin letters, a hyphen, and a digit; a formula that tallies Cyrillic letters, Latin letters, and spaces silently drops `-` and `2` and sizes the box for eight of its ten characters.

**Preserve printed labels.** A label the reader matches against a physical thing — a cabinet, a splice closure, a port map — carries the exact printed string. Don't transliterate it and don't re-case it; if one has to sit in an uppercase slot such as an eyebrow, drop the transform for that label rather than re-case the printed string. `Шкаф ODF-2` stays `Шкаф ODF-2`, not `Shkaf ODF-2`.

---

## Stroke, radius, spacing

| Token | Value | Use | Source token |
|---|---|---|---|
| `stroke-thin` | `0.8` | Tag-box outlines, leaf nodes | — |
| `stroke-default` | `1` | Most strokes | — |
| `stroke-strong` | `1.2` | Emphasis strokes, external/HTTP arrows | — |
| `radius-none` | `0` | Type tags, arrow-label masks, full-bleed bands | `{rounded.none}` |
| `radius-sm` | `5` | Node boxes | `{rounded.xs}` |
| `radius-md` | `8` | Containers, zones, rings | `{rounded.sm}` |
| `radius-lg` | `18` | Editorial summary cards (HTML, not SVG) | `{rounded.lg}` |
| `grid` | `4` | Every coord, size, and gap is divisible by 4 (hard rule) | — |

**The radius ladder is the source system's, with one value dropped and the rest
re-pointed.** The shipped skin used 4/6/8; Mine Final declares 0/5/8/11/18/full
and forbids inventing a value between them, so 4 and 6 are not available. Node
boxes take 5 and containers 8, which preserves the shipped skin's *relation* —
a node is rounder than nothing and less round than the zone enclosing it — at
values the system can express.

**Type tags and label masks take 0, not a small radius.** The shipped skin set
them at `rx=2` to keep a 12px-tall box from reading as a pill. The smallest
radius this system has is 5, which on a 12px box is 42% of its height and reads
as exactly the pill that rule exists to prevent. 0 is in the ladder, so 0 is the
answer. The source system's corollary — radius exists only while a block is
inset — pulls the other way for a tag sitting inside a node, and loses to the
measurement.

`{rounded.md}` 11px and `{rounded.full}` have no diagram role: 11 is for
controls and a diagram has none, and a capsule on a node box would make every
node read as a button.

**The grid is unaffected.** Diagram geometry stays on 4px. The source system's
one off-grid value, `{spacing.md}` 17px, is a component padding and never
reaches an SVG coordinate.

---

## Node type → treatment

Semantic role combinations — reference these by name in type specs.

| Type | Fill | Stroke |
|---|---|---|
| `focal` (1–2 max) | `accent-tint` | `accent` |
| `backend` | `paper-2` | `ink` |
| `store` | `ink @ 0.05` | `muted` |
| `external` | `ink @ 0.03` | `ink @ 0.30` |
| `input` | `muted @ 0.10` | `soft` |
| `optional` | `ink @ 0.02` | `ink @ 0.20` dashed `4,3` |
| `security` | `accent @ 0.05` | `accent @ 0.50` dashed `4,4` |

**`backend` is `paper-2`, not white.** The shipped skin hard-coded `#ffffff` for
the one node type that needed to read as lifted off the paper. On the light
ground `paper-2` *is* `#ffffff`, so nothing changes; on the dark ground white
would be a hole burned in the page. `paper-2` is the lift in both — `#0f1011`
over `#010102` — which is the whole reason the source system expresses depth as
a surface level rather than a shadow.

The seven treatments above are the only place color distinguishes node kinds,
and six of the seven are an ink ramp. A reader cannot name them from the fills
alone; that is what the legend strip is for, and why the §9 gate requires one
that covers every type used and nothing extra.

---

## Customizing the skin

Four options:

1. **Run onboarding** — see [`onboarding.md`](onboarding.md). Drop a URL; the skill extracts the palette + fonts and rewrites this file.
2. **Edit by hand** — change the hex values in the tables above. Run the pre-output taste gate afterward to verify the accent still reads as "focal" against the new paper color.
3. **Brand handoff** — paste your existing design-token JSON into a new section here and map its tokens to the semantic roles above.
4. **Client profiles** — save and switch named skins, or bind one to a project, using [`profiles.md`](profiles.md).

### Constraints (don't break these)

- **Contrast**: every *text* token (`ink`, `muted`, `soft`, `ink-strong`) must clear 4.5:1 on the paper it sits on, in both themes. `accent` is not a text token here and is held to 3:1 as an object. See the [contrast contract](#contrast-contract).
- **The accent never sets type.** Not at 32px, not in a legend, not as its own arrow's label. If a word needs emphasis, give it `ink` and put the accent on the object beside it.
- **One accent, one value, both themes**: two accents erases the focal signal, and a per-theme accent is two brands.
- **No second chroma**: if your brand ships 8 colors, pick 3 (paper, ink, accent). The rest become `muted` and `soft`. There is no `link`, no series palette, and no semantic red/green/amber.
- **One sans, one mono**: Inter and SF Mono. Two families, not three. Weight and size carry the register change the serif used to.
- **Paper is one of the two declared grounds**: `#f8f8f8` or `#010102`. Neither is warm; the shipped skin's "pick a cream with a hint of warmth" does not apply to a system whose only warmth is the accent.
- **No shadows, in either theme.** Depth is `paper-2` plus a 1px `rule`. A shadow on `#010102` is invisible and on `#f8f8f8` it is a second depth mechanism.
- **Dot pattern is off, not optional**: the 22×22 dot pattern reads as texture, and the source system expresses separation by changing surface level. Use `paper-2` where the shipped skin would have used dots.
- **Container is clean by default**: the diagram sits directly on the page paper, no secondary container background or border. A framed variant (`paper-2` bg + `rule` border + `radius-md` + padding) is available as an opt-in for card-heavy layouts, but don't reach for it by default — the extra chrome fights the figure.

---

## Known Gaps

- **The accent reads 3.06:1 on the light paper.** It clears the 3:1 an object
  needs and misses the 4.5:1 a word needs, by a margin thin enough that a nudge
  either way crosses a line. `verify-contrast.py` holds the floor by classifying
  the role as non-text, so a lighter accent fails CI — but nothing in the skill
  stops an author painting a word in it. No gate reads the drawn text: the
  upstream repository checked its own preview script for the misuse, and that
  script is not part of a vendored skill, so every diagram here is uncovered.
- **Three of four type roles are below every declared step.** 8px and 9px labels
  are off the source system's scale entirely, and their tracking values were
  chosen for legibility at that size rather than taken from a token.
- **`accent-tint` is derived and unexamined.** The source system declares no
  translucent accent; 0.10/0.14 were picked so a bordered box reads as filled.
  Nobody has looked at one.
- **The Latin advance constants are inherited, not recalibrated.** 0.60em sans
  and 0.62em mono were calibrated against Chromium renderings of the shipped
  skin's faces. They are kept because they measure conservative against Inter,
  `.SF NS Mono`, and `Menlo`, but that was read from the font files' own advance
  widths; nobody has re-rendered a label in a browser to confirm the margin, and
  the Cyrillic overshoot figure is a sum of advances with no kerning in it.
- **The mono stack's coverage past its two named faces is unverified.**
  `'SF Mono'` and `Menlo` were read off the glyph tables on a macOS host.
  `ui-monospace`, `SFMono-Regular`, and the `monospace` generic resolve to
  whatever the viewer's platform supplies, and the register-switch rule treats
  that tail as unknown rather than as covered. A Cyrillic eyebrow on a platform
  whose generic mono lacks Cyrillic falls back to a proportional face silently.
- **`verify-docs-sync.py` cannot run against a vendored skill.** Several of its
  invariants validate the upstream repository's shape rather than the skill's —
  `check_factory_install_surface` reads a root `README.md` that does not exist
  here and raises `FileNotFoundError`, and `main` calls it well before it
  reaches anything about type. The serif-stack invariant it used to carry is
  retired: it required all four templates to declare a `--font-serif` reaching
  `Noto Serif` ahead of any CJK serif face, and this skin declares no
  `--font-serif` anywhere. Nothing replaces it, because the title is set in
  Inter, whose Google Fonts slice carries Cyrillic directly — there is no
  fallback order left to get wrong.
- **Radar lost two series.** Three dash patterns on one ink is the honest
  ceiling, and the shipped skin supported five. A five-entity radar now has no
  representation in this skin at all.
