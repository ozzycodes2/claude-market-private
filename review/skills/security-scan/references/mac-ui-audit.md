# mac-ui source audit (idiom + security)

When `analyze` set `uses_mac_ui: true`, audit changed `.ts`/`.tsx` that define
or consume a `mac-*` component against mac-ui's **live** authority docs. The
framework changes often, so fetch at HEAD — do not audit from memory.

## Fetch the authority (repo is internal → use gh)

```bash
REPO="${MAC_UI_REF_REPO:-vlognow/mac-ui}"
fetch () { gh api "repos/$REPO/contents/$1" --jq '.content' | base64 -d; }

fetch CLAUDE.md                                   # Reading Authority table (start here)
fetch packages/mac-ui/docs/ai-code-audit.md       # Violation Catalog + structural transforms
fetch packages/mac-ui/docs/ai-behavior-spec.md    # component patterns / anti-patterns
fetch packages/mac-ui/docs/security.md            # security-specific guidance
```

The root `CLAUDE.md` "Reading Authority for Source-Code Audit During Review"
section is explicit that this pass is mandatory for changed `.ts` under a
package `src/` defining/consuming a `mac-*` component.

## What to flag (from the Violation Catalog — verify against the fetched doc)

Report these as a **mac-ui idiom** cluster, separate from generic correctness.
Security-relevant ones first:

- `element.innerHTML = someVar` → XSS; the blessed form is `textContent` or
  `this.safeSetHTML()`.
- `new CustomEvent(...)` dispatch → should be `this.emit("kebab-name", detail)`.
- `as any` / `as HTMLElement` where a real component type exists.
- State captured in a JS closure instead of on the DOM (`data-*`, `hidden`).
- `MelEvent<Target, Detail>` vs raw `CustomEvent` in event maps.

The fetched `ai-code-audit.md` is authoritative for the full catalog and for
which substitution each violation maps to; use it, not this summary, as the
source of truth — this list only tells you the pass exists and which items are
security-bearing.

> Idiom findings that are purely stylistic (not security) still belong in the
> review, but tag them clearly so they don't inflate the security severity
> counts that drive the merge recommendation.
