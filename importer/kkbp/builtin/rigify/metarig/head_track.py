"""Head tracking: the Head track target in front of the face, which the head turns to follow when its
"Track target" setting is on, with rotation limits and a choice of parent (head tweak, torso or
root). It was part of the legacy eye rig; the face rig (finish/face) replaced the rest of that.

The target sits where the legacy Eyes handle did: in front of the eyes' middle by 1.66 times their
front's distance from the head, at their height.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from mathutils import Vector

from .. import bones, constraints, drivers, meshes, names
from ..drivers import Variable

FORWARD = 1.66427  # the legacy Eyes handle's distance in front of the eyes, as a multiple of theirs
# Used when an eye's vertex group reaches no higher than 0 (cf_J_Eye07_s is the lower eyelid's).
EYE_FALLBACK = ("cf_J_Eye07_s_L", "cf_J_Eye07_s_R")
PROPERTIES = (
    ("01A) Limit rotation", "Limits the maximum reachable rotation of the head based on the settings below",
     0.0, 0.0, 1.0),
    ("01B) Min X rotation", "Minimum reachable X angle limit", -40.0, -180.0, 0.0),
    ("01C) Max X rotation", "Maximum reachable X angle limit", 50.0, 0.0, 180.0),
    ("01D) Min Y rotation", "Minimum reachable Y angle limit", -80.0, -180.0, 0.0),
    ("01E) Max Y rotation", "Maximum reachable Y angle limit", 80.0, 0.0, 180.0),
    ("01F) Min Z rotation", "Minimum reachable Z angle limit", -50.0, -180.0, 0.0),
    ("01G) Max Z rotation", "Maximum reachable Z angle limit", 50.0, 0.0, 180.0),
    ("02A) Track target", "Enables tracking of the head track target bone", 0.0, 0.0, 1.0),
    ("03A) Parent to head", "The bone will act as if it was parented to the head bone", 1, 0, 1),
    ("03B) Parent to torso", "The bone will act as if it was parented to the torso bone", 0, 0, 1),
    ("03C) Parent to root", "The bone will act as if it was parented to the root bone", 0, 0, 1),
)


@dataclass(frozen=True)
class Placeholders:
    """The bones the target's parent follows, named for the generated rig's controls (retargeted by
    finish/fixups)."""
    head_tweak: str
    torso: str
    root: str


def tracking_bones(build) -> Placeholders:
    """The target, its parent, the Head track bone that aims at it, and the placeholders. In Edit Mode."""
    metarig, body = build.metarig, build.body
    edit = metarig.data.edit_bones
    lb, rb = (meshes.group_bounds(body, g) for g in (names.LEFT_EYE_DEFORM_BONE, names.RIGHT_EYE_DEFORM_BONE))
    if not lb.max_z or not rb.max_z:
        lb, rb = (meshes.group_bounds(body, g) for g in EYE_FALLBACK)
    mid_z = statistics.mean([(lb.max_z + lb.min_z) / 2, (rb.max_z + rb.min_z) / 2])
    front = statistics.mean([lb.min_y, rb.min_y])
    head = edit[names.HEAD_BONE]

    target = bones.copy_bone(metarig, names.ORIGINAL_EYES_BONE, names.HEAD_TRACK_TARGET_BONE)
    target.translate(Vector((0.0, front * FORWARD, mid_z - target.head.z)))
    target.length = head.length
    parent = bones.copy_bone(metarig, names.HEAD_TRACK_TARGET_BONE, names.HEAD_TRACK_TARGET_PARENT_BONE)
    target.parent = parent
    parent.parent = None

    track = bones.copy_bone(metarig, names.ORIGINAL_EYES_BONE, names.HEAD_TRACK_BONE)
    eyes_y = statistics.mean([edit[names.LEFT_EYE_DEFORM_BONE].head.y, edit[names.RIGHT_EYE_DEFORM_BONE].head.y])
    length = edit[names.ORIGINAL_EYES_BONE].length
    track.head = (0.0, head.head.y, mid_z)
    track.tail = (0.0, eyes_y - length, mid_z)
    track.roll = 0.0
    track.parent = None
    made = [bones.new_bone(metarig, name + names.PLACEHOLDER_BONE_SUFFIX).name
            for name in (names.HEAD_TWEAK_BONE, names.TORSO_BONE, names.ROOT_BONE)]
    return Placeholders(*made)


def mechanism(build, placeholders: Placeholders):
    """The target's settings, the head's constraints and their drivers. In Object Mode."""
    rig = build.metarig
    target = names.HEAD_TRACK_TARGET_BONE
    paths = {name: drivers.bone_property(rig, target, name, description=description, default=default, min=low,
                                         max=high)
             for name, description, default, low, high in PROPERTIES}
    prop = lambda variable, key: Variable(variable, "SINGLE_PROP", rig, data_path=paths[key])  # noqa: E731

    rotation = constraints.transformation(
        rig, names.HEAD_BONE, names.HEAD_TRACK_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX + names.ROTATION_CONSTRAINT_SUFFIX,
        mix="REPLACE", space="LOCAL_WITH_PARENT", map_from="ROTATION",
        from_range=((math.radians(-180), math.radians(180)),) * 3, map_to="ROTATION",
        # x turns the other way
        to_range=((math.radians(180), math.radians(-180)), (math.radians(-180), math.radians(180)),
                  (math.radians(-180), math.radians(180))),
        from_rotation_mode="QUATERNION", to_euler_order="AUTO", map_to_from=("X", "Z", "Y"))
    limit = constraints.limit_rotation(
        rig, names.HEAD_BONE, name=names.LIMIT_ROTATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX, space="LOCAL",
        limits=((math.radians(-180), math.radians(180)),) * 3)
    parent = constraints.armature(
        rig, names.HEAD_TRACK_TARGET_PARENT_BONE, [placeholders.head_tweak, placeholders.torso, placeholders.root],
        name=names.ARMATURE_CONSTRAINT_BASE + names.PARENT_CONSTRAINT_SUFFIX)
    constraints.damped_track(rig, names.HEAD_TRACK_BONE, target,
                             name=names.DAMPED_TRACK_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX)

    drivers.add(rotation, "influence", type="AVERAGE", variables=[prop("track", "02A) Track target")])
    drivers.add(limit, "influence", type="AVERAGE", variables=[prop("limit", "01A) Limit rotation")])
    for (variable, key), channel in zip(
            (("minX", "01B) Min X rotation"), ("maxX", "01C) Max X rotation"), ("minY", "01D) Min Y rotation"),
             ("maxY", "01E) Max Y rotation"), ("minZ", "01F) Min Z rotation"), ("maxZ", "01G) Max Z rotation")),
            ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z")):
        drivers.add(limit, channel, type="SCRIPTED", variables=[prop(variable, key)], expression=f"radians({variable})")
    for i, (variable, key) in enumerate((("parentHead", "03A) Parent to head"), ("parentTorso", "03B) Parent to torso"),
                                         ("parentRoot", "03C) Parent to root"))):
        drivers.add(parent.targets[i], "weight", type="AVERAGE", variables=[prop(variable, key)])
