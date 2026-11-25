"""The Rigify Hook's teeth bones: five controls for each row of teeth, on
teeth that still follow the mouth bones as they did."""

import bpy
import pytest

from bundle_copy import copy_bundle
from conftest import golden, kkbp, submodule

names = submodule("builtin.rigify.names")
character = submodule("character")
settings = submodule("settings")
teeth = submodule("builtin.rigify.metarig.teeth")

SAMPLES = ("kk", "kks", "svs")
CONTROLS = [names.teeth_bone(row, place) for row in names.TEETH_ROWS for place in names.TEETH_PLACES]
# Mouth bones a game weights its teeth to, which both rigs have as controls.
MOUTH_BONES = ("cf_J_MouthCavity", "cf_J_MouthMove", "cf_J_Mouth_L")


@pytest.fixture(autouse=True)
def empty_scene():
    """Each test picks its own import; the scene isn't reset between tests."""
    yield


def _teeth(ch):
    body = ch.body
    slots = {i for i, s in enumerate(body.material_slots) if s.material and s.material.get("kkbp_role") == "teeth"}
    return sorted({v for p in body.data.polygons if p.material_index in slots for v in p.vertices})


def _positions(ch, vertices):
    bpy.context.view_layer.update()
    evaluated = ch.body.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return [evaluated.data.vertices[v].co.copy() for v in vertices]


def _moved_by(ch, bone, vertices, offset=(0.003, 0.002, 0.001)):
    """How far each of `vertices` goes when the rig's `bone` moves and turns."""
    pose_bone = ch.rig.pose.bones[bone]
    before = _positions(ch, vertices)
    pose_bone.location = offset
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler = (0.2, 0.1, 0.3)
    after = _positions(ch, vertices)
    pose_bone.location = (0, 0, 0)
    pose_bone.rotation_euler = (0, 0, 0)
    return [b - a for a, b in zip(before, after)]


def _without_teeth_bones(scenes, sample):
    """The Golden Sample with a Rigify rig that was given no teeth bones, to compare with."""
    def make(folder):
        copy = copy_bundle(golden(sample), folder / sample)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(settings, "option_defaults", lambda: {})
            mp.setattr(teeth, "add_bones", lambda build: None)
            result = kkbp.api.import_bundle(copy, hooks=["Rigify"])
        assert result.ok, f"{result.failed_step}: {result.error}"
        return result.character_key

    return character.Character(scenes.get(("no teeth bones", sample), make))


@pytest.mark.parametrize("sample", SAMPLES)
def test_each_row_of_teeth_gets_five_controls(golden_import, sample):
    _, ch = golden_import(sample, hooks=["Rigify"])
    rig = ch.rig
    for name in CONTROLS:
        bone = rig.pose.bones.get(name)
        assert bone is not None and bone.custom_shape is not None, name
        assert not any(bone.lock_location), name
    upper = [rig.data.bones[names.teeth_bone("upper", p)].head_local for p in names.TEETH_PLACES]
    lower = [rig.data.bones[names.teeth_bone("lower", p)].head_local for p in names.TEETH_PLACES]
    assert all(u.z > l.z for u, l in zip(upper, lower))
    for row in (upper, lower):
        assert [round(p.x, 4) for p in row] == sorted((round(p.x, 4) for p in row), reverse=True)  # left is +x
        assert abs(row[2].x) < 0.001 and row[2].y < min(row[0].y, row[4].y)  # the middle one is at the front


@pytest.mark.parametrize("sample", SAMPLES)
def test_every_teeth_vertex_keeps_a_whole_weight(golden_import, sample):
    _, ch = golden_import(sample, hooks=["Rigify"])
    body, rig = ch.body, ch.rig
    group_names = {g.index: g.name for g in body.vertex_groups}
    for index in _teeth(ch):
        weights = {group_names[g.group]: g.weight for g in body.data.vertices[index].groups
                   if g.weight > 0 and group_names[g.group] in rig.data.bones}
        assert abs(sum(weights.values()) - 1) < 1e-4, (index, weights)
        assert all(name.startswith("Teeth ") for name in weights), (index, weights)


@pytest.mark.parametrize("sample", SAMPLES)
def test_an_end_control_moves_its_end_of_its_row_only(golden_import, sample):
    _, ch = golden_import(sample, hooks=["Rigify"])
    vertices = _teeth(ch)
    rest = _positions(ch, vertices)
    moved = _moved_by(ch, names.teeth_bone("upper", "L2"), vertices)
    gone = [rest[i] for i, d in enumerate(moved) if d.length > 1e-6]
    assert gone and all(p.x > 0 for p in gone)
    assert max(d.length for d in moved) > 0.003  # the whole of the control's 3.7 mm, and its turn
    middle = (min(p.z for p in rest) + max(p.z for p in rest)) / 2
    assert min(p.z for p in gone) > middle - 0.004  # none of the lower row's own height


@pytest.mark.parametrize("sample", SAMPLES)
def test_the_teeth_follow_the_mouth_bones_as_without_teeth_bones(golden_import, scenes, sample):
    ch = _without_teeth_bones(scenes, sample)
    assert not [b.name for b in ch.rig.data.bones if b.name.startswith("Teeth ")]
    vertices = _teeth(ch)
    before = {bone: _moved_by(ch, bone, vertices) for bone in MOUTH_BONES}
    _, ch = golden_import(sample, hooks=["Rigify"])
    assert _teeth(ch) == vertices
    for bone in MOUTH_BONES:
        after = _moved_by(ch, bone, vertices)
        worst = max((a - b).length for a, b in zip(before[bone], after))
        assert worst < 1e-5, (bone, worst)
    assert any(d.length > 1e-4 for moved in before.values() for d in moved)
