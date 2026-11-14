"""Import Animation: a walk FBX onto a copy of the KK Golden Sample's Rigify rig (D34).

The walk is made here, not committed (ADR 0031): an armature whose bones carry the game's names, at the
rest positions of the bones the Rigify Hook renamed, with a 24-frame swing on the hips, spine, arms and
legs, written with Blender's FBX exporter at 1/FBX_SCALE, the scale the game's own FBX animations come in.
"""

import math

import bpy
import pytest
from mathutils import Vector

from conftest import submodule

character = submodule("character")
animation = submodule("tools.animation")
bone_names = submodule("bone_names")
compat = submodule("compat")
editing = submodule("editing")
settings = submodule("settings")
FRAMES = 24
# The bones the walk moves, and how far each swings (radians about its rest X axis) over FRAMES.
SWING = {"hips": 0.05, "chest": 0.1, "left_upper_arm": 0.6, "right_upper_arm": -0.6, "left_lower_arm": 0.3,
         "right_lower_arm": 0.3, "left_upper_leg": -0.5, "right_upper_leg": 0.5, "left_lower_leg": 0.4,
         "right_lower_leg": 0.4}


@pytest.fixture(autouse=True)
def no_preferences(monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})


@pytest.fixture
def walked(scenes, golden_import):
    """(Character, walk FBX, action): the KK Golden Sample with Rigify and the walk retargeted onto
    its rig. The retarget takes about ten seconds, so it is made once and each test opens a copy
    (SceneCache)."""
    def make(folder):
        result, rigged = golden_import("kk", hooks=["Rigify"])
        assert result.hooks[0].status == "ran", result.hooks
        path = _write_walk(rigged, folder)
        action = animation.import_animation(rigged, path, log=lambda m: None)
        return result.character_key, path, action.name

    key, path, name = scenes.get(("kk walk",), make)
    return character.Character(key), path, bpy.data.actions[name]


def _write_walk(rigged, folder):
    """Writes the walk FBX for `rigged`'s skeleton into `folder` and returns its path; the armature
    it was made from is gone again."""
    skeleton = rigged.bundle().skeleton
    metarig = rigged.armature.data.bones
    by_id = {b.id: b for b in skeleton.bones}
    # Bundle Id -> role, for every role the retargeting maps and the Rigify Hook renamed.
    roles = {b.id: b.role for b in skeleton.bones
             if b.role in animation.ROLE_TARGETS and bone_names.ROLE_NAMES.get(b.role, "") in metarig}

    def parent(bone_id):
        bone = by_id[bone_id].parent
        while bone is not None and bone not in roles:
            bone = by_id[bone].parent
        return bone

    data = bpy.data.armatures.new("Armature")
    source = bpy.data.objects.new("Armature", data)
    bpy.context.scene.collection.objects.link(source)
    source.matrix_world = rigged.armature.matrix_world
    with editing.editing(source):
        for bone_id, role in roles.items():
            rest = metarig[bone_names.ROLE_NAMES[role]]
            eb = data.edit_bones.new(bone_id)
            eb.head, eb.tail, eb.roll = rest.head_local, rest.tail_local, 0.0
            eb.matrix = rest.matrix_local
        for bone_id in roles:
            if parent(bone_id) is not None:
                data.edit_bones[bone_id].parent = data.edit_bones[parent(bone_id)]

    source.animation_data_create()
    source.animation_data.action = bpy.data.actions.new("walk")
    swinging = {b: SWING[r] for b, r in roles.items() if r in SWING}
    for frame in range(1, FRAMES + 1):
        phase = math.sin(2 * math.pi * (frame - 1) / FRAMES)
        for bone_id, amount in swinging.items():
            pb = source.pose.bones[bone_id]
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (amount * phase, 0.0, 0.0)
            pb.keyframe_insert("rotation_euler", frame=frame)
        hips = source.pose.bones[next(b for b, r in roles.items() if r == "hips")]
        hips.location = (0.0, 0.02 * phase, 0.0)
        hips.keyframe_insert("location", frame=frame)

    path = folder / "walk.fbx"
    for obj in bpy.context.view_layer.objects:
        obj.select_set(obj == source)
    bpy.context.view_layer.objects.active = source
    result = bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, object_types={"ARMATURE"},
                                      global_scale=1 / animation.FBX_SCALE, add_leaf_bones=False, bake_anim=True,
                                      bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
                                      bake_anim_force_startend_keying=True)
    assert result == {"FINISHED"}
    action = source.animation_data.action
    bpy.data.objects.remove(source)
    bpy.data.armatures.remove(data)
    bpy.data.actions.remove(action)
    return path


def _turn(matrix, rest):
    """The world rotation from rest to pose."""
    return matrix.to_quaternion() @ rest.to_quaternion().inverted()


def test_the_walk_drives_the_rig_like_the_game_bones(walked):
    rigged, walk, action = walked
    rig = rigged.rig
    assert action.name == "walk" and rig.animation_data.action == action
    assert not [o for o in bpy.data.objects if o.type == "ARMATURE" and o not in (rig, rigged.armature)
                and o.name.startswith("Armature") and "kkbp_key" not in o]  # the FBX's armature went
    source = next(o for o in compat.import_fbx(walk, animation.FBX_SCALE) if o.type == "ARMATURE")
    for frame in (6, 15):
        bpy.context.scene.frame_set(frame)
        for game, deform in (("cf_j_arm00_L", "DEF-Left arm"), ("cf_j_thigh00_R", "DEF-Right leg"),
                             ("cf_j_spine02", "DEF-Chest")):
            want = _turn(source.matrix_world @ source.pose.bones[game].matrix,
                         source.matrix_world @ source.data.bones[game].matrix_local)
            got = _turn(rig.matrix_world @ rig.pose.bones[deform].matrix,
                        rig.matrix_world @ rig.data.bones[deform].matrix_local)
            # Where each turn points the deform bone: Rigify spreads twist along its limb chains, so
            # the bone's direction is compared, not its roll.
            axis = (rig.matrix_world @ rig.data.bones[deform].matrix_local).to_3x3() @ Vector((0.0, 1.0, 0.0))
            angle = math.degrees((want @ axis).angle(got @ axis))
            assert angle < 5, (frame, game, angle)


def test_the_meshes_are_back_after_the_retarget(walked):
    """Issue 67: the meshes are kept out of the evaluation only while the retarget runs."""
    rigged, _, _ = walked
    meshes = [o for o in rigged.parts() if o.type == "MESH"]
    assert meshes and not any(o.hide_viewport for o in meshes)


def test_a_frame_the_quick_way_misses_is_posed_level_by_level(golden_import, tmp_path, monkeypatch):
    """Issue 67: when the controls don't reach their goals with one or two updates, the frame is posed
    with an update for each bone depth, and the result is the same."""
    result, rigged = golden_import("kk", hooks=["Rigify"])
    path = _write_walk(rigged, tmp_path)
    real, frames = animation._missed, set()

    def misses_at_first(rig, goals):
        frame = bpy.context.scene.frame_current
        if frame <= 6:  # these frames always "miss", so they take the slow way
            frames.add(frame)
            return set(goals)
        return real(rig, goals)

    monkeypatch.setattr(animation, "_missed", misses_at_first)
    said = []
    animation.import_animation(rigged, path, log=said.append)
    assert any(f"{len(frames)} frames were posed the slower way" in line for line in said), (said, sorted(frames))
    rig = rigged.rig
    source = next(o for o in compat.import_fbx(path, animation.FBX_SCALE) if o.type == "ARMATURE")
    bpy.context.scene.frame_set(6)
    for game, deform in (("cf_j_arm00_L", "DEF-Left arm"), ("cf_j_thigh00_R", "DEF-Right leg")):
        want = _turn(source.matrix_world @ source.pose.bones[game].matrix,
                     source.matrix_world @ source.data.bones[game].matrix_local)
        got = _turn(rig.matrix_world @ rig.pose.bones[deform].matrix,
                    rig.matrix_world @ rig.data.bones[deform].matrix_local)
        axis = (rig.matrix_world @ rig.data.bones[deform].matrix_local).to_3x3() @ Vector((0.0, 1.0, 0.0))
        assert math.degrees((want @ axis).angle(got @ axis)) < 5, game


def test_ik_snap_switches_the_limbs_to_ik(walked):
    rigged, _, _ = walked
    bpy.context.scene.frame_set(10)
    animation.ik_snap(rigged.rig)
    assert all(rigged.rig.pose.bones[f"{limb}_parent"]["IK_FK"] == 0 for limb in animation.LIMBS)
