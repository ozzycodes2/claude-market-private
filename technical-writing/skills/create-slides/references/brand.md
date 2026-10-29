# Machinify slide brand

Source: the Machinify master presentation (font Aptos, April 2026).
`assets/deck-template.html` implements every token below; use its CSS
variables rather than raw hex values.

## Colors

### Primary

| Token | Hex | Use |
|---|---|---|
| `--teal` | `#1F3539` | Dark slide ground |
| `--teal-mid` | `#2B4A50` | Rules and dividers on teal |
| `--green` | `#4ECF99` | Accent on teal: logo, top bar, side bar, focal number |
| `--amber` | `#FBAE40` | Eyebrow on teal |
| `--seafoam` | `#CFE9BC` | Soft panel ground |
| `--blue` | `#BFD1DD` | Secondary text on teal |
| `--ink` | `#171717` | Text on light slides |
| `--offwhite` | `#F8F8F8` | Light slide ground |

### Readable variants on light slides

Brand green and amber fall under 2:1 contrast on off-white, so text and
focal marks on light slides use the deep variants. Large fills and the
4px top bar keep brand green.

| Token | Hex | Contrast on `#F8F8F8` | Use |
|---|---|---|---|
| `--deep-g` | `#1A7A52` | 5.0:1 | Accent: focal number, icon, diagram accent |
| `--deep-a` | `#8A5A10` | 5.6:1 | Eyebrow |

### Neutrals

| Token | Hex | Use |
|---|---|---|
| `--backdrop` | `#081D27` | Page behind the slide (midnight blue) |
| `--gray4` | `#283B45` | Strong secondary text, page number |
| `--gray3` | `#5C6D76` | Labels on light slides |
| `--gray2` | `#C3D0D9` | Solid rules |
| `--gray1` | `#E2EAEF` | Hairlines, footer band |
| `--card` | `#F7FBFD` | Card ground |
| `--white` | `#FFFFFF` | Text on teal |

### Extended (charts only)

`#95E124` electric green, `#B0DCFD` light blue, `#005D97` sea blue,
`#166F1C` forest green, `#5546F6` indigo, `#C71EC4` magenta, `#855A2A`
copper. Diagrams reach these only through the Machinify diagram profile,
never by hand.

No other colors, no gradients, no shadows, no 3D.

## Typography

- Family: `'Aptos', 'Calibri', 'Segoe UI', system-ui, sans-serif`. Mono:
  `'SF Mono', ui-monospace, Menlo, monospace`. No Inter, no serif.
- Weights: 300 for headlines and numbers, 600 for emphasis via `<strong>`.
  Never bold a SemiBold run again.
- Line height 1.15.
- Sizes on a 1280×720 slide:

| Role | Size | Weight |
|---|---|---|
| Title slide `h1` | 53px | 300 |
| Divider `h2` | 48px | 300 |
| Content `h2` | 36px | 300, one line |
| Statement | 48px | 300 |
| Big number | 160px | 300 |
| Stat-strip number | 72px | 300 |
| Eyebrow | 13px | 600, uppercase, 2.5px tracking |
| Label under a number | 16–18px | 600, uppercase |
| Footer | 9.5px | 400 |

## Fixed elements

- **Footer** on every slide: `© Machinify. All rights reserved. Proprietary
  and confidential.` with the page number at right. The template's script
  adds it; do not write it by hand.
- **Green top bar**: 4px `--green` across the top of every content slide.
- **Logo mark**: three ascending `--green` pillars (16, 22, 28px) and the
  white wordmark, top-left on title and closing slides.
- **Divider**: 6px green side bar and a section numeral at 4% white.

## Icons

Material Symbols Outlined only, `FILL 0`, `wght 300`. One icon per concept,
never as a bullet. Color: `--deep-g` on light, `--green` on teal. Common
names: `hub`, `shield`, `cell_tower`, `language`, `sync_alt`, `balance`,
`bolt`, `fact_check`, `warning`, `lock_open`, `rocket_launch`. Browse
<https://fonts.google.com/icons?icon.style=Outlined>.

## Layout

- Slide 1280×720. Content padding 46px top, 88px sides.
- Content header (eyebrow + `h2`) is 86px; the body under it is 1104×520,
  the `slide-body` diagram preset.
