# technical-writing

Human-facing developer writing, done well — the prose that surrounds code.
Currently provides `writing-design-docs`. (For writing *for agents* — CLAUDE.md,
AGENTS.md, skills — see the `agent-authoring` plugin instead.)

## Skills

| Skill | What it does |
|-------|--------------|
| `writing-design-docs` | Produces a problem-statement design doc before you commit to a non-obvious technical direction. Ships with a `template.md`. |

## Usage

```
> let's write a design doc for X before we build it
```

The skill can also be invoked explicitly: `/technical-writing:writing-design-docs`.

## Attribution

These skills are adapted from [ceejbot/ceej-skills](https://github.com/ceejbot/ceej-skills)
by [ceej](https://blog.ceejbot.com), used under the MIT license. Thanks to the original
author.

## License

MIT — see the marketplace [LICENSE](../LICENSE).
