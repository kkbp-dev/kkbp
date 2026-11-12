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


def main_item(main, color_mask, detail_mask, line_mask, colors, floats, shadow_color, ramp, light: Light = KK):
    """KK's main_item (the teeth, the tongue, items) as the bake draws it: the colour mask over the
    main texture (white if none), darkened by the line mask's blue; its own shadow-extend scale; a
    highlight from the detail mask's red squared, which the bake doesn't clear; the lines mixed in
    linearly. `_LineColorG`'s colour is taken as white. Returns linear rgb."""
    col = np.ones(3, dtype=F)
    for i, color_ in enumerate(colors):
        col = col + color_mask[..., i:i + 1] * (color_ - col)
    base = main * col * (1 - line_mask[..., 2:3])
    line_r = line_mask[..., 0:1] + floats.get("_DetailRLineR", 0) * (detail_mask[..., 0:1] - line_mask[..., 0:1])
    full = line_r + floats.get("_AnotherRampFull", 0) * (1 - line_r)
    k = np.clip(2 - floats.get("_ShadowExtendAnother", 0) - full, 0, 1) * 0.67 + 0.33
    tint = k * item_tint(base, shadow_color, light)
    col = base * (tint + ramp * (1 - tint)) + detail_mask[..., 0:1] ** 2 * (1 - floats.get("_notusetexspecular", 0))
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
    x = col * (tint + ramp * e * (1 - tint)) * max(light.light * 0.6 + 0.4, light.ambient)
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
