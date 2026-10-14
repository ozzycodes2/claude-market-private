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
| `diagram-design-mine` | Draw the architecture as a self-contained HTML/SVG figure — 45 visual types, Mine Final skin, with `.drawio` / Mermaid / Excalidraw import. |

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

`diagram-design-mine` is independent of the other four and needs no setup.

## diagram-design-mine

A fork of Cathryn Lavery's [diagram-design](https://github.com/cathrynlavery/diagram-design)
(v2.6, MIT), reskinned to Mine Final. The layout grammar is unchanged — same
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

`skills/diagram-design-mine/scripts/` carries upstream's verifiers, retargeted
to run from the skill directory rather than a repository checkout:

```sh
cd architecture-design/skills/diagram-design-mine
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

Four upstream gates validate the *repository* rather than the skill and have no
subject here: `verify-docs-sync.py` (expects a root README, CHANGELOG, and
`docs/`), `verify-plugin-package.py` (diffs a git base ref for version bumps),
`verify-screenshot-freshness.py` (wants `docs/screenshots/*.png`, which would be
45 images of the upstream skin), and `verify-semantic-motion.py` (reads
`docs/adr/0002-semantic-patterns-do-not-expand-the-taxonomy.md`). They are kept
for provenance and are expected to fail.

`verify-docs-sync.py` is down to fifteen drift classes from upstream's sixteen.
The retired one required every template to declare a `--font-serif` stack
reaching `Noto Serif` before any CJK serif face; this skin has no serif, and its
Inter titles draw Cyrillic from Inter itself, so the invariant had no subject
rather than an unmet one.

The 41 `scripts/test-*.py` suites are the verifiers' own tests. Thirty-four
pass. The seven that do not are the harnesses for the repository-shaped gates
above plus `test-build-openai-plugin-zip.py`, `test-maintainer-policy.py` and
`test-plugin-package.py`; each wants a surface a vendored skill does not carry —
`.codex-plugin/plugin.json`, `.maintainer-policy.json`, `docs/adr/`,
`docs/screenshots/manifest.json`, a git base ref. `test-build-readme-thumbs.py`
is the one environmental failure: it needs Pillow.

```sh
for t in scripts/test-*.py; do python3 "$t" >/dev/null 2>&1 || echo "$t"; done
```

## License

MIT — see the marketplace [LICENSE](../LICENSE).

`skills/diagram-design-mine/` is derived from
[cathrynlavery/diagram-design](https://github.com/cathrynlavery/diagram-design),
MIT, © Cathryn Lavery — see
[skills/diagram-design-mine/LICENSE](skills/diagram-design-mine/LICENSE).
