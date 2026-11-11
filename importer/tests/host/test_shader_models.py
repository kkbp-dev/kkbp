"""The shader models (importer/tools/game_shaders/models.py) against the Golden Samples: each model,
run on a material's own bundle textures and colours, gives back the bundle's light and dark bakes.
The thresholds are mean absolute differences per channel on sRGB values over opaque pixels; the
legacy edit templates were 0.03 to 0.31 from the same bakes (ADR 0026)."""

import json
import struct

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
def _eyew(sample, mid, lut, light):
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
    lit, _ = models.toon_eyew(*args, ramp=1.0, light=light)
    dark, _ = models.toon_eyew(*args, ramp=0.0, light=light)
    return (models.baked(lit, lut), light_ref), (models.baked(dark, lut), dark_ref)


@pytest.mark.parametrize("mid,limit", [
    ("cf_m_sirome_00", 0.006), ("cf_m_sirome_00_2", 0.006),
    ("cf_m_mayuge_00", 0.01), ("cf_m_eyeline_00_up", 0.01),
    # The eyelines' semi-transparent edges blend differently in the bake; fully opaque, they are within 0.008.
    ("cf_m_eyeline_kage", 0.015), ("cf_m_eyeline_down", 0.015),
])
@pytest.mark.parametrize("game,light", [("kk", models.KK), ("kks", models.KKS)])
def test_toon_eyew_gives_back_the_bakes(game, light, mid, limit, lut):
    """KK's toon_eyew_lod0 and KKS's Koikano/main_eyew, each with its Game's maker light."""
    for model, reference in _eyew(Sample(game), mid, lut, light):
        assert difference(model, reference) < limit


@pytest.mark.parametrize("game", ["kk", "kks"])
def test_toon_nose_gives_back_the_bakes(game, lut):
    """KK's toon_nose_lod0; KKS's Koikano/main_nose bakes the same."""
    sample = Sample(game)
    m = sample.materials["cf_m_noseline_00"]
    light_ref, dark_ref, size = _bakes(sample, m)
    tex = sample.texture(m, "main", size=size)
    out, _ = models.toon_nose(tex[..., :3], tex[..., 3], models.color(m["colors"]["_Color"]))
    for reference in (light_ref, dark_ref):
        assert difference(models.baked(out, lut), reference) < 0.01


def _glb(path):
    """A glTF binary's JSON and an accessor reader."""
    data = path.read_bytes()
    n = struct.unpack("<I", data[12:16])[0]
    gltf, binary = json.loads(data[20:20 + n]), data[20 + n + 8:]

    def accessor(i):
        a = gltf["accessors"][i]
        view = gltf["bufferViews"][a["bufferView"]]
        comps = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        dtype = np.dtype({5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]])
        offset = view.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = view.get("byteStride") or comps * dtype.itemsize
        raw = np.frombuffer(binary, np.uint8, count=stride * (a["count"] - 1) + comps * dtype.itemsize, offset=offset)
        rows = np.lib.stride_tricks.as_strided(raw, (a["count"], comps * dtype.itemsize), (stride, 1))
        return rows.copy().view(dtype).reshape(a["count"], comps)
    return gltf, accessor


def _second_uv(sample, mid, size):
    """The material's second UV map (v up) at each pixel of its first, rows top-down as PIL gives
    them, as the exporter's flat mesh draws it: the island met first in vertex order in front, and
    off the mesh the quad, whose second UV map is its first."""
    w, h = size
    ys, xs = np.mgrid[0:h, 0:w]
    out = np.stack([(xs + 0.5) / w, 1 - (ys + 0.5) / h], -1)
    for path in sample.root.glob("outfits/*/outfit.glb"):
        gltf, accessor = _glb(path)
        names = [m["name"] for m in gltf["materials"]]
        if mid not in names:
            continue
        prims = [p for m in gltf["meshes"] for p in m["primitives"] if p.get("material") == names.index(mid)]
        for prim in prims:
            uv0 = accessor(prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
            uv1 = accessor(prim["attributes"]["TEXCOORD_1"]).astype(np.float64)
            uv1[:, 1] = 1 - uv1[:, 1]  # glTF's v runs down
            tris = accessor(prim["indices"]).reshape(-1, 3).astype(np.int64)
            parent = np.arange(len(uv0))

            def find(i):
                while parent[i] != i:
                    parent[i] = parent[parent[i]]
                    i = parent[i]
                return i
            for a, b, c in tris:
                for other in (b, c):
                    ra, ro = find(a), find(other)
                    if ra != ro:
                        parent[ro] = ra
            first = {}
            for i in range(len(uv0)):
                first.setdefault(find(i), i)
            order = sorted(range(len(tris)), key=lambda t: -first[find(tris[t][0])])
            px = uv0 * [w, h] - 0.5
            for t in tris[order]:
                p = px[t]
                x0, y0 = np.maximum(np.floor(p.min(0)).astype(int), 0)
                x1, y1 = np.minimum(np.ceil(p.max(0)).astype(int), [w - 1, h - 1])
                if x1 < x0 or y1 < y0:
                    continue
                yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1]
                (ax, ay), (bx, by), (cx, cy) = p
                den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
                if abs(den) < 1e-12:
                    continue
                l1 = ((by - cy) * (xx - cx) + (cx - bx) * (yy - cy)) / den
                l2 = ((cy - ay) * (xx - cx) + (ax - cx) * (yy - cy)) / den
                l3 = 1 - l1 - l2
                inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6)
                value = l1[..., None] * uv1[t[0]] + l2[..., None] * uv1[t[1]] + l3[..., None] * uv1[t[2]]
                out[yy[inside], xx[inside]] = value[inside]
    return out


@pytest.mark.parametrize("game", ["kk", "kks"])
@pytest.mark.parametrize("mid", ["cf_m_hair_b_08_00", "cf_m_hair_f_14_00_i"])
def test_main_hair_gives_back_the_bakes(game, mid, lut):
    """KK's main_hair and main_hair_front, with KK's Maker Light; KKS's hair_main_sun and
    hair_main_sun_front bake the same. At 512 pixels, to keep it quick; what remains is at UV seams,
    where the exporter's mesh and quad renders meet."""
    sample = Sample(game)
    m = sample.materials[mid]
    size = (512, 512)
    tex = sample.texture(m, "main", size=size)
    main = np.ones(size + (3,)) if tex is None else tex[..., :3]
    color_mask = sample.texture(m, "color_mask", size=size)[..., :3]
    detail_mask = sample.texture(m, "detail_mask", size=size)[..., :3]
    gt = next(t for t in m["textures"] if t.get("raw") == "_HairGloss")
    with Image.open(sample.root / gt["file"]) as im:
        gloss_image = (np.asarray(im.convert("RGBA"), dtype=np.float64) / 255)[::-1]
    uv = _second_uv(sample, mid, size)
    colors = [models.color(m["colors"][k]) for k in ("_Color", "_Color2", "_Color3")]
    front = m["shader"].endswith("_front")
    for ramp, variant in ((1.0, "light"), (0.0, "dark")):
        u = uv[..., 0] + models.hair_gloss_shift(ramp, front)
        gloss = models.sample_repeat(gloss_image, u * gt["scale"][0] + gt["offset"][0],
                                     uv[..., 1] * gt["scale"][1] + gt["offset"][1])[..., 0:1]
        out = models.main_hair(main, color_mask, detail_mask, gloss, colors, models.color(m["colors"]["_ShadowColor"]),
                               m["floats"]["_ShadowExtend"], ramp)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < 0.01


def _mask(sample, holder, role, size):
    """A mask as the shader reads it: black where the material has none."""
    t = sample.texture(holder, role, size=size)
    return np.zeros(size[::-1] + (4,)) if t is None else t


@pytest.mark.parametrize("mid", ["cf_m_top_inner01", "cf_m_top_jacket06", "cf_m_bot_skirt01", "cf_m_socks_high01"])
def test_kk_create_topN_gives_back_the_composited_texture(mid):
    """The skirt has a pattern, scaled; the bundle's main texture is the game's own composite."""
    sample = Sample("kk")
    m = sample.materials[mid]
    create = m["extensions"]["kk"]["create"]
    reference = sample.texture(m, "main")
    size = reference.shape[1::-1]
    main = sample.texture(create, "main", size=size)
    h, w = reference.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    u, v = (xs + 0.5) / w, 1 - (ys + 0.5) / h
    patterns = []
    for k in (1, 2, 3):
        t = next((t for t in create["textures"] if t.get("raw") == f"_PatternMask{k}"), None)
        if t is None:
            patterns.append(np.ones((h, w, 1)))
            continue
        with Image.open(sample.root / t["file"]) as im:
            image = (np.asarray(im.convert("RGBA"), dtype=np.float64) / 255)[::-1]
        su, sv = (20 - 19 * create["floats"].get(f"_PatternScale{k}{a}", 0) for a in "uv")
        patterns.append(models.sample_repeat(image, u * su * t["scale"][0] + t["offset"][0],
                                             v * sv * t["scale"][1] + t["offset"][1])[..., 0:1])
    colors = [models.color(create["colors"][k]) for k in ("_Color", "_Color2", "_Color3")]
    pattern_colors = [np.append(models.color(create["colors"][f"_Color{k}_2"]), create["colors"][f"_Color{k}_2"][3])
                      for k in (1, 2, 3)]
    out, _ = models.create_topN(main[..., :3], main[..., 3], _mask(sample, create, "color_mask", size), patterns,
                                colors, pattern_colors)
    assert difference(out, reference) < 0.006


@pytest.mark.parametrize("mid,limit", [
    ("cf_m_top_inner01", 0.005), ("cf_m_top_deco01", 0.005), ("cf_m_bot_skirt01", 0.005),
    ("cf_m_shoes_roafer01", 0.006), ("cf_m_top_jacket06", 0.01),
    # Fine stripes and seams, resampled to 256 pixels here.
    ("cf_m_bra_01", 0.015), ("cf_m_shorts_01", 0.015), ("cf_m_socks_high01", 0.015),
])
def test_kk_main_opaque_gives_back_the_bakes(mid, limit, lut):
    sample = Sample("kk")
    m = sample.materials[mid]
    size = (256, 256)
    main = sample.texture(m, "main", size=size)[..., :3]
    for ramp, variant in ((1.0, "light"), (0.0, "dark")):
        out = models.main_opaque(main, _mask(sample, m, "detail_mask", size), _mask(sample, m, "line_mask", size),
                                 m["floats"], models.color(m["colors"]["_ShadowColor"]), ramp)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < limit


@pytest.mark.parametrize("mid,limit", [("cf_m_tooth", 0.005), ("cf_m_tang", 0.015)])
def test_kk_main_item_gives_back_the_bakes(mid, limit, lut):
    """The tongue has no main texture (white); its dark side's red is 0.02 short where it nears 1."""
    sample = Sample("kk")
    m = sample.materials[mid]
    size = (256, 256)
    tex = sample.texture(m, "main", size=size)
    main = np.ones(size + (3,)) if tex is None else tex[..., :3]
    colors = [models.color(m["colors"][k]) for k in ("_Color", "_Color2", "_Color3")]
    for ramp, variant in ((1.0, "light"), (0.0, "dark")):
        out = models.main_item(main, _mask(sample, m, "color_mask", size), _mask(sample, m, "detail_mask", size),
                               _mask(sample, m, "line_mask", size), colors, m["floats"],
                               models.color(m["colors"]["_ShadowColor"]), ramp)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < limit
