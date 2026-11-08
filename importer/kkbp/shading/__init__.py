"""The game's colour maths for edit materials (D42): LUT saturation and light and dark colours.

This package never imports bpy: the edit material tool gives it numpy arrays (rows bottom-up, as
Blender's `Image.pixels`) and colours, and puts what it returns into images and node inputs. It is
the legacy `editmaterial.py`'s numpy code, written as whole-array operations:

- `saturate` and `saturate_color` look colours up in the game's `Lut_TimeDay.png` colour grade, a
  1024 x 32 strip of 32 blue slices;
- `dark_pixels` and `dark_color` are the clothes and hair shadow of the game's item shader
  (`ShadeAdjustItem` in xukmi's KKShadersPlus and KKShadersRecreated, credited in NOTICE), `skin_dark_color`
  the skin shadow (`MapValuesMain`), and `eyew_dark_color` the eyebrows' (`toon_eyew`).

Colours are sRGB-encoded [r, g, b, a] floats, as the bundle writes them.
"""

from __future__ import annotations

import numpy as np

FLOAT = np.float32

# The LUT strip: x = red within a slice + the blue slice, y = green, slices interpolated by blue.
_SCALE = np.array([0.0302734375, 0.96875, 31.0], dtype=FLOAT)
_OFFSET = np.array([0.5 / 1024, 0.5 / 32, 0.0], dtype=FLOAT)
_SLICE = np.array([1 / 32, 0.0], dtype=FLOAT)

# Legacy's default shadow colour for materials without one.
DEFAULT_SHADOW = (0.764, 0.880, 1.0, 1.0)

# The maker's ambient and sun light (0.666 each) give this constant light colour in the shader.
_LIGHT = FLOAT(1.0656)
# Legacy's correction for the skin shadow, which comes out slightly off but consistently so.
_SKIN_FUDGE = np.array([0.02, 0.05, 0.0], dtype=FLOAT)


def saturate(pixels: np.ndarray, lut: np.ndarray, rows: int = 512) -> np.ndarray:
    """`pixels` (height, width, 4) through the LUT (32, 1024, 4), in batches of `rows` rows to bound
    memory. Returns a new array; alpha is kept."""
    out = np.array(pixels, dtype=FLOAT, copy=True)
    for start in range(0, out.shape[0], rows):
        chunk = out[start:start + rows]
        chunk[..., :3] = _lookup(chunk[..., :3], lut)[..., :3]
    return out


def saturate_color(color, lut: np.ndarray) -> tuple[float, float, float, float]:
    """One sRGB colour through the LUT, returned linear for a Blender colour input (alpha 1)."""
    rgb = np.array(color[:3], dtype=FLOAT).reshape(1, 1, 3)
    looked = _lookup(rgb, lut, linear=True)
    return (*(float(v) for v in looked[0, 0, :3]), 1.0)


def dark_pixels(pixels: np.ndarray, shadow=DEFAULT_SHADOW, rows: int = 512) -> np.ndarray:
    """The dark version of a main texture (height, width, 4) under the item shader's shadow.
    Alpha is kept; legacy also scaled it, an artefact of its four-wide arithmetic."""
    out = np.array(pixels, dtype=FLOAT, copy=True)
    for start in range(0, out.shape[0], rows):
        chunk = out[start:start + rows]
        chunk[..., :3] = _dark(chunk[..., :3], shadow)
    return out


def dark_color(color, shadow=DEFAULT_SHADOW) -> tuple[float, float, float, float]:
    """One sRGB colour under the item shader's shadow (clothes, hair and other non-skin parts)."""
    rgb = _dark(np.array(color[:3], dtype=FLOAT), shadow)
    return (*(float(v) for v in rgb), 1.0)


def eyew_dark_color(color, shadow=DEFAULT_SHADOW) -> tuple[float, float, float, float]:
    """One sRGB colour under the eyebrow and eye-white shader's shadow (toon_eyew), with the maker's
    ambient shadow (0.15, legacy's constant): what is left of the colour where it is fully shaded."""
    tint = np.array(shadow[:3], dtype=FLOAT)
    ambient = FLOAT(0.15)
    kept = 1 - (1 - ambient) * (1 - ambient)  # the ambient shadow's intensity, 0.2775
    shaded = np.where(tint > 0.5, 1 - (2 - 2 * tint) * (1 - kept), kept * tint * 2)
    rgb = np.array(color[:3], dtype=FLOAT) * np.clip(shaded, 0, 1)
    return (*(float(v) for v in rgb), 1.0)


def skin_dark_color(color) -> tuple[float, float, float, float]:
    """One sRGB skin colour under the skin shader's shadow."""
    diffuse = np.array(color[:3], dtype=FLOAT)
    adjust = _hue_tint(diffuse, hue_offsets=(-0.0799999982, -0.413333356, 0.25333333), saturation=0.660000026)
    rgb = diffuse * _shadow_factor(adjust) * _LIGHT + _SKIN_FUDGE
    return (*(float(v) for v in rgb), 1.0)


# --- the LUT ----------------------------------------------------------------------------------

def _lookup(rgb, lut, linear=False):
    """Trilinear lookup of rgb (..., 3) in the LUT strip: bilinear within the two nearest blue
    slices, then blended by blue. `linear` returns linear colours instead of the LUT's sRGB."""
    lut = np.asarray(lut, dtype=FLOAT)
    coord = rgb * _SCALE + _OFFSET
    slice_frac, slice_floor = np.modf(coord[..., 2:3])
    bottom = coord[..., :2] + slice_floor * _SLICE
    top = np.clip(bottom + _SLICE, 0, 1)
    low, high = _bilinear(lut, bottom), _bilinear(lut, top)
    if linear:  # for colours, legacy linearised each slice and blended them linear
        low, high = _srgb_to_linear(low), _srgb_to_linear(high)
    return low * (1 - slice_frac) + high * slice_frac


def _bilinear(lut, coords):
    h, w, _ = lut.shape
    x = coords[..., 0] * (w - 1)
    # Legacy's nudge against reading the neighbouring slice at the strip's edges.
    x = x + (x / 1024 - 0.5)
    y = coords[..., 1] * (h - 1)
    x0 = np.clip(np.floor(x).astype(int), 0, w - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y0 = np.clip(np.floor(y).astype(int), 0, h - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    xf = (x - x0)[..., None]
    yf = (y - y0)[..., None]
    left = lut[y0, x0] * (1 - yf) + lut[y1, x0] * yf
    right = lut[y0, x1] * (1 - yf) + lut[y1, x1] * yf
    return left * (1 - xf) + right * xf


def _srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, np.power((np.maximum(c, 0) + 0.055) / 1.055, 2.4))


# --- the shadow -------------------------------------------------------------------------------

def _dark(diffuse, shadow):
    tint = np.array(shadow[:3], dtype=FLOAT)
    adjust = _hue_tint(diffuse * tint, hue_offsets=(0.0, -0.333333343, 0.333333343), saturation=0.5)
    return diffuse * _shadow_factor(adjust) * _LIGHT


def _hue_tint(rgb, hue_offsets, saturation):
    """The shaders' ShadeAdjust: rgb's hue (shifted by `hue_offsets`) at value 1 and `saturation`
    times its saturation. The shader's swizzled code is the usual branchless RGB -> HSV -> RGB."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    eps = FLOAT(1.00000001e-10)
    # p = g >= b ? (g, b, 0, -1/3) : (b, g, -1, 2/3)
    ge = g >= b
    px, py = np.where(ge, g, b), np.where(ge, b, g)
    pz = np.where(ge, FLOAT(0.0), FLOAT(-1.0))
    pw = np.where(ge, FLOAT(-1 / 3), FLOAT(0.666666687))
    # q = r >= p.x ? (r, p.y, p.z, p.x) : (p.x, p.y, p.w, r)
    rge = r >= px
    qx = np.where(rge, r, px)
    qy = py
    qz = np.where(rge, pz, pw)
    qw = np.where(rge, px, r)
    d = qx - np.minimum(qw, qy)
    hue = np.abs(qz + (qw - qy) / (d * 6 + eps))
    sat = d / (qx + eps) * FLOAT(saturation)
    channels = hue[..., None] + np.array(hue_offsets, dtype=FLOAT)
    channels = np.clip(np.abs(1 - 2 * (channels - np.floor(channels))) * 3 - 1, 0, 1)
    return sat[..., None] * (channels - 1) + 1


def _shadow_factor(adjust):
    """How much light a shadowed pixel keeps, from the ShadeAdjust colour (the shader's lines
    352-374 with the constant inverted ambient shadow 0.7225)."""
    shaded = 1 - FLOAT(0.7225) * (2 - FLOAT(1.79999995) * adjust)
    return np.clip(np.where(adjust > FLOAT(0.555555582), shaded, adjust * FLOAT(1.79999995)), 0, 1)
