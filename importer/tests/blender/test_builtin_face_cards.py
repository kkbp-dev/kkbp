"""Face cards on the builder's Character (golden samples: run.py hooks --each)."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")
templates = submodule("templates")


def _import(build):
    b = BundleBuilder()
    materials = {m["id"]: m for m in b.materials}
    materials["cf_m_hitomi_00"]["textures"] = [b.add_texture("_MainTex", role="main", variant="light"),
                                               b.add_texture("_MainTex", role="main", variant="dark")]
    result = kkbp.api.import_bundle(build(b), hooks=["Face cards"])
    assert result.ok and result.hooks[0].status == "ran", result.hooks
    return character.Character(result.character_key), result


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
