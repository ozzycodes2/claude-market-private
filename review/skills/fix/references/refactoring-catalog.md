# Refactoring catalog — smell to named move

Keyed on the smell vocabulary the review passes already emit, so the diagnosis
and the cure share one name set. The checklists under
`skills/<pass>/references/checklist.md` append the resolving refactoring after a
`·`; this file is the other half of that contract.

Sources: Fowler, *Refactoring* (2nd ed.); Kerievsky, *Refactoring to Patterns*.

**The rule that governs every row:** add no trait, generic, or indirection the
smell does not demand. The move is a starting point, not a quota. Where the
language's idiom diverges, see `language-idioms.md` — the idiom wins, and the
commit body says which was applied and why.

## Mechanics, non-negotiable

1. **Smallest step.** One move at a time.
2. **Tests green between steps**, where there is a local suite to run.
3. **Behavior unchanged.** Same inputs, outputs, side effects, error values. If
   the fix requires a behavior change, it is a repair, not a refactoring — stop
   and report.
4. **Find every call site** before changing a signature. A compiler that catches
   them all is a tool, not an excuse to skip looking.

## Structure and size

| Smell | Move |
|---|---|
| Long function, complexity budget blown | **Extract Function**; **Decompose Conditional** for a gnarly predicate |
| Mixed abstraction levels in one function | **Extract Function** — give the lower level a name and get it out of the way |
| Deep nesting | **Replace Nested Conditional with Guard Clauses** |
| Long parameter list | **Introduce Parameter Object**; **Preserve Whole Object** when the caller already holds the aggregate |
| Boolean flag argument | **Remove Flag Argument** — two named functions beat one with a mode |
| Magic literal | **Replace Magic Literal** with a named constant |
| Duplication across branches or call sites | **Extract Function**; **Substitute Algorithm**; Kerievsky **Form Template Method** — but only at three or more sites |
| Dead or commented-out code | **Remove Dead Code**. Delete it; do not comment it out again |

## Classes, modules, and ownership

| Smell | Move |
|---|---|
| God class, god service, divergent change | **Extract Class** — split along the axis that changes for one reason |
| Shallow class explosion | **Inline Class**; **Combine Functions into Class** |
| Feature envy, inappropriate intimacy | **Move Function**, **Move Field**, **Hide Delegate** — put the behavior where the data lives |
| Leaked internals | **Encapsulate Record**, **Encapsulate Collection**, **Hide Delegate** |
| Shared mutable global | **Encapsulate Variable**; **Inline Singleton** |
| Layering violation (SQL in a controller, HTTP in the domain) | **Move Function** |
| Framework types deep in the domain | **Extract Interface** — the framework is a detail |
| Foreign or legacy DTO used as the internal source of truth | **Extract Class**; Kerievsky **Unify Interfaces with Adapter** |
| Accidental synonyms for one concept (`User` / `Account` / `Customer`) | **Rename Field**, **Change Function Declaration** — pick the domain's word |

## Types and conditionals

| Smell | Move |
|---|---|
| Primitive obsession | **Replace Primitive with Object**; Kerievsky **Replace Type Code with Class** |
| String- or int-typed states | **Replace Type Code with Subclasses**; Kerievsky **Replace State-Altering Conditionals with State** |
| Conditional dispatching on a type tag | **Replace Conditional with Polymorphism**; Kerievsky **Replace Conditional Dispatcher with Command** |
| Pervasive null checks | **Introduce Special Case**; Kerievsky **Introduce Null Object** |
| Error codes, swallowed errors | **Replace Error Code with Exception** — but this changes behavior, so route it as a repair |
| Misuse-prone API | **Introduce Parameter Object**; **Replace Constructor with Factory Function**; Kerievsky **Move Creation Knowledge to Factory**, **Encapsulate Classes with Factory** |
| Temporal coupling (call A before B or it breaks) | **Combine Functions into Transform**; encapsulate the sequence so the order cannot be got wrong |

## Refactoring *away* from a pattern

The half of Kerievsky that usually goes unread. A pattern that is not paying for
itself is a smell like any other:

| Smell | Move |
|---|---|
| Speculative generality, gold plating, YAGNI | **Inline Function**, **Collapse Hierarchy**, **Remove Dead Code** |
| A strategy, factory, or visitor with exactly one implementation | **Inline Class**, **Collapse Hierarchy** — reintroduce it when the second case arrives |
| An indirection whose only caller is its own test | **Remove Dead Code** |

## Moves that are often wrong

- **Replace Conditional with Polymorphism**, applied to an exhaustive `match` or
  `switch` over a closed set, in a language that checks exhaustiveness. The
  compiler is doing work that dynamic dispatch would throw away. Apply it only
  when the arms are genuinely open-world — extensible by code you do not own.
- **Introduce Null Object**, in any language with a first-class optional type.
  Use the optional.
- **Extract Class**, where the language's unit of encapsulation is the module,
  not the class. Split the module instead.
- **Replace Primitive with Object**, taken as licence to add getters and setters.
  A newtype with the conversions it actually needs is the whole fix.
