# Fetching mac-ui's live docs

`@vlognow/mac-ui` (Machinify Web Components, `github.com/vlognow/mac-ui`) is a
fast-moving framework. Its docs — not this skill — are the authority, so fetch
them at HEAD when a PR touches `mac-*` components or `docs/adrs/` inside a
mac-ui repo. The repo is `internal`, so use `gh api` (WebFetch can't read it).

## Entry point: the Reading Authority table

The repo root `CLAUDE.md` lists the authoritative sources in priority order.
Fetch it first and follow it — the file list below can go stale, the table
won't:

```bash
gh api repos/vlognow/mac-ui/contents/CLAUDE.md \
  --jq '.content' | base64 -d
```

## Fetch a doc at HEAD

```bash
fetch_macui () {  # $1 = path within the mac-ui repo
  gh api "repos/vlognow/mac-ui/contents/$1" --jq '.content' | base64 -d
}
```

## Docs that matter for drift/completeness review

| Path | Use for |
|------|---------|
| `docs/adrs/` (+ `README.md`, `template.md`) | mac-ui's own ADR set — for the ADR cross-checks in Step 4 when reviewing the mac-ui repo itself |
| `packages/mac-ui/docs/ai-behavior-spec.md` | Component patterns, decorators, events, a11y, anti-patterns |
| `packages/mac-ui/docs/ai-code-audit.md` | Violation Catalog + structural transforms — the authority for whether a doc's described pattern is still current |
| `packages/mac-ui/docs/INDEX.md` | Index of per-component docs; confirms which `mac-*.md` exist |
| `packages/mac-ui/docs/mac-{name}.md` and `packages/mac-ui/docs/ai/mac-{name}.md` | Per-component slots/attributes/events/CSS parts |

## How to use them here

1. From the diff, collect the set of `mac-*` component names referenced.
2. Fetch the per-component doc for each and the behavior spec.
3. When a repo's own docs (README, usage guide) describe a component's API,
   verify that claim against the fetched component doc — a renamed slot,
   attribute, or event that the consuming repo's docs still document the old way
   is drift class #1/#2.

> This skill checks *documentation* drift. Auditing changed `.ts` source against
> the Violation Catalog is `security-scan`'s job (it fetches the same
> docs). Don't duplicate the source audit here.
