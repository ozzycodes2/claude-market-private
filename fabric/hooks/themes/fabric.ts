import type { Skin } from '../skin'

// One chroma, no hue to tell kinds apart: every tool kind is ink, and the glyph says which.
// Tokens are the Fabric roles in architecture-design's style-guide.md; `zebra` is the one
// derived value, the guide's `accent-tint` laid on its paper. `err` is the one hue, since a
// failed call must read as one. `code` is the guide's `accent`, the one place the skin lets it
// set type; `commandBg` puts it behind the shell card's command, and `shimmer` sweeps over it.
const skin: Skin = {
  name: 'fabric',
  label: 'Fabric',
  palette: {
    read: '#f7f8f8',
    write: '#f7f8f8',
    run: '#f7f8f8',
    search: '#f7f8f8',
    web: '#f7f8f8',
    mcp: '#f7f8f8',
    other: '#f7f8f8',
    user: '#f7f8f8',
    fg: '#f7f8f8',
    muted: '#8a8f98',
    surface: '#0f1011',
    zebra: '#220f03',
    ok: '#f7f8f8',
    err: '#f87171',
    warn: '#d0d6e0',
    code: '#ef6306',
    codeBg: 'transparent',
    command: '#f7f8f8',
    commandBg: '#ef6306',
    shimmer: '#ef6306',
  },
  light: {
    read: '#171717',
    write: '#171717',
    run: '#171717',
    search: '#171717',
    web: '#171717',
    mcp: '#171717',
    other: '#171717',
    user: '#171717',
    fg: '#171717',
    muted: '#616161',
    surface: '#ffffff',
    zebra: '#f7e9e0',
    ok: '#171717',
    err: '#c42b2b',
    warn: '#4d4d4d',
    code: '#ef6306',
    codeBg: 'transparent',
    command: '#ffffff',
    commandBg: '#ef6306',
    shimmer: '#ef6306',
  },
  spinner: ['Thinking', 'Working', 'Considering'],
  done: ['Done', 'Finished'],
}

export default skin
