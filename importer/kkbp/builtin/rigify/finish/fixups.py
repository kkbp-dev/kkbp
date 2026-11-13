"""What the generated rig needs after Rigify: the head's constraints in order, targets moved from
the metarig and its placeholders to the rig, which bones deform, the root's colour, the visible
collections, the bundle tags on the bones Rigify made, and IK stretch off. In Object Mode, except
`edit_bones`."""

from __future__ import annotations

import math

from .. import bone_collections, constraints, drivers, names
from ..bones import copy_tags, delete_bone, outfit_of

ROOT_COLOURS = {"normal": (0.956863, 0.788235, 0.047059), "select": (0.313989, 0.783538, 1.000000),
                "active": (0.552011, 1.000000, 1.000000)}
VISIBLE = ("Torso", "Arm.L IK", "Arm.R IK", "Leg.L IK", "Leg.R IK", "Root")
# The bones Rigify makes from an ORG- bone, which take its bundle Id and Outfit.
MADE_FROM = ("{}", "DEF-{}", "{}_ik", "{}_ik.parent", "{}_master", "MCH-{}", "MCH-{}_drv")
IK_PARENTS = ("Left arm_parent", "Left leg_parent", "Right arm_parent", "Right leg_parent")
# The tongue's tip chain, which the rig shows with the eyes; its side bones go with the face MCH.
TONGUE_SHOWN = ("cf_j_tang_02_master", "cf_j_tang_02", "cf_j_tang_01")
TONGUE_SIDES = ("cf_j_tang_R_03", "cf_j_tang_R_04", "cf_j_tang_R_05", "cf_j_tang_L_03", "cf_j_tang_L_04", "cf_j_tang_L_05")
HEAD_ROTATION = names.TRANSFORMATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX + names.ROTATION_CONSTRAINT_SUFFIX
HEAD_LIMIT = names.LIMIT_ROTATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX


def display(build):
    build.rig.show_in_front = True
    build.rig.display_type = "TEXTURED"


def head_constraints(build):
    """The head's tracking constraints go last in its stack, and the head tweak control gets the same
    rotation limit, driven by the same settings."""
    rig = build.rig
    head = rig.pose.bones[names.ORIGINAL_BONE_PREFIX + names.HEAD_BONE]
    constraints.move(rig, head.name, HEAD_ROTATION, len(head.constraints) - 1)
    constraints.move(rig, head.name, HEAD_LIMIT, len(head.constraints) - 1)
    tweak_limit = constraints.limit_rotation(rig, names.HEAD_TWEAK_BONE, name=HEAD_LIMIT, space="LOCAL",
                                             limits=((math.radians(-180), math.radians(180)),) * 3)
    # A snapshot: the drivers added here are on the head tweak, not the head.
    for fcurve in list(rig.animation_data.drivers):
        path = fcurve.data_path
        if path.startswith("pose.bones") and path.split('"')[1] == head.name and path.split('"')[3] == HEAD_LIMIT:
            variable = fcurve.driver.variables[0]
            copy = drivers.Variable(variable.name, variable.type, rig, bone=variable.targets[0].bone_target,
                                    data_path=variable.targets[0].data_path)
            drivers.add(tweak_limit, path.rsplit(".", 1)[1], type=fcurve.driver.type, variables=[copy],
                        expression=fcurve.driver.expression)


def retarget(build):
    """What still points at the metarig or a placeholder points at the rig, and the joint
    corrections' location drivers read the limbs' DEF- bones instead of their ORG- ones."""
    rig, metarig = build.rig, build.metarig
    for pose_bone in rig.pose.bones:
        for constraint in pose_bone.constraints:
            if constraint.type == "ARMATURE":
                for target in constraint.targets:
                    if target.subtarget:
                        target.target = rig
                        target.subtarget = target.subtarget.removesuffix(names.PLACEHOLDER_BONE_SUFFIX)
    for fcurve in build.body.data.shape_keys.animation_data.drivers:
        if fcurve.data_path.startswith("key_blocks") and fcurve.data_path.split('"')[1] == names.EYELIDS_SHAPE_KEY_COPY:
            for variable in fcurve.driver.variables:
                for target in variable.targets:
                    if target.id == metarig:
                        target.id = rig
    for fcurve in rig.animation_data.drivers:
        path = fcurve.data_path
        if path.startswith("pose.bones") and path.split('"')[1] in names.BONES_WITH_DRIVERS and path.rsplit(".", 1)[1] == "location":
            for variable in fcurve.driver.variables:
                for target in variable.targets:
                    for limb in names.TARGETS_TO_CHANGE:
                        if target.bone_target == names.ORIGINAL_BONE_PREFIX + limb:
                            target.bone_target = names.DEFORM_BONE_PREFIX + limb


def edit_bones(build):
    """The Junk bones go; the deform, NSFW, face, eye and Charamaker bones deform and are unlocked;
    the tongue's bones go back to their collections; the tracking targets are free of the head. In
    Edit Mode."""
    rig = build.rig
    edit = rig.data.edit_bones
    collections = rig.data.collections
    # These loops walk the live list as the legacy script did, the first one while deleting from it.
    for bone in edit:
        if bone.collections.get(names.JUNK_LAYER):
            delete_bone(rig, bone.name)
            continue
        if (bone.collections.get(names.DEF_LAYER_INDEX) or bone.collections.get(names.NSFW_LAYER)
                or bone.name == names.WAIST_JOINT_CORRECTION_BONE):
            bone.use_deform = True
    for bone in edit:
        if bone.collections.get(names.RIGGED_TONGUE_LAYER) or bone.name in TONGUE_SHOWN:
            collections[names.EYES_LAYER].assign(bone)
    for bone in edit:
        if bone.collections.get(names.FACE_LAYER) or bone.collections.get(names.EYES_LAYER):
            bone.use_deform = True
            bone_collections.lock(rig, bone.name, False)
    for bone in edit:
        if bone.name in TONGUE_SIDES:
            collections[names.EYES_LAYER].unassign(bone)
            collections[names.FACE_LAYER + names.MCH_LAYER_SUFFIX].assign(bone)
    for bone in edit:
        if any(bone.collections.get(c) for c in (names.FACE_LAYER + names.MCH_LAYER_SUFFIX, names.NSFW_LAYER,
                                                 names.DEFORM_LAYER, names.CHARAMAKER_LAYER)):
            bone_collections.lock(rig, bone.name, False)
            bone.use_deform = True
    if edit.get(names.RIGHT_BUTTOCK_DEFORM_BONE):
        edit[names.RIGHT_BUTTOCK_DEFORM_BONE].use_deform = True
        edit[names.LEFT_BUTTOCK_DEFORM_BONE].use_deform = True
    edit[names.EYES_TRACK_TARGET_PARENT_BONE].parent = None
    edit[names.HEAD_TRACK_TARGET_PARENT_BONE].parent = None


def root_colour(build):
    """The root bone is yellow, on both its bone and its pose bone."""
    rig = build.rig
    rig.pose.bones[names.ROOT_BONE].color.palette = "CUSTOM"
    for owner in (rig.data.bones[names.ROOT_BONE], rig.pose.bones[names.ROOT_BONE]):
        for state, colour in ROOT_COLOURS.items():
            setattr(owner.color.custom, state, colour)


def visible_collections(build):
    for collection in build.rig.data.collections_all:
        collection.is_visible = False
    for name in VISIBLE:
        build.rig.data.collections_all[name].is_visible = True


def tags(build):
    """Each bone Rigify made from an ORG- bone takes its bundle Id and Outfit, and so does the tail
    bone (.001) Rigify sometimes adds under an MCH-..._drv bone."""
    bones = build.rig.data.bones
    for bone in bones:
        if (bone.get("id") or outfit_of(bone) is not None) and bone.name.startswith(names.ORIGINAL_BONE_PREFIX):
            base = bone.name[len(names.ORIGINAL_BONE_PREFIX):]
            for pattern in MADE_FROM:
                name = pattern.format(base)
                if made := bones.get(name):
                    copy_tags(bone, made)
                    if "MCH-" in name and "_drv" in name and made.children and made.children[0].children:
                        copy_tags(bone, made.children[0].children[0])


def ik_stretch_off(build):
    for name in IK_PARENTS:
        build.rig.pose.bones[name]["IK_Stretch"] = 0
