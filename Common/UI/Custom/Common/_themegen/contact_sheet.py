#!/usr/bin/env python3
"""Shared contact-sheet builder for the molten-family UI themes.

Builds _MoltenContactSheet.png for a theme: every output on neutral mid-grey,
plus 9-slice STRETCH previews of FullPatch / Secondary / Toast so the straight
edges can be eyeballed for seamlessness. Dev-only (excluded from the shipped
jar). Each theme's thin _make_contact_sheet.py calls build(out_dir).
"""
import os
from PIL import Image, ImageDraw, ImageFont

BG = (0x7a, 0x7a, 0x7a)
DEFAULT_TITLE = "MOLTEN - Cracked Obsidian + Crimson Lava Veins (final)  bg #7a7a7a"

FILES = [
    "ContainerFullPatch@2x.png", "ContainerPatch@2x.png",
    "ContainerPanelPatch@2x.png", "ContainerPanelLightPatch@2x.png",
    "ContainerHeader@2x.png", "ContainerHeaderNoRunes@2x.png",
    "ContainerDecorationTop@2x.png", "ContainerDecorationBottom@2x.png",
    "ContainerCloseButton@2x.png", "ContainerCloseButtonHovered@2x.png",
    "ContainerCloseButtonPressed@2x.png", "Buttons/Secondary@2x.png",
    "Buttons/Secondary_Hovered@2x.png", "Buttons/Secondary_Pressed@2x.png",
    "MmoToastFrame@2x.png",
]


def nine_slice_stretch(img, border, target_w, target_h):
    w, h = img.size
    b = border
    out = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    def crop(l, t, r, bo): return img.crop((l, t, r, bo))
    tl = crop(0, 0, b, b); tr = crop(w - b, 0, w, b)
    bl = crop(0, h - b, b, h); br = crop(w - b, h - b, w, h)
    top = crop(b, 0, w - b, b).resize((target_w - 2 * b, b))
    bot = crop(b, h - b, w - b, h).resize((target_w - 2 * b, b))
    lft = crop(0, b, b, h - b).resize((b, target_h - 2 * b))
    rgt = crop(w - b, b, w, h - b).resize((b, target_h - 2 * b))
    cen = crop(b, b, w - b, h - b).resize((target_w - 2 * b, target_h - 2 * b))
    out.paste(cen, (b, b))
    out.paste(top, (b, 0)); out.paste(bot, (b, target_h - b))
    out.paste(lft, (0, b)); out.paste(rgt, (target_w - b, b))
    out.paste(tl, (0, 0)); out.paste(tr, (target_w - b, 0))
    out.paste(bl, (0, target_h - b)); out.paste(br, (target_w - b, target_h - b))
    return out


def get_font(sz):
    for name in ["arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            continue
    return ImageFont.load_default()


def build(out_dir, title=DEFAULT_TITLE):
    cell_w = 320
    label_h = 26
    pad = 14
    max_h = 240
    font = get_font(15)
    fbig = get_font(17)

    def make_tile(img, caption):
        iw, ih = img.size
        scale = min(cell_w / iw, max_h / ih, 3.0)
        nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
        disp = img.resize((nw, nh), Image.NEAREST if scale > 1 else Image.LANCZOS)
        tile = Image.new("RGBA", (cell_w, max_h + label_h), BG + (255,))
        ox = (cell_w - nw) // 2
        oy = label_h + (max_h - nh) // 2
        tile.alpha_composite(disp.convert("RGBA"), (ox, oy))
        d = ImageDraw.Draw(tile)
        d.text((6, 5), caption, font=font, fill=(255, 255, 255, 255))
        d.rectangle([0, 0, cell_w - 1, max_h + label_h - 1], outline=(40, 40, 40, 255))
        return tile

    tiles = []
    for fn in FILES:
        img = Image.open(os.path.join(out_dir, fn)).convert("RGBA")
        tiles.append(make_tile(img, fn))

    full = Image.open(os.path.join(out_dir, "ContainerFullPatch@2x.png")).convert("RGBA")
    tiles.append(make_tile(nine_slice_stretch(full, 20, 300, 200),
                           "FullPatch 9-slice STRETCH 300x200"))
    sec = Image.open(os.path.join(out_dir, "Buttons/Secondary@2x.png")).convert("RGBA")
    tiles.append(make_tile(nine_slice_stretch(sec, 12, 300, 70),
                           "Secondary 9-slice STRETCH 300x70"))
    toast = Image.open(os.path.join(out_dir, "MmoToastFrame@2x.png")).convert("RGBA")
    tiles.append(make_tile(nine_slice_stretch(toast, 20, 300, 130),
                           "Toast 9-slice STRETCH 300x130"))

    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    tw, th = tiles[0].size
    sheet = Image.new("RGBA", (cols * (tw + pad) + pad, rows * (th + pad) + pad + 40),
                      BG + (255,))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 10), title, font=fbig, fill=(20, 20, 20, 255))
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        x = pad + c * (tw + pad)
        y = 40 + pad + r * (th + pad)
        sheet.alpha_composite(t, (x, y))
    out_path = os.path.join(out_dir, "_MoltenContactSheet.png")
    sheet.convert("RGB").save(out_path)
    print("Contact sheet:", out_path, sheet.size)
