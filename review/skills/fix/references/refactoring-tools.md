# Refactoring tools — apply the move deterministically

A refactoring engine resolves symbols: it renames the function and its callers,
and leaves alone the unrelated local that shares its name and the log string
that mentions it. A hand edit gets the same result only if the agent reads
every site correctly. The tool removes that dependence, so **apply the move with
a tool whenever a row below covers it**, and hand-edit only what the tool leaves
— a doc comment, a prose mention, a test name the finding calls out.

Load only the rows for the finding's move and `context.languages.primary`.

## Preference order

1. **Refactoring engine** — scope-aware: rope, gopls, ts-morph, OpenRewrite.
2. **Structural rewrite** — syntax-aware, not scope-aware: `ast-grep`,
   `rust-analyzer ssr`, `gofmt -r`, `semgrep --autofix`. Review every match
   before writing; `ast-grep` without `-U` and `rust-analyzer search` list them.
3. **Hand edits** — when no row applies or the tool is unavailable.

`sed`, `perl -pi`, and other text replacement are not on the list: they match
the string, not the symbol.

## Availability and scope

- Check before use: `command -v <tool>`, then `<tool> --help` for the exact
  flags of the installed version.
- Run Python tools ephemerally — `uv run --with rope python -I script.py` or
  `uvx ruff …`. Never add a dependency to the repository to get a tool.
- **Pass explicit paths, all inside the finding's file set.** A tool that
  rewrites a whole crate or project — `cargo clippy --fix`, `cargo fix`,
  `eslint --fix .`, `rust-analyzer ssr` — is orchestrator-only, run like S0,
  because it edits files another agent owns.
- A rename's file set is every file that references the symbol. The
  orchestrator computes it before partitioning, with LSP `findReferences` or
  `rg -w <symbol>`.

## By move

| Move | Python | Go | TypeScript / JS | Rust | Java |
|---|---|---|---|---|---|
| Rename, Change Function Declaration (name) | rope `Rename` (script below) | `gopls rename -w <file>:<line>:<col> <New>` | ts-morph `.rename()` | hand edit + `cargo check` | OpenRewrite `ChangeMethodName`, `ChangeType` |
| Change Function Declaration (parameters) | rope `ChangeSignature` | `gopls codeaction` (`refactor.rewrite.*`) | ts-morph | hand edit + `cargo check` | OpenRewrite |
| Extract Function | rope `ExtractMethod` | `gopls codeaction -kind=refactor.extract.function` | ts-morph `getEditsForRefactor` ("Extract Symbol") | hand edit | IDE only; hand edit |
| Inline Function / Variable | rope `create_inline` | `gopls codeaction -kind=refactor.inline.call` | ts-morph `getEditsForRefactor` ("Inline variable") | hand edit | hand edit |
| Move Function | rope `create_move` | hand edit | ts-morph ("Move to a new file") | hand edit | hand edit |
| Remove Dead Code (unused import, variable) | `uvx ruff check --select F401,F841 --fix <files>` | `goimports -w <files>` | `eslint --fix <files>` (repo config) | `cargo clippy --fix` — orchestrator-only | OpenRewrite `RemoveUnusedImports` |
| Same rewrite at several sites (Replace Magic Literal, Substitute Algorithm, API migration) | `ast-grep run -l python -p '<pat>' -r '<rewrite>' -U <files>` | `gofmt -r '<pat> -> <rewrite>' -w <files>` | `ast-grep … -l ts` | `rust-analyzer ssr '<pat> ==>> <rewrite>'` — orchestrator-only | `ast-grep … -l java` |

## Analyzer findings with an autofix

A finding carrying `extra.rule` came from an analyzer. When that rule ships an
autofix, the autofix is the fix:

- semgrep, rule with a `fix:` key — `semgrep scan --config <rule> --autofix <files>`
- ruff — `uvx ruff check --select <code> --fix <files>`
- clippy, machine-applicable lint — `cargo clippy --fix -- -A clippy::all -W clippy::<lint>` — orchestrator-only

A repair still needs its covering test; the autofix only replaces the hand edit.

## rope rename

```python
import sys
from rope.base.project import Project
from rope.refactor.rename import Rename

root, path, symbol, new = sys.argv[1:5]
proj = Project(root, ropefolder=None)  # writes no .ropeproject into the repo
res = proj.get_resource(path)
offset = res.read().index(f"def {symbol}") + len("def ")
proj.do(Rename(proj, res, offset).get_changes(new))
proj.close()
```

```bash
TOOLS=$(mktemp -d)   # outside the repository; one per agent
# write the script above to "$TOOLS/rope_rename.py", then:
uv run --with rope python -I "$TOOLS/rope_rename.py" "$PWD" orders/store.py get_ord get_order
```

For a class or attribute, compute the offset of its name instead of `def `.
