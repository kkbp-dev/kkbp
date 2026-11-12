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


def _raster(paths, mid, size, attributes):
    """The material's mesh attributes (glTF names; UVs with v up) at each pixel of its first UV map,
    rows top-down as PIL gives them, as the exporter's flat mesh draws it: the island met first in
    vertex order in front. A dict of arrays, with a `covered` mask; NaN where no mesh is."""
    w, h = size
    out = {a: None for a in attributes}
    covered = np.zeros((h, w), dtype=bool)
    for path in paths:
        gltf, accessor = _glb(path)
        names = [m["name"] for m in gltf["materials"]]
        if mid not in names:
            continue
        prims = [p for m in gltf["meshes"] for p in m["primitives"] if p.get("material") == names.index(mid)]
        for prim in prims:
            uv0 = accessor(prim["attributes"]["TEXCOORD_0"]).astype(np.float64)
            values = {}
            for a in attributes:
                if a not in prim["attributes"]:
                    continue
                v = accessor(prim["attributes"][a]).astype(np.float64)
                if a.startswith("TEXCOORD"):
                    v[:, 1] = 1 - v[:, 1]  # glTF's v runs down
                values[a] = v
                if out[a] is None:
                    out[a] = np.full((h, w, v.shape[1]), np.nan)
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
                covered[yy[inside], xx[inside]] = True
                for a, v in values.items():
                    value = l1[..., None] * v[t[0]] + l2[..., None] * v[t[1]] + l3[..., None] * v[t[2]]
                    out[a][yy[inside], xx[inside]] = value[inside]
    out["covered"] = covered
    return out


def _second_uv(sample, mid, size):
    """The material's second UV map (v up) at each pixel of its first; off the mesh, the bake's quad,
    whose second UV map is its first."""
    w, h = size
    ys, xs = np.mgrid[0:h, 0:w]
    quad = np.stack([(xs + 0.5) / w, 1 - (ys + 0.5) / h], -1)
    r = _raster(sample.root.glob("outfits/*/outfit.glb"), mid, size, ["TEXCOORD_1"])
    return quad if r["TEXCOORD_1"] is None else np.where(r["covered"][..., None], r["TEXCOORD_1"], quad)


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


@pytest.mark.parametrize("game,mid,line_blue,limits", [
    ("kk", "cf_m_tooth", 1.0, (0.005, 0.005)), ("kk", "cf_m_tang", 1.0, (0.005, 0.015)),
    # KKS's Koikano/main_clothes_item, approximated without the line mask's darkening; legacy was
    # 0.073 / 0.051 and 0.081 / 0.076.
    ("kks", "cf_m_tooth", 0.0, (0.005, 0.015)), ("kks", "cf_m_tang", 0.0, (0.005, 0.05)),
])
def test_main_item_gives_back_the_bakes(game, mid, line_blue, limits, lut):
    """The tongue has no main texture (white); KK's dark side's red is 0.02 short where it nears 1."""
    sample = Sample(game)
    m = sample.materials[mid]
    size = (256, 256)
    tex = sample.texture(m, "main", size=size)
    main = np.ones(size + (3,)) if tex is None else tex[..., :3]
    colors = [models.color(m["colors"][k]) for k in ("_Color", "_Color2", "_Color3")]
    for ramp, variant, limit in ((1.0, "light", limits[0]), (0.0, "dark", limits[1])):
        out = models.main_item(main, _mask(sample, m, "color_mask", size), _mask(sample, m, "detail_mask", size),
                               _mask(sample, m, "line_mask", size), colors, m["floats"],
                               models.color(m["colors"]["_ShadowColor"]), ramp, line_blue=line_blue)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < limit


class _BodyOnly:
    """A sample whose meshes `_second_uv` reads from body.glb (the eyes, the face)."""

    def __init__(self, sample):
        self.root = type("Root", (), {"glob": staticmethod(lambda _: [sample.root / "body.glb"])})()


def _image(sample, texture):
    with Image.open(sample.root / texture["file"]) as im:
        return (np.asarray(im.convert("RGBA"), dtype=np.float64) / 255)[::-1]


@pytest.mark.parametrize("mid", ["cf_m_hitomi_00", "cf_m_hitomi_00_2"])
def test_kk_toon_eye_gives_back_the_bakes(mid, lut):
    """The iris turned by `_rotation` then placed by its texture transform; the highlights on the
    second UV map, on the eye mesh only (the bake's quad has them cleared)."""
    sample = Sample("kk")
    m = sample.materials[mid]
    light = sample.texture(m, "main", "light")
    size = light.shape[1::-1]
    h, w = light.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    u, v = (xs + 0.5) / w, 1 - (ys + 0.5) / h
    tex = next(t for t in m["textures"] if t.get("raw") == "_MainTex" and not t.get("variant"))
    ru, rv = models.eye_rotation(u, v, m["floats"]["_rotation"])
    main = models._bilinear(_image(sample, tex), ru * tex["scale"][0] + tex["offset"][0], rv * tex["scale"][1] + tex["offset"][1])
    uv = _second_uv(_BodyOnly(sample), mid, size)
    on = (np.abs(uv - np.stack([u, v], -1)).sum(-1) > 1e-9)[..., None]
    overlays = []
    for raw in ("_overtex1", "_overtex2"):
        t = next(t for t in m["textures"] if t.get("raw") == raw)
        read = models._bilinear(_image(sample, t), uv[..., 0] * t["scale"][0] + t["offset"][0],
                                uv[..., 1] * t["scale"][1] + t["offset"][1])
        overlays.append(np.where(on, read, 0))
    colors = [np.append(models.color(m["colors"][k]), m["colors"][k][3]) for k in ("_overcolor1", "_overcolor2")]
    for ramp, variant in ((1.0, "light"), (0.0, "dark")):
        out, _ = models.toon_eye(main, *overlays, *colors, m["floats"]["_isHighLight"],
                                 models.color(m["colors"]["_shadowcolor"]), ramp)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < 0.006


def test_kk_create_eye_gives_back_the_composited_iris():
    sample = Sample("kk")
    m = sample.materials["cf_m_hitomi_00"]
    create = m["extensions"]["kk"]["create"]
    main = sample.texture(create, "main")
    h, w = main.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    u, v = (xs + 0.5) / w, 1 - (ys + 0.5) / h
    grad = create["vectors"]["_grad"]
    s = 1 - grad[3]
    mask = next(t for t in create["textures"] if t.get("role") == "color_mask")
    at_grad = models._bilinear(_image(sample, mask), (u + grad[0]) * 2 * s + 0.5 - s, (v + grad[1]) * 2 * s + 0.5 - s)
    out = models.create_eye(main[..., :3], at_grad, models.color(create["colors"]["_Color"]),
                            models.color(create["colors"]["_Color2"]), create["floats"]["_Blend"])
    assert difference(out, sample.texture(m, "main", size=(w, h))) < 0.003


def _create_raw(sample, create, name, u, v, uv=None, default=0.0):
    """A create texture by its Raw Property, read at `uv` (default the first UV map) through its own
    transform; `default` everywhere when the material has none."""
    t = next((t for t in create["textures"] if t.get("raw") == name), None)
    if t is None:
        return np.full(u.shape + (4,), default)
    uu, vv = (u, v) if uv is None else uv
    return models._bilinear(_image(sample, t), uu * t["scale"][0] + t["offset"][0], vv * t["scale"][1] + t["offset"][1])


@pytest.mark.parametrize("game", ["kk", "kks"])
@pytest.mark.parametrize("mid", ["cf_m_body", "cf_m_face_00"])
def test_create_body_and_head_give_back_the_composited_skin(game, mid):
    """A missing tan line texture reads white (the body's skin colour unmixed); missing decals read
    transparent. KKS's create_skinbody and create_skinface composite the same."""
    sample = Sample(game)
    m = sample.materials[mid]
    create = m["extensions"]["kk"]["create"]
    reference = sample.texture(m, "main")
    h, w = reference.shape[:2]
    ys, xs = np.mgrid[0:h, 0:w]
    u, v = (xs + 0.5) / w, 1 - (ys + 0.5) / h
    main = sample.texture(create, "main", size=(w, h))[..., :3]
    mask = _mask(sample, create, "color_mask", (w, h))
    colors = {k: np.append(models.color(c), c[3]) for k, c in create["colors"].items()}
    vec = create["vectors"]
    raw = lambda name, uv=None, default=0.0: _create_raw(sample, create, name, u, v, uv, default)  # noqa: E731
    if mid == "cf_m_body":
        out = models.create_body(main, mask, raw("_Texture4", default=1.0), raw("_Texture3", models.paint_uv(u, v, vec["_paint1"])),
                                 raw("_Texture6", models.paint_uv(u, v, vec["_paint2"])), raw("_paintmask"), colors)
    else:
        out = models.create_head(main, mask, raw("_Texture4", models.face_uv(u, v, vec["_tex4uv"])),
                                 raw("_Texture5", models.face_uv(u, v, vec["_tex5uv"])),
                                 raw("_Texture3", models.paint_uv(u, v, vec["_paint1"])),
                                 raw("_Texture7", models.paint_uv(u, v, vec["_paint2"])), raw("_paintmask"),
                                 raw("_Texture6", models.mole_uv(u, v, vec["_hokuro"])), colors)
    assert difference(out, reference) < 0.003


@pytest.mark.parametrize("game,mid,light,limits", [
    ("kk", "cf_m_body", models.KK, (0.01, 0.01)), ("kk", "cf_m_face_00", models.KK, (0.01, 0.015)),
    # KKS's Koikano/main_skin, approximated (models.KKS_SKIN); legacy was 0.051 / 0.028 and 0.094 / 0.059.
    ("kks", "cf_m_body", models.KKS_SKIN, (0.012, 0.03)), ("kks", "cf_m_face_00", models.KKS_SKIN, (0.008, 0.035)),
])
def test_main_skin_gives_back_the_bakes(game, mid, light, limits, lut):
    """With the overlays on the mesh's second to fourth UV maps, scaled by the vertex colour."""
    sample = Sample(game)
    m = sample.materials[mid]
    floats = m["floats"]
    size = (512, 512)
    r = _raster([sample.root / "body.glb"], mid, size, ["TEXCOORD_1", "TEXCOORD_2", "TEXCOORD_3", "COLOR_0"])
    on = r["covered"][..., None]
    vertex = np.ones(size + (4,)) if r["COLOR_0"] is None else np.nan_to_num(r["COLOR_0"], nan=1.0)
    uv1, uv2, uv3 = (np.nan_to_num(r[f"TEXCOORD_{i}"]) for i in (1, 2, 3))
    reads = []
    for k, uv in ((1, models.nipple_uv(uv1, vertex[..., 0:1], floats.get("_nip", 0), floats.get("_nipsize", 0))),
                  (2, uv2 * vertex[..., 2:3]), (3, uv3)):
        t = next((t for t in m["textures"] if t.get("raw") == f"_overtex{k}"), None)
        read = np.zeros(size + (4,)) if t is None else models._bilinear(
            _image(sample, t), uv[..., 0] * t["scale"][0] + t["offset"][0], uv[..., 1] * t["scale"][1] + t["offset"][1])
        reads.append(np.where(on, read, 0))
    colors = [np.append(models.color(m["colors"][f"_overcolor{k}"]), m["colors"][f"_overcolor{k}"][3]) for k in (1, 2, 3)]
    col = models.skin_overlays(sample.texture(m, "main", size=size)[..., :3], *reads, colors, floats)
    for ramp, variant, limit in ((1.0, "light", limits[0]), (0.0, "dark", limits[1])):
        out = models.main_skin(col, _mask(sample, m, "detail_mask", size), _mask(sample, m, "line_mask", size), floats,
                               ramp, light)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < limit


@pytest.mark.parametrize("mid,limits", [
    ("cf_top_defshirt_m", (0.025, 0.04)), ("cf_bot_defpants_m", (0.015, 0.055)), ("cf_m_bra_01", (0.012, 0.025)),
    ("cf_m_shorts_01", (0.013, 0.028)), ("cf_m_socks_crewori", (0.035, 0.012)), ("cf_m_shoes_tennis", (0.008, 0.03)),
])
def test_kks_main_clothes_opaque_comes_close_to_kk_main_opaque(mid, limits, lut):
    """KKS's Koikano/main_clothes_opaque against KK's model with KK's values: closer than the legacy
    templates (0.04 to 0.16), not exact (its physically based half isn't modelled)."""
    sample = Sample("kks")
    m = sample.materials[mid]
    size = (128, 128)
    main = sample.texture(m, "main", size=size)[..., :3]
    for ramp, variant, limit in ((1.0, "light", limits[0]), (0.0, "dark", limits[1])):
        out = models.main_opaque(main, _mask(sample, m, "detail_mask", size), _mask(sample, m, "line_mask", size),
                                 m["floats"], models.color(m["colors"]["_ShadowColor"]), ramp)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < limit


def test_kk_main_emblem_gives_back_the_bakes(lut):
    """`_ambientshadow` is unset (0). At 256 pixels the light side's sharp edges resample apart."""
    sample = Sample("kk")
    m = sample.materials["cf_m_emblem"]
    light = sample.texture(m, "main", "light")
    size = light.shape[1::-1]
    main = sample.texture(m, "main", size=size)[..., :3]
    no_ambient = models.Light(light=1.0, ambient=0.0)
    for ramp, variant, limit in ((1.0, "light", 0.025), (0.0, "dark", 0.005)):
        out = models.main_emblem(main, ramp, no_ambient)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < limit


class _Export(Sample):
    """A KK export besides the Golden Sample: importer/tests/.work/extra/kk-alpha, made from a card with
    main_alpha clothes and accessories (`scripts/auto-export.sh kk <card> importer/tests/.work/extra/kk-alpha`).
    Its tests skip without it."""

    def __init__(self):
        folder = REPO / "importer" / "tests" / ".work" / "extra" / "kk-alpha"
        bundles = sorted(folder.glob("*/materials.json")) if folder.is_dir() else []
        if not bundles:
            pytest.skip("no extra KK export with main_alpha in importer/tests/.work/extra/kk-alpha")
        self.root = bundles[-1].parent
        self.materials = {m["id"]: m for m in json.loads((self.root / "materials.json").read_text())["materials"]}


@pytest.mark.parametrize("mid,limits", [
    ("acs_m_hair_butterfly", (0.02, 0.015)), ("cf_m_panst_02", (0.008, 0.004)),
    ("cf_m_top_inner01", (0.004, 0.006)), ("cf_m_top_jacket06", (0.025, 0.005)),
])
def test_kk_main_alpha_gives_back_the_bakes(mid, limits, lut):
    sample = _Export()
    m = sample.materials[mid]
    size = (256, 256)
    main = sample.texture(m, "main", size=size)[..., :3]
    spec = models.color(m["colors"].get("_SpecularColor", (1, 1, 1, 1)))
    for ramp, variant, limit in ((1.0, "light", limits[0]), (0.0, "dark", limits[1])):
        out = models.main_alpha(main, _mask(sample, m, "detail_mask", size), m["floats"], spec,
                                models.color(m["colors"]["_ShadowColor"]), ramp)
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < limit


@pytest.mark.parametrize("mid", ["acs_m_schandbag", "acs_m_megane06"])
def test_kk_main_item_reads_its_other_ramp_and_loses_its_highlight_in_shadow(mid, lut):
    """The handbag's detail red (1) swaps in its other ramp and draws the highlight, on the lit side
    only; the glasses frame has neither."""
    sample = _Export()
    m = sample.materials[mid]
    size = (256, 256)
    ramp_texture = next(t for t in m["textures"] if t.get("raw") == "_AnotherRamp")
    row = _image(sample, ramp_texture)[4, :, 0]
    colors = [models.color(m["colors"][k]) for k in ("_Color", "_Color2", "_Color3")]
    for ramp, variant in ((1.0, "light"), (0.0, "dark")):
        out = models.main_item(np.ones(size + (3,)), _mask(sample, m, "color_mask", size), _mask(sample, m, "detail_mask", size),
                               np.zeros(size + (4,)), colors, m["floats"], models.color(m["colors"]["_ShadowColor"]), ramp,
                               another_ramp=(row[0], row[-1]))
        assert difference(models.baked(out, lut), sample.texture(m, "main", variant, size)) < 0.01
