# Language idioms — where the catalog's move is the wrong move

Fowler's and Kerievsky's catalogs were written against class-based
object-oriented languages. Applied literally elsewhere they produce code that is
technically refactored and idiomatically wrong — and the indirection they add
outlives the PR that introduced it.

Load only the section for `context.languages.primary`. **Where the catalog and
the idiom disagree, the idiom wins**, and the commit body names the divergence
and the reason.

---

## Rust

The largest divergence set, because Rust's type system does statically what
several of the catalog's patterns do at runtime.

| Catalog move | Rust idiom | Why |
|---|---|---|
| Replace Type Code with Subclasses | **`enum` + exhaustive `match`** | The compiler checks every arm. A trait hierarchy throws that check away. Use trait objects only when downstream crates must add arms. |
| Introduce Null Object | **`Option<T>`** with `unwrap_or_default`, `ok_or`, `?` | Never author a `NullFoo` impl. The optional is the language's answer. |
| Replace Primitive with Object | **newtype** — `struct UserId(Uuid)` plus `From`, `Display`, `FromStr` as needed | No getter ceremony. The tuple struct *is* the value object. |
| Encapsulate Record / Collection | `pub(crate)` fields, accessor returning `&[T]` or `impl Iterator<Item = &T>` | Do not clone to satisfy encapsulation. |
| Combine Functions into Transform, for temporal coupling | **typestate** — `Conn<Open>` → `Conn<Sent>` — or a `self`-consuming builder | Makes the wrong order a compile error rather than a runtime assert. |
| Extract Class | **split the module** | `mod` is Rust's unit of encapsulation. A new trait is not a class boundary. |
| Move Function, for feature envy | move into the envied type's `impl` | An extension trait only when the type is foreign (orphan rule). |
| Collapse Hierarchy, for speculative generality | drop the type parameter; collapse a single-impl trait into the concrete type | A trait with one implementor is indirection with no payer. |
| Replace Error Code with Exception | `Result<T, E>` with a `thiserror` enum and `?` | Rust has no exceptions. **Removing a swallowed error changes behavior — route it as a repair, not a refactoring.** |
| Unify Interfaces with Adapter | `From` / `TryFrom` on an owned domain type | Conversion traits are the adapter. |
| Introduce Parameter Object | borrow the aggregate (`&Config`) | Do not clone a struct to satisfy a refactoring. |
| Replace Constructor with Factory Function | `TryFrom` for validating construction; `#[non_exhaustive]` config struct, or a builder | |

**Do not apply Replace Conditional with Polymorphism to an exhaustive `match`.**
It is compiler-checked; dynamic dispatch deletes the check and makes the code
worse. Only for genuinely open-world arms.

`#[cfg(test)]` helpers are not dead code.

---

## Python

| Catalog move | Python idiom |
|---|---|
| Replace Type Code with Subclasses | `enum.Enum` (or `StrEnum`), not a subclass per code |
| Replace Primitive with Object | `typing.NewType`, or a frozen `@dataclass` — not a class with getters |
| Extract Interface | `typing.Protocol` (structural), not an `abc.ABC` the caller must inherit |
| Introduce Null Object | `None` plus an early return; `Optional[T]` in the signature |
| Introduce Parameter Object | a frozen `@dataclass`, or keyword-only arguments |
| Encapsulate Record | `@dataclass` with `field(init=False)`, or `@property` — never a bare `get_x()` |
| Replace Error Code with Exception | raise a specific exception subclass; do not return a status tuple |
| Form Template Method | a function taking a callable, before a base class with hooks |

Properties over accessor methods. A `@property` is how Python encapsulates a
field without changing the call site.

---

## TypeScript

| Catalog move | TypeScript idiom |
|---|---|
| Replace Type Code with Subclasses | **discriminated union** + exhaustive `switch` with a `never` check |
| Replace Primitive with Object | branded type (`type UserId = string & { __brand: 'UserId' }`) |
| Introduce Null Object | `T \| undefined` with optional chaining and `??` |
| Encapsulate Collection | `readonly T[]`, `as const` — not a defensive copy on every read |
| Extract Interface | a structural `interface` or `type`; classes are rarely needed |
| Introduce Parameter Object | an options object with named fields |
| Replace Error Code with Exception | a `Result`-shaped union, or `throw` — be consistent with the file |

Exhaustiveness: `const _never: never = x` in the default arm makes a missed
variant a compile error. Preserve it; do not replace it with dispatch.

---

## Go

| Catalog move | Go idiom |
|---|---|
| Extract Interface | define the interface **on the consumer side**, minimal, where it is used |
| Replace Type Code with Subclasses | a typed constant set plus a `switch`; embedding, never inheritance |
| Introduce Null Object | the zero value, or an explicit `error` return |
| Replace Error Code with Exception | `error` as the last return value; `errors.Is` / `errors.As`, not sentinel `==` |
| Collapse Hierarchy | remove the interface; return the concrete type |
| Introduce Parameter Object | a config struct, or functional options |

Do not introduce generics without at least two real instantiations. Accept
interfaces, return structs.

---

## Any other language

Apply the catalog move, but check three things first:

1. **Does the language have a first-class optional?** If so, never build a Null
   Object.
2. **Does it check exhaustiveness over a closed set?** If so, do not replace a
   checked conditional with dynamic dispatch.
3. **What is the unit of encapsulation** — class, module, package, file? Extract
   Class means "split along that unit", whatever it is.
