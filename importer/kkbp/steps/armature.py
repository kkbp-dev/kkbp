"""Armature Steps: one armature for every Pass, its bone tree, bone tails and roll, and its bone
collections. Bones are found by Bone Role and Bone Group, never by a Game's bone names.
"""

from __future__ import annotations

import math
from collections import defaultdict

import bpy
from mathutils import Quaternion, Vector

from ..editing import editing
from ..character import OUTFIT


def join_armatures(ctx):
    """Joins every Pass's armature onto the Body Pass's by bone Id (ADR 0006): the Outfit-owned bones
    are added with their rest pose and their Outfit (`kkbp_outfit`, D29), the Outfit meshes are moved
    onto the Body armature, and the other armatures go. The Body Pass has only the body skeleton, so
    every bone added here is Outfit-owned (ADR 0009)."""
    ch = ctx.character
    armatures = ch.parts("armature")
    body = next(a for a in armatures if OUTFIT not in a)
    others = [a for a in armatures if a != body]
    if not others:
        return
    have = set(body.data.bones.keys())
    wanted = []  # (name, head, tail, matrix, parent, properties) of every bone the body armature lacks
    for other in others:
        for bone in other.data.bones:
            if bone.name not in have:
                have.add(bone.name)
                wanted.append((bone.name, bone.head_local.copy(), bone.tail_local.copy(),
                               bone.matrix_local.copy(), bone.parent.name if bone.parent else None,
                               {**dict(bone.items()), OUTFIT: other[OUTFIT]}))
    with editing(body, "EDIT"):
        bones = body.data.edit_bones
        for name, head, tail, matrix, _, props in wanted:
            eb = bones.new(name)
            eb.head, eb.tail = head, tail
            eb.matrix = matrix
            eb.length = (tail - head).length
            for k, v in props.items():
                eb[k] = v
        for name, _, _, _, parent, _ in wanted:
            if parent is not None:
                bones[name].parent = bones[parent]
    for other in others:
        for obj in list(other.children):
            matrix = obj.matrix_world.copy()
            obj.parent = body
            obj.matrix_world = matrix
            for m in obj.modifiers:
                if m.type == "ARMATURE" and m.object == other:
                    m.object = body
        data = other.data
        bpy.data.objects.remove(other)
        if data.users == 0:
            bpy.data.armatures.remove(data)
    body.pop(OUTFIT, None)


def trim_skeleton(ctx):
    """Keeps the body skeleton under the `body_root` Bone Role and the bones that carry it, as the
    legacy importer did: `body_root` becomes the root, and the bones between it and the skeleton's
    root move under the IK helpers' parent. Other bones go unless something is weighted to them."""
    ch, skeleton = ctx.character, ctx.bundle.skeleton
    root = skeleton.by_role("body_root")
    if root is None:
        ctx.log.warning("The skeleton has no body_root bone, so it is kept whole")
        return
    parent_of = {b.id: b.parent for b in skeleton.bones}
    keep = _subtree(skeleton, root.id)
    carriers = []
    bone = parent_of.get(root.id)
    while bone is not None and parent_of.get(bone) is not None:
        carriers.append(bone)
        bone = parent_of[bone]
    keep |= set(carriers)
    ik = skeleton.by_role("left_hand_ik") or skeleton.by_role("right_hand_ik")
    ik_parent = ik.parent if ik is not None else None

    armature = ch.armature
    weighted = _weighted_bones(ch)
    doomed = [b.name for b in armature.data.bones if b.name not in keep]
    kept_weighted = [name for name in doomed if name in weighted]
    if kept_weighted:
        ctx.log.warning(f"Kept {len(kept_weighted)} bones outside the body skeleton that meshes are weighted to: "
                        f"{', '.join(sorted(kept_weighted)[:10])}")
    doomed = [name for name in doomed if name not in weighted]
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        bones[root.id].parent = None
        for name in carriers:
            if name in bones:
                bones[name].parent = bones.get(ik_parent) if ik_parent else None
        for name in doomed:
            bones.remove(bones[name])
    gone = set(doomed)
    for obj in [o for o in ch.parts() if o.type == "MESH"]:
        for group in [g for g in obj.vertex_groups if g.name in gone]:
            obj.vertex_groups.remove(group)


def set_bone_tails_and_roll(ctx):
    """Sets every bone's tail and roll from the Game Profile's rules (ADR 0017): upright bones point
    straight up with roll 0, chains point along themselves, and every other bone keeps the game's
    rotation, aimed along the game bone's local -Z with its local +Y as the bone's Z axis."""
    ch, skeleton, rules = ctx.character, ctx.bundle.skeleton, ctx.profile.bones
    world = _world_rotations(skeleton)
    under = {}
    for rule in rules.upright:
        for anchor in (rule.under, rule.outside):
            if anchor and anchor not in under:
                bone = skeleton.by_role(anchor)
                under[anchor] = _subtree(skeleton, bone.id) if bone else set()
    children = defaultdict(list)
    for b in skeleton.bones:
        children[b.parent].append(b.id)

    armature = ch.armature
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        connect = []
        for eb in bones:
            bone = skeleton.bone(eb.name)
            if bone is None:
                continue
            upright = _upright_length(rules, bone, under)
            if upright is not None:
                eb.tail = eb.head + Vector((0.0, 0.0, upright))
                eb.roll = 0.0
                continue
            rotation = world.get(bone.id)
            if rotation is not None:
                aim, up = _blender(rotation @ Vector((0.0, 0.0, -1.0))), _blender(rotation @ Vector((0.0, 1.0, 0.0)))
                eb.tail = eb.head + aim * rules.aim_length
                eb.align_roll(up)
            if bone.group in rules.chains:
                kids = [c for c in children[bone.id] if c in bones and skeleton.bone(c).group == bone.group]
                if len(kids) == 1:
                    eb.tail = bones[kids[0]].head
                    connect.append(kids[0])
                else:
                    eb.tail = eb.head - Vector((0.0, 0.0, rules.chains[bone.group]))
        for name in connect:
            bones[name].use_connect = True


def bend_limbs_for_ik(ctx):
    """Bends the knees, elbows and feet slightly and lines the hand IK bones up with the hands, as
    the legacy importer did so its IK and Rigify set-up bend the right way."""
    armature = ctx.character.armature
    skeleton = ctx.bundle.skeleton

    def bone(role):
        b = skeleton.by_role(role)
        return armature.data.edit_bones.get(b.id) if b else None

    with editing(armature, "EDIT"):
        for side in ("left", "right"):
            knee, foot, toes = bone(f"{side}_lower_leg"), bone(f"{side}_foot"), bone(f"{side}_toes")
            elbow, hand, hand_ik = bone(f"{side}_lower_arm"), bone(f"{side}_hand"), bone(f"{side}_hand_ik")
            if knee and foot:
                knee.tail.z = foot.head.z
                knee.roll = 0.0
                knee.head.y -= 0.01  # forward a little, or the IK may bend the knee backwards
            if elbow and hand:
                elbow.tail.x = hand.head.x
                elbow.tail.z = hand.head.z
                elbow.roll = -math.pi / 2
            if hand_ik and hand:
                hand_ik.tail = hand.tail
                hand_ik.tail.z += 0.01  # a little longer, so the hand and its IK bone can both be clicked
                hand_ik.head = hand.head
            if foot and toes:
                foot.tail.y = toes.head.y
                foot.tail.z = toes.head.z
                foot.roll = 0.0


def orient_fingers_and_legs(ctx):
    """KK's finger and leg bone directions, as the legacy importer set them for its KK Rigify rig:
    the thumbs turn in the hand's plane, the right fingers point down, the left fingers up, and the
    legs and feet straight up."""
    armature = ctx.character.armature
    skeleton = ctx.bundle.skeleton
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        for b in skeleton.bones:
            eb = bones.get(b.id)
            role = b.role or ""
            if eb is None or not role:
                continue
            side, _, part = role.partition("_")
            if "thumb" in part:
                offset = eb.tail - eb.head
                angle = -math.pi / 2
                eb.tail.x = eb.head.x + offset.x * math.cos(angle) - offset.y * math.sin(angle)
                eb.tail.y = eb.head.y + offset.x * math.sin(angle) + offset.y * math.cos(angle)
                eb.roll = 0.0
            elif any(f in part for f in ("index", "middle", "ring", "little")):
                eb.tail = eb.head + Vector((0.0, 0.0, 0.05 if side == "left" else -0.05))
            elif part in ("upper_leg", "lower_leg", "foot"):
                eb.tail = eb.head + Vector((0.0, 0.0, 0.1))


# Bone collections: the first rule that matches puts a bone in its collection. Roles first, then
# Bone Groups; a bone that matches nothing goes to Junk. The same for every Game.
_SIDES = (("left", "L"), ("right", "R"))
COLLECTIONS_BY_ROLE = {
    "Torso": {"hips", "spine", "chest", "upper_chest", "neck", "head", "left_shoulder", "right_shoulder",
              "left_breast", "right_breast"},
    **{f"Arm.{s} FK": {f"{side}_upper_arm", f"{side}_lower_arm", f"{side}_hand"} for side, s in _SIDES},
    **{f"Leg.{s} FK": {f"{side}_upper_leg", f"{side}_lower_leg", f"{side}_foot", f"{side}_toes"} for side, s in _SIDES},
    "Fingers": {f"{side}_{finger}_{joint}" for side, _ in _SIDES
                for finger in ("thumb", "index", "middle", "ring", "little")
                for joint in ("proximal", "intermediate", "distal")},
}
COLLECTIONS_BY_GROUP = {
    "skirt": "Skirt", "nsfw": "NSFW", "hair": "Hair/Accessories", "accessory": "Hair/Accessories",
    "face": "Face", "eye": "Face", "eyebrow": "Face", "mouth": "Face", "deform": "Deform bones",
    "breast": "Deform bones", "helper": "Junk",
}
TONGUE_COLLECTION = "Rigged tongue"  # the bones under the tongue_root Bone Role
OTHER_COLLECTION = "Junk"


def sort_bone_collections(ctx):
    """Puts every bone in one bone collection by its Bone Role and Bone Group."""
    armature, skeleton = ctx.character.armature, ctx.bundle.skeleton
    tongue_root = skeleton.by_role("tongue_root")
    tongue = _subtree(skeleton, tongue_root.id) if tongue_root else set()
    data = armature.data
    for c in list(data.collections_all):
        data.collections.remove(c)
    made = {}
    for bone in data.bones:
        b = skeleton.bone(bone.name)
        name = _collection_for(b, tongue)
        if name not in made:
            made[name] = data.collections.new(name)
        made[name].assign(bone)
    data.display_type = "STICK"


def _collection_for(bone, tongue):
    if bone is None:
        return OTHER_COLLECTION
    if bone.id in tongue:
        return TONGUE_COLLECTION
    for name, roles in COLLECTIONS_BY_ROLE.items():
        if bone.role in roles:
            return name
    return COLLECTIONS_BY_GROUP.get(bone.group, OTHER_COLLECTION)


# --- helpers ------------------------------------------------------------------------------

def _upright_length(rules, bone, under):
    for rule in rules.upright:
        if rule.roles:
            if bone.role in rule.roles:
                return rule.length
            continue
        if bone.role is not None or bone.group not in rule.groups:
            continue
        if rule.under and bone.id not in under[rule.under]:
            continue
        if rule.outside and bone.id in under[rule.outside]:
            continue
        return rule.length
    return None


def _world_rotations(skeleton):
    """Each bone's world rotation in glTF space, from skeleton.json's local rotations."""
    parent_of = {b.id: b for b in skeleton.bones}
    world = {}

    def rotation(bone_id):
        if bone_id in world:
            return world[bone_id]
        b = parent_of[bone_id]
        x, y, z, w = b.rotation
        local = Quaternion((w, x, y, z))
        result = local if b.parent is None or b.parent not in parent_of else rotation(b.parent) @ local
        world[bone_id] = result
        return result

    for b in skeleton.bones:
        rotation(b.id)
    return world


def _blender(v):
    """A glTF-space direction (+Y up) in Blender space (+Z up)."""
    return Vector((v.x, -v.z, v.y))


def _subtree(skeleton, root_id):
    children = defaultdict(list)
    for b in skeleton.bones:
        children[b.parent].append(b.id)
    found, todo = set(), [root_id]
    while todo:
        bone = todo.pop()
        found.add(bone)
        todo.extend(children[bone])
    return found


def _weighted_bones(ch):
    weighted = set()
    for obj in [o for o in ch.parts() if o.type == "MESH"]:
        names = {g.index: g.name for g in obj.vertex_groups}
        for v in obj.data.vertices:
            for g in v.groups:
                if g.weight > 0:
                    weighted.add(names[g.group])
    return weighted
