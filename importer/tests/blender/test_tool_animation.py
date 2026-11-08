"""Import Animation: a walk FBX onto a copy of the KK Golden Sample's Rigify rig (D34).

The walk is made here, not committed (ADR 0031): an armature whose bones carry the game's names, at the
rest positions of the bones the Rigify Hook renamed, with a 24-frame swing on the hips, spine, arms and
legs, written with Blender's FBX exporter at 1/FBX_SCALE, the scale the game's own FBX animations come in.
"""

import math
import shutil

import bpy
import pytest
from mathutils import Vector

from conftest import golden, kkbp, submodule

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
def rigged(tmp_path):
    copy = tmp_path / "kk"
    shutil.copytree(golden("kk"), copy, ignore=shutil.ignore_patterns("kkbp_cache"))
    result = kkbp.api.import_bundle(copy, hooks=["Rigify"])
    assert result.ok and result.hooks[0].status == "ran", result.hooks
    return character.Character(result.character_key)


@pytest.fixture
def walk(rigged, tmp_path):
    """Writes the walk FBX for `rigged`'s skeleton and returns its path; the armature it was made
    from is gone again."""
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

    path = tmp_path / "walk.fbx"
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


def test_the_walk_drives_the_rig_like_the_game_bones(rigged, walk):
    action = animation.import_animation(rigged, walk, log=lambda m: None)
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


def test_ik_snap_switches_the_limbs_to_ik(rigged, walk):
    animation.import_animation(rigged, walk, log=lambda m: None)
    bpy.context.scene.frame_set(10)
    animation.ik_snap(rigged.rig)
    assert all(rigged.rig.pose.bones[f"{limb}_parent"]["IK_FK"] == 0 for limb in animation.LIMBS)
