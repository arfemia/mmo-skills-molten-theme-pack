# MOLTEN UI theme

A premium **cracked-obsidian + glowing crimson-lava** reskin of Hytale's Common UI
frame/button/header art for the MMO Skill Tree mod. Every texture is a brand-new
**synthesized** molten surface (numpy + Pillow), NOT a luminance recolor of the
original art. Each output keeps the source texture's exact dimensions, its alpha
silhouette, and its 9-slice border metrics, so it drops in as a frame replacement.

Style summary: near-black glassy obsidian rock, a continuous glowing crimson lava
rim that frames content, dark/calm interior fields so overlaid body text stays
legible, and a single cohesive crimson lava gradient + corner-treatment language
across the whole family. **RED-dominant**: crimson/scarlet for the entire vein
body; orange only as the razor-thin hottest highlight, white-hot only at the seam
core; crimson bloom (R >> G,B).

## Regenerate

```bash
cd src/main/resources/Common/UI/Custom/Common/Molten
python molten_theme_gen.py        # writes all 15 textures here
python _make_contact_sheet.py     # writes _MoltenContactSheet.png
```

`molten_theme_gen.py` is a thin PARAMS block; ALL synthesis lives in the shared
engine `../_themegen/theme_synth.py` (the contact sheet in `../_themegen/contact_sheet.py`).
The Python tooling (both per-theme scripts and the shared `_themegen/` engine) is
dev-only and excluded from the shipped jar; only the `@2x.png` art ships.

Sources are read from the in-repo official Hytale Shared Source
(`hytale-shared-source/HytaleAssets/Common/UI/Custom/Common/`) plus the mod's own
`MmoToastFrame@2x.png`. Only the alpha channel of each source is used (for the
silhouette + 9-slice metrics); the RGB is fully synthesized.

## Source -> output map

| Source (upstream / mod)                | Output (here)                       | Size      | 9-slice border | Builder              |
|----------------------------------------|-------------------------------------|-----------|----------------|----------------------|
| `ContainerFullPatch@2x.png`            | `ContainerFullPatch@2x.png`         | 132x132   | 20             | `build_patch`        |
| `ContainerPatch@2x.png`                | `ContainerPatch@2x.png`             | 132x132   | 20             | `build_patch`        |
| `ContainerPanelPatch@2x.png`           | `ContainerPanelPatch@2x.png`        | 24x24     | 4              | `build_panel`        |
| `ContainerPanelLightPatch@2x.png`      | `ContainerPanelLightPatch@2x.png`   | 24x24     | 4              | `build_panel`        |
| `ContainerHeader@2x.png`               | `ContainerHeader@2x.png`            | 1428x76   | (full-width)   | `build_header`       |
| `ContainerHeaderNoRunes@2x.png`        | `ContainerHeaderNoRunes@2x.png`     | 1428x76   | (full-width)   | `build_header`       |
| `ContainerDecorationTop@2x.png`        | `ContainerDecorationTop@2x.png`     | 472x22    | (strip)        | `build_decoration`   |
| `ContainerDecorationBottom@2x.png`     | `ContainerDecorationBottom@2x.png`  | 472x22    | (strip)        | `build_decoration`   |
| `ContainerCloseButton@2x.png`          | `ContainerCloseButton@2x.png`       | 64x64     | (round)        | `build_close_button` |
| `ContainerCloseButtonHovered@2x.png`   | `ContainerCloseButtonHovered@2x.png`| 64x64     | (round)        | `build_close_button` |
| `ContainerCloseButtonPressed@2x.png`   | `ContainerCloseButtonPressed@2x.png`| 64x64     | (round)        | `build_close_button` |
| `Buttons/Secondary@2x.png`             | `Buttons/Secondary@2x.png`          | 440x88    | 12             | `build_patch`        |
| `Buttons/Secondary_Hovered@2x.png`     | `Buttons/Secondary_Hovered@2x.png`  | 440x88    | 12             | `build_patch`        |
| `Buttons/Secondary_Pressed@2x.png`     | `Buttons/Secondary_Pressed@2x.png`  | 440x88    | 12             | `build_patch`        |
| `MmoToastFrame@2x.png` (mod)           | `MmoToastFrame@2x.png`              | 128x128   | 20             | `build_patch`        |

`_MoltenContactSheet.png` is a montage of the whole set on neutral mid-grey
(`#7a7a7a`), including 9-slice STRETCH previews so the straight edges can be
eyeballed for seamlessness. `_make_contact_sheet.py` regenerates it.

## The lava gradient (RED-dominant)

The single `LAVA_STOPS` ramp (position 0 = cool shoulder, 1 = white-hot core).
Crimson `#b41d14` is the dominant band; orange/amber/white are squeezed into the
top few percent so they only appear at the hottest seam slivers.

```
0.00  #160605   near-black cooled crust shoulder
0.20  #5a0c07   deep maroon
0.46  #8e140e   dark crimson   (big red band)
0.66  #b41d14   crimson        (DOMINANT, low green)
0.80  #d62816   scarlet        (still clearly red)
0.90  #f23c16   red-orange     (narrow)
0.965 #ff6e1e   orange         (very narrow, hottest highlight)
0.99  #ffb446   amber          (razor-thin)
1.00  #fff2cf   white-hot      (thinnest seam core only)
```

Rock anchors: `ROCK_DARK #0d0908` -> `ROCK_MID #1d1310` (glassy obsidian, faint
warm tint). Bloom tint: `GLOW_TINT (1.0, 0.15, 0.08)` (crimson, keeps glow RED).

## The 9-slice approach (why the frames do not tear when stretched)

For any patch with border N, the N-pixel straight EDGE strips (top/bottom rows and
left/right columns BETWEEN the corners) must be a **constant cross-section** so
stretching repeats one identical line profile. The generator enforces this twice:

1. `apply_constant_edges` stamps a single `rim_profile` (dark crust -> continuous
   glowing lava line -> faint inner ember) into the heat field's edge strips.
2. After bloom (which can perturb edges column-to-column), `enforce_constant_edges_rgb`
   re-stamps each straight edge on the FINAL RGB with the midpoint cross-section.

Result: the RGB along every straight edge is byte-identical across its length
(verified variance 0). Irregular cracks and the hottest detail live ONLY in the
corner insets (which are never stretched) and the calm center fill. Corner-node
brightness is **levelled to the edge-run brightness** (`corner_cracks` +
`edge_level`) so the frame reads as ONE continuous molten rim, not four corner
lamps. (Note: `ContainerPatch` has an intrinsic semi-transparent left edge in its
SOURCE ALPHA, which is preserved deliberately - only its RGB is held constant.)

Interior legibility: `corner_cracks(center_damp=...)` darkens the obsidian and
damps vein density toward the middle third, so the bright veins stay concentrated
near the rim where they frame content and overlaid text/icons stay readable.

## Per-asset treatment

- **Frames** (`build_patch`): obsidian field, levelled continuous crimson rim,
  calm dark center, corner-only irregular cracks.
- **Panels** (`build_panel`): subtle DARK OBSIDIAN tint (the LightPatch a touch
  brighter) with a faint crimson rim seam. These are multiply-tinted at runtime via
  `.Background.Color`, so they are kept low-contrast and dark - they read on-theme
  when tinted instead of washing out to grey.
- **Header bars** (`build_header`): the brightest, most LIQUID lava bar in the set -
  a dark obsidian metal bar with a bright crimson->scarlet lava UNDERLINE + bloom,
  a faint top ember rim, and (runes variant) subtle ember rune nodes. Built as a
  single column profile tiled along X, so it is constant cross-section / full-width
  safe.
- **Decoration strips** (`build_decoration`): a thin glowing crimson seam following
  the source alpha centroid, with small ember nodes; same crimson temperature as
  the frame.
- **Close button** (`build_close_button`): a round molten seal - forged dark rim,
  glowing crimson lava ring, faint ember core behind a legible hot X, plus a
  machined CONCENTRIC BEVEL (grooves + raised inner land) for forged depth.
  Hovered = brighter ring + stronger crimson bloom; Pressed = dimmer + sunken
  upper-left inset shading. All three states clearly distinct, all RED-dominant.
- **Buttons** (`build_patch`, border 12): forged obsidian bar with a continuous
  red-hot crimson edge; Hovered hotter, Pressed dimmer. Kept neutral-friendly so
  the mod's per-state `PatchStyle.Color` tint still works.

## Reskin to another theme (one PARAMS block)

A new theme is a thin script next to a `Molten*/` dir that defines a PARAMS dict
and calls `theme_synth.run(PARAMS)`; the shared `_themegen/` engine is never forked.
Copy `molten_theme_gen.py` (or `Molten_02/molten02_theme_gen.py`) and edit PARAMS:

> **Set `lava_stops` (the seam gradient), `rock_dark`/`rock_mid` (the rock),
> `glow_tint` (the bloom color), `patch_style` (`'veins'` thin-rim or `'band'`
> wide-lava), and the two patch tunables (`patch_glow_radius`/`patch_core_boost`);
> then run the thin script.**

Examples: an icy theme = blue/white gradient + slate rock + cyan glow; a toxic
theme = green gradient + dark-bog rock + green glow. The crack/rim/bevel geometry,
9-slice enforcement, and per-asset builders all stay as-is in the shared engine.
`Molten` uses `patch_style: 'veins'`; `Molten_02` uses `patch_style: 'band'`.
