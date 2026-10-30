# architecture-design

Design deep modules and sharpen a project's domain model — a shared vocabulary for
module depth and seams, ubiquitous language and ADRs, and a codebase deepening scan
that ends in a visual report.

## Skills

| Skill | What it does |
|-------|--------------|
| `codebase-design` | Shared vocabulary for designing deep modules — interfaces, seams, testability, and AI-navigability. Use when designing or improving a module's interface or finding deepening opportunities. |
| `domain-modeling` | Build and sharpen a project's domain model — pin down ubiquitous language and record architectural decisions (ADRs). |
| `improve-codebase-architecture` | Scan a codebase for deepening opportunities, present them as a visual HTML report, then grill through whichever one you pick. |
| `setup-matt-pocock-skills` | One-time repo setup — configures the issue tracker, triage label vocabulary, and domain doc layout. Run once before first use of the other skills. |
| `create-diagram` | Draw the architecture as a self-contained HTML/SVG figure — 45 visual types, Fabric skin, with `.drawio` / Mermaid / Excalidraw import. |

## Usage

```
> run setup-matt-pocock-skills on this repo   # once, first
> help me design a deeper interface for this module
> let's define the domain terms for the billing subsystem
> scan this codebase for architecture-deepening opportunities
> draw the service topology as a layered architecture diagram
```

Each skill can also be invoked explicitly, e.g. `/architecture-design:codebase-design`.

## Commands

| Command | What it does |
|---------|--------------|
| `/architecture-design:diagram-doctor` | Environment diagnostics for diagram generation. Read-only. |
| `/architecture-design:diagram-profile` | Save, load, inspect, or delete a client skin profile. |
| `/architecture-design:export-diagram` | Export a generated diagram to `.svg` / `.png`, plus an optional block registry. |
| `/architecture-design:import-drawio` | Digest a `.drawio` file into nodes, edges, and budget flags. |
| `/architecture-design:import-mermaid` | Same, for Mermaid source. |
| `/architecture-design:import-excalidraw` | Same, for `.excalidraw`. |

Importers extract rather than render — they never reproduce the source tool's
automatic spacing and routing.

> **Run `setup-matt-pocock-skills` once** before the others — it lays down the issue
> tracker, label vocabulary, and domain doc layout the rest depend on.

`create-diagram` is independent of the other four and needs no setup.

## create-diagram

A fork of Cathryn Lavery's [diagram-design](https://github.com/cathrynlavery/diagram-design)
(v2.6, MIT), reskinned to Fabric. The layout grammar is unchanged — same
forty-five visual types, same six connector rules, same nine-node / twelve-arrow
budget, same 217 worked examples at the same coordinates. Three skin rules
override what upstream ships:

- The accent paints objects, never type. It reads 3.06:1 on the light paper,
  which clears the 3:1 a graphical object needs and misses the 4.5:1 a word
  needs.
- One chroma, so no `link` role. An external or HTTP call is `ink` at 1.2
  against `muted` at 1; series separate by dash, capped at three.
- An essential mark is not a hairline. Axes, baselines and lifelines take
  `soft`; `rule` is 1.33:1 light and 1.69:1 dark, and only ever encloses.

No serif, no shadows, no dot pattern. The terminal variant keeps the upstream
palette as a deliberate opt-in alternate.

### Gates

`skills/create-diagram/scripts/` carries upstream's verifiers, retargeted
to run from the skill directory rather than a repository checkout:

```sh
cd architecture-design/skills/create-diagram
python3 scripts/verify-contrast.py            # 18 role-and-use pairs, both skins
python3 scripts/lint-skin.py --all            # palette and font conformance
python3 scripts/verify-geometry.py --all      # the six connector rules
python3 scripts/verify-block-registry.py --all  # every example's block inventory
python3 scripts/verify-skin-polarity.py --all # light/dark claims against the ramp
python3 scripts/verify-motion.py --shipped    # animated examples
python3 scripts/self_check.py <file>          # per-diagram, before shipping one
```

The per-type verifiers (`verify-sankey.py`, `verify-treemap.py`,
`verify-polar.py`, and so on) each take `--all` to sweep every example of their
type, or explicit paths. `verify-contrast.py` and `verify-dumbbell.py` take no
arguments. A bare invocation that prints a usage block and exits 2 wants `--all`;
it is not a failure.

`verify-bar.py`, `verify-gantt.py`, `verify-line.py` and `verify-scatter.py` are
local, not upstream. Each one checks that drawn marks sit where their bound
`data-*` values put them on one linear scale, which is Tufte's graphical
integrity rule from *The Visual Display of Quantitative Information*. ADR 0003
in `skills/create-diagram/docs/adr/` records the Tufte decisions the whole skill
now follows.

Two further gates run clean once pointed at this layout:

```sh
python3 scripts/verify-docs-sync.py           # routing and browsing surfaces
python3 scripts/verify-semantic-motion.py     # the semantic-pattern taxonomy
```

`verify-docs-sync.py` resolves `commands/`, `.claude-plugin/` and the README at
the plugin root, since a vendored skill keeps them as siblings of `skills/`. It
is down to thirteen drift classes from upstream's sixteen. Two retired classes
guarded Factory Droid's `.factory-plugin/` install contract and a README
architecture tree that upstream rooted at its one skill directory; the third
required every template to declare a `--font-serif` stack reaching `Noto Serif`
before any CJK serif face, and this skin has no serif at all.

`verify-plugin-package.py` and `bump-plugin-version.py` are upstream's release
pipeline. They describe a one-plugin-one-skill package whose `SKILL.md`
`metadata.version` tracks the manifest MAJOR.MINOR — a relationship that cannot
hold for a plugin hosting five skills. They are kept for provenance, run only
against fixture repositories, and are not part of this plugin's release.

All 37 `scripts/test-*.py` suites pass:

```sh
for t in scripts/test-*.py; do python3 "$t" >/dev/null 2>&1 || echo "$t"; done
```

## License

MIT — see the marketplace [LICENSE](../LICENSE).

`skills/create-diagram/` is derived from
[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design),
MIT, © Cathryn Lavery — see
[skills/create-diagram/LICENSE](skills/create-diagram/LICENSE).
