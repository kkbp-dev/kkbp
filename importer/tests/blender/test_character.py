"""Character on small hand-built scenes (docs/design/character.md, "Testing")."""

import bpy
import pytest

from conftest import submodule

character = submodule("character")
Character, CharacterError = character.Character, character.CharacterError


def _obj(name, data=None):
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _mesh(name, material=None):
    mesh = bpy.data.meshes.new(name)
    if material:
        mesh.materials.append(material)
    return _obj(name, mesh)


def _chika(tmp_path=None):
    ch = Character.new("Chika", "KK", tmp_path or "/nowhere")
    ch.add_part(_obj("Armature", bpy.data.armatures.new("Armature")), "armature")
    ch.add_part(_mesh("Body"), "body")
    ch.add_part(_mesh("Hair front"), "hair", outfit=0)
    ch.add_part(_mesh("Hair back"), "hair", outfit=0)
    ch.add_part(_mesh("Top"), "outfit", outfit=0)
    ch.add_part(_mesh("Top (alt)"), "alt_outfit", outfit=0)
    ch.add_part(_mesh("Skirt"), "outfit", outfit=1)
    ch.add_part(_mesh("Tears"), "tears")
    return ch


def test_parts_by_role():
    ch = _chika()
    assert ch.body.name == "Body"
    assert ch.armature.name == "Armature"
    assert ch.rig is None and ch.gag_eyes is None
    assert not hasattr(ch, "tongue")  # the tongue is part of Body (ADR 0039)
    assert ch.control is ch.armature
    assert sorted(o.name for o in ch.hairs) == ["Hair back", "Hair front"]
    assert sorted(o.name for o in ch.outfits) == ["Skirt", "Top"]
    assert [o.name for o in ch.alt_outfits] == ["Top (alt)"]
    assert sorted(o.name for o in ch.outfit(0)) == ["Hair back", "Hair front", "Top", "Top (alt)"]
    assert sorted(o.name for o in ch.parts(roles=("tears", "body"))) == ["Body", "Tears"]


def test_character_values_live_on_every_part():
    ch = _chika()
    again = Character.of(bpy.data.objects["Skirt"])
    assert again == ch and again.key == ch.key
    assert (again.name, again.game, str(again.bundle_path)) == ("Chika", "KK", "/nowhere")
    assert bpy.data.objects["Skirt"]["kkbp_outfit"] == 1
    assert "kkbp_outfit" not in bpy.data.objects["Body"]


def test_the_rig_is_the_control():
    ch = _chika()
    ch.add_part(_obj("Rig", bpy.data.armatures.new("Rig")), "rig")
    assert ch.control.name == "Rig"
    assert ch.armature.name == "Armature"


def test_names_and_collections_dont_count():
    ch = _chika()
    body = ch.body
    body.name = "Chika's body, renamed"
    stray = _mesh("Body")
    other = bpy.data.collections.new("Elsewhere")
    bpy.context.scene.collection.children.link(other)
    other.objects.link(body)
    assert ch.body == body
    assert Character.of(stray) is None


def test_a_duplicated_body_is_a_clear_error():
    ch = _chika()
    copy = ch.body.copy()
    bpy.context.scene.collection.objects.link(copy)
    with pytest.raises(CharacterError, match=r"Chika has 2 body Parts \(Body, Body.001\)"):
        ch.body


def test_add_part_checks_its_input():
    ch = _chika()
    with pytest.raises(ValueError, match="isn't a Part Role"):
        ch.add_part(_mesh("Hat"), "hat")
    with pytest.raises(ValueError, match="needs its Outfit index"):
        ch.add_part(_mesh("Socks"), "outfit")
    other = Character.new("Yui", "SVS", "/elsewhere")
    with pytest.raises(CharacterError, match="already a Part of another Character"):
        other.add_part(ch.body, "body")


def test_a_new_character_knows_its_values_before_it_has_parts():
    ch = Character.new("Yui", "SVS", "/elsewhere")
    assert (ch.name, ch.game, str(ch.bundle_path)) == ("Yui", "SVS", "/elsewhere")
    assert ch.parts() == [] and ch.body is None


def test_two_characters_in_one_scene():
    chika = _chika()
    yui = Character.new("Yui", "SVS", "/elsewhere")
    yui.add_part(_mesh("Yui body"), "body")
    assert chika.key != yui.key
    assert Character.all(bpy.context.scene) == [chika, yui]
    assert yui.body.name == "Yui body" and chika.body.name == "Body"


def test_materials_with_clashing_names():
    chika, yui = Character.new("Chika", "KK", "/a"), Character.new("Yui", "KK", "/b")
    first = bpy.data.materials.new("cf_m_body")
    second = bpy.data.materials.new("cf_m_body")
    assert second.name == "cf_m_body.001"
    chika.tag_material(first, "cf_m_body", role="body")
    yui.tag_material(second, "cf_m_body", role="body")
    chika.add_part(_mesh("Chika body", first), "body")
    assert chika.material("cf_m_body") == first
    assert yui.material("cf_m_body") == second
    assert chika.materials(roles="body") == [first]
    assert chika.material("missing") is None


def test_materials_by_part_role():
    ch = _chika()
    skin = ch.tag_material(bpy.data.materials.new("skin"), "cf_m_body", role="body")
    cloth = ch.tag_material(bpy.data.materials.new("cloth"), "ct_top")
    ch.body.data.materials.append(skin)
    ch.outfits[0].data.materials.append(cloth)
    assert ch.materials(parts="outfit") == [cloth]
    assert set(ch.materials(roles=None, parts=("body", "outfit"))) == {skin, cloth}
    assert ch.materials(roles="body", parts="outfit") == []


def test_images():
    ch = _chika()
    image = ch.tag_image(bpy.data.images.new("0001.png", 1, 1), "textures/0001.png")
    assert ch.image("textures/0001.png") == image
    assert ch.image("textures/0002.png") is None


def test_undo_in_the_middle_of_a_lookup():
    ch = _chika()
    bpy.ops.ed.undo_push(message="parts made")
    ch.add_part(_mesh("Gag eyes"), "gag_eyes")
    bpy.ops.ed.undo_push(message="gag eyes added")
    held = ch.gag_eyes
    assert held.name == "Gag eyes"
    bpy.ops.ed.undo()
    # The held reference is gone; a fresh lookup through the same Character still works.
    with pytest.raises(ReferenceError):
        held.name
    assert ch.gag_eyes is None
    assert ch.body.name == "Body"


def test_which_character_a_tool_works_on():
    with pytest.raises(CharacterError, match="no KKBP Character"):
        Character.for_tool(bpy.context)
    chika = _chika()
    assert Character.for_tool(bpy.context) == chika
    yui = Character.new("Yui", "SVS", "/elsewhere")
    yui_body = yui.add_part(_mesh("Yui body"), "body")
    with pytest.raises(CharacterError, match="Select an object"):
        Character.for_tool(bpy.context)
    with bpy.context.temp_override(active_object=yui_body):
        assert Character.for_tool(bpy.context) == yui


def test_bundle_reopens_the_export_bundle(build):
    path = build()
    ch = Character.new("Test Chara", "KK", path)
    ch.add_part(_mesh("Body"), "body")
    assert ch.bundle().path == path


def test_bundle_that_moved_is_a_clear_error(build, tmp_path):
    path = build()
    ch = Character.new("Test Chara", "KK", path)
    ch.add_part(_mesh("Body"), "body")
    path.rename(tmp_path / "moved")
    with pytest.raises(character.BundleMissingError, match="Test Chara's Export Bundle is no longer at"):
        ch.bundle()


def test_the_collection_is_the_characters_own_not_a_sub_collection():
    ch = _chika()
    own = ch.add_collection(bpy.context.scene.collection)
    sub = bpy.data.collections.new("Alts 00 Chika")
    sub[character.KEY], sub[character.SUB_COLLECTION] = ch.key, "Alts 00 Chika"
    own.children.link(sub)
    for _ in range(3):  # whatever order bpy.data.collections lists them in
        assert ch.collection == own
        sub.name = "A" + sub.name
