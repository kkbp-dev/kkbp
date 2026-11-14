"""The generated rig's custom shapes: sizes and turns that make the controls readable. In Object
Mode."""

from __future__ import annotations

import math

from .. import names

# (bone, scale); a bone the rig doesn't have is skipped.
SCALES = (
    (names.EYES_TRACK_TARGET_BONE, 1.5), (names.HEAD_TWEAK_BONE, 1.1),
    (names.LEFT_BREAST_DEFORM_BONE1, 0.4), (names.RIGHT_BREAST_DEFORM_BONE1, 0.4),
    (names.LEFT_BREAST_BONE2, 3), (names.RIGHT_BREAST_BONE2, 3),
    (names.LEFT_BREAST_DEFORM_BONE2, 0.3), (names.RIGHT_BREAST_DEFORM_BONE2, 0.3),
    (names.LEFT_BREAST_BONE3, 2), (names.RIGHT_BREAST_BONE3, 2),
    (names.LEFT_BREAST_DEFORM_BONE3, 0.2), (names.RIGHT_BREAST_DEFORM_BONE3, 0.2),
    (names.LEFT_NIPPLE_BONE1, 1), (names.RIGHT_NIPPLE_BONE1, 1),
    (names.LEFT_NIPPLE_DEFORM_BONE1, 0.1), (names.RIGHT_NIPPLE_DEFORM_BONE1, 0.1),
    (names.LEFT_NIPPLE_BONE2, 0.5), (names.RIGHT_NIPPLE_BONE2, 0.5),
    (names.LEFT_NIPPLE_DEFORM_BONE2, 0.05), (names.RIGHT_NIPPLE_DEFORM_BONE2, 0.05),
    (names.LEFT_SHOULDER_BONE, 1.25), (names.RIGHT_SHOULDER_BONE, 1.25),
    (names.LEFT_THUMB_BONE1, 1.3), (names.RIGHT_THUMB_BONE1, 1.3),
    (names.LEFT_THUMB_BONE2, 1.3), (names.RIGHT_THUMB_BONE2, 1.3),
    (names.LEFT_THUMB_BONE3, 1.2), (names.RIGHT_THUMB_BONE3, 1.2),
    (names.LEFT_INDEX_FINGER_BONE2, 1.1), (names.RIGHT_INDEX_FINGER_BONE2, 1.1),
    (names.LEFT_INDEX_FINGER_BONE3, 1.1), (names.RIGHT_INDEX_FINGER_BONE3, 1.1),
    (names.LEFT_MIDDLE_FINGER_BONE2, 1.1), (names.RIGHT_MIDDLE_FINGER_BONE2, 1.1),
    (names.LEFT_MIDDLE_FINGER_BONE3, 1.1), (names.RIGHT_MIDDLE_FINGER_BONE3, 1.1),
    (names.LEFT_RING_FINGER_BONE2, 1.1), (names.RIGHT_RING_FINGER_BONE2, 1.1),
    (names.LEFT_RING_FINGER_BONE3, 1.1), (names.RIGHT_RING_FINGER_BONE3, 1.1),
    (names.LEFT_LITTLE_FINGER_PALM_BONE, 1.1), (names.RIGHT_LITTLE_FINGER_PALM_BONE, 1.1),
    (names.LEFT_LITTLE_FINGER_PALM_FK_BONE, 1.1), (names.RIGHT_LITTLE_FINGER_PALM_FK_BONE, 1.1),
    (names.LEFT_LITTLE_FINGER_BONE2, 1.1), (names.RIGHT_LITTLE_FINGER_BONE2, 1.1),
    (names.LEFT_LITTLE_FINGER_BONE3, 1.1), (names.RIGHT_LITTLE_FINGER_BONE3, 1.1),
    (names.ROOT_BONE, 0.25), (names.EYES_HANDLE_BONE, 0.72),
    (names.LEFT_EYE_HANDLE_BONE, 0.72), (names.RIGHT_EYE_HANDLE_BONE, 0.72),
)
BETTER_PENETRATION_SCALE = 0.5
# The breast and nipple controls, which face forward.
FORWARD = (names.LEFT_BREAST_BONE2, names.RIGHT_BREAST_BONE2, names.LEFT_BREAST_BONE3, names.RIGHT_BREAST_BONE3,
           names.LEFT_NIPPLE_BONE1, names.RIGHT_NIPPLE_BONE1, names.LEFT_NIPPLE_BONE2, names.RIGHT_NIPPLE_BONE2)
BUTTOCK_HANDLE = " Buttock handle"  # the left and right handles, and the rig's ORG- and DEF- copies


def _scale(rig, bone, scale):
    if pose_bone := rig.pose.bones.get(bone):
        pose_bone.custom_shape_scale_xyz = (scale, scale, scale)


def scale_and_turn(build):
    rig = build.rig
    for bone, scale in SCALES:
        _scale(rig, bone, scale)
    for bone in [b.name for b in rig.data.bones if b.name.startswith(names.BETTER_PENETRATION_BONE_PREFIX)]:
        _scale(rig, bone, BETTER_PENETRATION_SCALE)
    for bone in FORWARD:
        if pose_bone := rig.pose.bones.get(bone):
            pose_bone.custom_shape_rotation_euler[0] = math.pi / 2
    for pose_bone in [b for b in rig.pose.bones if b.name.endswith(BUTTOCK_HANDLE)]:
        pose_bone.custom_shape_rotation_euler[0] = math.pi / 4
        pose_bone.custom_shape_rotation_euler[1] = 0.436 if "Right" in pose_bone.name else -0.436
    for bone in build.face_bone_names():
        if pose_bone := rig.pose.bones.get(bone):
            pose_bone.custom_shape_rotation_euler[0] = math.pi / 2
    _scale(rig, names.CROTCH_BONE, 0.2)

