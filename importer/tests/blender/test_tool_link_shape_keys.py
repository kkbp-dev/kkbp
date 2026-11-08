"""Separating the eyes and eyebrows on the builder's Character."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")
link = submodule("tools.link_shape_keys")
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
    made = link.link_shape_keys(ch)
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
