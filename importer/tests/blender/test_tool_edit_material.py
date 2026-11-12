"""Edit material, Cancel, Reset, Save and Link hair on a copy of the KK golden sample (D37-D46). Every
material there has a template made from the game's shaders; the legacy templates' own behaviour
(texture groups, saturation) is tested on a built bundle whose top uses a shader no template models,
which falls back to KK General."""

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


@pytest.fixture
def legacy(build):
    """A built KK bundle whose top is drawn by a modded shader (xukmi/MainOpaquePlus): no template
    made from the game's shaders draws it, so it takes the legacy KK General."""
    b = BundleBuilder()
    textures = [b.add_texture("_MainTex", role="main", color=(200, 120, 90, 255)),
                b.add_texture("_MainTex", role="main", variant="light"),
                b.add_texture("_MainTex", role="main", variant="dark"),
                b.add_texture("_ColorMask", role="color_mask", color=(255, 0, 0, 255))]
    b.add_material("ct_modded", blend_mode="cutout", shader="xukmi/MainOpaquePlus", textures=textures,
                   colors={"_ShadowColor": [0.8, 0.85, 0.9, 1.0]},
                   create=b.add_create("Shader Forge/create_topN", colors={"_Color": [0.9, 0.3, 0.2, 1.0]}))
    b.add_mesh("o_modded", ["ct_modded"], outfit=0, bone="cf_j_spine01")
    result = kkbp.api.import_bundle(build(b), hooks=[])
    assert result.ok
    return character.Character(result.character_key)


def _image(mat, slot):
    node = templates.texture_node(mat, slot)
    return node.image if node is not None else None


def _users(material):
    return [o for o in bpy.data.objects if any(s.material == material for s in o.material_slots)]


def test_editing_the_body_composites_it_from_the_create_material(ch):
    """KK's body follows create_body and main_skin: its create textures and colours, linear."""
    bm = ch.bundle().material("cf_m_body")
    body = ch.material("cf_m_body")
    users = _users(body)
    edit = edit_material.edit(ch, body, log=lambda *_: None)
    assert edit.name == "Edit cf_m_body" and edit[templates.TEMPLATE] == "KK create_body"
    assert _users(edit) == users and not _users(body) and body.use_fake_user
    assert {"plain", "color_mask", "paint_mask", "detail_mask", "line_mask", "overlay1", "overlay2"} <= set(edit[edit_material.FILLED])
    assert not templates.own_groups(edit)
    assert tuple(templates.param(edit, "color").default_value) == pytest.approx(edit_material._linear(bm.create.colors["_Color"]))
    assert tuple(templates.param(edit, "paint1").default_value) == pytest.approx(bm.create.vectors["_paint1"][:3])
    assert templates.param(edit, "paint1_w").default_value == pytest.approx(bm.create.vectors["_paint1"][3])
    assert templates.param(edit, "tan_present").default_value == 0.0  # no tan lines: the skin colour alone
    assert templates.param(edit, "color3_alpha").default_value == 0.0  # no paint
    assert templates.param(edit, "nip").default_value == 1.0


def test_editing_a_legacy_material_copies_its_texture_groups(legacy):
    """A shader no template models takes KK General: its texture groups are its own (ADR 0025), its
    colours come in light and dark versions, and its dark texture is made once, into the Cache."""
    ch = legacy
    top = ch.material("ct_modded")
    users = _users(top)
    edit = edit_material.edit(ch, top, log=lambda *_: None)
    assert edit.name == "Edit ct_modded" and edit[templates.TEMPLATE] == "KK General"
    assert _users(edit) == users and not _users(top) and top.use_fake_user
    assert {"main", "main.dark", "color_mask.plain"} <= set(edit[edit_material.FILLED])  # a plain-mask shader
    own = templates.own_groups(edit)
    assert own and all(g.name.endswith("Edit ct_modded") and g.users == 1 for g in own)
    light = templates.param(edit, "color_mask_red.light").default_value
    dark = templates.param(edit, "color_mask_red.dark").default_value
    assert sum(dark[:3]) < sum(light[:3]) and light[0] > 0.5
    assert any(".dark." in p.name for p in ch.bundle().cache_dir("edit").iterdir())
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
    ("cf_m_face_00", "KK create_head", {"plain", "color_mask", "texture4", "overlay3"}, ("color", "color4", "tex4uv")),
    ("cf_m_top_inner01", "KK main_opaque", {"plain", "color_mask", "detail_mask"},
     ("color", "color2", "pattern_color3", "shadow_color")),
    ("cf_m_bot_skirt01", "KK main_opaque", {"pattern_mask1"}, ("color", "pattern_color1")),
    ("cf_m_hair_b_08_00", "KK main_hair", {"color_mask", "detail_mask", "hair_gloss"}, ("color", "color2", "color3")),
    ("cf_m_mayuge_00", "KK toon_eyew", {"main"}, ("color", "shadow_color")),
    ("cf_m_sirome_00", "KK create_eyewhite", {"create_main"}, ("create_color", "create_color2", "shadow_color")),
    ("cf_m_noseline_00", "KK toon_nose", {"main"}, ("color_alpha",)),  # its colour is black
    ("cf_m_tang", "KK main_item", {"color_mask", "detail_mask"}, ("color",)),
    ("cf_m_tooth", "KK main_item", {"main", "color_mask", "detail_mask"}, ("color", "shadow_color")),
    ("cf_m_emblem", "KK main_emblem", {"main"}, ()),
])
def test_each_template_gets_its_slots_and_colours(ch, id, template, slots, params):
    mat = ch.material(id)
    edit = edit_material.edit(ch, mat, log=lambda *_: None)
    assert edit[templates.TEMPLATE] == template
    assert slots <= set(edit[edit_material.FILLED])
    for name in params:
        value = templates.param(edit, name).default_value
        assert tuple(value) != (0.0, 0.0, 0.0, 1.0) if hasattr(value, "__len__") else True, name


def test_nothing_saturates_by_default(ch):
    """ADR 0026: no KK Role saturates by default; the templates made from the game's shaders (the hair's
    and the clothes' since issue 30) grade in their nodes instead, and the legacy ones don't saturate."""
    b = ch.bundle()
    for id, param, source in (("cf_m_hair_b_08_00", "color", b.material("cf_m_hair_b_08_00").colors["_Color"]),
                              ("cf_m_top_inner01", "color2", b.material("cf_m_top_inner01").create.colors["_Color2"]),
                              ("cf_m_body", "color", b.material("cf_m_body").create.colors["_Color"])):
        edit = edit_material.edit(ch, ch.material(id), log=lambda *_: None)
        assert not edit[edit_material.SATURATED], id
        assert tuple(templates.param(edit, param).default_value) == pytest.approx(edit_material._linear(source), abs=1e-3), id


@pytest.mark.parametrize("id, front", [("cf_m_hair_b_08_00", 0.0), ("cf_m_hair_f_14_00_i", 1.0)])
def test_the_hair_takes_its_shaders_values(ch, id, front):
    """main_hair without a main texture draws white under its colour mask; its shadow extend comes from
    the material, its gloss is placed by its texture transform, and main_hair_front reads it further on."""
    bm = ch.bundle().material(id)
    edit = edit_material.edit(ch, ch.material(id), log=lambda *_: None)
    assert "main" not in edit[edit_material.FILLED]  # KK hair has only its baked variants
    assert templates.param(edit, "use_main_texture").default_value == 0.0
    assert templates.param(edit, "shadow_extend").default_value == pytest.approx(bm.floats["_ShadowExtend"])
    assert templates.param(edit, "front").default_value == front
    gloss = next(t for t in bm.textures if t.raw == "_HairGloss")
    mapping = templates.texture_node(edit, "hair_gloss").texture_mapping
    assert tuple(mapping.translation[:2]) == pytest.approx(gloss.offset)
    assert tuple(mapping.scale[:2]) == pytest.approx(gloss.scale)


def test_the_eyebrows_take_the_games_own_colours_and_never_saturate(ch):
    """KK's eyebrows are drawn by toon_eyew_lod0, which the template follows: it gets the game's own
    colours linear, and grades in its nodes, so even an edit asked to saturate leaves the texture."""
    bm = ch.bundle().material("cf_m_mayuge_00")
    edit = edit_material.edit(ch, ch.material("cf_m_mayuge_00"), saturate=True, log=lambda *_: None)
    assert edit[templates.TEMPLATE] == "KK toon_eyew" and not edit[edit_material.SATURATED]
    assert tuple(templates.param(edit, "color").default_value) == pytest.approx(edit_material._linear(bm.colors["_Color"]))
    assert tuple(templates.param(edit, "shadow_color").default_value) == pytest.approx(
        edit_material._linear(bm.colors["_shadowcolor"]))
    image = templates.texture_node(edit, "main").image
    assert image.filepath and "saturated" not in image.name


def test_the_eyes_are_placed_by_their_texture_transform(ch):
    """toon_eye_lod0 turns the iris by `_rotation`, then places it by its texture transform; the
    highlights take their colours and the highlight switch from the material (D41)."""
    bm = ch.bundle().material("cf_m_hitomi_00")
    texture = bm.texture("main")
    edit = edit_material.edit(ch, ch.material("cf_m_hitomi_00"), log=lambda *_: None)
    assert edit[templates.TEMPLATE] == "KK toon_eye"
    mapping = templates.texture_node(edit, "main").texture_mapping
    assert tuple(mapping.translation[:2]) == pytest.approx(texture.offset)
    assert tuple(mapping.scale[:2]) == pytest.approx(texture.scale)
    assert templates.param(edit, "rotation").default_value == pytest.approx(bm.floats["_rotation"])
    right = edit_material.edit(ch, ch.material("cf_m_hitomi_00_2"), log=lambda *_: None)
    assert templates.param(right, "rotation").default_value == pytest.approx(-bm.floats["_rotation"])
    assert templates.param(edit, "overlay_color1_alpha").default_value == pytest.approx(bm.colors["_overcolor1"][3])
    assert templates.param(edit, "highlight").default_value == 1.0
    assert {"main", "overlay1", "overlay2"} <= set(edit[edit_material.FILLED])


def _red(edit):
    return tuple(templates.param(edit, "color_mask_red.light").default_value)


def test_edits_keep_the_bundle_colours_unless_saturated(legacy):
    """On a legacy template; the ones made from the game's shaders never saturate."""
    ch = legacy
    create = ch.bundle().material("ct_modded").create.colors["_Color"]
    edit = edit_material.edit(ch, ch.material("ct_modded"), log=lambda *_: None)
    plain = _red(edit)
    assert plain == pytest.approx(edit_material._linear(create), abs=1e-4)
    edit = edit_material.reset(ch, edit, saturate=True, log=lambda *_: None)
    assert _red(edit) != pytest.approx(plain, abs=1e-3)
    assert any(p.name.endswith(".saturated.png") for p in ch.bundle().cache_dir("edit").iterdir())


def test_reset_keeps_the_saturation_the_edit_was_made_with(legacy):
    """Issue #13: Reset used to fall back to the default and drop an On or Off choice."""
    ch = legacy
    edit = edit_material.edit(ch, ch.material("ct_modded"), saturate=True, log=lambda *_: None)
    saturated = _red(edit)
    assert edit[edit_material.SATURATED]
    edit = edit_material.reset(ch, edit, log=lambda *_: None)
    assert edit[edit_material.SATURATED] and _red(edit) == pytest.approx(saturated, abs=1e-4)
    edit = edit_material.reset(ch, edit, saturate=False, log=lambda *_: None)
    assert not edit[edit_material.SATURATED] and _red(edit) != pytest.approx(saturated, abs=1e-3)


def _edit_from_the_operator(ch, id, **props):
    mat = ch.material(id)
    obj = next(o for o in bpy.data.objects if any(s.material == mat for s in o.material_slots))
    obj.active_material_index = next(i for i, s in enumerate(obj.material_slots) if s.material == mat)
    with bpy.context.temp_override(active_object=obj, object=obj):
        assert bpy.ops.kkbp.edit_material(**props) == {"FINISHED"}
    return obj.active_material


def test_the_operator_saturates_as_asked_and_forgets_it_afterwards(legacy):
    """Issue #13: the panel passes the scene's Saturate choice; the operator keeps no value of its own."""
    ch = legacy
    assert bpy.context.scene.kkbp_edit_saturate == "DEFAULT"
    edit = _edit_from_the_operator(ch, "ct_modded", saturate="ON")
    assert edit[edit_material.SATURATED]
    edit_material.cancel(edit)
    edit = _edit_from_the_operator(ch, "ct_modded")  # Default: nothing saturates
    assert not edit[edit_material.SATURATED]


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
    templates.param(source, "color").default_value = (0.1, 0.2, 0.9, 1.0)
    linked = link_hair.link_hair(ch, source, log=lambda *_: None)
    assert len(linked) == len(hairs) - 1
    for edit in linked:
        assert edit_material.is_edit(edit)
        assert tuple(templates.param(edit, "color").default_value) == pytest.approx((0.1, 0.2, 0.9, 1.0))
        # Each hair keeps its own shader's values.
        front = ch.bundle().material(edit_material.original(edit)["kkbp_id"]).shader.endswith("_front")
        assert templates.param(edit, "front").default_value == (1.0 if front else 0.0)
