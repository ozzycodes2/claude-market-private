"""The Fabric skin's palette must stay on the tokens in the diagram style guide.

Both files carry the same hex values; this fails the build when one moves alone.
"""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "architecture-design/skills/create-diagram/references/style-guide.md"
THEME = ROOT / "fabric/hooks/themes/fabric.ts"

ROW = re.compile(r"^\| `([a-z0-9-]+)` \|.*\| `(#[0-9a-f]{6})` \| `(#[0-9a-f]{6})` \|$")
INK_SLOTS = ("read", "write", "run", "search", "web", "mcp", "other", "user", "fg", "ok")
# Slot -> guide role. Every slot not listed is ink; `zebra` and `err` have no guide role.
ROLE = {"muted": "soft", "surface": "paper-2", "warn": "muted", **{s: "ink" for s in INK_SLOTS}}


def guide_tokens():
    tokens = {}
    for line in GUIDE.read_text().splitlines():
        match = ROW.match(line)
        if match:
            tokens[match[1]] = {"light": match[2], "dark": match[3]}
    return tokens


def theme_palettes():
    source = THEME.read_text()
    palettes = {}
    for polarity, key in (("dark", "palette"), ("light", "light")):
        block = re.search(rf"^  {key}: \{{(.*?)^  \}},", source, re.S | re.M)
        palettes[polarity] = dict(re.findall(r"(\w+): '(#[0-9a-f]{6})'", block[1]))
    return palettes


class FabricTokens(unittest.TestCase):
    def test_guide_lists_the_roles_the_theme_maps(self):
        self.assertTrue({"ink", "soft", "paper-2", "muted"} <= guide_tokens().keys())

    def test_each_mapped_slot_matches_its_guide_role_in_both_polarities(self):
        tokens, palettes = guide_tokens(), theme_palettes()
        for polarity in ("dark", "light"):
            for slot, role in ROLE.items():
                with self.subTest(polarity=polarity, slot=slot):
                    self.assertEqual(palettes[polarity][slot], tokens[role][polarity])

    def test_both_polarities_fill_the_same_slots(self):
        palettes = theme_palettes()
        self.assertEqual(palettes["dark"].keys(), palettes["light"].keys())
        self.assertEqual(len(palettes["dark"]), 15)


if __name__ == "__main__":
    unittest.main()
