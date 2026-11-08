"""Edit material, Cancel, Reset, Save and Link hair on a copy of the KK golden sample (D37-D46)."""

import shutil

import bpy
import pytest

from bundle_builder import BundleBuilder
from conftest import golden, kkbp, submodule

character = submodule("character")
templates = submodule("templates")
edit_material = submodule("tools.edit_material")
link_hair = submodule("tools.link_hair")


@pytest.fixture(scope="module")
def kk_copy(tmp_path_factory):
    copy = tmp_path_factory.mktemp("edit") / "kk"
    shutil.copytree(golden("kk"), copy, ignore=shutil.ignore_patterns("kkbp_cache"))
    return copy


@pytest.fixture
def ch(kk_copy):
    result = kkbp.api.import_bundle(kk_copy, hooks=[])
    assert result.ok
    return character.Character(result.character_key)


def _image(mat, slot):
    node = templates.texture_node(mat, slot)
    return node.image if node is not None else None


def _users(material):
    return [o for o in bpy.data.objects if any(s.material == material for s in o.material_slots)]


def test_editing_the_body_fills_it_from_the_create_material(ch):
    body = ch.material("cf_m_body")
    users = _users(body)
    edit = edit_material.edit(ch, body, log=lambda *_: None)
    assert edit.name == "Edit cf_m_body" and edit[templates.TEMPLATE] == "KK Body"
    assert _users(edit) == users and not _users(body) and body.use_fake_user
    filled = set(edit[edit_material.FILLED])
    assert {"main", "main.dark", "plain", "color_mask", "line_mask", "detail_mask", "overlay1", "overlay2"} <= filled
    assert all(_image(edit, slot) is not None for slot in filled)
    # Its texture groups are its own (ADR 0025); the toon shading stays shared.
    own = templates.own_groups(edit)
    assert [g.name for g in own] == [".Tex Body Edit cf_m_body", ".Tex NSFW Edit cf_m_body"]
    assert all(g.users == 1 for g in own)
    # The skin colour is the create material's, and its dark version is darker.
    light = templates.param(edit, "skin_color.light").default_value
    dark = templates.param(edit, "skin_color.dark").default_value
    assert sum(dark[:3]) < sum(light[:3]) and light[0] > 0.5
    # The dark texture is made once, into the Cache.
    cache = ch.bundle().cache_dir("edit")
    assert any(".dark." in p.name for p in cache.iterdir())
    assert edit_material.edit(ch, edit) is edit


def test_cancel_restores_the_original_and_removes_the_copies(ch):
    body = ch.material("cf_m_body")
    users = _users(body)
    edit = edit_material.edit(ch, body, log=lambda *_: None)
    groups = [g.name for g in templates.own_groups(edit)]
    assert edit_material.cancel(edit) == body
    assert _users(body) == users and not body.use_fake_user
    assert "Edit cf_m_body" not in bpy.data.materials
    assert not any(name in bpy.data.node_groups for name in groups)


def test_editing_again_reuses_the_edit_material(ch):
    face = ch.material("cf_m_face_00")
    edit = edit_material.edit(ch, face, log=lambda *_: None)
    edit_material.cancel(edit)
    again = edit_material.edit(ch, face, log=lambda *_: None)
    assert again.name == "Edit cf_m_face_00"
    reset = edit_material.reset(ch, again, log=lambda *_: None)
    assert reset.name == "Edit cf_m_face_00" and _users(reset)


@pytest.mark.parametrize("id, template, slots, params", [
    ("cf_m_face_00", "KK Face", {"main", "plain", "color_mask", "texture4", "overlay2", "overlay3"},
     ("skin_color.light", "detail_color.dark", "light_blush_color.light")),
    ("cf_m_top_inner01", "KK General", {"main", "main.dark", "color_mask.plain", "detail_mask", "normal"},
     ("color_mask_red.light", "pattern_color_blue.dark")),
    ("cf_m_bot_skirt01", "KK General", {"pattern_mask1"}, ("color_mask_red.light",)),
    ("cf_m_hair_b_08_00", "KK Hair", {"color_mask", "detail_mask", "hair_gloss"}, ("hair_color.light",)),
    # Saturated, the eyebrows' dark colour is black, as the game bakes it.
    ("cf_m_mayuge_00", "KK Eyebrows (mayuge)", {"main"}, ("eyebrow_color",)),
    ("cf_m_tang", "KK General", {"color_mask", "detail_mask"}, ("color_mask_red.light",)),
])
def test_each_template_gets_its_slots_and_colours(ch, id, template, slots, params):
    mat = ch.material(id)
    edit = edit_material.edit(ch, mat, log=lambda *_: None)
    assert edit[templates.TEMPLATE] == template
    assert slots <= set(edit[edit_material.FILLED])
    for name in params:
        value = templates.param(edit, name).default_value
        assert tuple(value) != (0.0, 0.0, 0.0, 1.0) if hasattr(value, "__len__") else True, name


def test_only_hair_and_eyebrows_saturate_by_default(ch):
    """ADR 0026: they bake closest to the game saturated; the other materials don't."""
    b = ch.bundle()
    for id in ("cf_m_hair_b_08_00", "cf_m_mayuge_00", "cf_m_top_inner01"):
        edit = edit_material.edit(ch, ch.material(id), log=lambda *_: None)
        color = templates.param(edit, "hair_color.light" if "hair" in id else
                                "eyebrow_color" if "mayuge" in id else "color_mask_green.light").default_value
        source = b.material(id).colors["_Color"] if "top" not in id else b.material(id).create.colors["_Color2"]
        plain = edit_material._linear(source)
        assert (tuple(color) != pytest.approx(plain, abs=1e-3)) == (id != "cf_m_top_inner01"), id


def test_the_hair_without_a_plain_main_texture_keeps_the_colours(ch):
    edit = edit_material.edit(ch, ch.material("cf_m_hair_b_08_00"), log=lambda *_: None)
    assert "main" not in edit[edit_material.FILLED]  # KK hair has only its baked variants
    # Its root and tip colours show through its colour mask, as in the game.
    assert templates.param(edit, "use_color_mask.light").default_value == 1.0
    assert templates.param(edit, "use_color_mask.dark").default_value == 1.0


def test_the_eyebrows_multiply_their_texture_and_shade_as_toon_eyew(ch):
    bm = ch.bundle().material("cf_m_mayuge_00")
    edit = edit_material.edit(ch, ch.material("cf_m_mayuge_00"), saturate=False, log=lambda *_: None)
    assert templates.param(edit, "use_main_texture_color").default_value == 1.0
    light = templates.param(edit, "eyebrow_color").default_value
    dark = templates.param(edit, "eyebrow_color_dark").default_value
    shaded = edit_material._linear(submodule("shading").eyew_dark_color(bm.colors["_Color"], bm.colors["_shadowcolor"]))
    assert tuple(dark) == pytest.approx(shaded, abs=1e-4)
    assert all(d < l for d, l in zip(dark[:3], light[:3]))


def test_the_eyes_are_placed_by_their_texture_transform(ch):
    eye = ch.material("cf_m_hitomi_00")
    texture = ch.bundle().material("cf_m_hitomi_00").texture("main")
    edit = edit_material.edit(ch, eye, log=lambda *_: None)
    pupil = templates.node_at(edit, "textures/Eyepos/eye_scale")
    assert pupil.inputs["Scale X"].default_value == pytest.approx(texture.scale[0])
    assert pupil.inputs["Position X"].default_value == pytest.approx(50 * (0.5 - texture.offset[0]) / texture.scale[0])
    assert tuple(_node_mapping(edit, "main")) == (1.0, 1.0)
    # The positions group is this eye's own.
    right = edit_material.edit(ch, ch.material("cf_m_hitomi_00_2"), log=lambda *_: None)
    assert templates.node_at(right, "textures/Eyepos").node_tree != templates.node_at(edit, "textures/Eyepos").node_tree
    up = templates.param(edit, "highlight_up_intensity.light").default_value
    assert up == pytest.approx(ch.bundle().material("cf_m_hitomi_00").colors["_overcolor1"][3])


def _node_mapping(mat, slot):
    return templates.texture_node(mat, slot).texture_mapping.scale[:2]


def test_edits_keep_the_bundle_colours_unless_saturated(ch):
    create = ch.bundle().material("cf_m_top_inner01").create.colors["_Color2"]
    edit = edit_material.edit(ch, ch.material("cf_m_top_inner01"), log=lambda *_: None)
    plain = tuple(templates.param(edit, "color_mask_green.light").default_value)
    assert plain == pytest.approx(edit_material._linear(create), abs=1e-4)
    edit = edit_material.reset(ch, edit, saturate=True, log=lambda *_: None)
    saturated = tuple(templates.param(edit, "color_mask_green.light").default_value)
    assert saturated != pytest.approx(plain, abs=1e-3)
    assert any(p.name.endswith(".saturated.png") for p in ch.bundle().cache_dir("edit").iterdir())


def test_tears_and_gag_eyes_and_svs_are_not_editable(ch, build):
    assert "has no edit template" in edit_material.editable(ch, ch.materials("tears")[0])
    with pytest.raises(edit_material.EditError):
        edit_material.edit(ch, ch.materials("gag_eyes")[0])
    result = kkbp.api.import_bundle(build(BundleBuilder("SVS")), hooks=[])
    svs = character.Character(result.character_key)
    assert "isn't available for SVS" in edit_material.editable(svs, svs.material("cf_m_body"))


def test_save_bakes_light_and_dark_into_the_original(ch):
    mat = ch.material("cf_m_body")
    before = (_image(mat, "main.light"), _image(mat, "main.dark"))
    edit = edit_material.edit(ch, mat, log=lambda *_: None)
    saved = edit_material.save(ch, edit, log=lambda *_: None)
    assert saved == mat and "Edit cf_m_body" not in bpy.data.materials and _users(mat)
    light, dark = templates.texture(mat, "main", "light").image, templates.texture(mat, "main", "dark").image
    assert (light, dark) != before
    assert light.packed_file and tuple(light.size) == tuple(before[0].size or light.size)
    assert (ch.bundle().cache_dir("baked") / "cf_m_body light.png").is_file()
    assert _mean(light) > _mean(dark) > 0.0  # the dark bake is darker, and not empty
    # The Outfit's alpha mask is the Light Dark material's to apply, so the bake has no holes.
    assert _opaque(light) > 0.8 * _opaque(before[0])
    assert "KKBP bake" not in bpy.data.scenes


def _opaque(image):
    import numpy as np
    px = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    return float((px.reshape(-1, 4)[:, 3] > 0.5).mean())


def _mean(image):
    import numpy as np
    px = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    px = px.reshape(-1, 4)
    return float(px[px[:, 3] > 0.5, :3].mean()) if (px[:, 3] > 0.5).any() else 0.0


def test_link_hair_copies_the_active_hair_settings(ch):
    hairs = [m for m in ch.materials("hair") if _users(m)]
    assert len(hairs) > 1
    source = edit_material.edit(ch, hairs[0], log=lambda *_: None)
    templates.param(source, "hair_color.light").default_value = (0.1, 0.2, 0.9, 1.0)
    linked = link_hair.link_hair(ch, source, log=lambda *_: None)
    assert len(linked) == len(hairs) - 1
    for edit in linked:
        assert edit_material.is_edit(edit)
        assert tuple(templates.param(edit, "hair_color.light").default_value) == pytest.approx((0.1, 0.2, 0.9, 1.0))
