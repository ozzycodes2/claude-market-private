# mac-ui test analysis (dynamic rubric)

mac-ui's `CLAUDE.md` makes consulting its testing guide **mandatory** before
reviewing any test code in a mac-ui repo. The guide changes, so fetch it live.

## Fetch the authority

```bash
REPO="${MAC_UI_REF_REPO:-vlognow/mac-ui}"
fetch () { gh api "repos/$REPO/contents/$1" --jq '.content' | base64 -d; }

fetch CLAUDE.md                         # test Reading-Authority table
fetch docs/ai-testing-guide.md          # multi-axis rubric + anti-pattern catalog + pre-PR checklist
fetch packages/mac-ui/docs/ai-behavior-spec.md  # component test patterns (helpers.ts, base-styles mocking)
```

The guide fires on any changed `*.test.*`/`*.spec.*`, files under
`tests/`/`test/`/`__tests__/`, and test helpers/fixtures/mocks/setup files. It
does NOT fire on `*.stories.*` or visual-regression config.

## Use it as the rubric

Audit changed test files against the fetched guide, not this summary. Report:

- Which axes of its multi-axis rubric the changed tests satisfy vs miss.
- Anti-patterns from its catalog present in the diff (e.g. tests that assert
  nothing, characterization tests where a contract test is required,
  setup-discipline violations).
- Whether the pre-PR checklist items are met for the changed test files.

When a package has its own `CLAUDE.md`/testing doc, it wins for that package;
the monorepo guide is the baseline when the package doc is silent. The
package's `package.json` test scripts are authoritative for which framework/
config actually runs (CI runs the same commands).
