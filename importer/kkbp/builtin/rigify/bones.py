"""Bone helpers for the Rigify Hook. The edit-bone ones need the armature in Edit Mode."""

from __future__ import annotations

import random
import string

from ...character import OUTFIT


def random_id() -> str:
    """16 random letters and digits, for the metarig's id bone."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))


def new_bone(rig, name):
    """A new edit bone one unit long (a bone whose head and tail are the same is dropped)."""
    bone = rig.data.edit_bones.new(name)
    bone.head = (0, 1, 1)
    bone.tail = (0, 1, 2)
    return bone


def delete_bone(rig, name):
    """Deletes the edit bone `name`, after its constraints and the drivers on its pose bone.

    Both loops remove from the collection they walk, which skips every second item, as the legacy
    helper did; the constraints go with the bone anyway, and the drivers it skips stay behind."""
    bone = rig.data.edit_bones.get(name)
    pose_bone = rig.pose.bones[name]
    for constraint in pose_bone.constraints:
        pose_bone.constraints.remove(constraint)
    if rig.animation_data:
        for fcurve in rig.animation_data.drivers:
            if fcurve.data_path.startswith("pose.bones") and fcurve.data_path.split('"')[1] == name:
                rig.animation_data.drivers.remove(fcurve)
    rig.data.edit_bones.remove(bone)


def copy_bone(rig, source, name):
    """A new edit bone `name` where `source` is, with its roll and parent, replacing any bone of
    that name."""
    if rig.data.edit_bones.get(name) is not None:
        delete_bone(rig, name)
    bone = rig.data.edit_bones.new(name)
    original = rig.data.edit_bones.get(source)
    bone.tail = original.tail
    bone.head = original.head
    bone.roll = original.roll
    bone.parent = original.parent
    return bone


def outfit_of(idblock):
    """The Outfit index of a Part or bone (D29), or None."""
    value = idblock.get(OUTFIT)
    return value if isinstance(value, int) else None


def copy_tags(source, target):
    """The bundle Id and Outfit a generated rig bone takes from its ORG- bone."""
    for prop in ("id", OUTFIT):
        if prop in source:
            target[prop] = source[prop]
