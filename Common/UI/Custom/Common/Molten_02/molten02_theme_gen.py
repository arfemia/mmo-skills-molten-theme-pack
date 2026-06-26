#!/usr/bin/env python3
"""
MOLTEN FLOW premium UI theme  --  thin params + run (the SECOND molten drop).

Style: CRACKED OBSIDIAN + a WIDE FLOWING CRIMSON LAVA BAND (v2 "molten-flow"). The
sibling of Molten ("obsidian-veins", molten_01): SAME crimson lava family, seed,
rock + glow tint, so the two read as one set; the ONLY difference is the patch
interior - a wide molten band hugging the frame border ("more lava / flowing")
instead of molten_01's thin rim + faint deep veins. All synthesis lives in the
shared engine (../_themegen/theme_synth.py); this file is only the theme-specific
PARAMS block + the call. To reskin, copy this file and edit PARAMS; never fork the
engine.

RED DOMINANCE (inherited from molten_01): the lava ramp is crimson/scarlet for the
entire band body; orange appears only as the razor-thin hottest highlight sliver
and white-hot only at the seam core. Bloom is a crimson tint (R >> G,B). Nothing
reads orange-forward.

Requires: numpy, Pillow.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_themegen"))
import theme_synth

PARAMS = {
    "out_dir": os.path.dirname(os.path.abspath(__file__)),
    # Shared with molten_01 so the two themes are ONE family (per the engine docs).
    "seed": 1771,

    # Lava gradient (RED-DOMINANT) - identical ramp to molten_01. Position 0 = cool
    # shoulder, 1 = white-hot core. Crimson #b41d14 is the dominant band; orange/
    # amber/white squeezed into the top.
    "lava_stops": [
        (0.00, (0x16, 0x06, 0x05)),  # near-black cooled crust shoulder
        (0.20, (0x5a, 0x0c, 0x07)),  # deep maroon
        (0.46, (0x8e, 0x14, 0x0e)),  # dark crimson  (big red band)
        (0.66, (0xb4, 0x1d, 0x14)),  # crimson  (DOMINANT, low green)
        (0.80, (0xd6, 0x28, 0x16)),  # scarlet (still clearly red)
        (0.90, (0xf2, 0x3c, 0x16)),  # red-orange (narrow)
        (0.965, (0xff, 0x6e, 0x1e)),  # orange (very narrow, hottest highlight)
        (0.99, (0xff, 0xb4, 0x46)),  # amber (razor-thin)
        (1.00, (0xff, 0xf2, 0xcf)),  # white-hot (thinnest seam core only)
    ],

    # Rock base colors + crimson bloom tint - identical to molten_01.
    "rock_dark": [0x0d, 0x09, 0x08],
    "rock_mid": [0x1d, 0x13, 0x10],
    "glow_tint": [1.0, 0.15, 0.08],

    # Patch interior: the WIDE LAVA BAND (the molten_02 differentiator). The two
    # band tunables are the engine's documented molten_02 values.
    "patch_style": "band",
    "patch_glow_radius": 4.2,
    "patch_core_boost": 1.05,
}


if __name__ == "__main__":
    theme_synth.run(PARAMS)
