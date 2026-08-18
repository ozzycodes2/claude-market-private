# technical-writing

Human-facing developer writing, done well — the prose that surrounds code: commit
messages, code comments, and design docs. (For writing *for agents* — CLAUDE.md,
AGENTS.md, skills — see the `agent-authoring` plugin instead.)

## Skills

| Skill | What it does |
|-------|--------------|
| `writing-commit-messages` | Crafts commit messages and PR descriptions for work landing on main/trunk (squash-and-merge). Skips the ceremony for WIP/fixup commits on a feature branch. |
| `writing-code-comments` | Writes and revises code comments and API docs — doc comments, module docs, inline notes — that explain WHY, appear sparingly, and never overshadow the code. |
| `writing-design-docs` | Produces a problem-statement design doc before you commit to a non-obvious technical direction. Ships with a `template.md`. |

## Usage

```
> write the commit message for this change
> add doc comments to this module
> let's write a design doc for X before we build it
```

Each skill can also be invoked explicitly, e.g. `/technical-writing:writing-commit-messages`.

## Attribution

These skills are adapted from [ceejbot/ceej-skills](https://github.com/ceejbot/ceej-skills)
by [ceej](https://blog.ceejbot.com), used under the MIT license. Thanks to the original
author.

## License

MIT — see the marketplace [LICENSE](../LICENSE).
