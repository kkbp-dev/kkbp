"""Bone chains: the accessory and hair chains, the MCH bones that only move other bones, the body's
own chains, the rigged tongue's side bones and the skirt. In Edit Mode."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mathutils import Vector

from .. import bones, meshes, names

ACCESSORY = names.ORIGINAL_ACCESSORY_LAYER_INDEX  # the Core Import's Hair/Accessories collection
MCH = names.ORIGINAL_MCH_LAYER_INDEX  # Junk: bones no mesh is weighted to (prepare.py)
FACE = (names.ORIGINAL_UPPER_FACE_LAYER_INDEX, names.ORIGINAL_LOWER_FACE_LAYER_INDEX)
# A bone closer than this to its only child isn't pointed at it: Blender drops a bone of no length.
MIN_LENGTH = 0.005

# (child, parent, connected): each child's parent ends where the child starts.
TONGUE_CHAIN = ((names.RIGGED_TONGUE_BONE5, names.RIGGED_TONGUE_BONE4, True),
                (names.RIGGED_TONGUE_BONE4, names.RIGGED_TONGUE_BONE3, True),
                (names.RIGGED_TONGUE_BONE3, names.RIGGED_TONGUE_BONE2, True),
                (names.RIGGED_TONGUE_BONE2, names.RIGGED_TONGUE_BONE1, False))
BODY_CHAINS = (
    (names.HEAD_BONE, names.NECK_BONE, True),
    (names.NECK_BONE, names.UPPER_CHEST_BONE, False),
    (names.UPPER_CHEST_BONE, names.CHEST_BONE, True),
    (names.CHEST_BONE, names.SPINE_BONE, True),
    (names.SPINE_BONE, names.HIPS_BONE, True),
    (names.LEFT_WRIST_BONE, names.LEFT_ELBOW_BONE, True),
    (names.RIGHT_WRIST_BONE, names.RIGHT_ELBOW_BONE, True),
    (names.LEFT_ELBOW_BONE, names.LEFT_ARM_BONE, True),
    (names.RIGHT_ELBOW_BONE, names.RIGHT_ARM_BONE, True),
    (names.LEFT_ARM_BONE, names.LEFT_SHOULDER_BONE, False),
    (names.RIGHT_ARM_BONE, names.RIGHT_SHOULDER_BONE, False),
    (names.LEFT_THUMB_BONE3, names.LEFT_THUMB_BONE2, True),
    (names.RIGHT_THUMB_BONE3, names.RIGHT_THUMB_BONE2, True),
    (names.LEFT_THUMB_BONE2, names.LEFT_THUMB_BONE1, True),
    (names.RIGHT_THUMB_BONE2, names.RIGHT_THUMB_BONE1, True),
    (names.LEFT_INDEX_FINGER_BONE3, names.LEFT_INDEX_FINGER_BONE2, True),
    (names.RIGHT_INDEX_FINGER_BONE3, names.RIGHT_INDEX_FINGER_BONE2, True),
    (names.LEFT_INDEX_FINGER_BONE2, names.LEFT_INDEX_FINGER_BONE1, True),
    (names.RIGHT_INDEX_FINGER_BONE2, names.RIGHT_INDEX_FINGER_BONE1, True),
    (names.LEFT_MIDDLE_FINGER_BONE3, names.LEFT_MIDDLE_FINGER_BONE2, True),
    (names.RIGHT_MIDDLE_FINGER_BONE3, names.RIGHT_MIDDLE_FINGER_BONE2, True),
    (names.LEFT_MIDDLE_FINGER_BONE2, names.LEFT_MIDDLE_FINGER_BONE1, True),
    (names.RIGHT_MIDDLE_FINGER_BONE2, names.RIGHT_MIDDLE_FINGER_BONE1, True),
    (names.LEFT_RING_FINGER_BONE3, names.LEFT_RING_FINGER_BONE2, True),
    (names.RIGHT_RING_FINGER_BONE3, names.RIGHT_RING_FINGER_BONE2, True),
    (names.LEFT_RING_FINGER_BONE2, names.LEFT_RING_FINGER_BONE1, True),
    (names.RIGHT_RING_FINGER_BONE2, names.RIGHT_RING_FINGER_BONE1, True),
    (names.LEFT_LITTLE_FINGER_BONE3, names.LEFT_LITTLE_FINGER_BONE2, True),
    (names.RIGHT_LITTLE_FINGER_BONE3, names.RIGHT_LITTLE_FINGER_BONE2, True),
    (names.LEFT_LITTLE_FINGER_BONE2, names.LEFT_LITTLE_FINGER_BONE1, True),
    (names.RIGHT_LITTLE_FINGER_BONE2, names.RIGHT_LITTLE_FINGER_BONE1, True),
    (names.LEFT_TOE_BONE, names.LEFT_ANKLE_BONE, True),
    (names.RIGHT_TOE_BONE, names.RIGHT_ANKLE_BONE, True),
    (names.LEFT_ANKLE_BONE, names.LEFT_KNEE_BONE, True),
    (names.RIGHT_ANKLE_BONE, names.RIGHT_KNEE_BONE, True),
    (names.LEFT_KNEE_BONE, names.LEFT_LEG_BONE, True),
    (names.RIGHT_KNEE_BONE, names.RIGHT_LEG_BONE, True),
)

# The tongue's side bones: (left, right, factor along x, along y, along z) of the left bone's
# vertex group. The right ones mirror the left's x: the right groups' weights don't match them.
TONGUE_SIDES = ((names.RIGGED_TONGUE_LEFT_BONE3, names.RIGGED_TONGUE_RIGHT_BONE3, 0.75, None, None),
                (names.RIGGED_TONGUE_LEFT_BONE4, names.RIGGED_TONGUE_RIGHT_BONE4, 0.65, 0.5, 0.5),
                (names.RIGGED_TONGUE_LEFT_BONE5, names.RIGGED_TONGUE_RIGHT_BONE5, 0.65, 0.2, 0.3))

# Where each skirt chain's palm bone points from its head, measured on the default skirt.
SKIRT_PALM_DIRECTIONS = (
    Vector((-0.0000, -0.0083, 0.0287)), Vector((-0.0057, -0.0080, 0.0294)), Vector((-0.0136, -0.0002, 0.0317)),
    Vector((-0.0094, 0.0151, 0.0360)), Vector((-0.0010, 0.0153, 0.0333)), Vector((0.0094, 0.0151, 0.0360)),
    Vector((0.0136, -0.0002, 0.0317)), Vector((0.0057, -0.0080, 0.0294)),
)
# The skirt moves this much of its distance from the body's axis inwards.
SKIRT_SHRINK = 0.1


@dataclass
class Accessories:
    """The bone lists the chain phase makes for the type and collection phases."""
    bones: list = field(default_factory=list)  # in the Hair/Accessories collection
    mch: list = field(default_factory=list)  # Junk bones above them that move them
    face_mch: list = field(default_factory=list)  # Junk bones above the face bones
    connected_children: list = field(default_factory=list)
    connected_parents: list = field(default_factory=list)
    mch_connected_parents: list = field(default_factory=list)


def _in(metarig, name, collection):
    return metarig.data.bones[name].collections.get(collection)


def chains(build) -> Accessories:
    """Points each accessory and Junk bone with one child at it, lists the bones the later phases
    rig, renames the accessory bones' vertex groups to their deform names, and connects the
    tongue's and the body's chains."""
    metarig = build.metarig
    edit = metarig.data.edit_bones
    _point_at_only_child(metarig)

    found = Accessories()
    for bone in edit:
        if any(_in(metarig, bone.name, c) for c in FACE):
            parent = bone.parent.name
            if (_in(metarig, parent, MCH) and parent not in found.face_mch
                    and not any(_in(metarig, parent, c) for c in FACE)):
                found.face_mch.append(parent)
        if _in(metarig, bone.name, ACCESSORY):
            found.bones.append(bone.name)
            parent = bone.parent.name
            # Listed once per accessory child, as legacy did; the later loops don't mind repeats.
            if _in(metarig, parent, MCH) and not _in(metarig, parent, ACCESSORY):
                found.mch.append(parent)
    _up_the_chain(metarig, found.face_mch, FACE)
    _up_the_chain(metarig, found.mch, (ACCESSORY,), excluded=found.face_mch)

    parts = build.meshes()
    for name in found.bones:
        meshes.rename_group(parts, name, names.DEFORM_BONE_PREFIX + name)
        bone = edit[name]
        if not bone.use_connect or bone.parent.name not in found.bones:
            if any(child.use_connect and child.name in found.bones for child in bone.children):
                found.connected_parents.append(name)
            if bone.use_connect and bone.parent.name in found.mch:
                found.mch_connected_parents.append(bone.parent.name)
        else:
            found.connected_children.append(name)
            if bone.parent.name in found.mch:
                found.mch_connected_parents.append(bone.parent.name)

    for child, parent, connected in (TONGUE_CHAIN if build.features.rigged_tongue else ()) + BODY_CHAINS:
        connect(metarig, child, parent, connected)
    return found


def _point_at_only_child(metarig):
    """An accessory or Junk bone with one child points at it, and joins it if its own parent has no
    other child (connecting them all would bend the hands and fingers)."""
    for bone in metarig.data.edit_bones:
        if len(bone.children) == 1 and (_in(metarig, bone.name, ACCESSORY) or _in(metarig, bone.name, MCH)):
            p1, p2 = bone.head, bone.children[0].head
            if ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2) ** (1 / 2) > MIN_LENGTH:
                bone.tail = bone.children[0].head
                if len(bone.parent.children) == 1:
                    bone.use_connect = True


def _up_the_chain(metarig, mch, excluded_collections, excluded=None):
    """Adds to `mch` each Junk parent of a bone in it, and theirs in turn (the list grows as it is
    walked), up to the body root, a bone of `excluded_collections` or one in `excluded`."""
    for name in mch:
        bone = metarig.data.edit_bones[name]
        if bone.name == "Center":  # the body root's D23 name (bone_names.py)
            continue
        parent = bone.parent.name
        if (_in(metarig, parent, MCH) and parent not in mch
                and not any(_in(metarig, parent, c) for c in excluded_collections)
                and (excluded is None or parent not in excluded)):
            mch.append(parent)


def connect(metarig, child, parent, connected):
    """`parent` ends where `child` starts and becomes its parent."""
    edit = metarig.data.edit_bones
    edit[parent].tail = edit[child].head
    edit[child].parent = edit[parent]
    edit[child].use_connect = connected


def tongue_side_bones(build):
    """The rigged tongue's side bones sit across its width at their vertex groups, from the left
    groups, and the tongue's tip ends at its vertices'."""
    if not build.features.rigged_tongue:
        return
    edit = build.metarig.data.edit_bones
    needed = (names.RIGGED_TONGUE_BONE2, names.RIGGED_TONGUE_BONE5) + tuple(n for s in TONGUE_SIDES for n in s[:2])
    groups = tuple(s[0] for s in TONGUE_SIDES)
    if not (all(b in edit for b in needed) and not any(meshes.is_group_empty(build.body, g) for g in groups)):
        build.log.info("The tongue lacks some side bones or their vertex groups, so its side bones keep their places")
        return
    length = edit[names.RIGGED_TONGUE_BONE2].length
    for left_name, right_name, along_x, along_y, along_z in TONGUE_SIDES:
        left, right = edit[left_name], edit[right_name]
        b = meshes.group_bounds(build.body, left_name)
        left.head.x = b.min_x + math.dist([b.min_x], [b.max_x]) * along_x
        left.tail.x = left.head.x
        right.head.x = -left.head.x
        right.tail.x = right.head.x
        if along_y:
            left.head.y = b.min_y + math.dist([b.min_y], [b.max_y]) * along_y
            left.tail.y = left.head.y
            right.head.y = left.head.y
            right.tail.y = right.head.y
        if along_z:
            left.head.z = b.min_z + math.dist([b.min_z], [b.max_z]) * along_z
            right.head.z = left.head.z
        left.length = length
        right.length = length
    tip = edit[names.RIGGED_TONGUE_BONE5]
    b = meshes.group_bounds(build.body, names.RIGGED_TONGUE_LEFT_BONE5)
    tip.tail.z = b.min_z + math.dist([b.min_z], [b.max_z]) * 0.17
    tip.tail.y = b.min_y


def skirt(build):
    """Each skirt chain's palm bone turns to point down the chain, the chain moves in towards the
    body, and each bone bends halfway towards the one above."""
    edit = build.metarig.data.edit_bones
    if not build.features.skirt or edit.get(names.SKIRT_PARENT_BONE_COPY):
        return
    bones.copy_bone(build.metarig, names.SKIRT_PARENT_BONE, names.SKIRT_PARENT_BONE_COPY)
    for chain in range(8):
        palm = edit[names.skirt_bone(True, chain)]
        first, fifth, last = (edit[names.skirt_bone(False, chain, i)] for i in (0, 4, 5))
        palm.tail = palm.head - SKIRT_PALM_DIRECTIONS[chain]
        palm.length = first.length / 2
        head = palm.head.copy()
        palm.head = palm.tail
        palm.tail = head
        last.tail = last.head - (fifth.head - fifth.tail)
        palm_length = palm.length
        _shrink(palm)
        lengths, directions = [], []
        for i in range(6):
            bone = edit[names.skirt_bone(False, chain, i)]
            lengths.append(bone.length)
            directions.append(bone.tail - bone.head)
            _shrink(bone)
        palm.length = palm_length
        previous = palm.tail - palm.head
        for i in range(6):
            bone = edit[names.skirt_bone(False, chain, i)]
            if i == 0:
                bone.tail = bone.head + previous * Vector((0.4, 0.4, 0.4)) + directions[i] * Vector((0.6, 0.6, 0.6))
            else:
                bone.tail = bone.head + previous * Vector((0.5, 0.5, 0.5)) + directions[i] * Vector((0, 0, 0.5))
            bone.length = lengths[i]
            previous = bone.tail - bone.head


def _shrink(bone):
    offset = Vector((bone.head.x * SKIRT_SHRINK, bone.head.y * SKIRT_SHRINK, 0))
    bone.head = bone.head - offset
    bone.tail = bone.tail - offset
