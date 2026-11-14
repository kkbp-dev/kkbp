"""Each metarig bone's Rigify type and parameters: what Rigify generates for it. Every bone starts as
a raw copy; the tables below make the spine, limbs, fingers and face rigs. In Object Mode."""

from __future__ import annotations

from .. import bone_collections, names

TYPE = "rigify_type"  # on the pose bone; every other attribute is a Rigify parameter
WIDGET = "optional_widget_type"


def _both(left, right, attribute, value):
    return ((left, attribute, value), (right, attribute, value))


EYES = ((names.EYES_TRACK_TARGET_BONE, WIDGET, "pivot_cross"), (names.EYEBALLS_BONE, WIDGET, "bone"),
        *_both(names.LEFT_EYEBALL_BONE, names.RIGHT_EYEBALL_BONE, WIDGET, "bone"))
TONGUE = (
    (names.RIGGED_TONGUE_BONE1, WIDGET, "jaw"),
    (names.RIGGED_TONGUE_BONE2, TYPE, "limbs.super_finger"),
    (names.RIGGED_TONGUE_BONE2, "primary_rotation_axis", "-X"),
    (names.RIGGED_TONGUE_BONE2, "make_extra_ik_control", True),
    (names.RIGGED_TONGUE_BONE3, TYPE, ""),
    *_both(names.RIGGED_TONGUE_LEFT_BONE3, names.RIGGED_TONGUE_RIGHT_BONE3, WIDGET, "sphere"),
    (names.RIGGED_TONGUE_BONE4, TYPE, ""),
    *_both(names.RIGGED_TONGUE_LEFT_BONE4, names.RIGGED_TONGUE_RIGHT_BONE4, WIDGET, "sphere"),
    (names.RIGGED_TONGUE_BONE5, TYPE, ""),
    *_both(names.RIGGED_TONGUE_LEFT_BONE5, names.RIGGED_TONGUE_RIGHT_BONE5, WIDGET, "sphere"),
)
SPINE = (
    (names.HEAD_BONE, TYPE, ""),
    (names.HEAD_TRACK_BONE, "relink_constraints", True),
    (names.HEAD_TRACK_BONE, "parent_bone", names.HEAD_TWEAK_BONE),
    (names.HEAD_TRACK_TARGET_BONE, WIDGET, "pivot_cross"),
    (names.NECK_BONE, TYPE, "spines.super_head"),
    (names.NECK_BONE, "connect_chain", True),
    (names.UPPER_CHEST_BONE, TYPE, ""),
    (names.CHEST_BONE, TYPE, ""),
    (names.SPINE_BONE, TYPE, ""),
    (names.HIPS_BONE, TYPE, "spines.basic_spine"),
    (names.HIPS_BONE, "pivot_pos", 1),
    (names.WAIST_BONE, WIDGET, "diamond"),
    (names.CROTCH_BONE, WIDGET, "sphere"),
    (names.ANUS_BONE, WIDGET, "sphere"),
)
BETTER_PENETRATION = tuple((bone, WIDGET, "circle") for bone in (
    names.BETTER_PENETRATION_ROOT_CROTCH_BONE, names.BETTER_PENETRATION_FRONT_CROTCH_BONE,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE1, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE1,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE2, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE2,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE3, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE3,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE4, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE4,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE5, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE5,
    names.BETTER_PENETRATION_BACK_CROTCH_BONE))
BREASTS = (*_both(names.LEFT_BREAST_DEFORM_BONE1, names.RIGHT_BREAST_DEFORM_BONE1, WIDGET, "sphere"),
           *_both(names.LEFT_BREAST_DEFORM_BONE2, names.RIGHT_BREAST_DEFORM_BONE2, WIDGET, "sphere"),
           *_both(names.LEFT_BREAST_DEFORM_BONE3, names.RIGHT_BREAST_DEFORM_BONE3, WIDGET, "sphere"))
NIPPLES = (*_both(names.LEFT_NIPPLE_DEFORM_BONE1, names.RIGHT_NIPPLE_DEFORM_BONE1, WIDGET, "sphere"),
           *_both(names.LEFT_NIPPLE_DEFORM_BONE2, names.RIGHT_NIPPLE_DEFORM_BONE2, WIDGET, "sphere"))
ARMS = (
    *_both(names.LEFT_SHOULDER_BONE, names.RIGHT_SHOULDER_BONE, WIDGET, "shoulder"),
    *_both(names.LEFT_ARM_BONE, names.RIGHT_ARM_BONE, TYPE, "limbs.arm"),
    *_both(names.LEFT_ARM_BONE, names.RIGHT_ARM_BONE, "segments", 3),
    *_both(names.LEFT_ARM_BONE, names.RIGHT_ARM_BONE, "rotation_axis", "automatic"),
    *_both(names.LEFT_ARM_BONE, names.RIGHT_ARM_BONE, "limb_uniform_scale", True),
    *_both(names.LEFT_ARM_BONE, names.RIGHT_ARM_BONE, "auto_align_extremity", True),
    *_both(names.LEFT_ARM_BONE, names.RIGHT_ARM_BONE, "make_ik_wrist_pivot", True),
    *_both(names.LEFT_ELBOW_BONE, names.RIGHT_ELBOW_BONE, TYPE, ""),
    *_both(names.LEFT_WRIST_BONE, names.RIGHT_WRIST_BONE, TYPE, ""),
)
# The joint-correction bones that follow a limb's deform bone on the generated rig.
ARM_CORRECTIONS = (
    *_both(names.FRONT_LEFT_ELBOW_JOINT_CORRECTION_BONE, names.FRONT_RIGHT_ELBOW_JOINT_CORRECTION_BONE,
           "relink_constraints", True),
    (names.FRONT_LEFT_ELBOW_JOINT_CORRECTION_BONE, "parent_bone", names.LEFT_ELBOW_DEFORM_BONE1),
    (names.FRONT_RIGHT_ELBOW_JOINT_CORRECTION_BONE, "parent_bone", names.RIGHT_ELBOW_DEFORM_BONE1),
    *_both(names.MID_LEFT_ELBOW_JOINT_CORRECTION_BONE, names.MID_RIGHT_ELBOW_JOINT_CORRECTION_BONE,
           "relink_constraints", True),
    (names.MID_LEFT_ELBOW_JOINT_CORRECTION_BONE, "parent_bone", names.LEFT_ELBOW_DEFORM_BONE1),
    (names.MID_RIGHT_ELBOW_JOINT_CORRECTION_BONE, "parent_bone", names.RIGHT_ELBOW_DEFORM_BONE1),
)
PALMS = (
    *_both(names.LEFT_INDEX_FINGER_PALM_BONE, names.RIGHT_INDEX_FINGER_PALM_BONE, TYPE, "limbs.super_palm"),
    *_both(names.LEFT_INDEX_FINGER_PALM_BONE, names.RIGHT_INDEX_FINGER_PALM_BONE, "palm_both_sides", True),
    *_both(names.LEFT_INDEX_FINGER_PALM_BONE, names.RIGHT_INDEX_FINGER_PALM_BONE, "palm_rotation_axis", "X"),
    *_both(names.LEFT_INDEX_FINGER_PALM_BONE, names.RIGHT_INDEX_FINGER_PALM_BONE, "make_extra_control", True),
    *_both(names.LEFT_MIDDLE_FINGER_PALM_BONE, names.RIGHT_MIDDLE_FINGER_PALM_BONE, TYPE, ""),
    *_both(names.LEFT_RING_FINGER_PALM_BONE, names.RIGHT_RING_FINGER_PALM_BONE, TYPE, ""),
    *_both(names.LEFT_LITTLE_FINGER_PALM_BONE, names.RIGHT_LITTLE_FINGER_PALM_BONE, TYPE, ""),
)
FINGERS = tuple(row for first, second, third in (
    (names.LEFT_THUMB_BONE1, names.LEFT_THUMB_BONE2, names.LEFT_THUMB_BONE3),
    (names.RIGHT_THUMB_BONE1, names.RIGHT_THUMB_BONE2, names.RIGHT_THUMB_BONE3),
    (names.LEFT_INDEX_FINGER_BONE1, names.LEFT_INDEX_FINGER_BONE2, names.LEFT_INDEX_FINGER_BONE3),
    (names.RIGHT_INDEX_FINGER_BONE1, names.RIGHT_INDEX_FINGER_BONE2, names.RIGHT_INDEX_FINGER_BONE3),
    (names.LEFT_MIDDLE_FINGER_BONE1, names.LEFT_MIDDLE_FINGER_BONE2, names.LEFT_MIDDLE_FINGER_BONE3),
    (names.RIGHT_MIDDLE_FINGER_BONE1, names.RIGHT_MIDDLE_FINGER_BONE2, names.RIGHT_MIDDLE_FINGER_BONE3),
    (names.LEFT_RING_FINGER_BONE1, names.LEFT_RING_FINGER_BONE2, names.LEFT_RING_FINGER_BONE3),
    (names.RIGHT_RING_FINGER_BONE1, names.RIGHT_RING_FINGER_BONE2, names.RIGHT_RING_FINGER_BONE3),
    (names.LEFT_LITTLE_FINGER_BONE1, names.LEFT_LITTLE_FINGER_BONE2, names.LEFT_LITTLE_FINGER_BONE3),
    (names.RIGHT_LITTLE_FINGER_BONE1, names.RIGHT_LITTLE_FINGER_BONE2, names.RIGHT_LITTLE_FINGER_BONE3),
) for row in ((first, TYPE, "limbs.super_finger"), (first, "primary_rotation_axis", "-X"),
              (first, "make_extra_ik_control", True), (second, TYPE, ""), (third, TYPE, "")))
LEGS = (
    *_both(names.LEFT_LEG_BONE, names.RIGHT_LEG_BONE, TYPE, "limbs.leg"),
    *_both(names.LEFT_LEG_BONE, names.RIGHT_LEG_BONE, "extra_ik_toe", True),
    *_both(names.LEFT_LEG_BONE, names.RIGHT_LEG_BONE, "segments", 3),
    *_both(names.LEFT_LEG_BONE, names.RIGHT_LEG_BONE, "rotation_axis", "automatic"),
    *_both(names.LEFT_LEG_BONE, names.RIGHT_LEG_BONE, "limb_uniform_scale", True),
    *_both(names.LEFT_KNEE_BONE, names.RIGHT_KNEE_BONE, TYPE, ""),
    *_both(names.LEFT_ANKLE_BONE, names.RIGHT_ANKLE_BONE, TYPE, ""),
    *_both(names.LEFT_TOE_BONE, names.RIGHT_TOE_BONE, TYPE, ""),
    *_both(names.LEFT_HEEL_BONE, names.RIGHT_HEEL_BONE, TYPE, ""),
)
LEG_CORRECTIONS = (
    *_both(names.FRONT_LEFT_KNEE_JOINT_CORRECTION_BONE, names.FRONT_RIGHT_KNEE_JOINT_CORRECTION_BONE,
           "relink_constraints", True),
    (names.FRONT_LEFT_KNEE_JOINT_CORRECTION_BONE, "parent_bone", names.LEFT_LEG_DEFORM_BONE1),
    (names.FRONT_RIGHT_KNEE_JOINT_CORRECTION_BONE, "parent_bone", names.RIGHT_LEG_DEFORM_BONE1),
    *_both(names.MID_LEFT_KNEE_JOINT_CORRECTION_BONE, names.MID_RIGHT_KNEE_JOINT_CORRECTION_BONE, "relink_constraints",
           True),
    (names.MID_LEFT_KNEE_JOINT_CORRECTION_BONE, "parent_bone", names.LEFT_LEG_DEFORM_BONE1),
    (names.MID_RIGHT_KNEE_JOINT_CORRECTION_BONE, "parent_bone", names.RIGHT_LEG_DEFORM_BONE1),
)
# The breast and nipple control bones draw rigify.blend's face widget.
FACE_WIDGET_BONES = (names.LEFT_BREAST_BONE2, names.RIGHT_BREAST_BONE2, names.LEFT_BREAST_BONE3,
                     names.RIGHT_BREAST_BONE3)
FACE_WIDGET_NIPPLES = (names.LEFT_NIPPLE_BONE1, names.RIGHT_NIPPLE_BONE1, names.LEFT_NIPPLE_BONE2,
                       names.RIGHT_NIPPLE_BONE2)
# The bones above that the SFW Hook removes before this Hook runs (Bone Group nsfw, and its own list
# of nipple and breast bones): a Character without them gets a rig without their controls (D21).
# Any other bone missing is an error.
SFW_REMOVES = frozenset((
    names.CROTCH_BONE, names.ANUS_BONE,
    names.LEFT_BREAST_DEFORM_BONE2, names.RIGHT_BREAST_DEFORM_BONE2,
    names.LEFT_NIPPLE_BONE1, names.RIGHT_NIPPLE_BONE1, names.LEFT_NIPPLE_BONE2, names.RIGHT_NIPPLE_BONE2,
    names.LEFT_NIPPLE_DEFORM_BONE1, names.RIGHT_NIPPLE_DEFORM_BONE1,
    names.LEFT_NIPPLE_DEFORM_BONE2, names.RIGHT_NIPPLE_DEFORM_BONE2))


def rigify_types(build):
    metarig = build.metarig
    features = build.features
    for bone in metarig.pose.bones[:]:
        bone.rigify_type = "basic.raw_copy"
    rows = (EYES + (TONGUE if features.rigged_tongue else ()) + SPINE
            + (BETTER_PENETRATION if features.better_penetration else ()) + BREASTS
            + (NIPPLES if build.kk_extras else ()) + ARMS + (ARM_CORRECTIONS if build.kk_extras else ()) + PALMS
            + FINGERS + LEGS + (LEG_CORRECTIONS if build.kk_extras else ()))
    for bone, attribute, value in rows:
        if bone in SFW_REMOVES and bone not in metarig.pose.bones:
            continue
        pose_bone = metarig.pose.bones[bone]
        if attribute == TYPE:
            pose_bone.rigify_type = value
        else:
            setattr(pose_bone.rigify_parameters, attribute, value)
    face = build.widget(names.WIDGET_FACE)
    for bone in FACE_WIDGET_BONES + (FACE_WIDGET_NIPPLES if build.kk_extras else ()):
        if bone in SFW_REMOVES and bone not in metarig.pose.bones:
            continue
        metarig.pose.bones[bone].custom_shape = face
    for bone in (names.LEFT_BREAST_BONE2, names.RIGHT_BREAST_BONE2, names.LEFT_HEEL_BONE, names.RIGHT_HEEL_BONE):
        bone_collections.move(metarig, bone, names.ORIGINAL_FK_LAYER_INDEX)
