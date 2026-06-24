#!/usr/bin/env python3
"""
Shared molten-style UI theme texture SYNTHESIS ENGINE.

ONE parameterized engine behind every molten-family premium UI theme. A theme is
a thin ~15-line script (see Molten/molten_theme_gen.py, Molten_02/molten02_theme_gen.py)
that defines a PARAMS block and calls run(PARAMS); everything theme-agnostic lives
here so a new monthly drop is a parameter edit, not a 700-line fork.

Style family: CRACKED OBSIDIAN / COOLED-LAVA CRUST + GLOWING LAVA. We SYNTHESIZE a
brand-new molten RGB surface, then composite it through each source texture's own
ALPHA channel so the silhouette + 9-slice metrics are preserved exactly. Output
dimensions == source dimensions.

9-SLICE SAFETY: for any patch with Border N the straight edge strips are a CONSTANT
cross-section so stretching is byte-seamless; irregular detail lives only in the
corner insets (never stretched) and the center fill.

PER-THEME PARAMS (passed to configure()/run()):
  out_dir       output directory (each texture is written here; defaults to the
                caller-theme dir so outputs land beside the thin theme script).
  seed          master SEED (was 1771 for both molten themes).
  lava_stops    the gradient anchor rows (the SINGLE lava gradient for the set).
  rock_dark     near-black / cooled-crust rock anchor (RGB float array).
  rock_mid      lighter rock anchor (RGB float array).
  glow_tint     bloom tint (R >> G,B keeps the glow on-theme).
  patch_style   'veins' (thin rim + faint deep-interior veins, molten_01) or
                'band' (wide lava band around the border, molten_02).
  patch_glow_radius   build_patch's molten_surface glow_radius (4.5 veins / 4.2 band).
  patch_core_boost    build_patch's molten_surface core_boost (1.0 veins / 1.05 band).

Requires: numpy, Pillow.

Reskin to another theme: write a new params dict (lava_stops + rock anchors +
glow_tint + seed + patch_style + the two patch tunables) and call run(); do NOT
fork this engine.
"""

import os
import math
import numpy as np
from PIL import Image, ImageFilter

# ----------------------------------------------------------------------------
# Paths (shared across every molten-family theme; OUT is per-theme, set by
# configure() from the caller's params).
# ----------------------------------------------------------------------------
REPO = "d:/dev/business/hyMMO"
SRC_COMMON = os.path.join(REPO, "hytale-shared-source/HytaleAssets/Common/UI/Custom/Common")
SRC_TOAST = os.path.join(REPO, "src/main/resources/Common/UI/Custom/Pages/MmoToastFrame@2x.png")

# ----------------------------------------------------------------------------
# Per-theme state. configure() populates these module globals BEFORE any builder
# runs, mirroring the original per-theme module-level constants so the free
# functions below resolve them by name exactly as in the forked scripts (this
# keeps RNG call order + ops byte-identical).
# ----------------------------------------------------------------------------
SEED = None
rng = None
LAVA_STOPS = None
LAVA_LUT = None
ROCK_DARK = None
ROCK_MID = None
GLOW_TINT = None
OUT = None
PATCH_STYLE = "veins"
PATCH_GLOW_RADIUS = 4.5
PATCH_CORE_BOOST = 1.0


def configure(params):
    """Install a theme's params as module state, exactly mirroring the forked
    scripts' top-level constants, then build the per-theme LAVA_LUT + OUT dir."""
    global SEED, rng, LAVA_STOPS, LAVA_LUT, ROCK_DARK, ROCK_MID, GLOW_TINT, OUT
    global PATCH_STYLE, PATCH_GLOW_RADIUS, PATCH_CORE_BOOST

    SEED = params["seed"]
    rng = np.random.default_rng(SEED)  # parity with the forked scripts (unused below)
    LAVA_STOPS = params["lava_stops"]
    LAVA_LUT = build_lut(LAVA_STOPS)
    ROCK_DARK = np.array(params["rock_dark"], dtype=np.float64)
    ROCK_MID = np.array(params["rock_mid"], dtype=np.float64)
    GLOW_TINT = np.array(params["glow_tint"])
    OUT = params["out_dir"]
    PATCH_STYLE = params.get("patch_style", "veins")
    PATCH_GLOW_RADIUS = params.get("patch_glow_radius", 4.5)
    PATCH_CORE_BOOST = params.get("patch_core_boost", 1.0)

    os.makedirs(os.path.join(OUT, "Buttons"), exist_ok=True)


# ----------------------------------------------------------------------------
# Lava gradient LUT (the SINGLE lava gradient used by EVERY asset in a set).
# ----------------------------------------------------------------------------
def build_lut(stops, n=256):
    xs = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], dtype=np.float64)
    t = np.linspace(0.0, 1.0, n)
    lut = np.empty((n, 3))
    for c in range(3):
        lut[:, c] = np.interp(t, xs, cols[:, c])
    return lut


def lava_color(h):
    """h in [0,1] -> RGB float array. Vectorized."""
    idx = np.clip(h, 0.0, 1.0) * (LAVA_LUT.shape[0] - 1)
    lo = np.floor(idx).astype(int)
    hi = np.clip(lo + 1, 0, LAVA_LUT.shape[0] - 1)
    f = (idx - lo)[..., None]
    return LAVA_LUT[lo] * (1 - f) + LAVA_LUT[hi] * f


# ----------------------------------------------------------------------------
# Value noise (smooth fractal) - pure numpy, no scipy.
# ----------------------------------------------------------------------------
def _smoothstep(t):
    return t * t * (3 - 2 * t)


def value_noise(h, w, scale, seed):
    """Smooth value noise via bilinear-interp of a coarse random grid."""
    r = np.random.default_rng(seed)
    gh = max(2, int(h / scale) + 2)
    gw = max(2, int(w / scale) + 2)
    grid = r.random((gh, gw))
    ys = np.linspace(0, gh - 1.001, h)
    xs = np.linspace(0, gw - 1.001, w)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = _smoothstep(ys - y0)[:, None]
    fx = _smoothstep(xs - x0)[None, :]
    g00 = grid[np.ix_(y0, x0)]
    g01 = grid[np.ix_(y0, x0 + 1)]
    g10 = grid[np.ix_(y0 + 1, x0)]
    g11 = grid[np.ix_(y0 + 1, x0 + 1)]
    top = g00 * (1 - fx) + g01 * fx
    bot = g10 * (1 - fx) + g11 * fx
    return top * (1 - fy) + bot * fy


def fractal_noise(h, w, octaves=4, base_scale=40, seed=0):
    out = np.zeros((h, w))
    amp = 1.0
    total = 0.0
    for o in range(octaves):
        out += amp * value_noise(h, w, base_scale / (2 ** o), seed + o * 101)
        total += amp
        amp *= 0.5
    out /= total
    return out


# ----------------------------------------------------------------------------
# Crack network generators -> a "heat" field [0,1] (1 = on a seam core)
# ----------------------------------------------------------------------------
def gaussian_blur_np(arr, radius):
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8))
    img = img.filter(ImageFilter.GaussianBlur(radius))
    return np.asarray(img, dtype=np.float64) / 255.0


def polyline_cracks(h, w, n_lines, seed, width=1.3, jitter=0.35):
    """Several jagged random polylines drawn as heat lines."""
    r = np.random.default_rng(seed)
    heat = np.zeros((h, w))
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(n_lines):
        ang = r.uniform(0, 2 * math.pi)
        cy, cx = r.uniform(0, h), r.uniform(0, w)
        steps = int(max(h, w) * 1.3)
        pts = []
        for s in range(steps):
            pts.append((cy, cx))
            ang += r.uniform(-jitter, jitter)
            cy += math.sin(ang); cx += math.cos(ang)
            if cy < -5 or cy > h + 5 or cx < -5 or cx > w + 5:
                break
        for (py, px) in pts:
            d2 = (yy - py) ** 2 + (xx - px) ** 2
            heat = np.maximum(heat, np.clip(1.0 - np.sqrt(d2) / width, 0, 1))
    return heat


def ridged_cracks(h, w, seed, scale=22, sharp=0.92):
    """Thresholded ridged noise -> branching crack field."""
    n = fractal_noise(h, w, octaves=5, base_scale=scale, seed=seed)
    ridged = 1.0 - np.abs(n - 0.5) * 2.0  # ridge at the 0.5 isoline
    heat = np.clip((ridged - sharp) / (1 - sharp), 0, 1)
    return heat ** 0.7


# ----------------------------------------------------------------------------
# Surface compositor: given a heat field, produce molten RGB.
# ----------------------------------------------------------------------------
def molten_surface(heat, rock_noise=None, h=None, w=None,
                   glow_radius=4.0, glow_strength=0.85,
                   rock_brightness=1.0, vein_gamma=1.0,
                   core_boost=1.0, glow_tint=None):
    """heat: [0,1] field, 1 = hottest seam core. Returns float RGB 0..255."""
    if h is None:
        h, w = heat.shape
    if rock_noise is None:
        rock_noise = fractal_noise(h, w, octaves=4, base_scale=34, seed=SEED + 7)
    if glow_tint is None:
        glow_tint = GLOW_TINT

    heat = np.clip(heat, 0, 1) ** vein_gamma

    # Base obsidian rock: dark, glossy, subtle warm variation.
    rk = rock_noise[..., None]
    rock = ROCK_DARK[None, None, :] * (1 - rk) + ROCK_MID[None, None, :] * rk
    rock *= rock_brightness

    # Map heat -> position along the lava gradient. Push most of the vein body
    # into the RED band; only the brightest, thinnest cores reach orange/white.
    pos = np.clip(heat ** 0.70, 0, 1) * 0.80
    pos = np.clip(pos + (heat ** 5.0) * 0.32 * core_boost, 0, 1)
    vein_rgb = lava_color(pos)

    vein_a = np.clip(heat * 1.15, 0, 1)[..., None]
    surf = rock * (1 - vein_a) + vein_rgb * vein_a

    # BLOOM / GLOW: blurred copy of the emitted light, screen-blended.
    # (v4 graft: a purer, more incandescent two-radius falloff.)
    emit = (heat ** 1.4)
    glow = gaussian_blur_np(emit, glow_radius)
    glow2 = gaussian_blur_np(emit, glow_radius * 2.4) * 0.6
    glow_total = np.clip(glow + glow2, 0, 1)
    glow_rgb = glow_total[..., None] * glow_tint[None, None, :] * 255.0 * glow_strength
    surf = 255.0 - (255.0 - surf) * (255.0 - glow_rgb) / 255.0

    return np.clip(surf, 0, 255)


# ----------------------------------------------------------------------------
# Constant-cross-section molten RIM for 9-slice straight edges.
# ----------------------------------------------------------------------------
def rim_profile(depth):
    """Outer->inner cross-section heat profile. A continuous glowing lava line
    sits ~40% in from the outer crust, with a faint secondary inner ember."""
    x = np.arange(depth)
    line = depth * 0.40
    sigma = max(1.0, depth * 0.11)
    prof = np.exp(-((x - line) ** 2) / (2 * sigma ** 2))
    line2 = depth * 0.80
    prof += 0.32 * np.exp(-((x - line2) ** 2) / (2 * (sigma * 0.9) ** 2))
    return np.clip(prof, 0, 1)


def apply_constant_edges(heat, border, edge_level=1.0):
    """Overwrite the border strips of `heat` with a constant cross-section so
    each straight edge is identical along its length (9-slice safe). Corners are
    left to the irregular crack field. `edge_level` scales the rim brightness so
    the corner field can be levelled to MATCH it (one continuous rim)."""
    h, w = heat.shape
    b = border
    if b <= 0 or b * 2 >= min(h, w):
        return heat
    out = heat.copy()
    prof_v = rim_profile(b) * edge_level
    out[0:b, b:w - b] = prof_v[:, None]
    out[h - b:h, b:w - b] = prof_v[::-1][:, None]
    out[b:h - b, 0:b] = prof_v[None, :]
    out[b:h - b, w - b:w] = prof_v[::-1][None, :]
    return out


def enforce_constant_edges_rgb(surf, border):
    """Re-stamp the 4 straight-edge strips on the FINAL RGB with a single
    constant cross-section (bloom blur can perturb them column-to-column).
    Corners (b x b squares) are never stretched, left intact."""
    h, w, _ = surf.shape
    b = border
    if b <= 0 or b * 2 >= min(h, w):
        return surf
    out = surf.copy()
    midx = w // 2
    midy = h // 2
    out[0:b, b:w - b, :] = surf[0:b, midx, :][:, None, :]
    out[h - b:h, b:w - b, :] = surf[h - b:h, midx, :][:, None, :]
    out[b:h - b, 0:b, :] = surf[midy, 0:b, :][None, :, :]
    out[b:h - b, w - b:w, :] = surf[midy, w - b:w, :][None, :, :]
    return out


def corner_cracks(h, w, border, seed, *, edge_level=1.0,
                  center_damp=0.34, corner_level=1.0):
    """Irregular cracks concentrated in the 4 corner insets + a CALM center fill,
    not crossing the straight edge strips.

    Art-director refinements:
      * `center_damp` (<1) reduces vein density/contrast in the middle third so
        overlaid UI text/icons stay legible (v3 graft: calmer interior).
      * `corner_level` levels corner-node brightness toward the edge-run level so
        the frame reads as ONE continuous molten rim, not four corner lamps."""
    c1 = ridged_cracks(h, w, seed=seed, scale=22, sharp=0.93)
    c2 = polyline_cracks(h, w, max(2, (h + w) // 150), seed=seed + 3,
                         width=1.05, jitter=0.40)
    field = np.maximum(c1 * 0.55, c2 * 0.48)

    yy, xx = np.mgrid[0:h, 0:w]
    b = max(border, 1)

    # Corner emphasis weight (full in the corner insets, fades to center).
    corners = [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]
    cw = np.zeros((h, w))
    crad = b * 2.2
    for (cy, cx) in corners:
        d = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
        cw = np.maximum(cw, np.clip(1.0 - d / crad, 0, 1))

    # Center damp weight: 1.0 at the rim ring, `center_damp` in the deep middle.
    # Distance to nearest edge, normalized by half-min-dimension.
    de = np.minimum.reduce([yy, xx, h - 1 - yy, w - 1 - xx]).astype(np.float64)
    rim_frac = np.clip(de / (0.45 * min(h, w)), 0, 1)   # 0 at rim, 1 deep center
    center_w = 1.0 - (1.0 - center_damp) * rim_frac

    field = field * center_w

    # Corner cracks are levelled to ~the edge rim brightness (no bright lamps).
    # weight: corner -> edge_level*corner_level ; center -> faint.
    weight = (0.30 * center_w) + (edge_level * corner_level) * cw
    return np.clip(field * weight, 0, 1)


# ----------------------------------------------------------------------------
# CONTINUOUS rim from distance-to-edge. Eroding the actual silhouette gives a
# distance-to-edge field whose iso-contours follow the ROUNDED corners, so a rim
# placed at a fixed inset wraps the corner seamlessly (no hard corner seam) AND
# is constant along the straight runs (perpendicular distance there) => still
# 9-slice safe. This replaces the old per-edge-strip rim that left the corner
# squares to a mismatched random crack field (the visible hard-edge bug).
# ----------------------------------------------------------------------------
def edge_distance(alpha, maxd):
    """Distance (in px) from each opaque pixel to the OUTER silhouette edge, via
    iterative 3x3 erosion. The mask is PADDED with a transparent border first:
    the frame's straight edges sit FLUSH with the texture boundary (only the
    rounded corners carry transparency), so without the pad only the corners get
    a small distance and light up as lamps while the straight runs stay dark.
    With the pad every side erodes inward => dist = perpendicular distance on the
    straight runs (uniform along the run, so 9-slice safe) and follows the arc at
    the rounded corners, giving ONE continuous rim of even brightness."""
    P = maxd + 2
    mask = alpha > 40
    pad = np.zeros((mask.shape[0] + 2 * P, mask.shape[1] + 2 * P), dtype=bool)
    pad[P:-P, P:-P] = mask
    cur = Image.fromarray((pad * 255).astype(np.uint8))
    dist = np.full(pad.shape, float(maxd), dtype=np.float64)
    prev = pad.copy()
    for k in range(1, maxd + 1):
        cur = cur.filter(ImageFilter.MinFilter(3))  # erode 1px (3x3)
        cure = np.asarray(cur) > 127
        removed = prev & (~cure)
        dist[removed] = k - 1
        prev = cure
    dist[~pad] = -1.0
    return dist[P:-P, P:-P]


def rim_heat(dist, border, edge_level=1.0):
    """Continuous glowing lava rim at a fixed inset from the silhouette edge.
    Being a function of distance-to-edge, it turns the rounded corners with no
    seam and stays constant along the straight runs. Mirrors rim_profile():
    a main hot line ~40% in, plus a faint secondary inner ember ~80% in."""
    L = border * 0.40
    sigma = max(1.0, border * 0.13)
    prof = np.exp(-((dist - L) ** 2) / (2 * sigma ** 2))
    L2 = border * 0.80
    prof += 0.30 * np.exp(-((dist - L2) ** 2) / (2 * (sigma * 0.95) ** 2))
    prof[dist < 0] = 0.0
    return np.clip(prof * edge_level, 0, 1)


# ----------------------------------------------------------------------------
# Patch interior styles (the ONLY per-theme branch in build_patch).
#   'veins' (molten_01): thin rim + faint DEEP-interior veins only.
#   'band'  (molten_02): a WIDE lava band around the border + a faint cooled
#                        center, for the "more lava / flowing" look.
# Each returns the combined `heat` field given the rim + dist + geometry.
# ----------------------------------------------------------------------------
def _patch_heat_veins(rim, dist, h, w, border, seed, center_damp, edge_level):
    # Faint interior veins for life, but only DEEP inside (dist > 1.25*border) so
    # they never touch or compete with the rim, and damped toward the center.
    veins = corner_cracks(h, w, border, seed, edge_level=edge_level,
                          center_damp=center_damp, corner_level=0.0)
    interior = np.clip((dist - border * 1.25) / max(1.0, border), 0, 1)
    veins = veins * interior * 0.5

    return np.maximum(rim, veins)


def _patch_heat_band(rim, dist, h, w, border, seed, center_damp, edge_level):
    # LAVA BAND (the "more lava" look): a WIDE molten band around the border that
    # glows like flowing lava, hot near the rim and fading into the dark crust
    # center. Built from dist (constant cross-section on straight runs => 9-slice
    # safe via enforce below; wraps the rounded corners) with a subtle crust
    # crackle + bright lava seams confined to the band.
    bandprof = np.exp(-((dist - border * 0.40) ** 2) / (2 * (border * 0.52) ** 2))
    bandprof[dist < 0] = 0.0
    crust = fractal_noise(h, w, octaves=4, base_scale=max(8, border), seed=seed + 3)
    cracks = ridged_cracks(h, w, seed=seed + 5, scale=max(8, int(border * 0.8)),
                           sharp=0.86)
    band = np.clip(bandprof * (0.30 + 0.55 * crust) + cracks * 0.7 * bandprof, 0, 1)
    heat = np.maximum(rim, band)

    # Faint cooled-center life so the middle is not dead flat (kept deep + dim).
    interior = np.clip((dist - border * 1.6) / max(1.0, border), 0, 1)
    cen = corner_cracks(h, w, border, seed, edge_level=edge_level,
                        center_damp=center_damp, corner_level=0.0) * interior * 0.3
    return np.maximum(heat, cen)


_PATCH_HEAT_STYLES = {"veins": _patch_heat_veins, "band": _patch_heat_band}


# ----------------------------------------------------------------------------
# Generic patch builder for solid rounded-rect frames (FullPatch, Patch,
# Header, Secondary button, ToastFrame, PanelLight). The interior fill + the two
# molten_surface tunables (glow_radius / core_boost) come from the active theme.
# ----------------------------------------------------------------------------
def build_patch(alpha, border, seed, *, panel_subtle=False, panel_bright=1.0,
                bright=1.0, glow=0.9, state="normal", center_damp=0.34,
                edge_level=1.0):
    h, w = alpha.shape
    rock_noise = fractal_noise(h, w, octaves=4, base_scale=max(10, (h + w) // 8),
                               seed=seed + 11)

    if panel_subtle:
        return build_panel(h, w, seed, panel_bright)

    # CONTINUOUS rounded rim from distance-to-edge (wraps corners; 9-slice safe).
    dist = edge_distance(alpha, maxd=border + 2)
    rim = rim_heat(dist, border, edge_level=edge_level)

    # Per-theme interior fill (veins vs lava band).
    heat = _PATCH_HEAT_STYLES[PATCH_STYLE](
        rim, dist, h, w, border, seed, center_damp, edge_level)

    # State tint.
    if state == "hover":
        bright *= 1.18; glow *= 1.45; heat = np.clip(heat * 1.15, 0, 1)
    elif state == "press":
        bright *= 0.82; glow *= 0.7; heat = np.clip(heat * 0.85, 0, 1)

    surf = molten_surface(heat, rock_noise=rock_noise, glow_radius=PATCH_GLOW_RADIUS,
                          glow_strength=glow, rock_brightness=bright,
                          core_boost=PATCH_CORE_BOOST)

    # FINAL 9-slice enforcement on RGB: re-stamp each straight edge byte-constant
    # (the rounded corners are never stretched, so they keep the continuous rim).
    surf = enforce_constant_edges_rgb(surf, border)
    return surf


# ----------------------------------------------------------------------------
# PANELS (24x24, Border 4). Subtle DARK OBSIDIAN that reads clearly when
# multiply-tinted at runtime. Low contrast, a faint warm rim seam, mostly dark.
# Art-director fix: a clearly-readable dark-obsidian tint that does NOT wash out
# to grey; keep luminance low so .Background.Color multiply stays on-theme.
# ----------------------------------------------------------------------------
def build_panel(h, w, seed, panel_bright):
    # Dark obsidian field with very subtle warm fractal variation.
    rn = fractal_noise(h, w, octaves=4, base_scale=7, seed=seed + 2)
    rk = rn[..., None]
    rock = ROCK_DARK[None, None, :] * (1 - rk) + ROCK_MID[None, None, :] * rk
    # A faint crimson rim seam just inside the edge so the panel reads as molten.
    yy, xx = np.mgrid[0:h, 0:w]
    de = np.minimum.reduce([yy, xx, h - 1 - yy, w - 1 - xx]).astype(np.float64)
    rim = np.exp(-((de - 1.4) ** 2) / (2 * 1.1 ** 2)) * 0.45
    vein = ridged_cracks(h, w, seed=seed + 5, scale=8, sharp=0.90) * 0.22
    heat = np.clip(np.maximum(rim, vein), 0, 1)
    vein_rgb = lava_color(np.clip(heat ** 0.7 * 0.62, 0, 1))
    a = (heat * 0.9)[..., None]
    surf = rock * (1 - a) + vein_rgb * a
    # Faint crimson bloom so the seam emits, but keep the field dark.
    glow = gaussian_blur_np(heat, 1.6)[..., None] * GLOW_TINT[None, None, :] * 255.0 * 0.30
    surf = 255.0 - (255.0 - surf) * (255.0 - glow) / 255.0
    # panel_bright (>1 for the LightPatch) lifts the obsidian a touch but stays
    # dark enough not to wash grey; clamp to keep it on-theme.
    surf = surf * panel_bright
    return np.clip(surf, 0, 255)


# ----------------------------------------------------------------------------
# Round close button (molten seal) with a v2 forged CONCENTRIC BEVEL.
# v1 crimson ring + crisp X, plus v2's machined inner-ring depth.
# Hovered brightens the ring; Pressed dims + insets the seal.
# ----------------------------------------------------------------------------
def build_close_button(alpha, seed, state="normal"):
    h, w = alpha.shape
    cy, cx = (h - 1) / 2, (w - 1) / 2
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt((yy - cy) ** 2 + (xx - cx) ** 2)
    R = min(h, w) / 2
    rad = r / R  # 0 center .. 1 edge

    rock_noise = fractal_noise(h, w, octaves=4, base_scale=14, seed=seed + 2)

    # --- v2 GRAFT: machined concentric bevel rings on the forged metal face ---
    # Two faint dark ring-grooves + raised metal lands -> forged dimensionality.
    bevel = np.zeros((h, w))
    for rr, depth, sig in [(0.50, 0.55, 0.045), (0.86, 0.7, 0.05)]:
        bevel += depth * np.exp(-((rad - rr) ** 2) / (2 * sig ** 2))
    # raised land between center and the lava ring (lighter metal)
    land = np.clip((0.62 - rad) / 0.62, 0, 1) * (rad < 0.62)
    rock_face = rock_noise.copy()
    rock_face = rock_face + land * 0.55                 # raise inner land
    rock_face = rock_face * (1 - 0.55 * bevel)          # cut concentric grooves

    # glowing lava ring at ~0.70R (wide crimson body + thin bright core seam).
    ring_r = R * 0.70
    ring_body = np.exp(-((r - ring_r) ** 2) / (2 * (R * 0.085) ** 2)) * 0.55
    ring_seam = np.exp(-((r - ring_r) ** 2) / (2 * (R * 0.028) ** 2))
    ring = np.clip(ring_body + ring_seam, 0, 1)

    # faint deep-crimson ember behind the X (not a bright fill).
    core = np.exp(-(r ** 2) / (2 * (R * 0.32) ** 2)) * 0.55

    # cracks radiating across the disc, fading near rim.
    crack = ridged_cracks(h, w, seed=seed + 8, scale=10, sharp=0.90)
    crack *= np.clip(1.0 - rad, 0, 1) * 0.45

    # The X glyph (two diagonal bars) - a HOT crimson seam, legible.
    th = max(1.6, R * 0.085)
    d1 = np.abs((yy - cy) - (xx - cx)) / math.sqrt(2)
    d2 = np.abs((yy - cy) + (xx - cx)) / math.sqrt(2)
    arm = R * 0.42
    inarm = (np.abs(yy - cy) < arm) & (np.abs(xx - cx) < arm)
    xglyph = np.zeros((h, w))
    xglyph[inarm] = np.maximum(
        np.clip(1.0 - d1[inarm] / th, 0, 1),
        np.clip(1.0 - d2[inarm] / th, 0, 1),
    )

    heat = np.clip(ring + core * 0.55 + crack, 0, 1)
    heat = np.maximum(heat, xglyph)

    bright = 1.0; glow = 1.0; core_b = 1.0
    if state == "hover":
        # Brighten via BLOOM (crimson) + a modest heat lift; keep core_boost low
        # so the ring stays scarlet/crimson and does NOT blow out to orange-white.
        glow = 1.75; heat = np.clip(heat * 1.12, 0, 1); core_b = 1.05
    elif state == "press":
        bright = 0.80; glow = 0.70; heat = np.clip(heat * 0.9, 0, 1); core_b = 0.85

    # dark outer rim crust (forged iron lip).
    rimdark = np.clip((rad - 0.85) / 0.15, 0, 1)
    rock_face = rock_face * (1 - rimdark * 0.7)

    surf = molten_surface(heat, rock_noise=np.clip(rock_face, 0, 1.6),
                          glow_radius=3.5, glow_strength=glow,
                          rock_brightness=bright, core_boost=core_b)

    if state == "press":
        # sunken: shade the upper-left so the seal reads pressed-in / inset.
        shade = np.clip(0.55 - ((xx - cx) + (yy - cy)) / (R * 4), 0, 1)
        surf = surf * (0.82 + 0.18 * shade[..., None])

    return np.clip(surf, 0, 255)


# ----------------------------------------------------------------------------
# Decoration strips: a thin molten seam with small ember nodes (elegant).
# Tightened to the same crimson value as the main frame (no orange drift).
# ----------------------------------------------------------------------------
def build_decoration(alpha, seed, flip=False):
    h, w = alpha.shape
    a = alpha.astype(np.float64) / 255.0
    yy = np.arange(h)[:, None]
    xx = np.arange(w)[None, :]
    col_mass = a.sum(axis=0) + 1e-6
    centroid = (a * yy).sum(axis=0) / col_mass
    wob = fractal_noise(1, w, octaves=3, base_scale=40, seed=seed)[0] * 1.2 - 0.6
    centroid = centroid + wob
    line_sig = max(0.8, h * 0.10)
    heat = np.exp(-((yy - centroid[None, :]) ** 2) / (2 * line_sig ** 2))
    # ember nodes spaced along the seam, plus a central node (matches source).
    n_nodes = max(4, w // 70)
    node_x = np.concatenate([np.linspace(w * 0.12, w * 0.88, n_nodes), [w / 2]])
    rr = np.random.default_rng(seed + 4)
    for nx in node_x:
        amp = rr.uniform(0.7, 1.0)
        nd = np.exp(-((xx - nx) ** 2) / (2 * (w * 0.012) ** 2))
        heat = np.maximum(heat, nd * amp)
    heat = np.clip(heat, 0, 1)
    rock_noise = fractal_noise(h, w, octaves=3, base_scale=20, seed=seed + 1)
    # core_boost kept modest so the seam stays CRIMSON (no orange drift).
    surf = molten_surface(heat, rock_noise=rock_noise, glow_radius=3.0,
                          glow_strength=1.0, rock_brightness=0.9,
                          core_boost=1.0)
    return surf


# ----------------------------------------------------------------------------
# Header bar (v4 "magma-pour" GRAFT): the brightest, most LIQUID molten bar in
# the set. Constant cross-section ALONG X (9-slice / full-width safe): build a
# single column profile (h tall) and tile it, then add subtle ember rune nodes.
# Scarlet-capped underline keeps it RED-dominant.
# ----------------------------------------------------------------------------
def build_header(alpha, seed, runes=True):
    h, w = alpha.shape
    y = np.linspace(0, 1, h)
    # vertical cross-section heat: bright hot underline + bloom shoulder + faint
    # top ember rim + ambient body warmth (v4's liquid bar profile).
    underline = np.exp(-((y - 0.86) ** 2) / (2 * 0.045 ** 2))
    underglow = 0.55 * np.exp(-((y - 0.86) ** 2) / (2 * 0.12 ** 2))
    topglow = 0.24 * np.exp(-((y - 0.08) ** 2) / (2 * 0.05 ** 2))
    body = 0.07 * np.exp(-((y - 0.5) ** 2) / (2 * 0.25 ** 2))
    heat = np.clip(underline + underglow + topglow + body, 0, 1)

    # build the molten column directly (so it's perfectly constant along X).
    rock = (ROCK_DARK[None, :] + (ROCK_MID - ROCK_DARK)[None, :]
            * (0.5 * (1 - y))[:, None]) / 255.0
    expose = np.clip(heat * 1.3, 0, 1) ** 1.05
    # SCARLET-capped: crimson body, red-orange only at the razor center seam.
    razor = np.clip((heat - 0.85) / 0.15, 0, 1) ** 1.5
    lava_t = np.clip(0.44 + 0.20 * heat + 0.18 * razor, 0, 1)
    lava = lava_color(lava_t) / 255.0
    col = rock * (1 - expose[:, None]) + lava * expose[:, None]
    # crimson bloom along the column (RED-dominant).
    bl = gaussian_blur_np(np.tile(heat[:, None], (1, 8)), 3)[:, 0]
    bcol = np.stack([bl * 0.88, bl * 0.15, bl * 0.07], 1)
    col = 1 - (1 - col) * (1 - np.clip(bcol, 0, 1))
    col = np.clip(col, 0, 1)

    rgb = np.tile(col[:, None, :], (1, w, 1)) * 255.0

    if runes:
        # subtle evenly-spaced ember "rune" nodes along the underline.
        node_y = int(0.86 * h)
        ember = lava_color(np.array([0.85]))[0]  # scarlet ember
        for cx in range(80, w - 80, 150):
            rr = 7
            y0, y1 = node_y - rr, node_y + rr
            x0, x1 = cx - rr, cx + rr
            yy2, xx2 = np.mgrid[y0:y1, x0:x1]
            d = np.sqrt((yy2 - node_y) ** 2 + (xx2 - cx) ** 2)
            g = (np.clip(1 - d / rr, 0, 1) ** 1.5)[..., None]
            rgb[y0:y1, x0:x1, :] = np.clip(
                rgb[y0:y1, x0:x1, :] * (1 - g) + ember[None, None, :] * g, 0, 255)

    return np.clip(rgb, 0, 255)


# ----------------------------------------------------------------------------
# Compose synthesized RGB through the source alpha and save.
# ----------------------------------------------------------------------------
def composite_and_save(src_path, out_path, rgb_float):
    src = Image.open(src_path).convert("RGBA")
    alpha = np.array(src)[..., 3]
    rgb = np.clip(rgb_float, 0, 255).astype(np.uint8)
    out = np.dstack([rgb, alpha.astype(np.uint8)])
    Image.fromarray(out, "RGBA").save(out_path)
    return alpha


def load_alpha(src_path):
    return np.array(Image.open(src_path).convert("RGBA"))[..., 3]


# ----------------------------------------------------------------------------
# MAIN: the 11-source-texture manifest. Theme-agnostic; the active theme's
# gradient/rock/glow + patch interior style drive every builder.
# ----------------------------------------------------------------------------
def C(name):
    return os.path.join(SRC_COMMON, name)


def main():
    # --- Full window frame (Border 20). Calm center, levelled rim. ---
    a = load_alpha(C("ContainerFullPatch@2x.png"))
    composite_and_save(C("ContainerFullPatch@2x.png"),
                       os.path.join(OUT, "ContainerFullPatch@2x.png"),
                       build_patch(a, 20, 101, center_damp=0.30, edge_level=1.0))

    # --- Header-mode window frame (Border 20) ---
    a = load_alpha(C("ContainerPatch@2x.png"))
    composite_and_save(C("ContainerPatch@2x.png"),
                       os.path.join(OUT, "ContainerPatch@2x.png"),
                       build_patch(a, 20, 113, center_damp=0.30, edge_level=1.0))

    # --- Inset panels (subtle dark obsidian, runtime-tinted) ---
    a = load_alpha(C("ContainerPanelPatch@2x.png"))
    composite_and_save(C("ContainerPanelPatch@2x.png"),
                       os.path.join(OUT, "ContainerPanelPatch@2x.png"),
                       build_patch(a, 4, 131, panel_subtle=True, panel_bright=1.0))
    a = load_alpha(C("ContainerPanelLightPatch@2x.png"))
    composite_and_save(C("ContainerPanelLightPatch@2x.png"),
                       os.path.join(OUT, "ContainerPanelLightPatch@2x.png"),
                       build_patch(a, 4, 137, panel_subtle=True, panel_bright=1.4))

    # --- Header bars (v4 liquid lava bar graft) ---
    a = load_alpha(C("ContainerHeader@2x.png"))
    composite_and_save(C("ContainerHeader@2x.png"),
                       os.path.join(OUT, "ContainerHeader@2x.png"),
                       build_header(a, 201, runes=True))
    a = load_alpha(C("ContainerHeaderNoRunes@2x.png"))
    composite_and_save(C("ContainerHeaderNoRunes@2x.png"),
                       os.path.join(OUT, "ContainerHeaderNoRunes@2x.png"),
                       build_header(a, 207, runes=False))

    # --- Decoration strips (same crimson value as the frame) ---
    a = load_alpha(C("ContainerDecorationTop@2x.png"))
    composite_and_save(C("ContainerDecorationTop@2x.png"),
                       os.path.join(OUT, "ContainerDecorationTop@2x.png"),
                       build_decoration(a, 301))
    a = load_alpha(C("ContainerDecorationBottom@2x.png"))
    composite_and_save(C("ContainerDecorationBottom@2x.png"),
                       os.path.join(OUT, "ContainerDecorationBottom@2x.png"),
                       build_decoration(a, 307, flip=True))

    # --- Close button + states (v2 concentric bevel graft) ---
    for fn, st, sd in [("ContainerCloseButton@2x.png", "normal", 401),
                       ("ContainerCloseButtonHovered@2x.png", "hover", 401),
                       ("ContainerCloseButtonPressed@2x.png", "press", 401)]:
        a = load_alpha(C(fn))
        composite_and_save(C(fn), os.path.join(OUT, fn),
                           build_close_button(a, sd, state=st))

    # --- Buttons/Secondary patch + states (Border 12) ---
    for fn, st, sd in [("Secondary@2x.png", "normal", 501),
                       ("Secondary_Hovered@2x.png", "hover", 501),
                       ("Secondary_Pressed@2x.png", "press", 501)]:
        src = os.path.join(SRC_COMMON, "Buttons", fn)
        a = load_alpha(src)
        composite_and_save(src, os.path.join(OUT, "Buttons", fn),
                           build_patch(a, 12, sd, bright=1.0, glow=0.95, state=st,
                                       center_damp=0.42, edge_level=1.0))

    # --- Mod toast frame (Border 20, hollow). Same crimson as main frame. ---
    a = load_alpha(SRC_TOAST)
    composite_and_save(SRC_TOAST, os.path.join(OUT, "MmoToastFrame@2x.png"),
                       build_patch(a, 20, 601, center_damp=0.30, edge_level=1.0))

    print("Generated all molten textures into:", OUT)


def run(params):
    """Public entry point for a thin theme script: install PARAMS, synthesize."""
    configure(params)
    main()
