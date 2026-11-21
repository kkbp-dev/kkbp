"""Writes `importer/library-src/images/Lut_TimeDay inverse.exr`, the inverse of the maker camera's
colour grade (`Lut_TimeDay.png`), which `.KK ungrade` reads for Shown Colours (ADR 0056).

The strip has the grade's own layout (1024 x 32: 32 blue slices of 32 red by 32 green, rows bottom-up)
and holds, for each sRGB-encoded colour on the grid, a colour the grade turns into it
(models.grade). The grade moves each channel one way only and reaches every colour, so each has one;
where it clips (strong colours), several colours grade alike and the solver keeps the one it reaches
first. The values are 32-bit floats: an 8-bit strip would round the game colours it gives back.

Run on the harness's minimum Blender build (it needs bpy to write the EXR):

    <blender> --background --factory-startup --python-exit-code 1 --python importer/tools/make_ungrade_lut.py
"""

import sys
from pathlib import Path

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "game_shaders"))
import models  # noqa: E402  (no bpy)

IMAGES = HERE.parent / "library-src" / "images"
SOURCE = IMAGES / "Lut_TimeDay.png"
OUT = IMAGES / "Lut_TimeDay inverse.exr"
N = 32  # grid steps per channel, as the grade's
SEED = 21  # steps per channel of the forward grid each solve starts from
STEPS = 200  # fixed-point steps: x -= (grade(x) - target) / 2
TOLERANCE = 1e-4  # how close grade(inverse) must come to each grid colour


def _pixels(image):
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    return px.reshape(h, w, 4).astype(np.float64)


def _grid(n):
    g = np.linspace(0, 1, n)
    return np.stack(np.meshgrid(g, g, g, indexing="ij"), -1).reshape(-1, 3)


def solve(targets, lut):
    """A colour the grade turns into each target, from the nearest colour of a coarse forward grid."""
    seeds = _grid(SEED)
    graded = models.grade(seeds, lut)
    out = np.empty_like(targets)
    for start in range(0, len(targets), 4096):
        t = targets[start:start + 4096]
        nearest = ((t[:, None, :] - graded[None]) ** 2).sum(-1).argmin(1)
        x = seeds[nearest].copy()
        for _ in range(STEPS):
            x = np.clip(x - (models.grade(x, lut) - t) * 0.5, 0, 1)
        out[start:start + 4096] = x
    return out


def main():
    source = bpy.data.images.load(str(SOURCE), check_existing=False)
    source.colorspace_settings.name = "Non-Color"
    lut = _pixels(source)
    targets = _grid(N)  # [r, g, b] with b fastest
    inverse = solve(targets, lut)
    residual = np.abs(models.grade(inverse, lut) - targets).max()
    if residual > TOLERANCE:
        raise RuntimeError(f"the inverse grade is {residual:.6f} off somewhere")
    cube = inverse.reshape(N, N, N, 3)  # [r, g, b]
    strip = np.ones((N, N * N, 4), dtype=np.float32)
    for b in range(N):
        strip[:, b * N:(b + 1) * N, :3] = cube[:, :, b, :].transpose(1, 0, 2)  # rows green, columns red

    image = bpy.data.images.new(OUT.stem, N * N, N, alpha=True, float_buffer=True)
    image.colorspace_settings.name = "Non-Color"
    image.pixels.foreach_set(strip.ravel())
    image.filepath_raw = str(OUT)
    image.file_format = "OPEN_EXR"
    image.save()

    check = bpy.data.images.load(str(OUT), check_existing=False)
    check.colorspace_settings.name = "Non-Color"
    stored = np.abs(_pixels(check)[..., :3] - strip[..., :3]).max()
    if stored > 1e-6:
        raise RuntimeError(f"{OUT.name} doesn't hold its values as computed ({stored:.6f} off)")
    print(f"wrote {OUT} (grade of the inverse within {residual:.2e} of the grid)")


main()
