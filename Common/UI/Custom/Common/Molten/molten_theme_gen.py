#!/usr/bin/env python3
"""
MOLTEN premium UI theme  --  thin params + run.

Style: CRACKED OBSIDIAN + GLOWING CRIMSON LAVA VEINS (v1 "obsidian-veins"). All
synthesis lives in the shared engine (../_themegen/theme_synth.py); this file is
only the theme-specific PARAMS block + the call. To reskin, copy this file and
edit PARAMS (lava gradient + rock anchors + glow tint + patch interior style);
never fork the engine.

RED DOMINANCE: the lava ramp is crimson/scarlet for the entire vein body; orange
appears only as the razor-thin hottest highlight sliver and white-hot only at the
seam core. Bloom is a crimson tint (R >> G,B). Nothing reads orange-forward.

Requires: numpy, Pillow.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_themegen"))
import theme_synth

PARAMS = {
    "out_dir": os.path.dirname(os.path.abspath(__file__)),
    "seed": 1771,

    # Lava gradient (RED-DOMINANT). Position 0 = cool shoulder, 1 = white-hot core.
    # Crimson #b41d14 is the dominant band; orange/amber/white squeezed into the top.
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

    # Rock base colors (near-black glassy obsidian, subtle warm tint).
    "rock_dark": [0x0d, 0x09, 0x08],
    "rock_mid": [0x1d, 0x13, 0x10],
    # Crimson bloom tint (R >> G,B keeps the glow firmly RED, not orange).
    "glow_tint": [1.0, 0.15, 0.08],

    # Patch interior: thin rim + faint DEEP-interior veins.
    "patch_style": "veins",
    "patch_glow_radius": 4.5,
    "patch_core_boost": 1.0,
}


if __name__ == "__main__":
    theme_synth.run(PARAMS)
