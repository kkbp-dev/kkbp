"""Opening valid bundles: what the sections and lookups hand out."""

from types import MappingProxyType

import pytest

import bundle
from bundle_builder import BundleBuilder


@pytest.mark.parametrize("game", ["KK", "KKS", "SVS"])
def test_default_bundle_opens_without_warnings(build, game):
    b = bundle.open_bundle(build(BundleBuilder(game)))
    assert b.game == game
    assert b.warnings == ()


def test_manifest(build):
    path = build()
    m = bundle.open_bundle(path).manifest
    assert (m.schema_version, m.character_name, m.exported_at) == ("1.0", "Test Chara", "2026-11-01T12:00:00Z")
    assert m.card == path / "card.png"
    assert m.options.physics is True and m.options.all_outfits is False
    assert [(p.kind, p.outfit, p.mesh, p.data) for p in m.passes] == [
        ("body", None, "body.glb", "body.json"), ("outfit", 0, "outfits/00/outfit.glb", "outfits/00/outfit.json")]


def test_bundle_without_card(build):
    builder = BundleBuilder()
    builder.card = False
    assert bundle.open_bundle(build(builder)).manifest.card is None


def test_open_accepts_the_manifest_path(build):
    path = build()
    assert bundle.open_bundle(path / "manifest.json").path == path


def test_skeleton_lookups(build):
    s = bundle.open_bundle(build()).skeleton
    head = s.by_role("head")
    assert head.id == "cf_j_head" and head.parent == "cf_j_neck" and head.group == "deform"
    assert s.bone("cf_j_head") is head
    assert s.bone("missing") is None and s.by_role("jaw") is None
    assert [b.id for b in s.in_group("helper")] == ["N_Hair_pony"]
    assert head.translation == (0.0, 0.1, 0.0) and head.rotation == (0.0, 0.0, 0.0, 1.0)


def test_material_textures(build):
    path = build()
    b = bundle.open_bundle(path)
    body = b.material("cf_m_body")
    assert body.role == "body" and body.blend_mode == "opaque"
    assert body.texture("main").file == path / "textures/0001.png"
    assert body.texture("main", variant="light").variant == "light"
    assert body.texture("main", variant="dark").variant == "dark"
    assert body.texture("alpha_mask") is None
    assert [t.variant for t in body.textures_for("_MainTex")] == [None, "light", "dark"]
    assert [t.raw for t in body.textures if t.role is None] == ["_liquidmask"]
    eye = b.material("cf_m_hitomi_00")
    assert [t.raw for t in eye.textures_with_role("overlay")] == ["_overtex1", "_overtex2"]
    with pytest.raises(ValueError):
        eye.texture("overlay")
    gag = b.material("cf_m_gageye_00")
    assert gag.texture("main") is None
    assert gag.texture("main", pattern="cf_t_gageye_02").pattern == "cf_t_gageye_02"
    assert [m.id for m in b.materials_with_role("hair")] == ["c_m_hair_00"]
    assert b.material("missing") is None


def test_material_values_are_read_only(build):
    body = bundle.open_bundle(build()).material("cf_m_body")
    assert body.colors["_Color"] == (1.0, 1.0, 1.0, 1.0)
    assert body.floats["_Cutoff"] == 0.5
    with pytest.raises(TypeError):
        body.colors["_Color"] = (0, 0, 0, 0)
    with pytest.raises(AttributeError):
        body.role = "face"


@pytest.mark.parametrize("game", ["KK", "KKS"])
def test_create_materials(build, game):
    path = build(BundleBuilder(game))
    b = bundle.open_bundle(path)
    create = b.material("cf_m_body").create
    assert create.shader == "Shader Forge/create_body"
    assert create.colors["_Color"] == (1.0, 0.5, 0.5, 1.0)
    assert create.texture("main").file.parent == path / "textures"
    assert [t.raw for t in create.textures_for("_ColorMask")] == ["_ColorMask"]
    assert b.material("ct_top_shirt").create.shader == "Shader Forge/create_topN"
    assert b.material("cf_m_face_00").create is None
    assert b.material("cf_m_body").extension("kk") == {}  # create is read out of the Game Extension


def test_svs_has_no_create_materials(build):
    b = bundle.open_bundle(build(BundleBuilder("SVS")))
    assert all(m.create is None for m in b.materials)


def test_passes(build):
    path = build()
    b = bundle.open_bundle(path)
    body, outfit = b.passes
    assert (body.kind, body.outfit, body.mesh_path) == ("body", None, path / "body.glb")
    assert (outfit.kind, outfit.outfit, outfit.data_path) == ("outfit", 0, path / "outfits/00/outfit.json")
    assert [m.id for m in outfit.meshes] == ["o_hair_b", "o_top_shirt", "o_top_shirt_alt"]
    assert outfit.materials == ("c_m_hair_00", "ct_top_shirt")
    assert [m.alternate for m in outfit.meshes] == [False, False, True]
    assert body.body_textures == ()
    (bt,) = outfit.body_textures
    assert bt.material == "cf_m_body" and bt.texture.role == "alpha_mask"
    assert b.mesh("o_top_shirt").materials == ("ct_top_shirt",)
    assert b.pass_of("o_top_shirt") is outfit and b.pass_of("cf_O_face") is body
    assert b.mesh("missing") is None and b.pass_of("missing") is None


def test_expressions(build):
    e = bundle.open_bundle(build()).expressions
    happy = e.on_mesh("cf_O_face")[0]
    assert (happy.target, happy.category, happy.name, happy.game_name) == ("Eye Happy", "eye", "Eye Happy", "笑い")
    custom = [x for x in e.records if x.category == "other"][0]
    assert custom.name is None and custom.target == custom.game_name
    gag = e.effect("Gag Heart Eyes")
    assert gag.shows == ("cf_O_gag_eye_00",) and gag.hides == ("cf_Ohitomi_L", "cf_Ohitomi_R")
    (change,) = gag.material_changes
    assert change.material == "cf_m_gageye_00" and change.textures[0].pattern == "cf_t_gageye_02"
    assert change.vectors["_TileAnimation"] == (1.0, 1.0, 1.0, 0.0)
    assert e.effect("Eye Happy") is None


def test_physics(build):
    p = bundle.open_bundle(build()).physics
    (chain,) = p.chains
    assert chain.root == "cf_J_hairB_top" and chain.outfit == 0 and chain.colliders == ("Col_Head",)
    assert [x.bone for x in chain.particles] == ["cf_J_hairB_top", "cf_J_hairB_00"]
    assert p.colliders[0].bone == "cf_j_head" and p.colliders[0].direction == "y"


@pytest.mark.parametrize("game, present, absent", [
    ("KK", ["kk"], ["kks", "svs"]),
    ("KKS", ["kk", "kks"], ["svs"]),
    ("SVS", ["svs"], ["kk", "kks"]),
])
def test_game_extensions(build, game, present, absent):
    b = bundle.open_bundle(build(BundleBuilder(game)))
    for key in present:
        assert b.extension(key) == {} and isinstance(b.extension(key), MappingProxyType)
        assert b.material("cf_m_body").extension(key) == {}
        assert b.passes[0].extension(key) == {}
        assert b.manifest.options.extension(key) == {}
    for key in absent:
        assert b.extension(key) is None
        assert b.expressions.records[0].extension(key) is None


def test_cache_dir(build):
    path = build()
    b = bundle.open_bundle(path)
    assert not (path / "kkbp_cache").exists()
    logs = b.cache_dir("log")
    assert logs == path / "kkbp_cache" / "log" and logs.is_dir()
    for bad in ("", "Log", "../x", "a/b"):
        with pytest.raises(ValueError):
            b.cache_dir(bad)


def test_empty_bundle(build):
    b = bundle.open_bundle(build(BundleBuilder(empty=True)))
    assert [p.kind for p in b.passes] == ["body"] and b.passes[0].meshes == ()
    assert b.materials == () and b.expressions.records == () and b.physics.chains == ()
