"""What the legacy armature Step did only when Rigify was on, before the Rigify scripts ran: the
joint-correction drivers (KK and KKS), the eye controller with its UV warps, and the "clarity"
renames the scripts expect (D23, D24, D25).

Bones with a Bone Role are found by it. The joint-correction bones and the pelvis have none, so their
names are written here: they are the bones the game's own correction components move, which the
legacy drivers copy.
"""

from __future__ import annotations

import math

from mathutils import Vector

from ...editing import editing

from ...bone_names import EXACT_NAMES, ROLE_NAMES  # noqa: E402  (D23)

# ADR 0022: every bone the legacy joint-correction drivers and constraints, and the scripts' KK-only
# parts, name. KK and KKS have all of them; SVS lacks seven.
JOINT_CORRECTION_BONES = tuple(
    [f"{b}_{s}" for s in "LR" for b in (
        "cf_d_shoulder02", "cf_d_arm01", "cf_d_arm02", "cf_d_arm03", "cf_d_forearm02", "cf_d_wrist", "cf_d_hand",
        "cf_s_elbo", "cf_s_elboback", "cf_s_forearm01", "cf_d_siri", "cf_d_thigh02", "cf_d_thigh03", "cf_s_leg",
        "cf_d_kneeF", "cf_s_kneeB", "cf_s_leg01", "cf_d_leg02", "cf_d_leg03")]
    + ["cf_s_waist02", "cf_j_waist02"])
# ADR 0017: the legacy joint corrections were written for these bones pointing straight up.
UPRIGHT_LENGTH = 0.1
WAIST = "cf_j_waist02"  # the lower waist, which no Bone Role marks

# The eye controller (legacy create_eye_controller_bone).
EYES_X = "Eyesx"
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


def run(ctx, kk: bool):
    ch, skeleton = ctx.character, ctx.bundle.skeleton
    armature = ch.armature
    role = {b.role: b.id for b in skeleton.bones if b.role}
    if kk:
        _reaim(armature)
        _joint_corrections(armature, role)
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


def _reaim(armature):
    """The bones the joint corrections move point straight up, roll 0, as the legacy armature had them."""
    owners = [n for n in JOINT_CORRECTION_BONES if n != WAIST]
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        for name in owners:
            bone = bones.get(name)
            if bone is not None:
                bone.tail = bone.head + Vector((0.0, 0.0, UPRIGHT_LENGTH))
                bone.roll = 0.0


def _joint_corrections(armature, role):
    """The legacy importer's copies of the game's joint corrections, as constraints and drivers
    (create_joint_drivers; most of them came from a file by johnbbob_la_petite on the Koikatsu Discord)."""
    def by_role(name):
        side = "left" if name.endswith("_L") else "right"
        for prefix, part in (("cf_j_arm00", "upper_arm"), ("cf_j_forearm01", "lower_arm"), ("cf_j_hand", "hand"),
                             ("cf_j_thigh00", "upper_leg"), ("cf_j_leg01", "lower_leg")):
            if name.startswith(prefix + "_"):
                return role[f"{side}_{part}"]
        return name

    pose = armature.pose.bones

    def set_copy(bone, target, influence, axis="all", mix="replace", space="LOCAL"):
        constraint = pose[bone].constraints.new("COPY_ROTATION")
        constraint.target = armature
        constraint.subtarget = by_role(target)
        constraint.influence = influence
        constraint.target_space = constraint.owner_space = space
        if axis == "X":
            constraint.use_y = constraint.use_z = False
        elif axis == "Y":
            constraint.use_x = constraint.use_z = False
        elif axis == "antiX":
            constraint.use_y = constraint.use_z = False
            constraint.invert_x = True
        elif axis == "Z":
            constraint.use_x = constraint.use_y = False
        if mix == "add":
            constraint.mix_mode = "ADD"

    for s in "LR":
        set_copy(f"cf_d_shoulder02_{s}", f"cf_j_arm00_{s}", 0.5)
        set_copy(f"cf_d_arm01_{s}", f"cf_j_arm00_{s}", 0.75, axis="X")
        set_copy(f"cf_d_arm02_{s}", f"cf_j_arm00_{s}", 0.5, axis="X")
        set_copy(f"cf_d_arm03_{s}", f"cf_j_arm00_{s}", 0.25, axis="X")
        set_copy(f"cf_d_forearm02_{s}", f"cf_j_hand_{s}", 0.33, axis="X")
        set_copy(f"cf_d_wrist_{s}", f"cf_j_hand_{s}", 0.33, axis="X")
        set_copy(f"cf_d_kneeF_{s}", f"cf_j_leg01_{s}", 0.5, axis="antiX", mix="add")
        set_copy(f"cf_d_siri_{s}", f"cf_j_thigh00_{s}", 0.33)
        set_copy(f"cf_d_thigh02_{s}", f"cf_j_thigh00_{s}", 0.25, axis="Y")
        set_copy(f"cf_d_thigh03_{s}", f"cf_j_thigh00_{s}", 0.25, axis="Y")
        set_copy(f"cf_d_leg02_{s}", f"cf_j_leg01_{s}", 0.33, axis="Y")
        set_copy(f"cf_d_leg03_{s}", f"cf_j_leg01_{s}", 0.66, axis="Y")
    # the waist moves a little when one leg turns, and with the lower waist
    set_copy("cf_s_waist02", "cf_j_thigh00_L", 0.1, mix="add")
    set_copy("cf_s_waist02", "cf_j_thigh00_R", 0.1, mix="add")
    set_copy("cf_s_waist02", WAIST, 0.5, axis="antiX")
    # this rotation helps when doing a split
    set_copy("cf_s_leg_L", "cf_j_thigh00_L", 0.9, axis="Z", mix="add")
    set_copy("cf_s_leg_R", "cf_j_thigh00_R", 0.9, axis="Z", mix="add")

    def set_driver(bone, path, index, target, transform, factor, kind="move"):
        """A driver on `bone`'s `path`[`index`] from `target`'s local `transform`, times the target's
        distance to its parent, so different bone sizes give the same result."""
        target = by_role(target)
        fcurve = pose[bone].driver_add(path, index)
        variable = fcurve.driver.variables.new()
        variable.name = "var"
        variable.type = "TRANSFORMS"
        t = variable.targets[0]
        t.id = armature
        t.bone_target = target
        t.transform_type = transform
        t.transform_space = "LOCAL_SPACE"
        t.rotation_mode = "QUATERNION" if kind in ("scale", "quat") else "AUTO"
        length = str(round((pose[target].head - pose[target].parent.head).length, 3))
        base = f"var*{length}*{factor}"
        fcurve.driver.expression = {
            "move": base, "quat": base, "rotation": base,
            "movePos": f"{base} if var > 0 else 0", "moveNeg": f"{base} if var < 0 else 0",
            "moveABS": f"abs({base})", "moveABSNeg": f"-abs({base})",
            "moveexp": f"var*{base}", "scale": f"1 + {base}",
        }[kind]

    # knees: in toward the body and down toward the foot, faster as they bend
    for s in "RL":
        set_driver(f"cf_s_kneeB_{s}", "location", 1, f"cf_j_leg01_{s}", "ROT_X", "-0.2", kind="moveexp")
        set_driver(f"cf_s_kneeB_{s}", "location", 2, f"cf_j_leg01_{s}", "ROT_X", "-0.08")
    # knee tips: up toward the waist and in toward the body
    for s in "RL":
        set_driver(f"cf_d_kneeF_{s}", "location", 1, f"cf_j_leg01_{s}", "ROT_X", "0.02")
        set_driver(f"cf_d_kneeF_{s}", "location", 2, f"cf_j_leg01_{s}", "ROT_X", "-0.04")
    # butt: slightly up to the spine and in to the waist
    for s in "RL":
        set_driver(f"cf_d_siri_{s}", "location", 1, f"cf_j_thigh00_{s}", "ROT_X", "0.02")
        set_driver(f"cf_d_siri_{s}", "location", 2, f"cf_j_thigh00_{s}", "ROT_X", "0.02")
    # hands: up to the head and in towards the elbow
    set_driver("cf_d_hand_R", "location", 0, "cf_j_hand_R", "ROT_Z", "-0.4", kind="moveNeg")
    set_driver("cf_d_hand_R", "location", 1, "cf_j_hand_R", "ROT_Z", "-0.4", kind="moveNeg")
    set_driver("cf_d_hand_L", "location", 0, "cf_j_hand_L", "ROT_Z", "-0.4", kind="movePos")
    set_driver("cf_d_hand_L", "location", 1, "cf_j_hand_L", "ROT_Z", "0.4", kind="movePos")
    # elbow back: out to the chest and into the shoulder; the elbow tip the other way
    set_driver("cf_s_elboback_R", "location", 0, "cf_j_forearm01_R", "ROT_X", "-0.7")
    set_driver("cf_s_elboback_R", "location", 2, "cf_j_forearm01_R", "ROT_X", "0.6")
    set_driver("cf_s_elbo_R", "location", 0, "cf_j_forearm01_R", "ROT_X", "0.025")
    set_driver("cf_s_elbo_R", "location", 2, "cf_j_forearm01_R", "ROT_X", "0.025")
    set_driver("cf_s_elboback_L", "location", 0, "cf_j_forearm01_L", "ROT_X", "-0.7")
    set_driver("cf_s_elboback_L", "location", 2, "cf_j_forearm01_L", "ROT_X", "-0.6")
    set_driver("cf_s_elbo_L", "location", 0, "cf_j_forearm01_L", "ROT_X", "0.025")
    set_driver("cf_s_elbo_L", "location", 2, "cf_j_forearm01_L", "ROT_X", "-0.025")
    # shoulders
    set_driver("cf_d_shoulder02_R", "location", 1, "cf_j_arm00_R", "ROT_Z", "-0.1", kind="moveNeg")
    set_driver("cf_d_shoulder02_R", "location", 0, "cf_j_arm00_R", "ROT_Y", "0.1", kind="moveABSNeg")
    set_driver("cf_d_shoulder02_R", "location", 2, "cf_j_arm00_R", "ROT_Y", "-0.1")
    set_driver("cf_d_shoulder02_L", "location", 1, "cf_j_arm00_L", "ROT_Z", "0.1", kind="movePos")
    set_driver("cf_d_shoulder02_L", "location", 0, "cf_j_arm00_L", "ROT_Y", "-0.1", kind="moveABS")
    set_driver("cf_d_shoulder02_L", "location", 2, "cf_j_arm00_L", "ROT_Y", "0.1")
    # legs: up to the head and slightly forwards or backwards
    for s in "RL":
        set_driver(f"cf_s_leg_{s}", "location", 1, f"cf_j_thigh00_{s}", "ROT_X", "1", kind="moveexp")
        set_driver(f"cf_s_leg_{s}", "location", 2, f"cf_j_thigh00_{s}", "ROT_X", "-1.5")
    # the waist moves out to the chest a little when the lower waist turns
    set_driver("cf_s_waist02", "location", 2, WAIST, "ROT_X", "0.2", kind="moveABS")


def _eye_controller(ctx, armature, role):
    """Eyesx and the Eye Controller that moves the eye textures through two UV warp modifiers on Body.
    The legacy importer made them from the head hit box, which is never exported (exporter-core.md),
    then moved them to the nose bridge pointing forward, as they end up here; without a nose bridge
    they stay a little in front of the eyes' midpoint."""
    ch, skeleton = ctx.character, ctx.bundle.skeleton
    left, right, head = role.get("left_eye"), role.get("right_eye"), role.get("head")
    if not (left and right and head):
        ctx.log.warning("The skeleton has no eye or head bones, so there is no eye controller")
        return
    eyebrow_tops = [b.id for b in skeleton.bones if b.group == "eyebrow"]
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        middle = (bones[left].head + bones[right].head) / 2
        top = max((bones[b].tail.z for b in eyebrow_tops if b in bones), default=middle.z + 0.03)
        eyes_x = bones.new(EYES_X)
        eyes_x.head = Vector((0.0, middle.y - EYE_CONTROLLER_FORWARD, middle.z))
        eyes_x.tail = Vector((0.0, eyes_x.head.y, max(top, middle.z + 0.01)))
        eyes_x.parent = bones[head]
        eyes_x.roll = -math.pi / 2
        controller = bones.new(EYE_CONTROLLER)
        controller.head = eyes_x.head / 2
        controller.tail = eyes_x.tail / 2
        controller.matrix = eyes_x.matrix
        controller.parent = bones[head]
        controller.roll = -math.pi / 2
        # Legacy then moved both to the nose bridge, pointing forward (its y * 1.5), with the roll
        # kept: the Eyes handle Rigify copies from the controller lies flat, as its widget needs.
        # By exact name: no Bone Role marks the nose bridge, and all three Games have it.
        nose = bones.get(NOSE_BRIDGE)
        for bone in (eyes_x, controller):
            if nose is not None:
                bone.head = Vector((bone.head.x, nose.head.y, nose.head.z))
                bone.tail = Vector((bone.head.x, nose.head.y * 1.5, nose.head.z))
            else:
                bone.tail = bone.head + Vector((0.0, -EYE_CONTROLLER_LENGTH, 0.0))
            bone.roll = -math.pi / 2
    armature.pose.bones[EYE_CONTROLLER].lock_location[1] = True
    armature.data.bones[EYES_X].hide = True
    _collection(armature, EYES_X, "Deform bones")
    _collection(armature, EYE_CONTROLLER, "Torso")
    body = ch.body
    if body is None:
        return
    for material_role, name in UV_WARPS.items():
        modifier = body.modifiers.new(name, "UV_WARP")
        modifier.axis_u, modifier.axis_v = "Z", "X"
        modifier.object_from = modifier.object_to = armature
        modifier.bone_from, modifier.bone_to = EYES_X, EYE_CONTROLLER
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
