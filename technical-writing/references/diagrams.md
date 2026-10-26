# Diagram Rule

Shared by write-doc, review-doc, fix-doc, and writing-design-docs.
Cite this file for every diagram decision.

## When to add a diagram

Add one proactively, without being asked, when the doc describes:

- architecture or system structure
- a flow or sequence of steps between actors
- states and transitions
- relationships among more than three components that prose carries poorly

Skip it when a short paragraph or list says the same thing as clearly.

## Tool

- If `architecture-design:create-diagram` is available, invoke it with format `html+png`.
  It writes the `.html` source and the `.png` export.
  To export an existing diagram-design `.html`, invoke `architecture-design:export-diagram`; it writes `.svg` and `.png` next to the source.
- Otherwise write a fenced `mermaid` block in the doc.
  Do not hand-draw ASCII art.

## Placement in a GitHub or markdown doc

- Follow the repo's existing image convention.
  Find it by looking for committed `.png` or `.svg` files near the docs.
- With no convention, use `<doc-dir>/images/<doc-stem>-<slug>.png` and keep the `.html` source beside it.
- Link with a relative path: `![alt](images/<doc-stem>-<slug>.png)`.
- Alt text states what the diagram shows ("Request flows from the API gateway to the queue, then to two workers"), not "diagram" or "architecture".
- Mermaid fallback: the fenced block stays inline; GitHub renders it.

## Placement in Notion

Only when the user explicitly asked for Notion output.

- Upload the PNG with `notion-create-file-upload` (Notion MCP) and embed it in the page.
- With the Mermaid fallback, use a `mermaid` code block; Notion renders it natively.

## Never

- Never let a diagram carry information the prose omits.
  The prose stays complete without it, for screen readers, diffs, and search.
- Never add a diagram that only restates a two-item list.
- Never create export files (`.png`, `.svg`) the user did not ask for when only reviewing a doc; propose the diagram in the review instead.
