"""Bone collections and the Rigify parameters that name them. In Object Mode: the bones' collections
are read and written on the armature's bones, which Edit Mode leaves stale.

A collection named here is made, at the top level, the first time a bone goes in it, so the order
of the calls is the order the Rigify panel draws them in.
"""

from __future__ import annotations


def _top_level(rig, name):
    collections = rig.data.collections
    return collections.get(name) or collections.new(name)


def move(rig, bone, collection):
    """Puts the bone `bone`, if the armature has it, in `collection` and in no other."""
    if rig.mode != "OBJECT":
        raise RuntimeError(f"{rig.name} must be in Object Mode to move bones between collections")
    data_bone = rig.data.bones.get(bone)
    if data_bone is None:
        return
    data_bone.collections.clear()
    _top_level(rig, collection).assign(data_bone)


def _reference(rig, bone, refs_name, collection):
    pose_bone = rig.pose.bones.get(bone)
    if pose_bone is None:
        return
    refs = getattr(pose_bone.rigify_parameters, refs_name)
    if not len(refs):
        refs.add()
    _top_level(rig, collection)
    refs[0].name = collection


def tweak(rig, bone, collection):
    """The collection Rigify puts the bone's tweak controls in."""
    _reference(rig, bone, "tweak_coll_refs", collection)


def fk(rig, bone, collection):
    """The collection Rigify puts the limb's FK controls in."""
    _reference(rig, bone, "fk_coll_refs", collection)


def lock(rig, bone, locked=True):
    """Locks (or unlocks) every channel of the pose bone."""
    pose_bone = rig.pose.bones[bone]
    pose_bone.lock_location = (locked, locked, locked)
    pose_bone.lock_rotation = (locked, locked, locked)
    pose_bone.lock_rotation_w = locked
    pose_bone.lock_scale = (locked, locked, locked)
