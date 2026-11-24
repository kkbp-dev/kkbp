"""What the legacy armature Step did only when Rigify was on, before the Rigify scripts ran: the
eye controller and the eye UV warps, and the "clarity" renames the scripts expect (D23, D24, D25).
The legacy joint-correction drivers are gone: the joint corrections Step copies the game's own, and
the Rigify Hook puts them back on the generated rig (ADR 0038).

Bones with a Bone Role are found by it. The joint-correction bones and the pelvis have none, so their
names are written here: they are the bones the game's own correction components move, which the
scripts' KK-only parts use.
"""

from __future__ import annotations

import math

from mathutils import Vector

from ...editing import editing

from ...bone_names import EXACT_NAMES, ROLE_NAMES  # noqa: E402  (D23)

# ADR 0022: every bone the legacy joint-correction drivers and constraints, and the scripts' KK-only
# parts, named. KK and KKS have all of them; SVS lacks seven. The drivers are gone (ADR 0038), but the
# KK-only parts still run on the same test.
JOINT_CORRECTION_BONES = tuple(
    [f"{b}_{s}" for s in "LR" for b in (
        "cf_d_shoulder02", "cf_d_arm01", "cf_d_arm02", "cf_d_arm03", "cf_d_forearm02", "cf_d_wrist", "cf_d_hand",
        "cf_s_elbo", "cf_s_elboback", "cf_s_forearm01", "cf_d_siri", "cf_d_thigh02", "cf_d_thigh03", "cf_s_leg",
        "cf_d_kneeF", "cf_s_kneeB", "cf_s_leg01", "cf_d_leg02", "cf_d_leg03")]
    + ["cf_s_waist02", "cf_j_waist02"])

# The eye controller (legacy create_eye_controller_bone).
EYE_CONTROLLER = "Eye Controller"
EYE_CONTROLLER_FORWARD = 0.05
EYE_GROUPS = {"eye_l": "Left Eye", "eye_r": "Right Eye"}
NOSE_BRIDGE = "cf_J_NoseBridge_rx"
EYE_CONTROLLER_LENGTH = 0.0344  # legacy's, from the nose bridge's y
UV_WARPS = {"eye_l": "Left Eye UV warp", "eye_r": "Right Eye UV warp"}
UV_MAP = "uv_main"


def kk_extras(skeleton) -> bool:
    """Whether the KK-only Rigify parts run (ADR 0022)."""
    names = {b.id for b in skeleton.bones}
    return all(name in names for name in JOINT_CORRECTION_BONES)


def run(ctx):
    ch, skeleton = ctx.character, ctx.bundle.skeleton
    armature = ch.armature
    role = {b.role: b.id for b in skeleton.bones if b.role}
    _face_mch(ctx, armature)
    _eye_groups(ctx)  # before the UV warps, which can only name vertex groups that exist
    _eye_controller(ctx, armature, role)
    _rename(armature, role)


FACE, FACE_MCH, JUNK, HAIR = "Face", "Face (MCH)", "Junk", "Hair/Accessories"


def _face_mch(ctx, armature):
    """The legacy armature sorted the face bones by two lists of KK names: the ones meshes are weighted
    to in "Face", the ones that only move those in "Face (MCH)", and the rest, such as accessory
    attachment points and camera targets, in "Junk", which the rig leaves out. D7 put them all in
    "Face"; here they are sorted again by the same meaning, from the weights."""
    face = armature.data.collections_all.get(FACE)
    if face is None:
        return
    weighted = set()
    for obj in [o for o in ctx.character.parts() if o.type == "MESH"]:
        names = {g.index: g.name for g in obj.vertex_groups}
        for v in obj.data.vertices:
            weighted.update(names[g.group] for g in v.groups if g.weight > 0)

    def moves_something(bone):
        return bone.name in weighted or any(moves_something(child) for child in bone.children)

    collections = armature.data.collections_all
    mch = collections.get(FACE_MCH) or armature.data.collections.new(FACE_MCH)
    junk = collections.get(JUNK) or armature.data.collections.new(JUNK)
    for bone in [b for b in face.bones if b.name not in weighted]:
        face.unassign(bone)
        (mch if moves_something(bone) else junk).assign(bone)
    # Likewise the hair and accessory bones (legacy relayer_accessory_bones): a bone stays in "Hair/
    # Accessories" if a mesh is weighted to it, or it is the parent or first child of one that is, so
    # a chain keeps its unweighted root, such as cf_J_hairF_s above cf_J_hairF_00. The rest, such as
    # ct_hairB, go to "Junk", where the scripts rig them as helpers.
    hair = collections.get(HAIR)
    keep = set()
    for bone in [b for b in (hair.bones if hair else ()) if b.name in weighted]:
        keep.add(bone.name)
        if bone.parent is not None:
            keep.add(bone.parent.name)
        if bone.children:
            keep.add(bone.children[0].name)
    for bone in [b for b in (hair.bones if hair else ()) if b.name not in keep]:
        hair.unassign(bone)
        junk.assign(bone)


def _eye_controller(ctx, armature, role):
    """The Eye Controller, a metarig-only bone at the nose bridge pointing forward (a little in front
    of the eyes' midpoint without a nose bridge): the head is told apart by it and the head track
    target is placed from it. And the two UV warp modifiers on Body that slide the eye textures; the
    face rig drives their offset and scale (finish/face). The legacy importer made the bone from the
    head hit box, which is never exported (exporter-core.md), then moved it to the nose bridge."""
    ch = ctx.character
    left, right, head = role.get("left_eye"), role.get("right_eye"), role.get("head")
    if not (left and right and head):
        ctx.log.warning("The skeleton has no eye or head bones, so there is no eye controller")
        return
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        middle = (bones[left].head + bones[right].head) / 2
        controller = bones.new(EYE_CONTROLLER)
        controller.parent = bones[head]
        # By exact name: no Bone Role marks the nose bridge, and all three Games have it.
        nose = bones.get(NOSE_BRIDGE)
        if nose is not None:
            controller.head = Vector((0.0, nose.head.y, nose.head.z))
            controller.tail = Vector((0.0, nose.head.y * 1.5, nose.head.z))
        else:
            controller.head = Vector((0.0, middle.y - EYE_CONTROLLER_FORWARD, middle.z))
            controller.tail = controller.head + Vector((0.0, -EYE_CONTROLLER_LENGTH, 0.0))
        controller.roll = -math.pi / 2
    armature.pose.bones[EYE_CONTROLLER].lock_location[1] = True
    _collection(armature, EYE_CONTROLLER, "Torso")
    body = ch.body
    if body is None:
        return
    for material_role, name in UV_WARPS.items():
        modifier = body.modifiers.new(name, "UV_WARP")
        modifier.axis_u, modifier.axis_v = "Z", "X"
        modifier.vertex_group = EYE_GROUPS[material_role]
        modifier.uv_layer = UV_MAP
        modifier.show_expanded = False
        # right after the armature modifier, where the legacy armature Step put it before any outline
        armature_at = next((i for i, m in enumerate(body.modifiers) if m.type == "ARMATURE"), -1)
        body.modifiers.move(len(body.modifiers) - 1, armature_at + 1 + list(UV_WARPS).index(material_role))


def _collection(armature, bone, name):
    collection = armature.data.collections_all.get(name) or armature.data.collections.new(name)
    b = armature.data.bones[bone]
    for c in list(b.collections):
        c.unassign(b)
    collection.assign(b)


def _rename(armature, role):
    """D23. Renaming a bone also renames its vertex groups and the constraints and drivers that name it."""
    renames = {role[r]: name for r, name in ROLE_NAMES.items() if r in role}
    renames.update({old: new for old, new in EXACT_NAMES.items() if old in armature.data.bones})
    taken = {b.name for b in armature.data.bones} - set(renames)
    for old, new in renames.items():
        bone = armature.data.bones.get(old)
        if bone is None:
            continue
        if new in taken:  # an accessory bone already has the name; it gives way, as in the legacy scripts
            armature.data.bones[new].name = new + " (renamed)"
        bone.name = new


def _eye_groups(ctx):
    """D25: the Left and Right Eye vertex groups, which the UV warps move, are every vertex of the
    faces with the eye_l and eye_r materials, at weight 1."""
    ch = ctx.character
    for obj in [o for o in ch.parts() if o.type == "MESH"]:
        for material_role, name in EYE_GROUPS.items():
            slots = {i for i, s in enumerate(obj.material_slots)
                     if s.material is not None and s.material.get("kkbp_role") == material_role}
            if not slots:
                continue
            verts = sorted({v for p in obj.data.polygons if p.material_index in slots for v in p.vertices})
            group = obj.vertex_groups.get(name) or obj.vertex_groups.new(name=name)
            group.remove(range(len(obj.data.vertices)))
            group.add(verts, 1.0, "REPLACE")
