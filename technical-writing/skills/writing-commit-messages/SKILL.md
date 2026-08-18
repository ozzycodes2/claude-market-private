---
name: writing-commit-messages
description: Use when writing a commit message or PR description for work that will land on main/trunk (typically via squash-and-merge). Triggers on phrases like "write the commit message", "draft the PR", "what should this commit say", or before any commit that becomes part of the durable git log. Skip for WIP/fixup commits on a feature branch — those don't need ceremony.
---

# Writing Commit Messages

Helps draft a commit message worth living in `main` for years. The reader you're writing for is some future maintainer — often you, three years from now, with no memory of what you were thinking — staring at a single `git blame` line and trying to figure out why the code is the way it is.

**Core principle:** trunk commits are the durable record. Branch commits can be anything ("Friday is Hawaiian shirt day"). The commit trail in `main` is what survives the migration from GitHub to GitLab and back; that's what you're writing for.

Source: CJ's own "Writing great commit messages" document.

## When to use

- Writing a PR description for work intended to merge into `main` (or `master` or `latest`).
- Writing a message for a significant commit.
- Writing a message for any direct commit to trunk.
- User asks "what should this commit message be?" or "write the PR description for X."

**Skip if:** committing to a feature branch where the work will be squashed later — that's Hawaiian-shirt-day territory and anything goes. Also skip for trivial fixup commits the author plans to autosquash.

## Structure: the inverted pyramid

A great commit message is a newspaper article, not a diff summary. The pyramid:

1. _Headline_ Try for 50 chars. Conventional Commits prefix (`feat:`, `fix:`, `docs:`,
   `chore:`) is welcome — works great for humans and for tooling.
2. _Dek_ The subhed that tells what broke or what the change was, meaningfully.
3. _Lede paragraph._ What changed in the system's behavior, and _why_. Someone who reads
   only this paragraph should get the gist. Keep it short.
4. Consider if this is enough.
5. _Technical choices / background._ Optional. Use it if the implementation was non-obvious,
   if there was a viable alternative worth naming, or if the problem itself was hard.
   Keep it short.
6. _Details about how._ Optional. Bullet list of picky stuff: subtle invariants, edge cases
   handled, things deliberately not done. Include only if unusual or interesting in some way.
   Keep it short.
7. _Drive-by changes._ Additional small changes made along the way that did not relate
   to the main topic, but were easy to do, such as bug fixes in adjacent code.
8. _Bug / issue references._ At the end, to assist automation. Don't put these in the
   headline — they eat your 50 characters.

### Length

- Headline: ~50 chars so it fits in `git log --oneline` and GitHub file views.
- Body: hard-wrap at 80 chars. Unwrapped lines are miserable in a terminal pager. Linus Torvalds,
  noted relaxation coach, says 74; CJ says 80; pick something in 72–80 and stick with it.
- Body length: as long as the change deserves. A boring config tweak is one paragraph.
  A subtle concurrency fix can be ten. Think about the importance of the change and how
  difficult it will be to understand in the future: devote more words to critical changes,
  and fewer words to small changes.
- BE CONCISE no matter what. Use simple declarative sentences. Do not use emoji or **bold**.
- You may use `backticks` to indicate symbols, names in code, or shell commands.

Use clear, concise English prose. Don't repeat facts. Focus on information future readers will
need so they can understand why the work was done the way it was, and what your intentions were.

Avoid _leaked frames._ Leaked frames are references that only parse from inside the session that produced them. From inside they read as clear, which is why the writer cannot see them. Assume that the reader of a commit message has only the context of the repo itself.

### Tense

Imperative for the headline (matches Conventional Commits and Linux kernel convention);
past tense for the "how it was done" details reads naturally.

## Example: an inverted-pyramid commit

```
docs(commits): meta-description of an inverted-pyramid commit

The first paragraph is the lede. It must describe what change this
commit makes. How does the software behave after the commit that is
different from how it behaved before? Why did you make this change?
Somebody who reads ONLY this first paragraph should get the gist.

The second paragraph can get into the technical choices made to
accomplish the work, if they're at all interesting or if there was an
alternative to the method chosen. It might also go into the background
of the problem solved by the commit, if it was difficult or complex.

You can go longer if the change deserves more words.

Additional notes:

- This is where you can get into picky things.
- Mention things you did not related to the main work.
- Bullet items are optional but often helpful.
- You are writing a message to future maintainers of this software.
- Future-you might be one of those maintainers, with no memory of
  doing the work. The message is your gift to them.

Fixes #42, #44, #47.
```

## Anti-patterns when drafting

| Don't | Why |
| ----- | --- |
| Accept GitHub's default squash message | It's the concatenation of your WIP commits. Almost always noise.                                                       |
| Skip the body for "small" changes      | The change might be small; the _why_ often isn't. One body sentence body is still useful.                                  |
| Cram bug numbers into the headline     | Put them at the end of the message.               |
| Skip the _why_                         | The diff already says what changed. The why is the only thing the message uniquely contributes. |
| Mix tenses within one message          | Use the past tense. |
| Hand-wave "see PR"                     | Two years from now the PR may be archived, link-rotted, or behind an org boundary. The commit is the durable artifact. |
| Write ten paragraphs.                  | Long explanatations belong in documentation |

## When asked to draft

Procedure when the user asks for a commit/PR message draft:

1. **Look at the diff first.** `git diff <range>` or `git log <range>` — don't draft from memory or conversation context alone. The diff is ground truth.
2. **Propose the headline candidate** in chat before drafting the body. The headline is the single hardest line; getting it right early shapes the rest.
3. **Draft the body in inverted-pyramid order.** Lede first. Only add technical-choices and how-details paragraphs if the change actually warrants them — boring routine commits are headline + one paragraph.
4. **Hard-wrap the body at 80 chars.** Always, per the Length rules above.
5. **Confirm with the user** before pasting into a PR or running `git commit`. The user's voice and judgment about what's worth memorializing should win.

## What a great commit message is NOT — real-world specimens

CJ's collection from the wild. The fourth specimen is the most common — it's what GitHub gives you by default if you don't override the squash message.

```
fixed bug


made this better probably


fixed some lifestyle stuff


[four-letter word]


* a github workflow to kick off extra tests
* YAML fix.
* [expletive] YAML
* I [expletive] hate debugging workflows
* It has been 0 days since the last Bash quoting incident.
* Friday is Hawaiian shirt day.
* Will it work now?


[ the entire text of On Walden Pond by Henry David Thoreau ]
```

None of these belong in `main` forever.
