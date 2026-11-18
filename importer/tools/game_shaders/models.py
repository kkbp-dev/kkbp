"""Numpy models of the games' create and lit shaders, as the exporter bakes them (issue 30,
docs/design/library-from-code.md "What the measurements found").

These are the specification the edit templates' node groups follow: `host/test_shader_models.py`
checks each model against the Golden Samples' own textures, and the in-Blender tests check each node
group against its model. No bpy.

Conventions, measured on the samples:

- A bundle texture PNG holds the linear values the shader samples (`Materials.Read` copies it through
  a linear render target): use it as it is. Only `light` and `dark` are sRGB-encoded.
- Colours in the bundle are sRGB-encoded; a shader sees them linear: `lin(colour)`.
- A light or dark bake is the lit shader's linear output, sRGB-encoded, then graded by the maker
  camera's AmplifyColor LUT (`Lut_TimeDay.png`): `grade(srgb(out))`.
- The bake fixes the light: front-lit for `light` (ramp 1), back-lit for `dark` (ramp 0); no normal
  maps, no specular, no rim (the view faces the quad).

Images are float arrays (height, width, channels), rows top-down as PIL gives them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

F = np.float64


# --- colour ------------------------------------------------------------------------------

def lin(c):
    """sRGB-encoded to linear."""
    c = np.asarray(c, dtype=F)
    return np.where(c <= 0.04045, c / 12.92, ((np.maximum(c, 0) + 0.055) / 1.055) ** 2.4)


def srgb(c):
    """Linear to sRGB-encoded, clamped to 0..1 as an 8-bit render target clamps."""
    c = np.clip(np.asarray(c, dtype=F), 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def color(c):
    """A bundle colour as the shader sees it: linear rgb."""
    return lin(np.asarray(c, dtype=F)[:3])


def _bilinear(image, u, v):
    """GPU bilinear sampling with clamped edges: texel centres at (i + 0.5) / size."""
    h, w = image.shape[:2]
    x = u * w - 0.5
    y = v * h - 0.5
    x0 = np.floor(x)
    y0 = np.floor(y)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    xi0 = np.clip(x0.astype(int), 0, w - 1)
    xi1 = np.clip(x0.astype(int) + 1, 0, w - 1)
    yi0 = np.clip(y0.astype(int), 0, h - 1)
    yi1 = np.clip(y0.astype(int) + 1, 0, h - 1)
    top = image[yi0, xi0] * (1 - fx) + image[yi0, xi1] * fx
    bottom = image[yi1, xi0] * (1 - fx) + image[yi1, xi1] * fx
    return top * (1 - fy) + bottom * fy


def grade(rgb, lut):
    """AmplifyColor's LUT on sRGB-encoded colours. `lut` is the 1024 x 32 strip (rows bottom-up, as
    UV space has v up): 32 slices of red (x) by green (y), one per blue step, blended by blue."""
    rgb = np.clip(np.asarray(rgb, dtype=F), 0, 1)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    blue = b * 31
    low = np.floor(blue)
    frac = (blue - low)[..., None]
    high = np.minimum(low + 1, 31)
    u_red = (r * 31 + 0.5) / 1024
    v = (g * 31 + 0.5) / 32
    a = _bilinear(lut, u_red + low / 32, v)
    c = _bilinear(lut, u_red + high / 32, v)
    return (a * (1 - frac) + c * frac)[..., :3]


# --- the game's light, as the bake sets it ---------------------------------------------------

@dataclass(frozen=True)
class Light:
    """The maker's light and global shading values a Game's bake runs with (fitted, see the doc)."""

    light: float  # the `_LightColor0` term, `max(light * 0.6 + 0.4, ambient)`, per channel the same
    ambient: float  # `_ambientshadowG.a`: how strongly the ambient colour shades
    # The ambient colour, rgb: KK's is `_ambientshadowG.rgb` (the same 0.15); KKS's mixes in its light
    # probes, `lerp(_ambientshadowG.rgb, SH * 0.5 + 0.5, _KanoVerShift)`, which a bake's flat quad
    # sees as one colour. None: `ambient` in every channel.
    ambient_color: tuple[float, float, float] | None = None
    # How much of the lit colour the back-lit side keeps: KKS's `saturate(ramp + _ambientshadowG.a)`
    # with the ramp's own floor; KK's toon_eyew keeps none.
    shadow_floor: float = 0.0


KK = Light(light=1.0, ambient=0.15)
# Koikano/main_eyew, fitted to the KKS sample's eye-white family (the ambient strength, colour and
# floor trade off a little against each other; this is the best fit, within 0.003 of every bake).
KKS = Light(light=1.0, ambient=0.175, ambient_color=(0.225, 0.216, 0.203), shadow_floor=0.2)
# Koikano/main_skin under the bake, approximated by KK's main_skin with these (fitted to the KKS
# sample's body and face; KKS's shader also blends in light probes and a physically based term).
KKS_SKIN = Light(light=1.0, ambient=0.07, ambient_color=(0.145, 0.145, 0.145), shadow_floor=0.28)


def ambient_shadow(light: Light):
    """The shaders' ambient shadow intensity per channel, from the ambient colour and strength (the
    `finalAmbientShadow` block): an overlay of the two, `1 - (1 - a)(1 - colour)` for a >= 0."""
    a = light.ambient
    c = np.full(3, a, dtype=F) if light.ambient_color is None else np.asarray(light.ambient_color, dtype=F)
    w = a * 0.5 + 0.5
    s = 1 - 2 * (1 - w) * (1 - c) if w > 0.5 else 2 * w * c
    return np.clip(s, 0, 1)


def shade(shadow_color, s):
    """toon_eyew's shadow tint: the shadow colour's overlay with the ambient shadow `s`."""
    sc = np.asarray(shadow_color, dtype=F)
    return np.clip(np.where(sc > 0.5, 1 - (2 - 2 * sc) * (1 - s), 2 * s * sc), 0, 1)


# --- create shaders ------------------------------------------------------------------------

def create_eyewhite(main, color_, color2):
    """create_eyewhite (KK) and Koikano/create_eyew (KKS): the eye white's two colours by the
    texture's red. Alpha 1."""
    r = main[..., 0:1]
    rgb = color2 + r * (color_ - color2)
    return rgb, np.ones(main.shape[:2], dtype=F)


# --- lit shaders ---------------------------------------------------------------------------

def toon_eyew(main, alpha, color_, shadow_color, ramp, light: Light = KK):
    """KK's toon_eyew_lod0 and KKS's Koikano/main_eyew (eye whites, eyebrows, eyelines): the texture
    times the colour, shaded by the shadow colour's tint where the light doesn't reach. Returns
    linear rgb and alpha.

    Koikano/main_eyew also desaturates its light term by 75 % in shadow and takes
    `max(light * 0.67 + 0.33, ambient colour)`; with the bake's light (1.0) both give 1, as KK's
    term does, so the model leaves them out."""
    base = main * color_
    dark = base * shade(shadow_color, ambient_shadow(light))
    lit = min(1.0, ramp + light.shadow_floor)
    out = (dark + lit * (base - dark)) * max(light.light * 0.6 + 0.4, light.ambient)
    return out, alpha


def toon_nose(main, alpha, color_, _ramp=None, light: Light = KK):
    """KK's toon_nose_lod0: unlit, the colour where the texture's red is dark plus its green."""
    out = color_ * (1 - main[..., 0:1]) + main[..., 1:2]
    return out, alpha


def baked(out, lut):
    """A model's linear output as the bundle's light or dark PNG holds it."""
    return grade(srgb(out), lut)


def sample_repeat(image, u, v):
    """GPU bilinear sampling with repeating edges, `image` rows bottom-up (v up, as UV space)."""
    h, w = image.shape[:2]
    x = np.asarray(u, dtype=F) * w - 0.5
    y = np.asarray(v, dtype=F) * h - 0.5
    x0 = np.floor(x)
    y0 = np.floor(y)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    xi0 = x0.astype(int) % w
    xi1 = (xi0 + 1) % w
    yi0 = y0.astype(int) % h
    yi1 = (yi0 + 1) % h
    top = image[yi0, xi0] * (1 - fx) + image[yi0, xi1] * fx
    bottom = image[yi1, xi0] * (1 - fx) + image[yi1, xi1] * fx
    return top * (1 - fy) + bottom * fy


def hair_gloss_shift(ramp, front):
    """How far along u main_hair (or main_hair_front) reads `_HairGloss` from the second UV map: by
    the light's angle, `ndl` 1 for the bake's `light` (ramp 1) and -1 for `dark` (ramp 0). The
    texture's own offset and scale apply after."""
    ndl = ramp * 2 - 1
    return ndl * 0.02 + 0.99 if front else ndl * 0.005


def main_hair(main, color_mask, detail_mask, gloss, colors, shadow_color, shadow_extend, ramp, light: Light = KK):
    """KK's main_hair and main_hair_front, as the bake draws them on the flat mesh facing the camera
    (no rim light, no back-face darkening, no normal map). `main` is white for a hair without a main
    texture; `gloss` is `_HairGloss`'s red read at hair_gloss_shift. Returns linear rgb.

    The shader reads the gloss a second time 0.008 higher and darkens by the difference; no bake
    shows it, so the model leaves it out."""
    c1, c2, c3 = colors
    col = 1 + color_mask[..., 0:1] * (c1 - 1)
    col = col + color_mask[..., 1:2] * (c2 - col)
    col = col + color_mask[..., 2:3] * (c3 - col)
    base = main * col
    tint = shade(shadow_color, ambient_shadow(light))
    keep = 1 - detail_mask[..., 1:2]
    out = np.minimum(base * (tint + ramp * keep * (1 - tint)) + gloss * (ramp * 0.5 + 0.5), 1)
    extend = np.maximum(np.maximum(ramp, keep), 1 - shadow_extend)
    out = out * (tint + extend * (1 - tint))
    return out * max(light.light * 0.6 + 0.4, light.ambient)


# --- clothes and items: create_topN, main_opaque, main_item -------------------------------------

# The maker's line globals, which no material carries. Fitted to the KK sample's clothes; the two
# trade off (an alpha from 0 to 0.25 with its matching width fits as well), and they only matter
# where the detail mask's blue draws lines.
LINE_COLOR_ALPHA = 0.065  # _LineColorG.a
LINE_WIDTH = 0.32  # _linewidthG


def create_topN(main, alpha, color_mask, patterns, colors, pattern_colors):
    """create_topN (KK clothes): each colour mask channel picks its colour, or its pattern colour
    where its pattern mask is dark. `patterns` are the masks' red (1 where there is no mask), already
    read at `uv * (20 - 19 * scale)`; `pattern_colors` are linear rgb with their alpha last. Returns
    linear rgb and alpha."""
    col = np.ones(3, dtype=F)
    for i, (pattern, color_, pattern_color) in enumerate(zip(patterns, colors, pattern_colors)):
        p = np.maximum(pattern, 1 - pattern_color[3])
        c = pattern_color[:3] + p * (color_ - pattern_color[:3])
        col = col + color_mask[..., i:i + 1] * (c - col)
    return col * np.clip(main, 0, 1), alpha


def pastel(c):
    """ShadeAdjustItem's first step: the hue of `c` at half its saturation, value 1 (HSV)."""
    c = np.asarray(c, dtype=F)
    mx = c.max(-1, keepdims=True)
    chroma = mx - c.min(-1, keepdims=True)
    r, g, b = c[..., 0:1], c[..., 1:2], c[..., 2:3]
    safe = np.maximum(chroma, 1e-10)
    h = np.where(chroma == 0, 0.0, np.where(mx == r, ((g - b) / safe) % 6,
                                           np.where(mx == g, (b - r) / safe + 2, (r - g) / safe + 4))) / 6
    s = chroma / (mx + 1e-10) * 0.5
    k = np.concatenate([h, h - 1 / 3, h + 1 / 3], -1)
    hue = np.clip(np.abs(1 - 2 * (np.abs(k) % 1)) * 3 - 1, 0, 1)
    return 1 + s * (hue - 1)


def item_tint(base, shadow_color, light: Light = KK):
    """ShadeAdjustItem: the shadow tint of an item, from its own colour's hue (`base * shadow
    colour`, pastel, at 0.9) overlaid with the ambient shadow."""
    return shade(0.9 * pastel(base * shadow_color), ambient_shadow(light))


def main_opaque(main, detail_mask, line_mask, floats, shadow_color, ramp, light: Light = KK):
    """KK's main_opaque (clothes) as the bake draws it: a quad facing the camera, the normal map,
    specular and liquid off, the other ramp following the main one. `main` is create_topN's output,
    the masks rgba. Returns linear rgb."""
    tint = item_tint(main, shadow_color, light)
    line_r = line_mask[..., 0:1] + floats.get("_DetailRLineR", 0) * (detail_mask[..., 0:1] - line_mask[..., 0:1])
    line_g = line_mask[..., 1:2] + floats.get("_DetailBLineG", 0) * (detail_mask[..., 2:3] - line_mask[..., 1:2])
    tint = np.clip(np.maximum(1 - line_r, 1 - floats.get("_ShadowExtendAnother", 0)) * tint, 0, 1)
    extend = 1.2 * floats.get("_ShadowExtend", 0)
    e = np.minimum(1 - line_mask[..., 2:3], 1 - detail_mask[..., 1:2]) * extend + 1 - extend
    col = np.clip(main * (tint + ramp * e * (1 - tint)), 0, 1)
    a = LINE_COLOR_ALPHA
    line = np.clip(1 - (2 - 2 * a) * (1 - 0.5 * main * tint) if a > 0.5 else a * main * tint, 0, 1)
    width = (1 - LINE_WIDTH) * 0.89 + 0.01
    out = line + width ** line_g * (col * (tint + e * (1 - tint)) - line)
    return out * max(light.light * 0.6 + 0.4, light.ambient)


def main_item(main, color_mask, detail_mask, line_mask, colors, floats, shadow_color, ramp, light: Light = KK,
              line_blue=1.0, another_ramp=None):
    """KK's main_item (the teeth, the tongue, items) as the bake draws it: the colour mask over the
    main texture (white if none), darkened by the line mask's blue; its own shadow-extend scale; a
    highlight from the detail mask's red squared, which the bake doesn't clear; the lines mixed in
    linearly. `_LineColorG`'s colour is taken as white. KKS's Koikano/main_clothes_item doesn't darken
    by the line mask's blue (`line_blue` 0) and comes close this way.

    Where the red line (or `_AnotherRampFull`) says, `_AnotherRamp` read at n.h stands in for the main
    ramp: the bake reads it at 1 lit and 0 from behind (`another_ramp`, its red at 0 and at 1; without
    one it follows the ramp). The highlight is the lit side's only: from behind n.h is 0, and the
    shader's log(0) times the cleared `_SpecularPower` is a NaN the GPU saturates to 0. Returns linear
    rgb."""
    col = np.ones(3, dtype=F)
    for i, color_ in enumerate(colors):
        col = col + color_mask[..., i:i + 1] * (color_ - col)
    base = main * col * (1 - line_blue * line_mask[..., 2:3])
    line_r = line_mask[..., 0:1] + floats.get("_DetailRLineR", 0) * (detail_mask[..., 0:1] - line_mask[..., 0:1])
    full = line_r + floats.get("_AnotherRampFull", 0) * (1 - line_r)
    k = np.clip(2 - floats.get("_ShadowExtendAnother", 0) - full, 0, 1) * 0.67 + 0.33
    tint = k * item_tint(base, shadow_color, light)
    lit = min(1.0, ramp + light.shadow_floor)
    if another_ramp is not None:
        lit = lit + full * (another_ramp[1] * ramp + another_ramp[0] * (1 - ramp) - lit)
    col = base * (tint + lit * (1 - tint)) + ramp * detail_mask[..., 0:1] ** 2 * (1 - floats.get("_notusetexspecular", 0))
    col = col * max(light.light * 0.6 + 0.4, light.ambient)
    extend = 1.2 * floats.get("_ShadowExtend", 0)
    col = col * (tint + ((1 - detail_mask[..., 1:2]) * extend + 1 - extend) * (1 - tint))
    line_g = line_mask[..., 1:2] + floats.get("_DetailBLineG", 0) * (detail_mask[..., 2:3] - line_mask[..., 1:2])
    a = LINE_COLOR_ALPHA
    line = np.clip(1 - (2 - 2 * a) * (1 - base * tint) if a > 0.5 else 2 * a * tint * base, 0, 1)
    return col + line_g * (line - col)


# --- eyes: create_eye, toon_eye_lod0 ---------------------------------------------------------------

def create_eye(main, color_mask_at_grad, color_, color2, blend):
    """create_eye (KK irises): the colour mask's red (read at the `_grad` UV) picks between the two
    colours, which the texture's red then shades, vivid-light blended by `_Blend`. Alpha is the
    texture's times the colour's."""
    c = color2 + color_mask_at_grad[..., 0:1] * (color_ - color2)
    m = main[..., 0:1]
    safe = np.maximum(m, 1e-6)
    vivid = np.clip(np.where(m > 0.5, c / np.maximum(2 * (1 - m), 1e-6), 1 - (1 - c) * 0.5 / safe), 0, 1)
    return c * m + blend * (vivid - c * m)


def eye_rotation(u, v, rotation):
    """toon_eye_lod0's iris UV: turned about the middle by `_rotation` turns, before the texture's own
    offset and scale."""
    a = rotation * 2 * np.pi
    x, y = u - 0.5, v - 0.5
    return x * np.cos(a) + y * np.sin(a) + 0.5, -x * np.sin(a) + y * np.cos(a) + 0.5


def toon_eye(main, overlay1, overlay2, overcolor1, overcolor2, is_highlight, shadow_color, ramp, light: Light = KK):
    """KK's toon_eye_lod0 as the bake draws it (`_exppower` 0, no expression): the two highlight
    overlays (rgba, read on the second UV map; zero off the eye mesh, where the bake's quad has them
    cleared) over the iris, kept lit in the shadow where they show. `overcolor`s are linear rgb with
    their alpha last. Returns linear rgb and alpha."""
    o1 = overlay1[..., 3:4] * np.asarray(overcolor1, dtype=F)
    o2 = overlay2[..., 3:4] * np.asarray(overcolor2, dtype=F)
    o = np.maximum(o1, o2)
    hl = o[..., 3:4] * is_highlight
    col = main[..., :3] + hl * (o[..., :3] - main[..., :3])
    tint = shade(shadow_color, ambient_shadow(light))
    lit = np.clip(ramp + hl, 0, 1)
    out = np.clip((col * tint + lit * (col - col * tint)) * max(light.light * 0.6 + 0.4, light.ambient), 0, 1)
    return out, np.maximum(main[..., 3:4], hl)[..., 0]


# --- skin: main_skin --------------------------------------------------------------------------------

def skin_tint(col, light: Light = KK):
    """main_skin's shadow tint: the colour's own hue at 0.66 of its saturation (HSV, value 1), at 0.9,
    overlaid with the ambient shadow. Unlike the items' it takes no shadow colour."""
    return shade(0.9 * (1 + (pastel(col) - 1) * (0.66 / 0.5)), ambient_shadow(light))


def nipple_uv(uv1, vertex_red, nip, nip_size):
    """Where main_skin reads `_overtex1` on the body: the second UV map scaled about the nipple by
    `_nipsize` away from its middle, all times the vertex colour's red, when `_nip` is on."""
    reach = np.clip(np.linalg.norm(uv1 - 0.5, axis=-1, keepdims=True) * (1 / 0.06) - 1, 0, 1)
    scaled = uv1 * (2 - 1.4 * nip_size) + (0.7 * nip_size - 0.5)
    moved = uv1 + reach * (scaled - uv1)
    return vertex_red * (uv1 + nip * (moved - uv1))


def skin_overlays(main, overlay1, overlay2, overlay3, colors, floats):
    """main_skin's three overlays over the main texture, on the mesh only (the bake's quad has them
    cleared; pass zeros there): the nipples (`_overtex1`, tinted, with a `_tex1mask` mode), the
    underhair (`_overtex2`) and the face's eyeshadow (`_overtex3`). Overlays are rgba as read;
    `colors` the three `_overcolor`s, linear rgb with their alpha last."""
    c1, c2, c3 = (np.asarray(c, dtype=F) for c in colors)
    o1 = overlay1 * c1
    nipple = overlay1[..., 0:1] * (c1[:3] + overlay1[..., 1:2] * floats.get("_nip_specular", 0) * 0.33)
    o1rgb = o1[..., :3] + np.clip(floats.get("_tex1mask", 0), 0, 1) * (nipple - o1[..., :3])
    col = main + o1[..., 3:4] * (o1rgb - main)
    col = col + overlay2[..., 3:4] * c2[3] * (c2[:3] * overlay2[..., :3] - col)
    return col + overlay3[..., 3:4] * c3[3] * (overlay3[..., :3] * c3[:3] - col)


def main_skin(col, detail_mask, line_mask, floats, ramp, light: Light = KK):
    """KK's main_skin (body, face) as the bake draws it: the quad facing the camera with the normal
    maps, specular, rim and liquid off. `col` is the main texture with the overlays over it. The line
    mask's red and blue are weighted by `_DetailNormalMapScale`; `_LineColorG`'s colour is taken as
    white and the face shadow (`_FaceShadowG`) as at most 1. Returns linear rgb."""
    tint = skin_tint(col, light)
    scale = floats.get("_DetailNormalMapScale", 0)
    extend = 1.2 * floats.get("_ShadowExtend", 0)
    e = np.minimum(1 - line_mask[..., 2:3] * scale, 1 - detail_mask[..., 1:2]) * extend + 1 - extend
    lit = min(1.0, ramp + light.shadow_floor)
    x = col * (tint + lit * e * (1 - tint)) * max(light.light * 0.6 + 0.4, light.ambient)
    x = x * (tint + e * (1 - tint))
    lined = col * tint * ((1 - detail_mask[..., 1:2]) * 0.5 + 0.5)
    a = LINE_COLOR_ALPHA
    line = np.clip(1 - (2 - 2 * a) * (1 - lined) if a > 0.5 else 2 * a * lined, 0, 1)
    shows = np.minimum(1 - 0.5 * line_mask[..., 0:1] * scale, ((1 - LINE_WIDTH) * 0.8 + 0.2) ** line_mask[..., 1:2])
    shows = floats.get("_linetexon", 0) * (shows - 1) + 1
    return line + shows * (x - line)


# --- skin: create_body, create_head -----------------------------------------------------------------

def paint_uv(u, v, p):
    """create_body's and create_head's paint UV: `(uv + p.xy) * 2s + 0.5 - s`, s = 2 - 2 p.w, turned
    about the middle by p.z turns (eye_rotation's sense), before the texture's own transform."""
    s = 2 - 2 * p[3]
    return eye_rotation((u + p[0]) * 2 * s + 0.5 - s, (v + p[1]) * 2 * s + 0.5 - s, p[2])


def mole_uv(u, v, p):
    """create_head's mole (`_hokuro`) UV: paint_uv without the turn."""
    s = 2 - 2 * p[3]
    return (u + p[0]) * 2 * s + 0.5 - s, (v + p[1]) * 2 * s + 0.5 - s


def face_uv(u, v, p):
    """create_head's `_tex4uv` and `_tex5uv` placement: `(uv + p.xy) * s - s + 0.5`, s = 1 - p.zw."""
    su, sv = 1 - p[2], 1 - p[3]
    return (u + p[0]) * su - su + 0.5, (v + p[1]) * sv - sv + 0.5


def _layer(base, texture, color_):
    """A create shader's decal: the texture times the colour over `base`, by the texture's alpha
    times the colour's (rgba, linear rgb with alpha last)."""
    return base + texture[..., 3:4] * color_[3] * (texture[..., :3] * color_[:3] - base)


def create_body(main, color_mask, tan, paint1, paint2, paint_mask, colors):
    """create_body (KK): the skin colour (with the tan lines, `_Texture4`), the colour mask's green
    detail colour, the two paints (by the paint mask's red) and the nails (blue). `colors` maps
    `_Color` to `_Color6`, each linear rgb with its alpha last; textures are rgba as read."""
    c = colors
    t = np.maximum(tan[..., 0:1], 1 - c["_Color4"][3])
    skin = c["_Color4"][:3] + t * (c["_Color"][:3] - c["_Color4"][:3])
    detail = 1 + color_mask[..., 1:2] * c["_Color2"][3] * (c["_Color2"][:3] - 1)
    base = skin * main * detail
    base = base + paint1[..., 3:4] * c["_Color3"][3] * paint_mask[..., 0:1] * (paint1[..., :3] * c["_Color3"][:3] - base)
    base = base + paint2[..., 3:4] * c["_Color6"][3] * paint_mask[..., 0:1] * (paint2[..., :3] * c["_Color6"][:3] - base)
    return base + color_mask[..., 2:3] * (c["_Color5"][:3] * base - base)


def create_head(main, color_mask, texture4, texture5, paint1, paint2, paint_mask, mole, colors):
    """create_head (KK): the skin and detail colours by the colour mask (its blue keeps white), the
    face decals `_Texture4` and `_Texture5`, the two paints by the paint mask's red, and the mole.
    `colors` maps `_Color` to `_Color7`, linear rgb with alpha last."""
    c = colors
    skin = (1 + color_mask[..., 0:1] * (c["_Color"][:3] - 1)) * (1 + color_mask[..., 1:2] * (c["_Color2"][:3] - 1))
    base = np.maximum(color_mask[..., 2:3], skin) * main
    base = _layer(base, texture4, c["_Color4"])
    base = _layer(base, texture5, c["_Color5"])
    base = base + paint1[..., 3:4] * c["_Color3"][3] * paint_mask[..., 0:1] * (paint1[..., :3] * c["_Color3"][:3] - base)
    base = base + paint2[..., 3:4] * c["_Color7"][3] * paint_mask[..., 0:1] * (paint2[..., :3] * c["_Color7"][:3] - base)
    return _layer(base, mole, c["_Color6"])


# --- emblems: main_emblem -------------------------------------------------------------------------

def main_emblem(main, ramp, light: Light = KK):
    """KK's main_emblem (clothes emblems) as the bake draws it: the texture shaded by its own hue's
    tint (ShadeAdjustItem's, at 0.8 instead of 0.9, no shadow colour). It reads `_ambientshadow`,
    not `_ambientshadowG`; `light` gives it. Opaque where round(alpha ^ 0.3) is 1. Returns linear rgb."""
    tint = shade(0.8 * pastel(main), ambient_shadow(light))
    return (main * tint + ramp * (main - main * tint)) * max(light.light * 0.6 + 0.4, light.ambient)


# --- clothes: main_alpha ----------------------------------------------------------------------------

def main_alpha(main, detail_mask, floats, specular_color, shadow_color, ramp, light: Light = KK):
    """KK's main_alpha (see-through clothes) as the bake draws it: the quad facing the camera with
    the normal map, liquid and `_SpecularPower` off. The detail mask's red squared still adds the
    specular colour (half of it in shadow), its green holds the light off, and its blue (inverted,
    times `_DetailBLineGA`) draws the lines. Returns linear rgb; the alpha is the texture's."""
    tint = item_tint(main, shadow_color, light)
    keep = 1 - detail_mask[..., 1:2]
    lit = ramp * keep
    m = np.clip(main + detail_mask[..., 0:1] ** 2 * np.asarray(specular_color, dtype=F) * (0.5 + 0.5 * lit), 0, 1)
    col = m * (tint + lit * (1 - tint))
    held = np.maximum(np.maximum(1 - floats.get("_ShadowExtend", 0), ramp), keep)
    col = col * (tint + held * (1 - tint)) * max(light.light * 0.6 + 0.4, light.ambient)
    a = LINE_COLOR_ALPHA
    line = np.clip(1 - (2 - 2 * a) * (1 - main * tint) if a > 0.5 else 2 * a * main * tint, 0, 1)
    shows = ((1 - LINE_WIDTH) * 0.89 + 0.01) ** ((1 - detail_mask[..., 2:3]) * floats.get("_DetailBLineGA", 0))
    return line + shows * (col - line)


# --- SVS: the LIF shaders under URP -----------------------------------------------------------
#
# SVS (Unity 2021, URP) bakes with its own camera, so no post-processing grade: a bake is
# `srgb(out)`. Its light isn't a ramp end: the maker's directional light is turned to two fixed
# rotations, and the shaders read its colour, N.L, the light probe's ambient and any additional
# lights. `SvsLight` holds what one bake sees, read by the exporter's `probe_bake` request.

@dataclass(frozen=True)
class SvsLight:
    """What a LIF shader sees in one SVS bake: `_MainLightColor.rgb`, N.L on the flat quad (its
    normal faces the camera), the light probe's spherical harmonics evaluated at that normal
    (`SampleSH`, before its clamps), the additional lights' summed colour times N.L, and the main
    light's shadow attenuation (1: unshadowed)."""

    color: tuple[float, float, float]
    ndl: float
    ambient: tuple[float, float, float]
    additional: tuple[float, float, float] = (0.0, 0.0, 0.0)
    shadow: float = 1.0
    xy: tuple[float, float] = (0.0, 0.0)  # the direction toward the light along x and y (_MainLightPosition)


def sh_eval(sh, n):
    """A Unity SphericalHarmonicsL2 (27 floats, by colour then coefficient) at the unit normal `n`,
    as URP's SampleSH reads it: the stored coefficients are the shader's constants, rearranged."""
    c = np.asarray(sh, dtype=F).reshape(3, 9)
    x, y, z = n
    basis = np.array([1, y, z, x, x * y, y * z, 3 * z * z - 1, x * z, x * x - y * y], dtype=F)
    return c @ basis


# The SVS maker's scene during a bake, read by the exporter's `probe_bake` request on the Sample
# Card (2026-11-17): RenderSettings.ambientProbe (trilight sky, equator and ground at 1.3, no light
# probes in the scene, no reflection cubemap), `_MainLightColor` (1, 1, 1), no additional lights, and
# the light's direction for `light` and `dark` against the bake quad's normal, +z.
SVS_AMBIENT_PROBE = (
    0.18112286925315857, -0.04479600861668587, 0, 0, 0, 0, 0.0037154555320739746, 0, 0.01114637590944767,
    0.17080028355121613, 0.0020581278949975967, 0, 0, 0, 0, 0.005328360944986343, 0, 0.015985094010829926,
    0.18112288415431976, 0.04479600861668587, 0, 0, 0, 0, 0.0037154555320739746, 0, 0.01114637590944767,
)
SVS_QUAD_AMBIENT = tuple(float(v) for v in sh_eval(SVS_AMBIENT_PROBE, (0.0, 0.0, 1.0)))
SVS_LIGHT = SvsLight(color=(1.0, 1.0, 1.0), ndl=0.828421950340271, ambient=SVS_QUAD_AMBIENT,
                     xy=(0.3629303574562073, 0.4266132414340973))
SVS_DARK = SvsLight(color=(1.0, 1.0, 1.0), ndl=-0.9444175958633423, ambient=SVS_QUAD_AMBIENT,
                    xy=(0.05610156059265137, 0.32392600178718567))


def _smooth01(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def _rgb_hsv(c):
    """Amplify's RGBToHSV, as the shaders compile it: hue (0..1), saturation and value."""
    c = np.asarray(c, dtype=F)
    r, g, b = c[..., 0], c[..., 1], c[..., 2]
    step = (g >= b)[..., None]
    p = np.where(step, np.stack([g, b, np.zeros_like(r), np.full_like(r, -1 / 3)], -1),
                 np.stack([b, g, np.full_like(r, -1.0), np.full_like(r, 2 / 3)], -1))
    step = (r >= p[..., 0])[..., None]
    q = np.where(step, np.stack([r, p[..., 1], p[..., 2], p[..., 0]], -1),
                 np.stack([p[..., 0], p[..., 1], p[..., 3], r], -1))
    d = q[..., 0] - np.minimum(q[..., 3], q[..., 1])
    return np.abs(q[..., 2] + (q[..., 3] - q[..., 1]) / (6 * d + 1e-10)), d / (q[..., 0] + 1e-10), q[..., 0]


def _hsv_rgb(h, s, v):
    """Amplify's HSVToRGB."""
    k = np.stack([h + 1, h + 2 / 3, h + 1 / 3], axis=-1)
    p = np.clip(np.abs(np.mod(k, 1.0) * 6 - 3) - 1, 0, 1)
    return v[..., None] * (1 + s[..., None] * (p - 1))


def _overlay(a, b):
    """`b > 0.5 ? 1 - 2(1 - b)(1 - a) : 2ab`, clamped."""
    return np.clip(np.where(b > 0.5, 1 - 2 * (1 - b) * (1 - a), 2 * a * b), 0, 1)


def svs_baked(out):
    """A LIF model's linear output as the bundle's light or dark PNG holds it: no grade."""
    return srgb(out)


# The bluish constant LIF/lif_main_eyebrow (and its family) tints its shadow colour by.
SVS_SHADOW_TINT = np.array([0.686577916, 0.797912478, 1.0], dtype=F)


def svs_shadow_tint(col):
    """The shadow colour the LIF face-part shaders make from a colour: the hue and saturation of
    `(col + K) * K`, the saturation square-rooted, at the value of `col * K` (K = SVS_SHADOW_TINT)."""
    h, s, _ = _rgb_hsv((col + SVS_SHADOW_TINT) * SVS_SHADOW_TINT)
    _, _, v = _rgb_hsv(col * SVS_SHADOW_TINT)
    return _hsv_rgb(h, np.sqrt(s), v)


def svs_face_part_light(col, shadow_power, light: SvsLight, cap=1.0):
    """The light the LIF face-part shaders (eyebrow, eyelash) multiply their colour by: a lit term
    from the light and ambient, a shadow term overlaying the tinted shadow colour on the ambient,
    blended by how far the normal turns from the light, plus any light over 1 and the additional
    lights. `cap` caps how far into the shadow colour (the eye's `1 - 0.2 * highlights`). Returns
    rgb, per pixel when `col` is."""
    L = np.asarray(light.color, dtype=F)
    sh = np.minimum(np.maximum(np.asarray(light.ambient, dtype=F), 0), 1)
    mean_light = L.sum() / 3
    l5 = L * 0.75 + 0.25
    luma = l5 @ np.array([0.299, 0.587, 0.114])
    lit = np.clip(sh * 0.5 + l5 + (mean_light - 1) * -0.1 * (luma - l5), 0, 1)
    shadow_col = np.minimum(_overlay(np.clip(l5, 0, 1) * svs_shadow_tint(col), sh * 0.6 + 0.3) + sh * 0.1, 1)
    shadowed = _smooth01((0.8 - light.shadow) / 0.6)
    lit_attenuation = _smooth01((light.shadow - 0.2) / 0.6)
    over = min(max(mean_light, 1.0), 99.0)
    t = max(1 - light.ndl, shadowed) * over - 0.5 * (over - 1)
    mean_ambient = min(float(np.maximum(np.asarray(light.ambient, dtype=F), 0).mean()), 1.0)
    p = (0.75 - 0.65 * mean_ambient) + shadow_power * ((0.9 - 0.4 * mean_ambient) - (0.75 - 0.65 * mean_ambient))
    t = np.minimum(max(float(np.clip(1 - mean_light, 0, 1)), p * t), cap)
    t = np.asarray(t, dtype=F)[..., None] if np.ndim(t) else t
    mixed = lit + t * (shadow_col - lit)
    back = float(np.clip((0.2 - light.ndl) / 0.15, 0, 1))
    excess = np.clip(L - 1, 0, 99) * min(1 - back, lit_attenuation)
    return mixed + excess + np.asarray(light.additional, dtype=F)


def svs_face_part(tex, colors, floats, light: SvsLight, *, names, by_alpha, cut):
    """LIF/lif_main_eyebrow and lif_main_eyelash_up: the texture's red, green and blue pick the 2nd,
    3rd and 4th of `names` (each by its alpha, and with `by_alpha` by the texture's) over the 1st,
    tinted toward the light by `_Ligjht_influence`, then lit as `svs_face_part_light`. `colors` are
    linear rgb with their alpha last. Returns linear rgb and alpha (the texture's, 0 below `cut`)."""
    a = tex[..., 3:4]
    w = a if by_alpha else 1.0
    c1, c2, c3, line = (np.asarray(colors[k], dtype=F) for k in names)
    col = c1[:3] + tex[..., 0:1] * c2[3] * w * (c2[:3] - c1[:3])
    col = col + tex[..., 1:2] * c3[3] * w * (c3[:3] - col)
    col = col + tex[..., 2:3] * line[3] * w * (line[:3] - col)
    L = np.asarray(light.color, dtype=F)
    col = np.clip(col + 0.7 * floats.get("_Ligjht_influence", 0) * (L * col - col), 0, 1)
    out = np.clip(col * svs_face_part_light(col, floats.get("_Shadow_power", 0), light), 0, 1.05)
    return out, np.where(a[..., 0] >= cut, a[..., 0], 0)


def lif_main_eyebrow(tex, colors, floats, light: SvsLight):
    """LIF/lif_main_eyebrow: `tex` is `_eyebrow_texture` read at `eyebrow_uv`."""
    return svs_face_part(tex, colors, floats, light, by_alpha=True, cut=0.5,
                         names=("_eyebrow_color01", "_eyebrow_color02", "_eyebrow_color03", "_Line_color"))


def eyelash_texture(up, down):
    """LIF/lif_main_eyelash_up's texture: the lower eyelash's over the upper's by its alpha, with the
    larger alpha."""
    rgb = up[..., :3] + down[..., 3:4] * (down[..., :3] - up[..., :3])
    return np.concatenate([rgb, np.maximum(up[..., 3:4], down[..., 3:4])], axis=-1)


def lif_main_eyelash_up(tex, colors, floats, light: SvsLight):
    """LIF/lif_main_eyelash_up: `tex` is `eyelash_texture` of its two textures. Drawn where the alpha
    is at least 0.9."""
    return svs_face_part(tex, colors, floats, light, by_alpha=False, cut=0.9,
                         names=("_Eyelash_color01", "_Eyelash_color02", "_Eyelash_color03", "_Line_color"))


def eyebrow_uv(u, v, length, width):
    """Where LIF/lif_main_eyebrow reads its texture: stretched along u by `_BrowLength` (two
    formulas, picked by rounding it) and along v by `_BrowWidth`. Both 0.5 is the texture as it is."""
    a, b = 2 - 2 * length, 1.2 - 0.4 * length
    su = a + np.round(length) * (b - a)
    sv = 1.3 - 0.6 * width
    return u * su - 0.2 * (su - 1), v * sv - 0.5 * (0.3 - 0.6 * width)



# --- SVS eyes: lif_main_eye ---------------------------------------------------------------------

def _lerp(a, b, t):
    return a + t * (b - a)


def _turn(x, y, angle):
    c, s = np.cos(angle), np.sin(angle)
    return x * c + y * s, -x * s + y * c


def bake_view(u, v):
    """The view direction LIF/lif_main_eye's parallax reads on the bake quad, in tangent space: the
    camera at (0.5, 0.5, 1) over the quad at (1 - u, v, 0), whose tangent is -x and bitangent +y.
    Returns its x / (z + 0.42) and y / (z + 0.42), as the shader offsets by them."""
    x, y, z = 0.5 - u, 0.5 - v, np.ones_like(u)
    n = np.sqrt(x * x + y * y + 1)
    x, y, z = x / n, y / n, z / n
    return x / (z + 0.42), y / (z + 0.42)


def eye_uvs(u, v, floats, vectors):
    """Where LIF/lif_main_eye reads each texture: the UV turned by `_rotation` about the iris centre
    (`_Eye_position.zw + _Eye_position_add.zw`), then scaled about it for the gradient, iris, pupil
    and highlights, with the parallax offsets. Returns a dict of (u, v) pairs by texture, and the
    view offsets for the parallax."""
    f = floats
    ep, epa = (np.asarray(vectors[k], dtype=F) for k in ("_Eye_position", "_Eye_position_add"))
    c = epa[2:4] + ep[2:4]
    turn = _lerp(1 - f["_rotation"], f["_rotation"], f["_Eye_postion_rebers"])
    px, py = _turn(u - (0.5 - c[0]), v - (0.5 - c[1]), (turn * 0.1 - 0.05000001) * 2 * np.pi)
    px, py = px + 0.5 - c[0], py + 0.5 - c[1]
    ox, oy = bake_view(u, v)
    sx, sy = (ep[0] + f["_Eye_open"]) * epa[0], (ep[1] + f["_Eye_open"]) * epa[1]
    gx, gy = sx + 1 - 2 * f["_Grade_size"], sy + 1 - 2 * f["_Grade_size"]
    out = {"grade": ((c[0] + px) * gx - gx / 2 + 0.5,
                     (f["_Grade_position"] * 0.65 + ep[3] + py - 0.25) * gy - gy / 2 + 0.5)}
    qx, qy = (c[0] + px) * sx - sx / 2 + 0.5, (c[1] + py) * sy - sy / 2 + 0.5
    r = np.minimum(np.hypot(qx - 0.5, qy * 0.6 - 0.3) * 4 + 0.18, 1)
    depth = (r * 0.2 - 0.2) * (f["_Parallax"] - 0.5)
    out["iris"] = (qx + depth * ox, qy + depth * oy)
    ps = np.asarray(vectors["_Pipil_size"], dtype=F)[:2] + f["_Eye_open"]
    near = 0.05 - 0.1 * f["_Parallax"]
    out["pupil"] = ((c[0] + px) * ps[0] - ps[0] / 2 + near * ox + 0.5, (c[1] + py) * ps[1] - ps[1] / 2 + near * oy + 0.5)
    far = 0.1 * f["_Parallax"] - 0.05
    for k in (1, 2, 3):
        hp = np.asarray(vectors[f"_Highlight_0{k}_position"], dtype=F)
        hx, hy = hp[2] * 0.5 + c[0] + px, hp[3] * 0.5 + c[1] + py
        w, h = hp[0] * epa[0], hp[1] * epa[1]
        hx, hy = _turn(hx * w - w / 2, hy * h - h / 2, (f[f"_Highlight_0{k}_rotation"] - 0.5) * 2 * np.pi)
        out[f"highlight{k}"] = (hx + far * ox + 0.5, hy + far * oy + 0.5)
    return out


def lif_main_eye(textures, colors, floats, light: SvsLight):
    """LIF/lif_main_eye: the eye white from `_Shadow_mask` and its two colours, and over it by the
    iris mask's alpha the iris (two colours by its red, a linear-light third by its green), the pupil's
    three colours and lines, the gradient's soft light, then three highlights and their lines, lit
    as `svs_face_part_light` capped by the highlights. `textures` hold each texture read at its
    `eye_uvs` place (None for a missing one, which reads black and transparent); `colors` linear rgb
    with alpha last.

    Returns the lit eye, the lit eye white alone, and the eye white's coverage as the exporter
    measures it for the pupil layer (ADR 0034, LightBake.Pupil): the eye lit with its eye white
    black and white, their difference over the lit white."""
    col = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    shape = textures["shadow_mask"].shape[:2]
    tex = {k: (np.zeros(shape + (4,)) if t is None else t) for k, t in textures.items()}
    mk = tex["shadow_mask"]
    w1, w2 = col["_Eye_white_color_01"], col["_Eye_white_color_02"]
    white = _lerp(w1[:3], mk[..., :3] * w2[:3], (mk[..., 3] * w2[3])[..., None])
    em, pp, gr = tex["iris"], tex["pupil"], tex["grade"]
    iris = _lerp(col["_Eye_color_01"][:3], col["_Eye_color_02"][:3], (em[..., 0] * col["_Eye_color_02"][3] * em[..., 3])[..., None])
    e3 = col["_Eye_color_03"]
    iris = np.clip(_lerp(iris, iris + 2 * e3[:3] - 1, (em[..., 1] * e3[3] * em[..., 3])[..., None]), 0, 1)
    c = _lerp(iris, col["_Piple_color_01"][:3], (pp[..., 3] * col["_Piple_color_01"][3])[..., None])
    for k, ch in ((2, 0), (3, 1)):
        c = _lerp(c, col[f"_Piple_color_0{k}"][:3], (pp[..., ch] * col[f"_Piple_color_0{k}"][3] * pp[..., 3])[..., None])
    line = col["_Line_color"]
    c = _lerp(c, line[:3], (pp[..., 2] * line[3] * pp[..., 3] + line[3] * em[..., 2])[..., None])
    g, ga = gr[..., :3] * col["_Grade_color"][:3], gr[..., 0] * col["_Grade_color"][3]
    c = np.clip(_lerp(c, 2 * c * g + c * c * (1 - 2 * g), ga[..., None]), 0, 1)
    hs = [tex[f"highlight{k}"] for k in (1, 2, 3)]
    ha = [col[f"_Highlight_color_0{k}"][3] for k in (1, 2, 3)]
    amount = np.clip(sum(ha[k] * hs[k][..., 3] for k in range(3)), 0, 1) * floats["_Highlight_power"]
    lines = sum(ha[k] * hs[k][..., 2] * line[3] * hs[k][..., 3] for k in range(3))
    cap = 1 - 0.2 * np.clip(sum(h[..., 3] for h in hs), 0, 1)
    power = floats["_Shadow_power"]

    def lit(under):
        """The eye over the eye white `under`, lit."""
        eye = _lerp(under, c, em[..., 3:4])
        top = eye
        for k, h in enumerate(hs):
            top = _lerp(top, col[f"_Highlight_color_0{k + 1}"][:3], (h[..., 3] * ha[k])[..., None])
        top = _lerp(top, line[:3], lines[..., None])
        eye = _lerp(eye, top, amount[..., None])
        return np.clip(eye * svs_face_part_light(eye, power, light, cap), 0, 1.05)

    out = lit(white)
    white_out = np.clip(white * svs_face_part_light(white, power, light), 0, 1.05)
    one = np.ones(3, dtype=F)
    lit_white = np.minimum(one * svs_face_part_light(one, power, light), 1)
    uncovered = (np.minimum(lit(np.ones_like(white)), 1) - np.minimum(lit(np.zeros_like(white)), 1)) / lit_white
    return out, white_out, 1 - np.clip(uncovered.mean(axis=-1), 0, 1)


def pupil_layer(out, white, coverage):
    """The exporter's pupil layer from the eye and its eye white alone (LightBake.Pupil): the colour
    that, laid over the eye white with `coverage` in linear light, gives back the eye."""
    a = coverage[..., None]
    return np.where(a > 0, np.clip((out - (1 - a) * white) / np.maximum(a, 1e-6), 0, 1), white)


# --- SVS hair: lif_main_hair ----------------------------------------------------------------------

def hair_ramp_uv(detail1, light: SvsLight):
    """Where LIF/lif_main_hair reads its ramp (`_Lamp`, along its diagonal) for the bake quad, whose
    normal has no y: by N.L, and by N.L * 0.4 + 0.3, each pulled toward 0 by `_md_01`'s green."""
    k = 1 - 0.5 * detail1[..., 1]
    return (np.clip(k * np.clip(light.ndl, 0, 1), 0, 1),
            np.clip(k * np.clip(light.ndl * 0.4 + 0.3, 0, 1), 0, 1))


def lif_main_hair(color_mask, detail1, detail2, ramp1, ramp2, colors, floats, light: SvsLight):
    """LIF/lif_main_hair as the bake draws it: the colour mask's green and blue pick `_Sub_color_02`
    and `_Sub_color_01` over `_Main_color`, `_md_02`'s blue `_Add_skin_color`, and with their switches
    the mask's alpha (smoothstepped) `_Ex_hair_color2` and its red `_Ex_hair_color`; clamped to 0.95.
    It is lit by a mix of the light (with half the ambient) and the shadow colour (`_Shadow_color`
    overlaid on the ambient, or `_ShadowColor`), by how far the ramp says (`ramp1`, `ramp2` read at
    hair_ramp_uv). The rim, the reflection and the highlight (its texture cleared to black) give
    nothing on the bake quad. Returns linear rgb."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    f = floats
    col = _lerp(c["_Main_color"][:3], c["_Sub_color_02"][:3], (color_mask[..., 1] * c["_Sub_color_02"][3])[..., None])
    col = _lerp(col, c["_Sub_color_01"][:3], (color_mask[..., 2] * c["_Sub_color_01"][3])[..., None])
    col = _lerp(col, c["_Add_skin_color"][:3], (detail2[..., 2] * c["_Add_skin_color"][3])[..., None])
    if f.get("_Ex_hair_color2_onoff"):
        s = _smooth01((color_mask[..., 3] - 0.05) / 0.9) - 1
        col = _lerp(col, c["_Ex_hair_color2"][:3], (np.clip(-2 * s, 0, 1) * c["_Ex_hair_color2"][3])[..., None])
    if f.get("_Ex_hair_color_onoff"):
        col = _lerp(col, c["_Ex_hair_color"][:3], (color_mask[..., 0] * c["_Ex_hair_color"][3])[..., None])
    col = np.clip(col, 0, 0.95)
    L = np.asarray(light.color, dtype=F)
    sh = np.clip(np.asarray(light.ambient, dtype=F), 0, 1)
    mean = L.sum() / 3
    lum = min(max(float(L @ np.array([0.212672904, 0.715152204, 0.0721750036])), 1.0), 99.0)
    power = f["_Shadow_power"]
    p = sh.sum() * -0.1 + 0.5 + 0.4 * power
    p = p + f.get("_ShadowColorON", 0) * (power - p)
    ramp = np.clip(np.maximum(ramp2[..., 2] * power * 0.5, ramp1[..., 1]) + detail1[..., 1], 0, 1)
    t = np.clip(p * (np.maximum(ramp, np.clip(1 - mean, 0, 1)) * lum - 0.75 * (lum - 1)), 0, 1)
    l5 = L * 0.75 + 0.25
    luma = l5 @ np.array([0.299, 0.587, 0.114])
    lit = l5 + (mean - 1) * -0.25 * (luma - l5) + sh * 0.5
    shadow = _overlay(np.clip(l5, 0, 1) * c["_Shadow_color"][:3], sh * 0.7 + 0.1)
    shadow = _lerp(shadow, c["_ShadowColor"][:3], f.get("_ShadowColorON", 0))
    return np.clip(col * _lerp(lit, shadow, t[..., None]), 0, 1.1)


# --- SVS accessories, teeth, tongue: lif_main_acs ------------------------------------------------

def acs_pattern_uv(u, v, floats, k):
    """Where LIF/lif_main_acs reads pattern mask `k`: scaled by `_PatternScale_0k` (times the UV aspect,
    remapped from 0..1 to `_PatternRemapMin`..`Max`), moved by twice `_PatternOffset_0k` and turned by
    `_PatternRotator_0k` about the centre; with `_patternclampk` the place wraps into the tile."""
    f = floats
    span = f["_PatternRemapMax"] - f["_PatternRemapMin"]
    su = min(max(f[f"_PatternScale_0{k}u"] * f["_UVAspectRatioU"] * span + f["_PatternRemapMin"], 0), 999)
    sv = min(max(f[f"_PatternScale_0{k}v"] * f["_UVAspectRatioV"] * span + f["_PatternRemapMin"], 0), 999)
    x = u * su + 2 * f[f"_PatternOffset_0{k}u"] - 1 - 0.5 * su
    y = v * sv + 2 * f[f"_PatternOffset_0{k}v"] - 1 - 0.5 * sv
    x, y = _turn(x, y, (f[f"_PatternRotator_0{k}"] - 0.5) * 2 * np.pi)
    x, y = x + 0.5, y + 0.5
    c = f.get(f"_patternclamp{k}", 0)
    wrapped = (np.mod(np.clip(x, 0, 1), 1.0), np.mod(np.clip(y, 0, 1), 1.0))
    inside = np.minimum(np.ceil(x), np.ceil(y))
    return x + c * (wrapped[0] - x), y + c * (wrapped[1] - y), 1 + c * (inside - 1)


def _saturation(c):
    mx = c.max(axis=-1)
    return (mx - c.min(axis=-1)) / (mx + 1e-10)


def acs_color(mask, patterns, main, colors, inside1=1.0):
    """LIF/lif_main_acs's colour: each colour mask channel picks `_Main_color_0k` over `_Main_color_04`,
    with pattern k (where the mask's alpha is at least 0.5) tinting toward `_Sub_color_0k` times the
    pattern, or toward the pattern itself where it is saturated; then times the main texture. Returns
    linear rgba."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    on = (mask[..., 3] >= 0.5).astype(F)
    rgb = c["_Main_color_04"][:3]
    a = np.full(mask.shape[:2], c["_Main_color_04"][3])
    for k, ch in ((1, 0), (2, 1), (3, 2)):
        pm = patterns[k - 1]
        w = pm[..., 3] * (inside1 if k == 1 else 1.0)
        main_k, sub = c[f"_Main_color_0{k}"], c[f"_Sub_color_0{k}"]
        amount = on * w
        layer = _lerp(main_k[:3], sub[:3] * pm[..., :3], (amount * sub[3])[..., None])
        vivid = amount * np.clip(_saturation(pm[..., :3]) * 10 - 0.05, 0, 1) * sub[3]
        layer = _lerp(layer, pm[..., :3], vivid[..., None])
        rgb = _lerp(rgb, layer, mask[..., ch:ch + 1])
        a = _lerp(a, main_k[3], mask[..., ch])
    return np.concatenate([rgb, a[..., None]], axis=-1) * main


def svs_item_shadow_tint(c):
    """The shadow colour the LIF item shaders (accessories, clothes) make from a colour `c` (the colour
    times 0.95): its hue at saturation clamp(2 - 2v + sqrt(s), 0, 0.9) and value 0.99 v sqrt(1 - s),
    pulled toward (0.095, 0.413, 1) where the colour is blue or dull."""
    h, s, v = _rgb_hsv(c)
    root = np.sqrt(s)
    sat = np.clip(2 - 2 * v + root, 0, 0.9)
    tint = _hsv_rgb(h, sat, np.sqrt(1 - s) * v * 0.99)
    blue = np.clip(np.clip(c @ np.array([0.0642824322, 0.257129729, 0.964236498]) * 10 - 7.5, 0, 1) + 1 - root, 0, 1)
    return _lerp(tint, np.array([0.0953074992, 0.413035095, 1.0]), blue[..., None])


# The shadow tint the LIF item shaders' skin-face variant (`_TypeSelect` 3, the teeth) uses in place
# of svs_item_shadow_tint.
SVS_SKIN_FACE_TINT = np.array([0.357276797, 0.0573572218, 0.0388724506], dtype=F)


def svs_item_t(detail, ramp1, ramp2, floats, light: SvsLight):
    """How far into the shadow colour the LIF item and skin shaders go: the ramp (`ramp1`'s green times
    `_ShadowSetting.x`, `ramp2`'s blue times `_Shadow_power` and `.y`, plus the detail mask's green times
    `.w`) against the light's mean and luminance, weighted by `_Shadow_power`; then `_shadowextend`
    pushes the detail mask's green further in."""
    f = floats
    ss = np.asarray(f.get("_ShadowSetting", (1, 0, 0, 0)), dtype=F)
    L = np.asarray(light.color, dtype=F)
    sh = np.clip(np.asarray(light.ambient, dtype=F), 0, 1)
    mean = L.sum() / 3
    lum = min(max(float(L @ np.array([0.212672904, 0.715152204, 0.0721750036])), 1.0), 99.0)
    power = f["_Shadow_power"]
    p = sh.sum() * -0.1 + 0.5 + 0.4 * power
    p = p + f.get("_ShadowColorON", 0) * (power - p)
    d = detail[..., 1]
    ramp = np.clip(np.maximum(ramp1[..., 1] * ss[0], ramp2[..., 2] * power * ss[1]) + d * ss[3], 0, 1)
    t = np.clip(p * (np.maximum(ramp, np.clip(1 - mean, 0, 1)) * lum - 0.75 * (lum - 1)), 0, 1)
    return t + np.clip(d * f.get("_shadowextend", 0), 0, 1)


def svs_item_mix(t, tint, colors, floats, light: SvsLight):
    """The light the LIF item and skin shaders give: the lit term (the light desaturated toward its
    luma as it dims, plus half the ambient) toward the shadow colour (`tint` overlaid on the ambient,
    or `_ShadowColor`) by `t`. Returns rgb."""
    L = np.asarray(light.color, dtype=F)
    sh = np.clip(np.asarray(light.ambient, dtype=F), 0, 1)
    mean = L.sum() / 3
    l5 = L * 0.75 + 0.25
    luma = l5 @ np.array([0.299, 0.587, 0.114])
    lit = l5 + (mean - 1) * -0.25 * (luma - l5) + sh * 0.5
    shadow = _overlay(np.clip(l5, 0, 1) * tint, sh * 0.7 + 0.1)
    shadow = _lerp(shadow, np.asarray(colors["_ShadowColor"], dtype=F)[:3], floats.get("_ShadowColorON", 0))
    return _lerp(lit, shadow, np.asarray(t)[..., None])


def svs_item_light(col95, detail, ramp1, ramp2, floats, colors, light: SvsLight):
    """The light the LIF item shaders give a colour: `svs_item_mix` at `svs_item_t`, the shadow colour
    from `svs_item_shadow_tint` (`SVS_SKIN_FACE_TINT` for `_TypeSelect` 3). `col95` is the colour
    times 0.95. Returns rgb."""
    tint = SVS_SKIN_FACE_TINT if floats.get("_TypeSelect") == 3 else svs_item_shadow_tint(col95)
    return svs_item_mix(svs_item_t(detail, ramp1, ramp2, floats, light), tint, colors, floats, light)


def item_ramp_uv(detail, floats, light: SvsLight):
    """Where the LIF item shaders read their ramp: as `hair_ramp_uv`, pulled toward 0 by the detail
    mask's green times `_ShadowSetting.b`."""
    k = 1 - detail[..., 1] * np.asarray(floats.get("_ShadowSetting", (1, 0, 0, 0)), dtype=F)[2]
    return (np.clip(k * np.clip(light.ndl, 0, 1), 0, 1),
            np.clip(k * np.clip(light.ndl * 0.4 + 0.3, 0, 1), 0, 1))


def lif_main_acs(rgba, mask, detail, ramp1, ramp2, colors, floats, light: SvsLight):
    """LIF/lif_main_acs as the bake draws it, from its colour (`acs_color`): lit by `svs_item_light`,
    with the line colour (`_Line_color` by `_Line_power`, kept off by the mask's channels times
    `_LineColorIntensityk`) where the colour's alpha is low and along the detail mask's red. The rim,
    the matcaps and the specular (`_Smoothness`) give nothing on the bake quad. Returns linear rgb."""
    f = floats
    c95 = rgba[..., :3] * 0.95
    col = np.clip(c95, 0, 0.95)
    line = np.asarray(colors["_Line_color"], dtype=F)[:3]
    lc = _lerp(c95, line, f.get("_Line_power", 1))
    for k, ch in ((1, 0), (2, 1), (3, 2)):
        lc = _lerp(lc, c95, (mask[..., ch] * f.get(f"_LineColorIntensity{k}", 0))[..., None])
    lc = np.clip(lc, 0, 0.95)
    lit = col * svs_item_light(c95, detail, ramp1, ramp2, f, colors, light)
    shown = _lerp(lc, lit, rgba[..., 3:4])
    w = f.get("_LineWidthS", 0) * f.get("_Line_width", 0) * f.get("_LineWidthSS", 1)
    amount = np.minimum(np.clip(detail[..., 0] * (w * 3.9 + 0.1) + w * 0.35 - 0.35, 0, 0.9), f.get("_Line_texture_onoff", 0))
    base = shown if f.get("_AlphaLine", 0) else lit
    return np.maximum(np.clip(_lerp(base, lc, amount[..., None]), 0, 0.95), 0)


# --- SVS clothes: lif_main_cloth -----------------------------------------------------------------

def cloth_color(create, mask, detail2, colors, floats):
    """LIF/lif_main_cloth's colour: its composited texture (`_Create_main_texture`, the create shader's
    output), times the colour mask's colours when `_Main_color_switchtest` is on, toward
    `_Color_Cuvature` by `_Detail_mask_02`'s red. The liquid effects (off on a maker Character) are
    left out. Returns linear rgb."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    col = create[..., :3]
    if floats.get("_Main_color_switchtest"):
        m = _lerp(c["_Main_color_04"][:3], c["_Main_color_01"][:3], mask[..., 0:1])
        m = _lerp(m, c["_Main_color_02"][:3], mask[..., 1:2])
        col = col * _lerp(m, c["_Main_color_03"][:3], mask[..., 2:3])
    cuv = c["_Color_Cuvature"]
    return _lerp(col, cuv[:3], (detail2[..., 0] * cuv[3])[..., None])


def cloth_ramp_uv(detail1, detail2, floats, light: SvsLight):
    """Where LIF/lif_main_cloth reads its ramp: as `item_ramp_uv`, each lifted by `_Detail_mask_02`'s
    red times `_RimScale` (the second by half of it, after the pull)."""
    k = 1 - detail1[..., 1] * np.asarray(floats.get("_ShadowSetting", (1, 0, 0, 0)), dtype=F)[2]
    lift = detail2[..., 0] * floats.get("_RimScale", 0)
    return (np.clip(k * np.clip(np.clip(light.ndl, 0, 1) + lift, 0, 1), 0, 1),
            np.clip(lift * 0.5 + k * np.clip(light.ndl * 0.4 + 0.3, 0, 1), 0, 1))


def lif_main_cloth(col, create_alpha, detail1, ramp1, ramp2, colors, floats, light: SvsLight):
    """LIF/lif_main_cloth as the bake draws it, from its colour (`cloth_color`): lit as
    `svs_item_light` (its shadow tinted from the colour itself), the line colour (`_Line_color` by
    `_Line_power * 0.8 + 0.2`) where the composited texture's alpha rounds to 0 (with `_AlphaLine`)
    and by `_Detail_mask_01`'s red squared. Rim and reflection give nothing on the bake quad. Returns
    linear rgb."""
    f = floats
    shown = np.clip(col, 0, 0.95)
    line = np.clip(_lerp(col, np.asarray(colors["_Line_color"], dtype=F)[:3], f.get("_Line_power", 1) * 0.8 + 0.2), 0, 0.95)
    lit = shown * svs_item_light(col, detail1, ramp1, ramp2, f, colors, light)
    if f.get("_AlphaLine", 0):
        lit = _lerp(line, lit, np.round(create_alpha)[..., None])
    d = detail1[..., 0:1]
    return np.clip(lit + d * (d * line - lit), 0, 0.95)


# --- SVS create shaders: lif_create_main_cloth ---------------------------------------------------

def create_pattern_uv(u, v, floats, k):
    """Where LIF/lif_create_main_cloth reads pattern mask `k` (1 to 4): moved by twice
    `_PatternOffset_0k`, scaled by 20 - 19 * `_PatternScale_0k` and turned by `_PatternRotator_0k`
    about the centre."""
    f = floats
    x = (u + 2 * f[f"_PatternOffset_0{k}u"] - 1) * (20 - 19 * f[f"_PatternScale_0{k}u"]) - 0.5
    y = (v + 2 * f[f"_PatternOffset_0{k}v"] - 1) * (20 - 19 * f[f"_PatternScale_0{k}v"]) - 0.5
    x, y = _turn(x, y, (f[f"_PatternRotator_0{k}"] - 0.5) * 2 * np.pi)
    return x + 0.5, y + 0.5


def create_paint_uv(u, v, position):
    """Where the LIF create shaders read a paint: `_Paint_position_0k` moves it (xy), turns it (z, in
    turns) and sizes it (w)."""
    p = np.asarray(position, dtype=F)
    s = 2 - 2 * p[3]
    x = (u + p[0]) * 2 * s + 0.5 - s - 0.5
    y = (v + p[1]) * 2 * s + 0.5 - s - 0.5
    x, y = _turn(x, y, p[2] * 2 * np.pi)
    return x + 0.5, y + 0.5


def _pattern_layer(base, sub, pattern, amount):
    """A pattern over a colour: toward `sub` times the pattern by `amount` times sub's alpha, then
    toward the pattern itself where it is saturated."""
    layer = _lerp(base[:3], sub[:3] * pattern[..., :3], (amount * sub[3])[..., None])
    vivid = amount * np.clip(_saturation(pattern[..., :3]) * 10 - 0.05, 0, 1) * sub[3]
    return _lerp(layer, pattern[..., :3], vivid[..., None])


def svs_paints(col, paints, paint_mask, colors, on, prefix="_Paint_color_0", channels=(0, 1, 2)):
    """The LIF create shaders' three paints over a colour: each tints toward its texture times
    max(smoothstep of its saturation, its colour), by its alpha, its colour's alpha, its channel of
    the paint mask (`channels`) and `on`."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    for k, ch in zip((1, 2, 3), channels):
        pt = paints[k - 1]
        if pt is None:
            continue
        pc = c[f"{prefix}{k}"]
        f = np.minimum(pt[..., 3], _smooth01((_saturation(pt[..., :3]) - 0.3) * 2.5))
        tint = np.maximum(f[..., None], pc[:3])
        amount = pt[..., 3] * pc[3] * paint_mask[..., ch] * on
        col = col + amount[..., None] * (pt[..., :3] * tint - col)
    return col


def create_main_cloth(main, mask, patterns, paints, paint_mask, colors):
    """LIF/lif_create_main_cloth: the colour mask's channels pick `_Main_color_01..03` over
    `_Main_color_04`, each with its pattern (where the mask's alpha is at least 0.5: `_pattern_layer`
    with `_Sub_color_0k`); the three paints where the mask's alpha is 1; times the main texture.
    `patterns` are the four masks read at create_pattern_uv, `paints` the three read at
    create_paint_uv (None when missing). Returns linear rgb and alpha (the colours' alpha, its fourth
    root, times the main texture's)."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    on = (mask[..., 3] >= 0.5).astype(F)
    full = (mask[..., 3] >= 1.0).astype(F)
    layers = [_pattern_layer(c[f"_Main_color_0{k}"], c[f"_Sub_color_0{k}"], patterns[k - 1], on * patterns[k - 1][..., 3])
              for k in (1, 2, 3, 4)]
    rgb = layers[3]
    a = np.full(mask.shape[:2], c["_Main_color_04"][3])
    for k, ch in ((1, 0), (2, 1), (3, 2)):
        rgb = _lerp(rgb, layers[k - 1], mask[..., ch:ch + 1])
        a = _lerp(a, c[f"_Main_color_0{k}"][3], mask[..., ch])
    rgb = svs_paints(rgb, paints, paint_mask, colors, full)
    return rgb * main[..., :3], np.sqrt(np.sqrt(a)) * main[..., 3]


# --- SVS nails: lif_main_nail --------------------------------------------------------------------

def svs_skin_shadow_tint(col):
    """The shadow colour LIF's skin-body shaders (nails, body) make from a colour: its hue at
    saturation sqrt(s) + 0.1 and value 0.8 - 0.1 sqrt(v)."""
    h, s, v = _rgb_hsv(col)
    return _hsv_rgb(h, np.sqrt(s) + 0.1, 0.8 - 0.1 * np.sqrt(v))


def nail_color(mask, main, paints, colors):
    """LIF/lif_main_nail's colour: the colour mask's channels pick `_Nail_main_color_01..03` over white,
    the main texture is added by `_Nail_main_color_01`'s alpha, then the three paints (`paints`, read
    at create_paint_uv of `_Paint_position_offset_0k`; None when missing) over it by their alpha and
    their colour's. Returns linear rgb."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    col = _lerp(np.ones(3), c["_Nail_main_color_01"][:3], mask[..., 0:1])
    col = _lerp(col, c["_Nail_main_color_02"][:3], mask[..., 1:2])
    col = _lerp(col, c["_Nail_main_color_03"][:3], mask[..., 2:3])
    col = col + main[..., :3] * c["_Nail_main_color_01"][3]
    for k, pt in enumerate(paints, 1):
        if pt is not None:
            pc = c[f"_Paint_color_0{k}"]
            col = _lerp(col, pt[..., :3] * pc[:3], (pt[..., 3] * pc[3])[..., None])
    return col


def lif_main_nail(col, matcap, ramp1, ramp2, colors, floats, light: SvsLight):
    """LIF/lif_main_nail as the bake draws it, from its colour (`nail_color`): the matcap (`_Mat_cap`,
    not cleared, read at the quad's view normal: its centre) screened over it by `_Nail_gloss_power`,
    lit as `svs_item_mix` with the skin-body shadow tint and the ramp alone, plus a gloss of the
    matcap's red times the power where the light reaches. `ramp1`, `ramp2` are read at item_ramp_uv
    with no detail. The rim (off: `_RimMask` 1) and the line texture (off unless
    `_Line_textureonoff`, and not in the bundle) are left out. Returns linear rgb."""
    f = floats
    g = min(max(f.get("_Nail_gloss_power", 0), 0), 10)
    m = np.asarray(matcap, dtype=F)[..., :3]
    c = np.clip(_lerp(col, 1 - (1 - m) * (1 - col), g), 0, 0.95)
    t = svs_item_t(np.zeros(col.shape[:-1] + (4,)), ramp1, ramp2, f, light)
    lit = svs_item_mix(t, svs_skin_shadow_tint(col), colors, f, light)
    gloss = np.asarray(matcap, dtype=F)[..., 0] * f.get("_Nail_gloss_power", 0)
    spec = (gloss * np.minimum(gloss, np.maximum(1 - t, 0)))[..., None] * np.asarray(light.color, dtype=F)
    return np.clip(c * (lit + spec), 0, 1.01)


# --- SVS body: lif_main_skin_body ----------------------------------------------------------------
#
# The exporter bakes the skin from its mesh flattened into UV space, every normal toward the camera
# as on the quad (Bake.Flatten), with the quad's render under it where the mesh leaves gaps, its
# mesh-placed layers (nipples, under-hair) cleared.

def skin_nipple_uv(uv2, nip_size):
    """Where LIF/lif_main_skin_body reads `_Nip`: the second UV map scaled about its centre by
    `_Nip_size` (to 0.65 at 0.5), out to where the scaling fades, |uv2 - 0.5| = 0.015."""
    k = nip_size * 0.27 + 0.54
    reach = np.clip((np.linalg.norm(uv2 - 0.5, axis=-1, keepdims=True) + 0.15) * 6.060606 - 1, 0, 1)
    return _lerp(uv2 * (2 - 2 * k) + nip_size * 0.27 + 0.04, uv2, reach)


def highlight_uv(u, v, floats, light: SvsLight):
    """Where LIF/lif_main_skin_body reads its highlight (`_Detail_mask_01`'s blue): moved toward the
    light by `_SpeclarHeight` (`0.8 (h - 1)` times half the light's x and y; the view's part, under a
    camera 10 away, is left out)."""
    k = 0.8 * (floats.get("_SpeclarHeight", 1) - 1) * 0.5
    return u + k * light.xy[0], v + k * light.xy[1]


def skin_body_color(create, nip, underhair, detail2, vertex, colors, floats):
    """LIF/lif_main_skin_body's colour: its composited texture (`_Create_main_texture`) over `_MainColor`
    by its alpha; the nipples (`nip`, read at skin_nipple_uv: `_Nip_color_01` by its red, times
    `_Nip_color_02` by its green, by its alpha where the vertex colour's red is low) and the under-hair
    (`underhair`, read at the second UV map, where the red is high); times 0.95, toward `_Detail_color_02`
    by `_Detail_mask_02`'s red, `_Skin_red_power` and the base's value. Returns the base and the colour,
    linear rgb."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    base = _lerp(c["_MainColor"][:3], create[..., :3], create[..., 3:4])
    n1, n2 = c["_Nip_color_01"], c["_Nip_color_02"]
    nipped = _lerp(base, n1[:3], nip[..., 0:1])
    nipped = np.clip(_lerp(nipped, nipped * n1[:3] * n2[:3], nip[..., 1:2]), 0, 1)
    vr = vertex[..., 0:1]
    col = _lerp(base, nipped, nip[..., 3:4] * n1[3] * (1 - vr))
    uh = c["_Under_hair_color"]
    col = _lerp(col, underhair[..., :3] * uh[:3], underhair[..., 3:4] * uh[3] * vr)
    _, _, value = _rgb_hsv(base)
    d = c["_Detail_color_02"]
    red = detail2[..., 0] * floats.get("_Skin_red_power", 0) * d[3] * (value * 0.67 + 0.33)
    return base, np.clip(_lerp(col * 0.95, d[:3], red[..., None]), 0, 1)


def lif_main_skin_body(base, col, detail1, detail1_at_highlight, detail2, matcap, underhair_amount, ramp1, ramp2,
                       highlight_ramp, colors, floats, light: SvsLight):
    """LIF/lif_main_skin_body as the bake draws it, from `skin_body_color`'s base and colour: tinted
    toward `_Shadow_color` by the shade matcap's blue (`matcap`, read at the view normal: its centre);
    plus `_Highlight_color` where `_Detail_mask_01`'s blue (read at highlight_uv) and its alpha (times
    the matcap's red, off the under-hair) shine; lit as `svs_item_mix` with the skin-body shadow tint of
    the base, `_Detail_mask_02` as the detail; plus a gloss of the highlight where the light reaches.
    `ramp1`, `ramp2` are read at item_ramp_uv of `_Detail_mask_02`, `highlight_ramp` at N.L less 0.4
    times `_Detail_mask_01`'s green. The liquid, sweat, dents, bust shadow, rim (off: `_RimMask` 1),
    reflection (no cubemap) and line texture (off: `_linetexon`) are left out. Returns linear rgb."""
    f = floats
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    m = np.asarray(matcap, dtype=F)
    sc = c["_Shadow_color"]
    strength = f["_Shadow_power"] * 0.35 + 0.35
    tint = _lerp(np.ones(3), sc[:3], m[2] * sc[3] * strength)
    shaded = col * tint
    hl_ramp = np.maximum(np.maximum(detail2[..., 1] * f.get("_SkinIntensity", 1), highlight_ramp[..., 1]),
                         m[1] * sc[3] * strength)
    h = np.clip(detail1_at_highlight[..., 2] * 1.6666666, 0, 1) * f.get("_Highlight_power", 0) * (1 - hl_ramp)
    hc = c["_Highlight_color"]
    q = detail1[..., 3] * m[0]
    off_hair = 1 - underhair_amount
    mean = min(max(float(np.mean(light.color)), 0), 1)
    shine = np.clip((h * f.get("_High_light_power", 1) * (1 - q))[..., None] * hc[:3] * mean
                    + (q * (1 - q) * off_hair * mean)[..., None] * hc[:3], 0, 1)
    albedo = np.clip(shaded + hc[3] * shine, 0, 0.95)
    t = svs_item_t(detail2, ramp1, ramp2, f, light)
    lit = svs_item_mix(t, svs_skin_shadow_tint(base), colors, f, light)
    gloss = np.maximum(h * hc[:3].sum() * hc[3] * f.get("_High_light_power", 1) / 3, off_hair * q * hc[3])
    spec = (gloss * np.minimum(gloss, np.maximum(1 - t, 0)))[..., None] * np.asarray(light.color, dtype=F)
    return np.clip(albedo * (lit + spec), 0, 1.01)


def create_main_skin_body(sunburn, paints, paint_mask, colors):
    """LIF/lif_create_main_skin_body: `_Main_color` toward `_Sunburn_color` by the sunburn texture's red
    and its colour's alpha, then the three paints (svs_paints, all by the paint mask's red). `sunburn`
    is None when the bundle has none (the game's default, black). Returns linear rgb; its alpha is 1."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    shape = paint_mask.shape[:-1]
    burn = np.zeros(shape) if sunburn is None else sunburn[..., 0]
    col = _lerp(c["_Main_color"][:3], c["_Sunburn_color"][:3], (burn * c["_Sunburn_color"][3])[..., None])
    return svs_paints(col, paints, paint_mask, colors, 1.0, channels=(0, 0, 0))


# --- SVS face: lif_main_skin_head ----------------------------------------------------------------

def face_paint_uv(u, v, position, size=2.0):
    """Where LIF/lif_create_main_skin_head reads a paint (`size` 2) or the mole (`size` 2.4): as
    create_paint_uv, its v moved by 0.8 (y + 0.0966849998) and its size by `size * w`."""
    p = np.asarray(position, dtype=F)
    s = 2 - size * p[3]
    x = (u + p[0]) * 2 * s + 0.5 - s - 0.5
    y = (v + 0.8 * (p[1] + 0.0966849998)) * 2 * s + 0.5 - s - 0.5
    x, y = _turn(x, y, p[2] * 2 * np.pi)
    return x + 0.5, y + 0.5


def cheek_position(floats, vectors):
    """`_Cheek_position` and the cheek floats as the create_paint_uv position LIF/lif_main_skin_head
    reads `_Cheek_texture` at, on the second UV map."""
    f, cp = floats, np.asarray(vectors["_Cheek_position"], dtype=F)
    return (f["_Cheek_position_x"] * 0.24 + cp[0] - 0.12, f["_Cheek_position_y"] * -0.2 + cp[1] + 0.1,
            cp[2] - f["_Cheek_rotation"] + 0.5, f["_Cheek_size"] * 0.2 + cp[3] - 0.1)


def create_main_skin_head(skin_mask, facetype, paints, mole, paint_mask, eyeshadow, colors):
    """LIF/lif_create_main_skin_head: `_Main_color` toward `_Mouth_color` by the skin mask's red, times
    the face type texture (white when missing); the three paints over it (by their alpha and their
    colour's) and the mole (`_Hokuro_color` by its red), kept per channel by the paint mask; then the
    eyeshadow (`_Eyeshadow_color` by its red). `paints` (read at face_paint_uv), `mole` (face_paint_uv
    at 2.4) and `eyeshadow` are None when missing. Returns linear rgb; its alpha is 1."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    shape = paint_mask.shape[:-1]
    red = np.zeros(shape) if skin_mask is None else skin_mask[..., 0]
    base = _lerp(c["_Main_color"][:3], c["_Mouth_color"][:3], red[..., None])
    base = base * (np.ones(3) if facetype is None else facetype[..., :3])
    col = svs_paints(base, paints, np.ones(shape + (4,)), colors, 1.0)
    if mole is not None:
        col = _lerp(col, c["_Hokuro_color"][:3], (mole[..., 0] * c["_Hokuro_color"][3])[..., None])
    col = base + paint_mask[..., :3] * (col - base)
    if eyeshadow is not None:
        col = _lerp(col, c["_Eyeshadow_color"][:3], (eyeshadow[..., 0] * c["_Eyeshadow_color"][3])[..., None])
    return col


def skin_head_color(create, cheek, lip, nose, colors):
    """LIF/lif_main_skin_head's colour: its composited texture (`_Create_jm_main_skin_head`) over
    `_MainColor` by its alpha, times 0.95; the cheek blush (`_Cheek_color` by the cheek texture's red,
    `_Cheek_highlight_color` screened by its blue), the lips (`_Lip_color` by the lip texture's red, plus
    `_Lip_highlight_color` by its blue) and the nose: a tint from the composited texture's hue (less
    0.03), the root of its saturation and 0.75 + half the root of its value, by the nose texture's red
    and `_Nose_color`'s alpha, with `_Nose_line_color` by its blue. `cheek`, `lip`, `nose` are read on
    the mesh's second, third and fourth UV maps (the cheek at create_paint_uv of cheek_position).
    Returns the base and the colour, linear rgb."""
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    base = _lerp(c["_MainColor"][:3], create[..., :3], create[..., 3:4])
    cc, ch = c["_Cheek_color"], c["_Cheek_highlight_color"]
    col = _lerp(base * 0.95, cc[:3], (cheek[..., 0] * cc[3])[..., None])
    col = np.clip(_lerp(col, 1 - (1 - ch[:3]) * (1 - col), (cheek[..., 2] * ch[3])[..., None]), 0, 1)
    lc, lh = c["_Lip_color"], c["_Lip_highlight_color"]
    col = _lerp(col, lc[:3], (lip[..., 0] * lc[3])[..., None]) + (lip[..., 2] * lh[3])[..., None] * lh[:3]
    h, s, v = _rgb_hsv(create[..., :3])
    tint = (np.sqrt(v) * 0.5 + 0.75)[..., None] * _hsv_rgb(np.clip(np.abs(h) - 0.03, 0, 1), np.sqrt(s), np.ones_like(v))
    col = col * _lerp(np.ones(3), tint, (nose[..., 0] * c["_Nose_color"][3])[..., None])
    nl = c["_Nose_line_color"]
    col = _lerp(col, nl[:3], (nose[..., 2] * nl[3])[..., None])
    return base, np.clip(col, 0, 1)


def lif_main_skin_head(base, col, detail1, detail2, nose, matcap, ramp1, ramp2, colors, floats, light: SvsLight):
    """LIF/lif_main_skin_head as the bake draws it, from `skin_head_color`'s base and colour: tinted
    toward `_Shadow_color` by the shade matcap's blue (read at the view normal: its centre) off
    `_Detail_mask_02`'s blue, lit as `svs_item_mix` with the skin-body shadow tint of the base, the
    larger of `_Detail_mask_01`'s and the nose texture's green as the detail. `ramp1` and `ramp2` are
    read at face_ramp_uv. The liquid, sweat, blush expression (`_HohoakaIntensity`), specular map and
    lip line (not in the bundle), rim (off: `_RimMask` 1) and reflection (no cubemap) are left out.
    Returns linear rgb."""
    f = floats
    c = {k: np.asarray(v, dtype=F) for k, v in colors.items()}
    m = np.asarray(matcap, dtype=F)
    sc = c["_Shadow_color"]
    amount = m[2] * sc[3] * (1 - detail2[..., 2]) * (f["_Shadow_power"] * 0.35 + 0.35)
    albedo = np.clip(col * _lerp(np.ones(3), sc[:3], amount[..., None]), 0, 0.95)
    detail = np.zeros(col.shape[:-1] + (4,))
    detail[..., 1] = np.maximum(detail1[..., 1], nose[..., 1])
    t = svs_item_t(detail, ramp1, ramp2, f, light)
    lit = svs_item_mix(t, svs_skin_shadow_tint(base), colors, f, light)
    return np.clip(albedo * lit, 0, 1.01)


def face_ramp_uv(detail1, detail2, nose, floats, light: SvsLight):
    """Where LIF/lif_main_skin_head reads its ramp: N.L plus half `_Detail_mask_02`'s blue, pulled by
    the larger of `_Detail_mask_01`'s and the nose's green times `_ShadowSetting.b`; and four times
    N.L * 0.4 + 0.3."""
    d = np.maximum(detail1[..., 1], nose[..., 1])
    k = 1 - d * np.asarray(floats.get("_ShadowSetting", (1, 0, 0, 0)), dtype=F)[2]
    a = np.clip(np.clip(light.ndl + 0.5 * detail2[..., 2], 0, 1) * k, 0, 1)
    b = np.minimum(np.clip(light.ndl * 0.4 + 0.3, 0, 1) * 4, 1)
    return a, np.full_like(a, b)
