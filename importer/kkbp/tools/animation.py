"""Import Animation: puts a Koikatsu FBX animation on the Character's Rigify rig, and IK snap (legacy
importanimation, D34). KKBP retargets on its own: the FBX's bones carry the game's names, which are
the bundle's bone Ids, so each rig control is found from a Bone Role (or, for bones no Role marks,
the game name), with no retargeting add-on.

Each frame, every mapped control takes its source bone's change of world rotation from its rest
pose, applied to the control's own rest; the torso also follows the source hips' movement, scaled by
the ratio of the two hips' heights. Controls are posed parents first.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import bpy
from mathutils import Matrix

from .. import compat
from ..bone_names import ROLE_NAMES

FBX_SCALE = 96  # the legacy import's global scale for the game's FBX animations
# Bone Role -> the rig control it drives. FK controls are the legacy rig names plus "_fk".
_FK = ("spine", "chest", "upper_chest", "upper_arm", "lower_arm", "hand", "upper_leg", "lower_leg", "foot", "toes")
_FINGERS = [r for r in ROLE_NAMES if any(f in r for f in ("thumb", "index", "middle", "ring", "little"))]
ROLE_TARGETS = {
    "hips": "torso", "neck": "neck", "head": "head",
    **{r: f"{ROLE_NAMES[r]}_fk" for r in ROLE_NAMES if r.split("_", 1)[-1] in _FK or r in ("spine", "chest", "upper_chest")},
    **{f"{s}_shoulder": ROLE_NAMES[f"{s}_shoulder"] for s in ("left", "right")},
    **{r: ROLE_NAMES[r] for r in _FINGERS},
    "left_breast": "Left Breast handle", "right_breast": "Right Breast handle",
}
# Game bones no Bone Role marks, and the rig control each drives (the legacy retargeting list's).
NAME_TARGETS = {
    "cf_j_waist01": "Hips_fk", "cf_j_waist02": "cf_j_waist02", "cf_j_kokan": "cf_j_kokan", "cf_j_ana": "cf_j_ana",
    "cf_d_bust00": "Breasts handle", "cf_j_siri_L": "Left Buttock handle", "cf_j_siri_R": "Right Buttock handle",
    **{f"cf_j_{b}_{s}": f"cf_j_{b}_{s}" for s in "LR" for b in ("bust02", "bust03", "bnip02root", "bnip02")},
}
ARM_STRETCH = 1.05  # the legacy option: arms 5% longer look closer to the game in some poses
LIMBS = ("Left arm", "Right arm", "Left leg", "Right leg")


def pairs(skeleton, source, rig) -> list[tuple[str, str]]:
    """(source bone, rig control) for every mapping both armatures have, parents first."""
    by_role = {b.role: b.id for b in skeleton.bones if b.role}
    found = [(by_role[r], t) for r, t in ROLE_TARGETS.items() if r in by_role]
    found += list(NAME_TARGETS.items())
    found = [(s, t) for s, t in found if s in source.pose.bones and t in rig.pose.bones]
    return sorted(found, key=lambda p: _depth(rig.data.bones[p[1]]))


def import_animation(ch, path, stretch_arms: bool = True, log=print):
    """Retargets the FBX animation at `path` onto the Character's rig as a new action; returns it."""
    rig = ch.rig
    if rig is None:
        raise ValueError(f"{ch.name} has no Rigify rig; import the animation onto a Character with Rigify")
    imported = compat.import_fbx(path, FBX_SCALE)
    source = next((o for o in imported if o.type == "ARMATURE"), None)
    try:
        if source is None or source.animation_data is None or source.animation_data.action is None:
            raise ValueError(f"{Path(path).name} has no armature animation")
        mapping = pairs(ch.bundle().skeleton, source, rig)
        log(f"{len(mapping)} rig controls follow the animation")
        action = _retarget(rig, source, mapping, _name(path), stretch_arms)
    finally:
        for obj in imported:
            data, actions = obj.data, [obj.animation_data.action] if obj.animation_data and obj.animation_data.action else []
            bpy.data.objects.remove(obj)
            if data is not None and data.users == 0:
                getattr(bpy.data, "armatures" if isinstance(data, bpy.types.Armature) else "meshes").remove(data)
            for a in actions:
                if a.users == 0:
                    bpy.data.actions.remove(a)
    return action


def ik_snap(rig):
    """Snaps the IK controls of the four limbs to their FK pose, then switches the limbs to IK
    (legacy ik_snap)."""
    for side in ("Left", "Right"):
        compat.rigify_ik_to_fk(
            rig, prop_bone=f"{side} arm_parent", fk_bones=f'["{side} arm_fk", "{side} elbow_fk", "{side} wrist_fk"]',
            ik_bones=f'["{side} arm_ik", "MCH-{side} elbow_ik", "MCH-{side} arm_ik_target"]',
            ctrl_bones=f'["{side} arm_ik", "{side} arm_ik_target", "{side} wrist_ik"]', tail_bones="[]",
            extra_ctrls=f'["{side} wrist_ik_wrist"]')
        compat.rigify_ik_to_fk(
            rig, prop_bone=f"{side} leg_parent",
            fk_bones=f'["{side} leg_fk", "{side} knee_fk", "{side} ankle_fk", "{side} toe_fk"]',
            ik_bones=f'["{side} leg_ik", "MCH-{side} knee_ik", "MCH-{side} leg_ik_target"]',
            ctrl_bones=f'["{side} leg_ik", "{side} leg_ik_target", "{side} ankle_ik"]', tail_bones=f'["{side} toe_ik"]',
            extra_ctrls=f'["{side} ankle_heel_ik", "{side} ankle_spin_ik"]')
    for limb in LIMBS:
        rig.pose.bones[f"{limb}_parent"]["IK_FK"] = 0


def _retarget(rig, source, mapping, name, stretch_arms):
    scene = bpy.context.scene
    start, end = (int(round(f)) for f in source.animation_data.action.frame_range)
    for limb in LIMBS:  # FK, as the animation drives the FK controls
        rig.pose.bones[f"{limb}_parent"]["IK_FK"] = 1
    rig.pose.bones["torso"]["neck_follow"] = 1.0
    rig.pose.bones["torso"]["head_follow"] = 1.0
    for bone in rig.pose.bones:
        bone.matrix_basis = Matrix()
    bpy.context.view_layer.update()
    source_rest = {s: source.matrix_world @ source.data.bones[s].matrix_local for s, _ in mapping}
    target_rest = {t: rig.matrix_world @ rig.data.bones[t].matrix_local for _, t in mapping}
    hips = next((s for s, t in mapping if t == "torso"), None)
    ratio = target_rest["torso"].translation.z / source_rest[hips].translation.z if hips else 1.0
    levels = defaultdict(list)
    for s, t in mapping:
        levels[_depth(rig.data.bones[t])].append((s, t))

    rig.animation_data_create()
    action = bpy.data.actions.new(name)
    rig.animation_data.action = action
    frame = scene.frame_current
    try:
        for f in range(start, end + 1):
            scene.frame_set(f)
            for _, level in sorted(levels.items()):
                for s, t in level:
                    _pose(rig, rig.pose.bones[t], source.matrix_world @ source.pose.bones[s].matrix, source_rest[s],
                          target_rest[t], ratio if t == "torso" else None)
                bpy.context.view_layer.update()
            for _, t in mapping:
                pb = rig.pose.bones[t]
                rotation = "rotation_quaternion" if pb.rotation_mode == "QUATERNION" else "rotation_euler"
                pb.keyframe_insert(rotation, frame=f)
                if t == "torso":
                    pb.keyframe_insert("location", frame=f)
            if stretch_arms:
                for side in ("Left", "Right"):
                    arm = rig.pose.bones.get(f"{side} arm_fk")
                    if arm is not None:
                        arm.scale[1] = ARM_STRETCH
                        arm.keyframe_insert("scale", index=1, frame=f)
    finally:
        scene.frame_set(frame)
    scene.frame_start, scene.frame_end = start, end
    return action


def _pose(rig, pb, source_pose, source_rest, target_rest, ratio):
    """Gives the control the source bone's change of world rotation; with `ratio`, its movement too."""
    rotation = source_pose.to_quaternion() @ source_rest.to_quaternion().inverted() @ target_rest.to_quaternion()
    current = rig.matrix_world @ pb.matrix
    location = current.translation
    if ratio is not None:
        location = target_rest.translation + (source_pose.translation - source_rest.translation) * ratio
    world = Matrix.LocRotScale(location, rotation, current.to_scale())
    pb.matrix = rig.matrix_world.inverted() @ world


def _depth(bone):
    depth = 0
    while bone.parent is not None:
        bone, depth = bone.parent, depth + 1
    return depth


def _name(path):
    """The action's name: the file's, without the exporter's "-p_cf_body_bone-N" ending."""
    stem = Path(path).stem
    return stem.split("-p_cf_body_bone")[0]
