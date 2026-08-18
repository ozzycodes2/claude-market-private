---
name: writing-code-comments
description: Use when writing or revising code comments or API documentation — doc comments, Rust doc strings, module docs, inline comments. Triggers on phrases like "add comments", "document this function", "write doc comments", "clean up these comments", or whenever generating code that includes comments. Comments explain WHY, appear sparingly, and never overshadow the code.
---

# Writing Code Comments

Helps write comments that earn their place. A comment is a claim that the code
cannot speak for itself — so before writing one, check whether that claim is
true. Often the better fix is clearer code: a well-named function needs no
introduction.

For prose style within comments, apply the rules in the
`ceej-skills:writing-clearly` skill: active voice, definite concrete language,
omit needless words, present tense for software behavior ("crashes", not
"will crash"). Disciplined economy matters *more* in comments than in
documents, because comments share the screen with code.

## The four rules

1. **Document what cannot be seen in the code.** The code already says what it
   does. A comment restating it is a maintenance liability: it rots the moment
   the code changes, and then it lies.
2. **Explain WHY, not what.** The valuable comment records intent, constraint,
   or history invisible in the text: why this algorithm and not the obvious
   one, what external system forces this shape, which bug this guards against.
3. **Use comments sparingly.** They exist to make the code understandable and
   must never overshadow it. A reader scans code; every comment interrupts
   that scan. If a function needs a comment every three lines, the function is
   the problem.
4. **Doc strings follow the same law.** The signature is already there to be
   read. Tell the reader something the signature cannot.

## Doc comments (Rust doc strings, and kin)

A function signature documents the name, the parameters, their types, and the
return type. Do not repeat any of that. Instead answer the questions a caller
actually has:

- When would someone call this? What problem does it solve?
- Does it have side effects? Does it block, allocate, retry, log?
- How does it fit with the rest of the API? What's the usual call sequence?
- What are the failure modes? When does it return `Err`, and what should the
  caller do about it?
- Usage examples are valuable — in Rust they're also tests. Include one when
  the call pattern isn't obvious from the signature.

Javadoc-style parameter descriptions are NOT valuable. `@param name — the
name` insults everyone involved.

```rust
// BAD: restates the signature, line by line.
/// Gets the user by id.
///
/// # Arguments
/// * `id` - the id of the user
///
/// # Returns
/// The user, or an error.
pub fn user_by_id(&self, id: UserId) -> Result<User, StoreError>

// GOOD: says what the signature cannot.
/// Fetches from the cache first, then the database; a hit refreshes the
/// cache TTL. Returns `StoreError::NotFound` for unknown ids — callers
/// treating absence as normal should match on it rather than bubbling.
pub fn user_by_id(&self, id: UserId) -> Result<User, StoreError>
```

## Inline comments

The good ones record a decision or a trap:

```rust
// BAD: narrates the next line.
// Increment the retry counter.
retries += 1;

// GOOD: explains a constraint the code can't show.
// The vendor API rejects bursts; 250ms spacing is the documented floor.
sleep(Duration::from_millis(250)).await;

// GOOD: wards off a tempting "fix".
// Deliberately not sorted: the upstream feed is ordered by priority
// and we must preserve it. See INV-2213.
```

## Anti-patterns

| Don't | Why |
| ----- | --- |
| Narrate the next line | The reader can read. The comment is pure noise. |
| Restate the signature in a doc string | Rots on the next refactor, then lies. |
| `@param`/`# Arguments` boilerplate | Types and names already say it. |
| Comment your own change ("fixed the bug here") | That's a commit message. Git remembers; the code shouldn't. |
| Talk to the reviewer ("this handles the edge case now") | Noise the moment the PR merges. Write for the next reader, not the current one. |
| Leave commented-out code | Delete it. Git remembers that too. |
| Comment every few lines | The comments have overwhelmed the code. Refactor instead. |

## When asked to revise existing comments

1. **Read the code first.** You can't judge whether a comment adds anything
   until you know what the code already says.
2. **Delete before you edit.** Most bad comments should vanish, not improve.
   A restated signature becomes an empty line, not better restatement.
3. **Check comments against the code.** A comment that contradicts the code is
   the worst kind — flag it, then determine which one is right before touching
   either.
4. **Preserve the load-bearing ones.** Comments citing tickets, incidents,
   spec sections, or vendor quirks are often the most valuable text in the
   file. Keep them even when they're ugly.
5. **Match the codebase's comment density and idiom.** A sparse codebase stays
   sparse.
