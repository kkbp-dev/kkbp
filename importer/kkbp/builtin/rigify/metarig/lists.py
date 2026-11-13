"""Which metarig bones the rig keeps, and how: the control bones Rigify makes controls for, the
useful bones it keeps as they are, and the deform bones the meshes are weighted to. Everything else
goes to Junk, which the rig drops. Also the skirt, accessory, MCH and face bones' Rigify types and
collections. In Object Mode."""

from __future__ import annotations

from dataclasses import dataclass

from .. import bone_collections, meshes, names


@dataclass
class BoneLists:
    """What the collection phase needs from this one."""
    deform: list
    useful: list
    eyes_secondary: list
    torso: list
    torso_tweak: list


TONGUE_PRIMARY = (names.RIGGED_TONGUE_BONE1, names.RIGGED_TONGUE_BONE2, names.RIGGED_TONGUE_BONE3,
                  names.RIGGED_TONGUE_BONE4, names.RIGGED_TONGUE_BONE5)
TONGUE_SECONDARY = (names.RIGGED_TONGUE_LEFT_BONE3, names.RIGGED_TONGUE_RIGHT_BONE3, names.RIGGED_TONGUE_LEFT_BONE4,
                    names.RIGGED_TONGUE_RIGHT_BONE4, names.RIGGED_TONGUE_LEFT_BONE5, names.RIGGED_TONGUE_RIGHT_BONE5)
BETTER_PENETRATION = (
    names.BETTER_PENETRATION_ROOT_CROTCH_BONE, names.BETTER_PENETRATION_FRONT_CROTCH_BONE,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE1, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE1,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE2, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE2,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE3, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE3,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE4, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE4,
    names.BETTER_PENETRATION_LEFT_CROTCH_BONE5, names.BETTER_PENETRATION_RIGHT_CROTCH_BONE5,
    names.BETTER_PENETRATION_BACK_CROTCH_BONE)
BREAST_HANDLES = (names.BREASTS_HANDLE_BONE, names.LEFT_BREAST_HANDLE_BONE, names.RIGHT_BREAST_HANDLE_BONE)
# The bones the Hook makes that move others but need no control.
USEFUL = (
    names.EYES_X_BONE, names.EYES_BONE, names.LEFT_EYE_BONE, names.RIGHT_EYE_BONE, names.EYES_TRACK_TARGET_PARENT_BONE,
    names.EYES_HANDLE_MARKER_BONE, names.LEFT_EYE_HANDLE_MARKER_BONE, names.RIGHT_EYE_HANDLE_MARKER_BONE,
    names.LEFT_EYE_HANDLE_MARKER_X_BONE, names.RIGHT_EYE_HANDLE_MARKER_X_BONE, names.LEFT_EYE_HANDLE_MARKER_Z_BONE,
    names.RIGHT_EYE_HANDLE_MARKER_Z_BONE, names.EYEBALLS_TRACK_BONE, names.LEFT_EYEBALL_TRACK_BONE,
    names.RIGHT_EYEBALL_TRACK_BONE, names.LEFT_EYEBALL_TRACK_CORRECTION_BONE, names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE,
    names.LEFT_HEAD_MARKER_X_BONE, names.RIGHT_HEAD_MARKER_X_BONE, names.LEFT_HEAD_MARKER_Z_BONE,
    names.RIGHT_HEAD_MARKER_Z_BONE, names.HEAD_TRACK_BONE, names.HEAD_TRACK_TARGET_PARENT_BONE)
FACE = (names.ORIGINAL_UPPER_FACE_LAYER_INDEX, names.ORIGINAL_LOWER_FACE_LAYER_INDEX)
HAIR_MCH = names.HAIR_LAYER + names.MCH_LAYER_SUFFIX
SKIRT_DETAIL = names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX


def _add(names_list, name):
    if name not in names_list:
        names_list.append(name)


def bone_lists(build, found) -> BoneLists:
    metarig = build.metarig
    features = build.features
    torso = [n for n in names.TORSO_LAYER_BONE_NAMES if not (features.male and n in BREAST_HANDLES)]
    eyes_primary = [n for n in names.EYES_PRIMARY_LAYER_BONE_NAMES
                    if features.rigged_tongue or n not in TONGUE_PRIMARY]
    eyes_secondary = [n for n in names.EYES_SECONDARY_LAYER_BONE_NAMES
                      if features.rigged_tongue or n not in TONGUE_SECONDARY]
    torso_tweak = [n for n in names.TORSO_TWEAK_LAYER_BONE_NAMES
                   if features.better_penetration or n not in BETTER_PENETRATION]

    control = [*eyes_primary, *eyes_secondary, *torso, *torso_tweak, *names.LEFT_ARM_IK_LAYER_BONE_NAMES,
               *names.RIGHT_ARM_IK_LAYER_BONE_NAMES, *names.FINGERS_LAYER_BONE_NAMES,
               *names.LEFT_LEG_IK_LAYER_BONE_NAMES, *names.RIGHT_LEG_IK_LAYER_BONE_NAMES]
    for bone in metarig.data.bones:
        if any(bone.collections.get(c) for c in FACE) and bone.name != names.ORIGINAL_ROOT_UPPER_BONE:
            _add(control, bone.name)
    useful = [build.metarig_id_bone, *USEFUL, *control]
    deform = meshes.weighted_bones(metarig, build.meshes())
    for name in deform:
        _add(useful, name)

    if features.skirt:
        _skirt(metarig, control, useful)
    _accessories(metarig, found, control, useful)
    _mch(metarig, found, control, useful)
    for name in found.face_mch:
        _add(control, name)
        _add(useful, name)
        metarig.pose.bones[name].rigify_parameters.optional_widget_type = "pivot"
    for bone in metarig.pose.bones:
        if metarig.data.bones[bone.name].collections.get(names.ORIGINAL_UPPER_FACE_LAYER_INDEX):
            bone.rigify_parameters.optional_widget_type = "circle"
    for bone in metarig.pose.bones:
        if metarig.data.bones[bone.name].collections.get(names.ORIGINAL_LOWER_FACE_LAYER_INDEX):
            bone.rigify_parameters.optional_widget_type = "sphere"
    metarig.pose.bones[names.PELVIS_BONE].rigify_parameters.optional_widget_type = "sphere"

    # Deform bones go in DEF, and are locked if Rigify also makes a control for them; useful bones
    # with no control go in MCH, locked. The list grows as it is walked: what a useful bone's parent,
    # constraints and drivers name is useful too.
    for name in useful:
        if name in deform:
            bone_collections.move(metarig, name, names.DEF_LAYER_INDEX)
            if name in control:
                bone_collections.lock(metarig, name)
        elif name not in control:
            bone_collections.move(metarig, name, names.MCH_LAYER_INDEX)
            bone_collections.lock(metarig, name)
        for related in _related(metarig, name):
            _add(useful, related)

    for bone in metarig.pose.bones:
        if bone.name not in useful:
            bone_collections.move(metarig, bone.name, names.JUNK_LAYER)
            continue
        if bone.rigify_type in ("basic.raw_copy", "basic.super_copy"):
            _relink(bone)
    return BoneLists(deform, useful, eyes_secondary, torso, torso_tweak)


def _related(rig, name):
    """The bones `name` depends on: its parent, its constraints' targets and its drivers' bones."""
    pose = rig.pose.bones
    if not pose.get(name):
        return []
    bone = pose[name]
    found = []
    if bone.parent and pose.get(bone.parent.name):
        _add(found, bone.parent.name)
    for constraint in bone.constraints:
        subtarget = getattr(constraint, "subtarget", None)  # Armature and Limit constraints have none
        if subtarget is not None and pose.get(subtarget):
            _add(found, subtarget)
    if rig.animation_data:
        for fcurve in rig.animation_data.drivers:
            if fcurve.data_path.startswith("pose.bones") and fcurve.data_path.split('"')[1] == name:
                for variable in fcurve.driver.variables:
                    for target in variable.targets:
                        if pose.get(target.bone_target):
                            _add(found, target.bone_target)
    return found


def _skirt(metarig, control, useful):
    """Each skirt chain's palm and bones; the third chain's palm makes the palm control for all."""
    for chain in range(8):
        palm = names.skirt_bone(True, chain)
        _add(control, palm)
        _add(useful, palm)
        bone_collections.move(metarig, palm, SKIRT_DETAIL)
        pose_bone = metarig.pose.bones[palm]
        if chain == 2:
            pose_bone.rigify_type = "limbs.super_palm"
            pose_bone.rigify_parameters.palm_both_sides = True
            pose_bone.rigify_parameters.palm_rotation_axis = "X"
            pose_bone.rigify_parameters.make_extra_control = True
            bone_collections.tweak(metarig, palm, SKIRT_DETAIL)
        else:
            pose_bone.rigify_type = ""
        for i in range(6):
            name = names.skirt_bone(False, chain, i)
            _add(control, name)
            _add(useful, name)
            bone_collections.move(metarig, name, names.SKIRT_LAYER)
            bone_collections.tweak(metarig, name, SKIRT_DETAIL)
            if i == 0:
                metarig.pose.bones[name].rigify_type = "limbs.super_finger"
                metarig.pose.bones[name].rigify_parameters.make_extra_ik_control = True
            else:
                metarig.pose.bones[name].rigify_type = ""


def _accessories(metarig, found, control, useful):
    """An accessory chain's first bone makes a finger control for the chain; a lone accessory bone a
    control of its own."""
    for name in found.bones:
        _add(useful, name)
        if name == names.ORIGINAL_ROOT_UPPER_BONE:
            continue
        _add(control, name)
        bone = metarig.pose.bones[name]
        bone_collections.move(metarig, name, HAIR_MCH)
        bone_collections.tweak(metarig, name, names.HAIR_LAYER)
        if name in found.connected_parents:
            bone.rigify_type = "limbs.super_finger"
            bone.rigify_parameters.make_extra_ik_control = True
            bone_collections.move(metarig, name, names.HAIR_LAYER)
            bone_collections.tweak(metarig, name, names.HAIR_LAYER + names.DETAIL_LAYER_SUFFIX)
        elif name in found.connected_children:
            bone.rigify_type = ""
        else:
            bone.rigify_type = "basic.super_copy"
            bone.rigify_parameters.make_control = True
            bone.rigify_parameters.make_widget = True
            bone.rigify_parameters.super_copy_widget_type = "limb"
            bone.rigify_parameters.make_deform = True


def _mch(metarig, found, control, useful):
    """The Junk bones above accessory chains. Sibling ones that each start a connected chain share a
    palm control, made on the two furthest apart; the others get a limb widget."""
    palms = []
    for name in found.mch:
        _add(control, name)
        _add(useful, name)
        bone = metarig.pose.bones[name]
        bone_collections.move(metarig, name, HAIR_MCH)
        if name in palms:
            continue
        if name in found.mch_connected_parents:
            siblings = []
            for other in found.mch_connected_parents:
                if other == name:
                    continue
                other_bone = metarig.pose.bones[other]
                if bone.parent == other_bone.parent:
                    palms.append(other_bone.name)
                    siblings.append(other_bone)
                    other_bone.rigify_type = ""
            if siblings:
                palms.append(bone.name)
                siblings.append(bone)
                bone.rigify_type = ""
                furthest = 0
                for a in siblings:
                    for b in siblings:
                        distance = (a.head - b.head).length
                        if distance > furthest:
                            bone = a
                            furthest = distance
                bone.rigify_type = "limbs.super_palm"
                bone.rigify_parameters.palm_both_sides = True
                bone.rigify_parameters.make_extra_control = True
                continue
            bone.rigify_parameters.optional_widget_type = "limb"
        else:
            bone.rigify_parameters.optional_widget_type = "limb"


def _relink(bone):
    """A copied bone's constraints that target a limb bone retarget its DEF- bone on the rig, which
    Rigify reads from the "@" suffix of the constraint's name."""
    for constraint in bone.constraints:
        for target in names.TARGETS_TO_CHANGE:
            # Armature and Limit constraints have no subtarget.
            if getattr(constraint, "subtarget", None) == target:
                bone.rigify_parameters.relink_constraints = True
                base = constraint.name[:constraint.name.index("@")] if "@" in constraint.name else constraint.name
                constraint.name = base + "@" + names.DEFORM_BONE_PREFIX + target
