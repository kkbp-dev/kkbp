"""Separate meshes on the builder's Character (golden samples: run.py hooks --each)."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")


def _two_outfits():
    b = BundleBuilder()
    b.add_material("ct_bot_skirt", blend_mode="cutout", textures=[b.add_texture("_MainTex", role="main")])
    b.add_mesh("o_bot_skirt", ["ct_bot_skirt"], outfit=0, bone="cf_j_hips")
    b.add_outfit(1)
    b.add_material("ct_top_coat", textures=[b.add_texture("_MainTex", role="main")])
    b.add_mesh("o_top_coat", ["ct_top_coat"], outfit=1, bone="cf_j_spine01")
    return b


def test_each_piece_of_clothing_is_its_own_part(build):
    result = kkbp.api.import_bundle(build(_two_outfits()), options={"separation_type": "by_material"},
                                    hooks=["Separate meshes"])
    assert result.ok and result.hooks[0].status == "ran", result.hooks
    ch = character.Character.for_tool(bpy.context)
    pieces = {o.name: o for o in ch.outfits}
    assert set(pieces) == {"ct_top_shirt", "ct_bot_skirt", "ct_top_coat"}
    assert [s.material.get("kkbp_id") for s in pieces["ct_bot_skirt"].material_slots] == ["ct_bot_skirt"]
    assert {o.get("kkbp_outfit") for o in pieces.values()} == {0, 1}
    assert pieces["ct_top_coat"].get("kkbp_outfit") == 1
    assert len(ch.alt_outfits) == 1 and len(ch.hairs) == 1  # alternate clothes and hair stay whole


def test_off_is_one_object_per_outfit(build):
    result = kkbp.api.import_bundle(build(_two_outfits()), hooks=["Separate meshes"])
    assert result.hooks[0].status == "off"
    assert len(character.Character.for_tool(bpy.context).outfits) == 2
