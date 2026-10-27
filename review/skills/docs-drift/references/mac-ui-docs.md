# Fetching mac-ui's live docs

mac-ui is a fast-moving Web Components framework whose repo is set by
`$MAC_UI_REF_REPO` (`owner/repo`). Its docs — not this skill — are the
authority, so fetch them at HEAD when a PR touches `mac-*` components or
`docs/adrs/` inside a mac-ui repo. The repo may be private, so use `gh api`
(WebFetch can't read it).

## Entry point: the Reading Authority table

The repo root `CLAUDE.md` lists the authoritative sources in priority order.
Fetch it first and follow it:

```bash
fetch_macui () {  # $1 = path within the mac-ui repo
  gh api "repos/${MAC_UI_REF_REPO:?}/contents/$1" --jq '.content' | base64 -d
}
fetch_macui CLAUDE.md
```

## Docs that matter for drift/completeness review

From the table, fetch:

- the repo's own ADR set, for the ADR cross-checks in Step 4 when reviewing the
  mac-ui repo itself;
- the behavior spec (component patterns, events, a11y, anti-patterns);
- the per-component docs index and each referenced `mac-{name}` doc (slots,
  attributes, events, CSS parts).

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
