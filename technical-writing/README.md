# technical-writing

Human-facing developer writing, done well — the prose that surrounds code.
Provides the `writing-design-docs` skill and the `laconic` output style.

## Skills

| Skill | What it does |
|-------|--------------|
| `writing-design-docs` | Produces a problem-statement design doc before you commit to a non-obvious technical direction. Ships with a `template.md`. |

## Output styles

| Style | What it does |
|-------|--------------|
| `technical-writing:laconic` | Terse, salient prose for anything read by someone who was not in the room — comments, PR bodies, review replies, commit messages. Names the "leaked frame" failure mode and what to write instead. |

Select it with `/output-style technical-writing:laconic`, or make it the default
by setting `"outputStyle": "technical-writing:laconic"` in `settings.json`.

## Usage

```
> let's write a design doc for X before we build it
```

The skill can also be invoked explicitly: `/technical-writing:writing-design-docs`.

## Attribution

`writing-design-docs` is adapted from [ceejbot/ceej-skills](https://github.com/ceejbot/ceej-skills)
by [ceej](https://blog.ceejbot.com), used under the MIT license.

The `laconic` output style is copied verbatim from
[chrisdickinson/pertinent](https://github.com/chrisdickinson/pertinent) (`styles/laconic/style.md`)
by Chris Dickinson, used under the MIT license.

Thanks to both authors.

## License

MIT — see the marketplace [LICENSE](../LICENSE).
