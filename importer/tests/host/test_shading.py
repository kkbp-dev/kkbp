"""kkbp/shading/: the edit materials' colour maths (D42), checked against independent formulas and
the legacy importer's own numpy code."""

import colorsys

import numpy as np
import pytest
from PIL import Image

import shading
from conftest import REPO

LUT_FILE = REPO / "importer" / "library-src" / "images" / "Lut_TimeDay.png"


@pytest.fixture(scope="module")
def lut():
    """The game's LUT as Blender's Image.pixels gives it: floats, rows bottom-up."""
    with Image.open(LUT_FILE) as im:
        pixels = np.asarray(im.convert("RGBA"), dtype=np.float32) / 255
    return pixels[::-1]


def _identity_lut():
    """A 32-slice strip that maps every colour to itself."""
    col, row, slice_ = np.meshgrid(np.arange(32), np.arange(32), np.arange(32), indexing="xy")
    lut = np.zeros((32, 1024, 4), dtype=np.float32)
    lut[row, slice_ * 32 + col] = np.stack([col / 31, row / 31, slice_ / 31, np.ones_like(col)], -1)
    return lut


COLOURS = [(0.9, 0.2, 0.1), (0.1, 0.8, 0.3), (0.2, 0.3, 0.95), (0.5, 0.5, 0.5), (1.0, 0.905, 0.875),
           (0.0, 0.0, 0.0), (1.0, 1.0, 1.0), (0.69, 0.495, 0.321)]


def test_the_lut_is_the_games_strip(lut):
    assert lut.shape == (32, 1024, 4)


@pytest.mark.parametrize("rgb", COLOURS)
def test_identity_lut_keeps_colours(rgb):
    pixels = np.array([[[*rgb, 0.5]]], dtype=np.float32)
    out = shading.saturate(pixels, _identity_lut())
    assert np.allclose(out[0, 0, :3], rgb, atol=0.02)
    assert out[0, 0, 3] == pytest.approx(0.5)


def test_saturate_color_is_linear(lut):
    rgb = (0.5, 0.5, 0.5)
    looked = shading.saturate(np.array([[[*rgb, 1]]], dtype=np.float32), lut)[0, 0, :3]
    linear = shading.saturate_color(rgb, lut)
    assert linear[3] == 1.0
    srgb = np.where(np.array(linear[:3]) <= 0.0031308, np.array(linear[:3]) * 12.92,
                    1.055 * np.power(np.array(linear[:3]), 1 / 2.4) - 0.055)
    assert np.allclose(srgb, looked, atol=0.01)


def test_saturation_batches_match_one_pass(lut):
    rng = np.random.default_rng(1)
    pixels = rng.random((37, 11, 4), dtype=np.float32)
    assert np.array_equal(shading.saturate(pixels, lut, rows=5), shading.saturate(pixels, lut, rows=100))
    assert not np.shares_memory(shading.saturate(pixels, lut), pixels)


def test_the_real_lut_saturates(lut):
    """The game's grade makes a muted colour more saturated."""
    rgb = (0.6, 0.45, 0.4)
    out = shading.saturate(np.array([[[*rgb, 1]]], dtype=np.float32), lut)[0, 0, :3]
    h0, s0, _ = colorsys.rgb_to_hsv(*rgb)
    h1, s1, _ = colorsys.rgb_to_hsv(*out)
    assert s1 > s0 and abs(h1 - h0) < 0.05


@pytest.mark.parametrize("rgb", COLOURS)
@pytest.mark.parametrize("offsets, shift, saturation", [((0.0, -0.333333343, 0.333333343), 0.0, 0.5),
                                                         ((-0.0799999982, -0.413333356, 0.25333333), -0.08, 0.66)])
def test_hue_tint_is_hsv(rgb, offsets, shift, saturation):
    h, s, _ = colorsys.rgb_to_hsv(*rgb)
    want = colorsys.hsv_to_rgb((h + shift) % 1, s * saturation, 1)
    got = shading._hue_tint(np.array(rgb, dtype=np.float32), offsets, saturation)
    assert np.allclose(got, want, atol=1e-4)


def _legacy_dark(pixels, shadow):
    """The legacy create_darktex on (n, 4) pixels, verbatim apart from names and one fix: legacy
    compared red with green (`t1[:, [x]]`) where the shader compares it with the larger of green and
    blue (`t2[:, [x]]`; `u_xlat1.w>=u_xlat2.x` in KKShadersRecreated's KKItemDiffuse.cginc, and
    legacy's own one-colour version), which darkened pixels bluer than green wrongly."""
    x, y, z, w = 0, 1, 2, 3
    t0 = pixels
    sc = np.asarray([*shadow[:3], 1], dtype=np.float32)
    t1 = t0[:, [y, z, z, x]] * sc[[y, z, z, x]]
    t2 = t1[:, [y, x]]
    t3 = t0[:, [y, z]] * sc[[y, z]] + (-t2)
    t30 = (t2[:, [y]] >= t1[:, [y]]).astype(int)
    t2 = np.hstack((t2[:, [x, y]], np.full((t2.shape[0], 1), -1, t2.dtype), np.full((t2.shape[0], 1), 0.666666687, t2.dtype)))
    t3 = np.hstack((t3[:, [x, y]], np.full((t3.shape[0], 1), 1, t3.dtype), np.full((t3.shape[0], 1), -1, t3.dtype)))
    t2 = t30 * t3 + t2
    t30 = (t1[:, [w]] >= t2[:, [x]]).astype(int)
    t1 = np.hstack((t2[:, [x, y, w]], t1[:, [w]]))
    t2 = np.hstack((t1[:, [w, y]], t2[:, [z]], t1[:, [x]]))
    t2 = -t1 + t2
    t1 = t30 * t2 + t1
    t30 = np.minimum(t1[:, [y]], t1[:, [w]])
    t30 = -t30 + t1[:, [x]]
    t2[:, [x]] = t30 * 6 + 1.00000001e-10
    t11 = (-t1[:, [y]] + t1[:, [w]]) / t2[:, [x]] + t1[:, [z]]
    t1[:, [x]] = t1[:, [x]] + 1.00000001e-10
    t30 = t30 / t1[:, [x]] * 0.5
    t1 = np.absolute(t11) + np.asarray([0.0, -0.333333343, 0.333333343, 1])
    t1 = t1 - np.floor(t1)
    t1 = np.clip(np.absolute(-t1 * 2 + 1) * 3 - 1, 0, 1) - 1
    adj = t30 * t1 + 1
    shaded = -(-(adj * 0.899999976 - 0.5) * 2 + 1) * 0.7225 + 1
    adj = np.clip(np.where(0.555555582 < adj, shaded, adj * 1.79999995), 0, 1)
    return pixels * adj * np.asarray([1.0656, 1.0656, 1.0656, 1])


def test_dark_pixels_match_legacy():
    rng = np.random.default_rng(2)
    pixels = rng.random((16, 16, 4), dtype=np.float32)
    shadow = (0.686, 0.77, 1.0, 1.0)
    want = _legacy_dark(pixels.reshape(-1, 4), shadow).reshape(16, 16, 4)
    got = shading.dark_pixels(pixels, shadow, rows=5)
    assert np.allclose(got[..., :3], want[..., :3], atol=1e-5)
    assert np.array_equal(got[..., 3], pixels[..., 3])  # alpha kept


@pytest.mark.parametrize("rgb", COLOURS)
def test_dark_color_is_dark_pixels(rgb):
    shadow = (0.83, 0.866, 0.941, 1)
    pixel = shading.dark_pixels(np.array([[[*rgb, 1]]], dtype=np.float32), shadow)[0, 0]
    assert np.allclose(shading.dark_color(rgb, shadow), pixel, atol=1e-6)


def test_skin_dark_color():
    """Legacy's skin shadow of its default skin colour, worked through by hand from MapValuesMain."""
    rgb = (1.0, 0.905, 0.875)
    h, s, _ = colorsys.rgb_to_hsv(*rgb)
    adjust = np.array(colorsys.hsv_to_rgb((h - 0.08) % 1, s * 0.66, 1))
    factor = np.clip(np.where(adjust > 0.555555582, 1 - 0.7225 * (2 - 1.8 * adjust), adjust * 1.8), 0, 1)
    want = np.array(rgb) * factor * 1.0656 + (0.02, 0.05, 0)
    assert np.allclose(shading.skin_dark_color(rgb)[:3], want, atol=1e-4)
    assert all(c < r + 0.06 for c, r in zip(shading.skin_dark_color(rgb)[:3], rgb))


def test_eyew_dark_color():
    """toon_eyew's fully shaded colour with the maker's ambient shadow 0.15, worked through by hand:
    1 - (2 - 2 * shadow) * 0.7225 for a shadow channel above 0.5, 0.555 * shadow below."""
    shadow = (0.63, 0.64, 0.4, 1)
    got = shading.eyew_dark_color((1.0, 1.0, 1.0), shadow)
    assert got[:3] == pytest.approx((1 - 0.74 * 0.7225, 1 - 0.72 * 0.7225, 0.555 * 0.4), abs=1e-5)
    assert shading.eyew_dark_color((0.5, 0.2, 0.0), shadow)[:3] == pytest.approx(
        (0.5 * got[0], 0.2 * got[1], 0.0), abs=1e-5)


def test_grade_reads_the_lut_as_the_shader_models_do(lut):
    """ADR 0056: Shown Colours are graded as `.KK grade` does, which follows models.grade."""
    from game_shaders import models
    rgb = np.random.default_rng(3).random((500, 3))
    assert np.abs(shading.grade(rgb, lut) - models.grade(rgb, lut.astype(np.float64))).max() < 1e-6


def test_a_shown_colour_is_what_the_inverse_table_gives_back_the_colour_from(lut):
    """ADR 0056, with a stand-in for the grade's inverse table: the identity strip, whose inverse of
    any colour is that colour, so the Shown Colour solved for through it is the colour itself."""
    colour = (0.918, 0.938, 0.958, 1.0)
    shown = shading.shown_color(colour, _identity_lut(), _identity_lut())
    assert shown[3] == 1.0
    assert np.asarray(shown[:3]) == pytest.approx(shading._srgb_to_linear(np.array(colour[:3])), abs=1e-6)
