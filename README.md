# MMO Skill Tree - Molten / Obsidian Veins (premium menu theme)

A premium menu theme pack for the [MMO Skill Tree](https://mmo-skill-tree-docs.ziggfreed.com/)
Hytale mod. Reskins the in-game menu with a fiery obsidian palette and bespoke
9-slice frame art. This is the first premium theme `.zip` product; it ships ONLY
art + theme data and needs no jar change.

## Gating (fail-closed)

Applying any non-default theme requires an active **Pro** entitlement
(`WHITE_LABEL`, the Pro Edition plan marker) on the server. Without it the pack loads harmlessly and the
menu paints the free default (Verdant): a leaked `.zip` is a no-op without Pro.
The gate lives entirely in the mod (`UIThemeConfig.getEffectivePalette()`), never
in the pack.

## What it ships

- `Server/MMOSkillTree/UIThemes/Molten.json` - the theme: a full palette
  (frame / ornaments / per-state buttons) plus a `textureDir` pointing at the
  bespoke 9-slice art below. It overrides the mod's baked-in Molten **recolor**
  teaser (precedence `defaults < pack < owner`), upgrading it from a pure colour
  recolor to the textured art tier.
- `Server/MMOSkillTree/Control/MMOSkillMoltenTheme.json` - declares `UIThemes: add`
  (merge this theme into the mod's themes, do not replace).
- `Common/UI/Custom/Common/Molten/*.png` - the bespoke 9-slice frame / panel /
  button / ornament textures (generated; see the in-pack generator + README).

The theme name resolves through the mod's existing localization key
`ui.menu_theme.name.molten` (shipped in the jar for all locales), so the pack
ships no `.lang`.

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
