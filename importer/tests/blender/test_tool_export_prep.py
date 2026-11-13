"""Export prep on a copy of the KK golden sample, imported without Rigify."""

import bpy
import pytest

from bundle_copy import copy_bundle
from conftest import golden, kkbp, submodule

character = submodule("character")
export_prep = submodule("tools.export_prep")
settings = submodule("settings")
templates = submodule("templates")


@pytest.fixture(autouse=True)
def no_preferences(monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})


def _kk(tmp_path):
    copy = tmp_path / "kk"
    copy_bundle(golden("kk"), copy)
    result = kkbp.api.import_bundle(copy, hooks=["Outlines"])
    assert result.ok
    return character.Character(result.character_key)


@pytest.mark.parametrize("target, bones", [
    ("vrm", {"Hips", "Spine", "Left arm", "Left ankle"}),
    ("unreal", {"pelvis", "spine_01", "upperarm_l", "calf_l", "foot_l"}),
    ("koikatsu", {"cf_j_hips", "cf_j_arm00_L", "cf_n_height"}),
])
def test_targets_name_the_bones(tmp_path, target, bones):
    ch = _kk(tmp_path)
    export_prep.prep(ch, target, "simple", "none", log=lambda m: None)
    assert bones <= set(ch.armature.data.bones.keys())
    assert ch.collection.exporters and ch.collection.exporters[0].export_properties.filepath.endswith(".fbx")


def test_very_simple_merges_the_face_and_vrm_drops_the_hips(tmp_path):
    ch = _kk(tmp_path)
    before = len(ch.armature.data.bones)
    export_prep.prep(ch, "vrm", "very_simple", "none", log=lambda m: None)
    bones = ch.armature.data.bones
    assert len(bones) < before and "cf_J_FaceBase" not in bones and "Left Eye" in bones
    assert bones["Hips"].parent is None and bones["Spine"].parent.name == "Hips"


def test_the_atlas_copy_uses_one_atlas_per_object(tmp_path):
    ch = _kk(tmp_path)
    collection = export_prep.prep(ch, "no_change", "none", "atlas", log=lambda m: None)
    outfit = next(o for o in collection.objects if o.type == "MESH" and o.name.startswith("Outfit 00"))
    lights = {s.material.node_tree.nodes["tex.main.light"].image for s in outfit.material_slots
              if s.material and s.material.name.endswith(" Atlas")}
    assert len(lights) == 1
    assert (ch.bundle().cache_dir("atlas")).is_dir()
    # The alpha mask is folded into the atlas, so no atlas material hides behind its empty slot.
    atlases = {s.material for o in collection.objects for s in o.material_slots
               if s.material and s.material.name.endswith(" Atlas")}
    assert atlases and all(templates.param(m, "force_visibility").default_value == 0 for m in atlases)
    assert all(not m.show_viewport for o in collection.objects for m in o.modifiers if m.type == "SOLIDIFY")
    assert ch.rig is None and "Outfit 00" in ch.outfits[0].name  # the original is untouched


def test_a_rigged_character_is_refused(tmp_path):
    ch = _kk(tmp_path)
    ch.add_part(bpy.data.objects.new("Rig", bpy.data.armatures.new("Rig")), "rig")
    bpy.context.scene.collection.objects.link(bpy.data.objects["Rig"])
    with pytest.raises(character.CharacterError, match="needs a Character imported without Rigify"):
        export_prep.prep(ch, "vrm", "simple", "none")
