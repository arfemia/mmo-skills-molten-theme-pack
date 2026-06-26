# MMO Skill Tree - Molten (premium menu themes)

A premium menu theme pack for the [MMO Skill Tree](https://mmo-skill-tree-docs.ziggfreed.com/)
Hytale mod. Reskins the in-game menu with a fiery obsidian palette and bespoke
9-slice frame art. Ships **two** menu themes from one cohesive crimson-lava family:
**Molten** (obsidian veins - a thin glowing rim + faint deep veins) and **Molten Flow**
(a wide flowing lava band hugging the frame). This is the first premium theme `.zip`
product; it ships ONLY art + theme data and needs no jar change.

## Gating (fail-closed)

Applying any non-default theme requires an active **Pro** entitlement
(`WHITE_LABEL`, the Pro Edition plan marker) on the server. Without it the pack loads harmlessly and the
menu paints the free default (Verdant): a leaked `.zip` is a no-op without Pro.
The gate lives entirely in the mod (`UIThemeConfig.getEffectivePalette()`), never
in the pack.

## What it ships

- `Server/MMOSkillTree/UIThemes/Molten.json` + `Molten_02.json` - the two themes:
  each a full palette (frame / ornaments / per-state buttons) plus a `textureDir`
  pointing at its bespoke 9-slice art below. Each overrides the mod's baked-in
  same-id **recolor** teaser (precedence `defaults < pack < owner`), upgrading it
  from a pure colour recolor to the textured art tier.
- `Server/MMOSkillTree/Control/MMOSkillMoltenTheme.json` - declares `UIThemes: add`
  (merge these themes into the mod's themes, do not replace). It merges the whole
  `UIThemes/` folder, so both `Molten.json` and `Molten_02.json` are picked up.
- `Common/UI/Custom/Common/Molten/*.png` + `Molten_02/*.png` - the bespoke 9-slice
  frame / panel / button / ornament textures for each theme (generated; see each
  theme's in-pack generator + README).

The theme names resolve through the mod's existing localization keys
`ui.menu_theme.name.molten` / `ui.menu_theme.name.molten_02` (shipped in the jar
for all locales), so the pack ships no `.lang`.

## Tiers (what actually paints, and what is in-game-verify)

- **RECOLOR (verified):** the palette drives the confirmed `PatchStyle.Color`
  retint of the shared frame body, inner panel, ornaments, and the per-state
  shared button styles. This is the verified launch tier and works today.
- **TEXTURE art (in-game-verify):** the `textureDir` drives a Java-sent
  `PatchStyle.TexturePath` swap of the frame / panel art. The runtime
  texture-PATH resolution form is the one unconfirmed nuance (the Colour retint is
  proven); verify on a live client. If a client renders a missing-texture red X,
  the validated fallback is the whole-`.ui` swap via the mod's
  `templateOverrides` / `getEffectiveTemplateForPage` path. The named-style button
  retint form is likewise best-guess / in-game-verify (worst case a harmless
  no-op).

## Build + install

```powershell
.\build.ps1                  # build the zip, install to $env:HYTALE_MODS_DIR
.\build.ps1 -Install:$false  # build only
```

Or from the monorepo root: `.\rebuild.ps1 -Packs molten`.

## Requirements

- MMO Skill Tree `^1.4.0` (hard dependency; the pack is dormant without it).
- Hytale server `>=0.5.0-pre.0 <0.6.0`.
