import type { Skin } from '../skin'

// One chroma, no hue to tell kinds apart: every tool kind is ink, and the glyph says which.
// Tokens are the Fabric roles in architecture-design's style-guide.md; `zebra` is the one
// derived value, a step off `surface`. `err` is the one hue, since a failed call must read as one.
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
    zebra: '#16171a',
    ok: '#f7f8f8',
    err: '#f87171',
    warn: '#d0d6e0',
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
    zebra: '#f2f2f2',
    ok: '#171717',
    err: '#c42b2b',
    warn: '#4d4d4d',
  },
  spinner: ['Thinking', 'Working', 'Considering'],
  done: ['Done', 'Finished'],
}

export default skin
