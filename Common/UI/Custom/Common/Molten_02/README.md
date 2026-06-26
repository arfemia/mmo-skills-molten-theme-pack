# MOLTEN FLOW UI theme (molten_02)

The SECOND molten drop: a premium **cracked-obsidian + wide flowing crimson-lava
band** reskin of Hytale's Common UI frame/button/header art for the MMO Skill Tree
mod. The sibling of [Molten](../Molten/README.md) ("obsidian veins"): SAME crimson
lava family, seed, rock + glow tint, so the two read as one set. The ONLY
difference is the patch interior - a WIDE molten band hugging the frame border
("more lava / flowing") instead of Molten's thin rim + faint deep veins.

Every texture is a brand-new **synthesized** molten surface (numpy + Pillow), NOT a
luminance recolor of the original art. Each output keeps the source texture's exact
dimensions, its alpha silhouette, and its 9-slice border metrics, so it drops in as
a frame replacement.

## Regenerate

```bash
cd content-packs/molten-theme-pack/Common/UI/Custom/Common/Molten_02
python molten02_theme_gen.py      # writes all 15 textures here
python _make_contact_sheet.py     # writes _MoltenContactSheet.png
```

`molten02_theme_gen.py` is a thin PARAMS block; ALL synthesis lives in the shared
engine `../_themegen/theme_synth.py`. The molten_02 PARAMS are identical to Molten's
except `patch_style="band"` and the two band tunables (`patch_glow_radius=4.2`,
`patch_core_boost=1.05`); the lava gradient, rock anchors, glow tint, and seed
(1771) are shared with Molten so the two themes stay one family. The Python tooling
(both per-theme scripts and the shared `_themegen/` engine) is dev-only and excluded
from the shipped jar/zip; only the `@2x.png` art ships.

Sources are read from the in-repo official Hytale Shared Source
(`hytale-shared-source/HytaleAssets/Common/UI/Custom/Common/`) plus the mod's own
`MmoToastFrame@2x.png`. Only the alpha channel of each source is used (for the
silhouette + 9-slice metrics); the RGB is fully synthesized. The source -> output
map is identical to [Molten](../Molten/README.md#source---output-map).

## Reskin to another theme

Write a new thin params script (a new lava gradient + rock anchors + glow tint +
seed + `patch_style` + the two patch tunables) and call `theme_synth.run(PARAMS)`;
do NOT fork the engine. See the engine docstring for the full PARAMS contract.
