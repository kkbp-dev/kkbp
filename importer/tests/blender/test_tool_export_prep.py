"""Export prep on a copy of the KK golden sample, imported without Rigify."""

import bpy
import pytest

from conftest import submodule

character = submodule("character")
export_prep = submodule("tools.export_prep")
atlas = submodule("tools.export_prep.atlas")
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
    lights = {atlas.shown(s.material, "main.light") for s in outfit.material_slots
              if s.material and s.material.get(atlas.ATLAS_OF)}
    assert len(lights) == 1 and None not in lights
    folder = ch.bundle().cache_dir("atlas")
    assert folder.is_dir()
    # The dark atlas is a file for other programs; no atlas material shows it (ADR 0050).
    assert list(folder.glob("* main.dark.png")) and not [i for i in bpy.data.images if i.filepath.endswith("main.dark.png")]
    # No outlines: no Solidify modifier, no outline material (the Character has both).
    assert any(m.type == "SOLIDIFY" for o in ch.parts() for m in getattr(o, "modifiers", ()))
    assert not any(m.type == "SOLIDIFY" for o in collection.objects for m in o.modifiers)
    assert not any(s.material and s.material.get(atlas.OUTLINE) for o in collection.objects for s in o.material_slots)
    assert ch.rig is None and "Outfit 00" in ch.outfits[0].name  # the original is untouched


def _atlas_materials(collection):
    return {s.material for o in collection.objects for s in o.material_slots
            if s.material and s.material.get(atlas.ATLAS_OF)}


def test_an_atlas_material_is_a_principled_bsdf_the_fbx_exporter_reads(ch):
    """Issue 103, ADR 0050: Blender's FBX exporter finds a material's textures through this wrapper,
    which sees only a Principled BSDF in the material's own tree."""
    from bpy_extras.node_shader_utils import PrincipledBSDFWrapper

    collection = export_prep.prep(ch, "no_change", "none", "atlas", log=lambda m: None)
    materials = _atlas_materials(collection)
    assert materials and not any(m.get(templates.TEMPLATE) for m in materials)
    with_normal = 0
    for material in materials:
        wrapper = PrincipledBSDFWrapper(material, is_readonly=True)
        light = atlas.shown(material, "main.light")
        assert light is not None and light.packed_file is not None
        assert wrapper.base_color_texture.image == light and wrapper.alpha_texture.image == light, material.name
        normal = atlas.shown(material, "normal")
        if normal is not None:
            with_normal += 1
            assert wrapper.normalmap_texture.image == normal and normal.colorspace_settings.name == "Non-Color"
    assert with_normal
    for obj in [o for o in collection.objects if o.type == "MESH"]:
        used = [s.material for s in obj.material_slots]
        assert len(used) == len(set(used)), obj.name  # one slot per material


def _original_material(ch, obj, polygon):
    """The Character's material on `polygon` of the atlas copy `obj` (the copy keeps the faces' order)."""
    # obj.copy() names the copy after its original, with a number added
    original = max((o for o in ch.parts() if o.type == "MESH" and obj.name.startswith(o.name)), key=lambda o: len(o.name))
    return original.material_slots[original.data.polygons[polygon].material_index].material


def test_the_materials_of_an_atlas_are_merged_by_render_method(ch):
    """An atlas gets one material for its dithered materials and one for its blended ones, and every
    face keeps its material's render method."""
    collection = export_prep.prep(ch, "no_change", "none", "atlas", log=lambda m: None)
    body = next(o for o in collection.objects if o.type == "MESH" and o.name.startswith("Body"))
    atlased = {s.material for s in body.material_slots if s.material and s.material.get(atlas.ATLAS_OF)}
    assert {m.surface_render_method for m in atlased} == {"DITHERED", "BLENDED"}
    assert len(atlased) == 2 and {m.name for m in atlased} == {f"{atlas._safe(body.name)} Atlas", f"{atlas._safe(body.name)} Atlas Blended"}
    for polygon in body.data.polygons:
        copy = body.material_slots[polygon.material_index].material
        if copy in atlased:
            original = _original_material(ch, body, polygon.index)
            assert copy.surface_render_method == original.surface_render_method, original.name
            assert original[character.ID] in atlas.sources(copy)


def test_the_fbx_holds_the_atlases(ch, tmp_path):
    """Issue 103: the collection's exporter embeds the light and normal atlases in the FBX."""
    collection = export_prep.prep(ch, "no_change", "none", "atlas", log=lambda m: None)
    exporter = collection.exporters[0]
    assert exporter.export_properties.embed_textures and exporter.export_properties.path_mode == "COPY"
    path = tmp_path / "model.fbx"
    exporter.export_properties.filepath = str(path)
    with bpy.context.temp_override(collection=collection):
        assert bpy.ops.collection.exporter_export(index=0) == {"FINISHED"}
    fbx = path.read_bytes()
    shown = {i for m in _atlas_materials(collection) for i in (atlas.shown(m, "main.light"), atlas.shown(m, "normal"))
             if i is not None}
    assert len(shown) > 2
    for image in shown:
        assert bytes(image.packed_file.data) in fbx, image.name
    assert not list(tmp_path.glob("*.png"))  # embedded, not copied beside the FBX


def test_atlas_without_the_eyes_gives_them_a_simple_material_of_their_own(ch):
    collection = export_prep.prep(ch, "no_change", "none", "skip_eyes", log=lambda m: None)
    eyes = {m[character.ID]: m for m in ch.materials(roles=["eye_l", "eye_r"])}
    simple = [m for m in _atlas_materials(collection) if m[atlas.ATLAS_OF] in eyes]  # one source each
    assert len(simple) == len(eyes) == 2
    for material in simple:
        assert material.name.endswith(" Simple")
        assert atlas.shown(material, "main.light") == templates.texture(eyes[material[atlas.ATLAS_OF]], "main", "light").image


def test_the_face_atlas_holds_one_of_its_two_bakes(ch):
    """ADR 0046: the atlas holds the face's bake with eyeshadow or the one without, by its Eyeshadow
    input, and no bake in the face's own UV layout is left in the copy."""
    face = ch.materials(roles="face")[0]
    bakes = {templates.texture(face, "main", v).image for v in ("light", "dark", "light_no_eyeshadow", "dark_no_eyeshadow")}
    collection = export_prep.prep(ch, "no_change", "none", "atlas", log=lambda m: None)
    copy = next(m for m in _atlas_materials(collection) if face[character.ID] in atlas.sources(m))
    images = {n.image for n in copy.node_tree.nodes if n.type == "TEX_IMAGE"}
    assert images and not images & bakes


def test_an_atlas_over_the_cap_is_split_into_several(ch):
    """Issue 12: Body's atlas would be 8192 px, so under a 4096 px limit its materials go into several
    atlases, none scaled down, and the UVs land inside them."""
    sizes = {m.name: tuple(m.node_tree.nodes["tex.main.light"].image.size) for m in bpy.data.materials
             if m.get("kkbp_id") and "tex.main.light" in m.node_tree.nodes and m.node_tree.nodes["tex.main.light"].image}
    said = []
    collection = export_prep.prep(ch, "no_change", "none", "atlas", log=said.append, max_atlas=4096)
    body = next(o for o in collection.objects if o.type == "MESH" and o.name.startswith("Body"))
    atlas_slots = {i: s.material for i, s in enumerate(body.material_slots)
                   if s.material and s.material.get(atlas.ATLAS_OF)}
    images = {atlas.shown(m, "main.light") for m in atlas_slots.values()}
    assert len(images) > 1 and all(max(i.size) <= 4096 for i in images), [tuple(i.size) for i in images]
    assert any("atlases" in line and "4096 px" in line for line in said), said
    # Not scaled down: a material's texture takes as many atlas pixels as it has.
    uv = body.data.uv_layers["uv_main"].data
    by_original = {}
    for p in body.data.polygons:
        if p.material_index in atlas_slots:
            by_original.setdefault(_original_material(ch, body, p.index).name, []).extend(p.loop_indices)
    for name, loops in by_original.items():
        if not name.startswith(("cf_m_face_00", "cf_m_body")):
            continue  # the tongue's UVs go below 0, which no atlas, split or not, makes room for
        coords = [uv[i].uv for i in loops]
        box = (min(c.x for c in coords), max(c.x for c in coords), min(c.y for c in coords), max(c.y for c in coords))
        assert -1e-4 <= box[0] and box[1] <= 1 + 1e-4 and -1e-4 <= box[2] and box[3] <= 1 + 1e-4, (name, box, said)
    face_id = ch.materials(roles="face")[0][character.ID]
    face = next(m for m in atlas_slots.values() if face_id in atlas.sources(m))
    assert sizes["cf_m_face_00"] == (4096, 4096)
    assert tuple(atlas.shown(face, "main.light").size) == (4096, 4096)  # an atlas of its own
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
