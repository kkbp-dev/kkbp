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
