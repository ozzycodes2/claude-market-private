# mac-ui source audit (idiom + security)

When `analyze` set `uses_mac_ui: true`, audit changed `.ts`/`.tsx` that define
or consume a `mac-*` component against mac-ui's **live** authority docs. The
framework changes often, so fetch at HEAD — do not audit from memory.

## Fetch the authority (the repo may be private → use gh)

```bash
REPO="${MAC_UI_REF_REPO:?set MAC_UI_REF_REPO to owner/repo}"
fetch () { gh api "repos/$REPO/contents/$1" --jq '.content' | base64 -d; }

fetch CLAUDE.md   # Reading Authority table (start here)
```

The root `CLAUDE.md` names the authoritative audit docs (Violation Catalog,
behavior spec, security guidance) in priority order. Fetch each one it lists for
source-code audit during review, and follow its rule for when the pass is
mandatory.

## What to flag

Report the fetched Violation Catalog's violations as a **mac-ui idiom**
cluster, separate from generic correctness. Security-relevant ones first —
unescaped HTML sinks (XSS), raw event dispatch that bypasses the framework's
helper, and unsafe casts where a real component type exists.

The fetched catalog is authoritative for the full list and for which
substitution each violation maps to; use it, not this summary, as the source of
truth.

> Idiom findings that are purely stylistic (not security) still belong in the
> review, but tag them clearly so they don't inflate the security severity
> counts that drive the merge recommendation.
