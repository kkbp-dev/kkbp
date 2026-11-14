"""Export prep on a copy of the KK golden sample, imported without Rigify."""

import bpy
import pytest

from conftest import submodule

character = submodule("character")
export_prep = submodule("tools.export_prep")
settings = submodule("settings")
templates = submodule("templates")


@pytest.fixture(autouse=True)
def no_preferences(monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})


@pytest.fixture
def ch(golden_import):
    return golden_import("kk", hooks=["Outlines"])[1]


@pytest.mark.parametrize("target, bones", [
    ("vrm", {"Hips", "Spine", "Left arm", "Left ankle"}),
    ("unreal", {"pelvis", "spine_01", "upperarm_l", "calf_l", "foot_l"}),
    ("koikatsu", {"cf_j_hips", "cf_j_arm00_L", "cf_n_height"}),
])
def test_targets_name_the_bones(ch, target, bones):
    export_prep.prep(ch, target, "simple", "none", log=lambda m: None)
    assert bones <= set(ch.armature.data.bones.keys())
    assert ch.collection.exporters and ch.collection.exporters[0].export_properties.filepath.endswith(".fbx")


def test_very_simple_merges_the_face_and_vrm_drops_the_hips(ch):
    before = len(ch.armature.data.bones)
    export_prep.prep(ch, "vrm", "very_simple", "none", log=lambda m: None)
    bones = ch.armature.data.bones
    assert len(bones) < before and "cf_J_FaceBase" not in bones and "Left Eye" in bones
    assert bones["Hips"].parent is None and bones["Spine"].parent.name == "Hips"


def test_the_atlas_copy_uses_one_atlas_per_object(ch):
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


def test_an_atlas_over_the_cap_is_split_into_several(ch):
    """Issue 12: Body's atlas would be 8192 px, so under a 4096 px limit its materials go into several
    atlases, none scaled down, and the UVs land inside them."""
    sizes = {m.name: tuple(m.node_tree.nodes["tex.main.light"].image.size) for m in bpy.data.materials
             if m.get("kkbp_id") and "tex.main.light" in m.node_tree.nodes and m.node_tree.nodes["tex.main.light"].image}
    said = []
    collection = export_prep.prep(ch, "no_change", "none", "atlas", log=said.append, max_atlas=4096)
    body = next(o for o in collection.objects if o.type == "MESH" and o.name.startswith("Body"))
    atlas_slots = {i: s.material for i, s in enumerate(body.material_slots)
                   if s.material and s.material.name.endswith(" Atlas")}
    images = {m.node_tree.nodes["tex.main.light"].image for m in atlas_slots.values()}
    assert len(images) > 1 and all(max(i.size) <= 4096 for i in images), [tuple(i.size) for i in images]
    assert any("atlases" in line and "4096 px" in line for line in said), said
    # Not scaled down: a material's texture takes as many atlas pixels as it has.
    uv = body.data.uv_layers["uv_main"].data
    for index, material in atlas_slots.items():
        if not material.name.startswith(("cf_m_face_00", "cf_m_body")):
            continue  # the tongue's UVs go below 0, which no atlas, split or not, makes room for
        coords = [uv[i].uv for p in body.data.polygons if p.material_index == index for i in p.loop_indices]
        box = (min(c.x for c in coords), max(c.x for c in coords), min(c.y for c in coords), max(c.y for c in coords))
        assert -1e-4 <= box[0] and box[1] <= 1 + 1e-4 and -1e-4 <= box[2] and box[3] <= 1 + 1e-4, (material.name, box, said)
    face = next(m for m in atlas_slots.values() if m.name.startswith("cf_m_face_00"))
    assert sizes["cf_m_face_00"] == (4096, 4096)
    assert tuple(face.node_tree.nodes["tex.main.light"].image.size) == (4096, 4096)  # an atlas of its own
    names = sorted(i.filepath.replace("\\", "/").rsplit("/", 1)[-1] for i in images)
    assert names[0].endswith(" 1 main.light.png") and names[1].endswith(" 2 main.light.png"), names


def test_the_operator_offers_the_atlas_sizes():
    prop = bpy.ops.kkbp.export_prep.get_rna_type().properties["atlas_size"]
    assert [i.identifier for i in prop.enum_items] == ["2048", "4096", "8192", "16384"]
    assert prop.default == "8192"


def test_a_rigged_character_is_refused(ch):
    ch.add_part(bpy.data.objects.new("Rig", bpy.data.armatures.new("Rig")), "rig")
    bpy.context.scene.collection.objects.link(bpy.data.objects["Rig"])
    with pytest.raises(character.CharacterError, match="needs a Character imported without Rigify"):
        export_prep.prep(ch, "vrm", "simple", "none")
