"""The shader models (importer/tools/game_shaders/models.py) against the Golden Samples: each model,
run on a material's own bundle textures and colours, gives back the bundle's light and dark bakes.
The thresholds are mean absolute differences per channel on sRGB values over opaque pixels; the
legacy edit templates were 0.03 to 0.31 from the same bakes (ADR 0026)."""

import json

import numpy as np
import pytest
from PIL import Image

from conftest import REPO, golden
from game_shaders import models

LUT = REPO / "importer" / "library-src" / "images" / "Lut_TimeDay.png"


@pytest.fixture(scope="module")
def lut():
    with Image.open(LUT) as im:
        return (np.asarray(im.convert("RGBA"), dtype=np.float64) / 255)[::-1]  # rows bottom-up, as UV space


class Sample:
    def __init__(self, game):
        self.root = golden(game)
        self.materials = {m["id"]: m for m in json.loads((self.root / "materials.json").read_text())["materials"]}

    def texture(self, holder, role, variant=None, size=None):
        t = next((t for t in holder["textures"] if t.get("role") == role and t.get("variant") == variant
                  and not t.get("pattern")), None)
        if t is None:
            return None
        with Image.open(self.root / t["file"]) as im:
            im = im.convert("RGBA")
            if size is not None and im.size != size:
                im = im.resize(size, Image.BILINEAR)
            return np.asarray(im, dtype=np.float64) / 255


def difference(model, reference):
    opaque = reference[..., 3] > 0.5
    return float(np.abs(model - reference[..., :3])[opaque].mean())


def _bakes(sample, material):
    light = sample.texture(material, "main", "light")
    size = light.shape[1::-1]
    return light, sample.texture(material, "main", "dark", size), size


# (game, material, model inputs) -> the light and dark the model gives.
def _eyew(sample, mid, lut):
    m = sample.materials[mid]
    light_ref, dark_ref, size = _bakes(sample, m)
    create = m.get("extensions", {}).get("kk", {}).get("create")
    if create is not None:
        main, alpha = models.create_eyewhite(sample.texture(create, "main", size=size)[..., :3],
                                             models.color(create["colors"]["_Color"]),
                                             models.color(create["colors"]["_Color2"]))
    else:
        tex = sample.texture(m, "main", size=size)
        main, alpha = tex[..., :3], tex[..., 3]
    args = (main, alpha, models.color(m["colors"].get("_Color", (1, 1, 1, 1))), models.color(m["colors"]["_shadowcolor"]))
    light, _ = models.toon_eyew(*args, ramp=1.0)
    dark, _ = models.toon_eyew(*args, ramp=0.0)
    return (models.baked(light, lut), light_ref), (models.baked(dark, lut), dark_ref)


@pytest.mark.parametrize("mid,limit", [
    ("cf_m_sirome_00", 0.006), ("cf_m_sirome_00_2", 0.006),
    ("cf_m_mayuge_00", 0.01), ("cf_m_eyeline_00_up", 0.01),
    # The eyelines' semi-transparent edges blend differently in the bake; fully opaque, they are within 0.008.
    ("cf_m_eyeline_kage", 0.015), ("cf_m_eyeline_down", 0.015),
])
def test_kk_toon_eyew_gives_back_the_bakes(mid, limit, lut):
    for model, reference in _eyew(Sample("kk"), mid, lut):
        assert difference(model, reference) < limit


def test_kk_toon_nose_gives_back_the_bakes(lut):
    sample = Sample("kk")
    m = sample.materials["cf_m_noseline_00"]
    light_ref, dark_ref, size = _bakes(sample, m)
    tex = sample.texture(m, "main", size=size)
    out, _ = models.toon_nose(tex[..., :3], tex[..., 3], models.color(m["colors"]["_Color"]))
    for reference in (light_ref, dark_ref):
        assert difference(models.baked(out, lut), reference) < 0.01
