"""Separating the eyes and eyebrows on the builder's Character."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")
separate_eyes = submodule("builtin.separate_eyes")
settings = submodule("settings")


def test_the_eyes_become_a_part_with_linked_keys(build, monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})
    b = BundleBuilder()
    b.add_expression("cf_Ohitomi_L", "Eye Happy", "eye", game_name="笑い")
    result = kkbp.api.import_bundle(build(b), hooks=[])
    ch = character.Character(result.character_key)
    faces_before = len(ch.body.data.polygons)
    ch.armature.location = (0.0, 0.2, 0.0)
    ch.body.location = (0.1, 0.0, 0.3)  # an offset from the armature, which the parts mustn't repeat
    bpy.context.view_layer.update()
    made = separate_eyes.separate(ch)
    bpy.context.view_layer.update()
    eyes = ch.parts("eyes")
    assert made == eyes and len(eyes) == 1 and eyes[0].parent == ch.body
    # Its origin is Body's, so it stays exactly where it was in Body.
    assert (eyes[0].matrix_world.translation - ch.body.matrix_world.translation).length < 1e-6
    assert all(abs(a - b) < 1e-6 for ra, rb in zip(eyes[0].matrix_world, ch.body.matrix_world) for a, b in zip(ra, rb))
    assert {s.material.get("kkbp_role") for s in eyes[0].material_slots if s.material} <= {"eye_l", "eye_r"}
    assert len(ch.body.data.polygons) + len(eyes[0].data.polygons) == faces_before
    driven = [fc.data_path for fc in eyes[0].data.shape_keys.animation_data.drivers]
    assert 'key_blocks["Eye Happy"].value' in driven


def test_the_hook_runs_after_rigify_and_puts_the_parts_in_their_own_collection(build, monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})
    steps = submodule("pipeline.steps")
    assert steps.BUILTIN_HOOKS.index("Separate Eyes") == steps.BUILTIN_HOOKS.index("Rigify") + 1
    b = BundleBuilder()
    b.add_expression("cf_Ohitomi_L", "Eye Happy", "eye", game_name="笑い")
    result = kkbp.api.import_bundle(build(b), options={"separate_eyes": True}, hooks=["Separate Eyes"])
    assert result.hooks[0].status == "ran", result.hooks
    ch = character.Character(result.character_key)
    eyes = ch.parts("eyes")
    assert len(eyes) == 1
    assert [c.name for c in eyes[0].users_collection] == [f"Eyes and Eyebrows {ch.name}"]
    assert ch.body.users_collection[0] is ch.collection


def _cryptomatte_passes():
    return [(layer.use_pass_cryptomatte_object, layer.use_pass_cryptomatte_material)
            for layer in bpy.context.scene.view_layers]


def test_the_hook_turns_on_the_cryptomatte_passes_of_every_view_layer(build, monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})
    bpy.context.scene.view_layers.new("Second")
    b = BundleBuilder()
    b.add_expression("cf_Ohitomi_L", "Eye Happy", "eye", game_name="笑い")
    assert kkbp.api.import_bundle(build(b), hooks=[]).ok
    assert _cryptomatte_passes() == [(False, False), (False, False)]  # an import without the Hook leaves them
    result = kkbp.api.import_bundle(build(b), options={"separate_eyes": True}, hooks=["Separate Eyes"])
    assert result.hooks[0].status == "ran", result.hooks
    assert _cryptomatte_passes() == [(True, True), (True, True)]
    assert not any(layer.use_pass_cryptomatte_asset for layer in bpy.context.scene.view_layers)


def test_the_eyeline_shadow_goes_with_the_eyes(build, monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})
    b = BundleBuilder()
    b.add_material("cf_m_eyeline_kage", role="eyeline_shadow", blend_mode="alpha",
                   textures=[b.add_texture("_MainTex", role="main")])
    b.add_mesh("cf_O_eyeline_kage", ["cf_m_eyeline_kage"], bone="cf_j_head")
    b.add_expression("cf_Ohitomi_L", "Eye Happy", "eye", game_name="笑い")
    ch = character.Character(kkbp.api.import_bundle(build(b), hooks=[]).character_key)
    assert any(s.material.get("kkbp_role") == "eyeline_shadow" for s in ch.body.material_slots if s.material)
    separate_eyes.separate(ch)
    roles = lambda o: {s.material.get("kkbp_role") for s in o.material_slots if s.material}
    assert "eyeline_shadow" in roles(ch.parts("eyes")[0])
    # Body keeps its material slots, but no face uses the shadow's any more.
    used = {ch.body.material_slots[p.material_index].material.get("kkbp_role") for p in ch.body.data.polygons}
    assert "eyeline_shadow" not in used


def test_svs_eyelashes_and_eyelids_go_with_the_eyes(golden_import):
    """Issue 27: SVS draws its eye lines with an eyelash and an eyelid material, which go to the eyes
    Part as KK's eyelines do."""
    result, ch = golden_import("svs", hooks=["Separate Eyes"], options={"separate_eyes": True})
    assert result.hooks[0].status == "ran", result.hooks

    def roles(obj):
        used = {p.material_index for p in obj.data.polygons}
        return {s.material.get("kkbp_role") for i, s in enumerate(obj.material_slots) if s.material and i in used}

    eyes, = ch.parts("eyes")
    assert roles(eyes) == {"eye_l", "eye_r", "eye_white", "eyelash", "eyelid"}
    eyebrows, = ch.parts("eyebrows")
    assert roles(eyebrows) == {"eyebrow"}
    assert not roles(ch.body) & {"eye_l", "eye_r", "eye_white", "eyelash", "eyelid", "eyebrow"}
