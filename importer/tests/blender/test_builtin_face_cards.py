"""Face cards on the builder's Character (golden samples: run.py hooks --each)."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")
templates = submodule("templates")


def _baked(b, id, role):
    """A material with light and dark textures, on a mesh of its own."""
    b.add_material(id, role=role, textures=[b.add_texture("_MainTex", role="main", variant="light"),
                                            b.add_texture("_MainTex", role="main", variant="dark")])
    b.add_mesh(f"o_{id}", [id], bone="cf_j_head")


def _import(build, b=None):
    if b is None:
        b = BundleBuilder()
        materials = {m["id"]: m for m in b.materials}
        materials["cf_m_hitomi_00"]["textures"] = [b.add_texture("_MainTex", role="main", variant="light"),
                                                   b.add_texture("_MainTex", role="main", variant="dark")]
    result = kkbp.api.import_bundle(build(b), hooks=["Face cards"], options={"use_face_cards": True})
    assert result.ok and result.hooks[0].status == "ran", result.hooks
    return character.Character(result.character_key), result


def _card_material(ch, name):
    return next(s.material for o in ch.parts("face_card") if o.type == "MESH" for s in o.material_slots
                if s.material and s.material.name.startswith(name))


def test_the_cards_are_parts_on_the_head_with_the_characters_eyes(build):
    ch, _ = _import(build)
    cards = {o.name.split(".")[0]: o for o in ch.parts("face_card")}
    assert set(cards) == {"Face card rig", "Face card eyes", "Face card mouth"}
    rig = cards["Face card rig"]
    assert (rig.parent, rig.parent_type, rig.parent_bone) == (ch.armature, "BONE", "cf_j_head")
    pupil = next(s.material for s in cards["Face card eyes"].material_slots if s.material.name.startswith("Pupil L"))
    eye = ch.material("cf_m_hitomi_00")
    assert pupil.node_tree.nodes["tex.eye_l"].image == templates.texture(eye, "main", "light").image


def test_the_collection_starts_excluded(build):
    ch, _ = _import(build)
    collection = next(c for c in ch.collection.children if c.name.startswith("Face cards"))
    layer = next(lc for lc in bpy.context.view_layer.layer_collection.children[ch.collection.name].children
                 if lc.collection == collection)
    assert collection.name == "Face cards Test Chara"
    assert layer.exclude


def test_a_second_character_shares_the_mouth_atlas(build):
    _import(build)
    _import(build)
    assert len([i for i in bpy.data.images if i.name.startswith("MouthAtlas")]) == 1


def test_a_layer_with_no_texture_draws_nothing(build):
    ch, _ = _import(build)  # the default Character has no eyelines
    eyeline = _card_material(ch, "Eyeline card").node_tree
    group = next(n for n in eyeline.nodes if n.type == "GROUP")
    for name in ("tex.eyeline_upper", "tex.eyeline_shadow", "tex.eyeline_lower"):
        assert not any(o.links for o in eyeline.nodes[name].outputs), name
    assert all(s.default_value == 0.0 for s in group.inputs if s.name == "Alpha")


def test_a_kk_eye_white_keeps_kks_mask(build):
    b = BundleBuilder()
    _baked(b, "cf_m_sirome_00", "eye_white")
    ch, _ = _import(build, b)
    eyewhite = _card_material(ch, "Eyewhite card").node_tree.nodes
    assert eyewhite["tex.eye_white"].image == templates.texture(ch.material("cf_m_sirome_00"), "main", "light").image
    assert eyewhite["tex.eye_white_mask"].image.name == "Eye_White_Alpha"
    assert not any(i.name.startswith("SVS Eye_White_Alpha") for i in bpy.data.images)


def test_an_svs_character_gets_its_eyelash_and_eye_white_mask(build):
    b = BundleBuilder("SVS")
    _baked(b, "cf_m_eyelash_up_00", "eyelash")
    _baked(b, "cf_m_hitomi_00_L_white", "eye_white")
    ch, _ = _import(build, b)
    eyeline = _card_material(ch, "Eyeline card").node_tree.nodes
    lash = templates.texture(ch.material("cf_m_eyelash_up_00"), "main", "light").image
    assert eyeline["tex.eyeline_upper"].image == lash
    assert not any(o.links for o in eyeline["tex.eyeline_lower"].outputs)
    mask = _card_material(ch, "Eyewhite card").node_tree.nodes["tex.eye_white_mask"].image
    assert mask.name == "SVS Eye_White_Alpha" and mask.packed_file and not mask.use_fake_user
    assert not any(i.name.startswith("Eye_White_Alpha") for i in bpy.data.images)  # KK's, unused, is removed


def test_a_second_svs_character_shares_the_mask(build):
    for _ in range(2):
        b = BundleBuilder("SVS")
        _baked(b, "cf_m_hitomi_00_L_white", "eye_white")
        _import(build, b)
    assert len([i for i in bpy.data.images if i.name.startswith("SVS Eye_White_Alpha")]) == 1
