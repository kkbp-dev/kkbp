"""The controls on the face: each sits on the skin where it acts and moves only the ways that mean
something. Blink (between the eyes) and each eye's lid close downwards; the middle brow control
raises and lowers both brows and each side's raises or lowers its own; the emote control (orange,
on the forehead) goes sad upwards and angry downwards; each mouth corner goes up, down or out; the
jaw opens the mouth, in the shape the board's mouth shape and open mood grids pick (board.py).

One side's brow and mouth corner controls drive halves of the Game's keys (split.py), since the
Games have no one-sided keys for them.
"""

from __future__ import annotations

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .....editing import editing
from ... import names
from . import shapes, split
from .terms import axis

HEAD = names.ORIGINAL_BONE_PREFIX + names.HEAD_BONE
TRAVEL = 0.008  # metres a control moves for full strength; the jaw goes twice as far
LIFT = 0.004  # how far in front of the skin a control sits
COLOR, EMOTE_COLOR = (0.35, 0.85, 1.0), (1.0, 0.55, 0.35)
# control: (y range, x range or None, widget)
CONTROLS = {
    "lids": ((-TRAVEL, 0), None, "down"),
    "lid L": ((-TRAVEL, 0), None, "down"),
    "lid R": ((-TRAVEL, 0), None, "down"),
    "brow mid": ((-TRAVEL, TRAVEL), None, "updown"),
    "brow L": ((-TRAVEL, TRAVEL), None, "updown"),
    "brow R": ((-TRAVEL, TRAVEL), None, "updown"),
    "emote": ((-TRAVEL, TRAVEL), None, "emote"),
    "jaw": ((-2 * TRAVEL, 0), None, "down"),
    "corner L": ((-TRAVEL, TRAVEL), (0, TRAVEL), "corner L"),
    "corner R": ((-TRAVEL, TRAVEL), (-TRAVEL, 0), "corner R"),
}
# (control, transform, sign, Face Key Role, half): moving the control fully that way gives the role's
# keys at their weights; `half` drives that side's half of the role's first key instead.
TERMS = (
    ("lids", "LOC_Y", -1, "blink", None),
    ("lid L", "LOC_Y", -1, "wink_l", None),
    ("lid R", "LOC_Y", -1, "wink_r", None),
    ("brow mid", "LOC_Y", 1, "brows_up", None),
    ("brow mid", "LOC_Y", -1, "brows_down", None),
    ("brow L", "LOC_Y", 1, "brows_up", "L"),
    ("brow L", "LOC_Y", -1, "brow_down_side", "L"),
    ("brow R", "LOC_Y", 1, "brows_up", "R"),
    ("brow R", "LOC_Y", -1, "brow_down_side", "R"),
    ("emote", "LOC_Y", 1, "emote_sad_brows", None),
    ("emote", "LOC_Y", 1, "emote_sad_eyes", None),
    ("emote", "LOC_Y", -1, "emote_angry_brows", None),
    ("emote", "LOC_Y", -1, "emote_angry_eyes", None),
    ("corner L", "LOC_Y", 1, "corner_up", "L"),
    ("corner L", "LOC_Y", -1, "corner_down", "L"),
    ("corner L", "LOC_X", 1, "corner_out", "L"),
    ("corner R", "LOC_Y", 1, "corner_up", "R"),
    ("corner R", "LOC_Y", -1, "corner_down", "R"),
    ("corner R", "LOC_X", -1, "corner_out", "R"),
)
HALF_BLEND = {"brows_up": 0.008, "brow_down_side": 0.008, "corner_up": 0.006, "corner_down": 0.006,
              "corner_out": 0.006}


def bone_name(control):
    return names.FACE_CONTROL_PREFIX + control


def places(build, eyes) -> dict:
    """Where each control goes: the game face bones' X and Z, pushed onto the skin from the front."""
    rig, body = build.rig, build.body
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(body.evaluated_get(depsgraph), depsgraph)
    bones = rig.data.bones
    org = names.ORIGINAL_BONE_PREFIX

    def bone(name):
        found = bones.get(name) or bones.get(org + name) or bones.get(names.DEFORM_BONE_PREFIX + name)
        return found.head_local if found is not None else None

    def on_skin(x, z, fallback_y):
        hit, *_ = bvh.ray_cast(Vector((x, -2.0, z)), Vector((0.0, 1.0, 0.0)))
        return Vector((x, (hit.y if hit else fallback_y) - LIFT, z))

    out = {}
    front = min(eyes["L"].front, eyes["R"].front)
    for side, sign in (("L", 1), ("R", -1)):
        brow = bone(names.LEFT_BROW_BONE if side == "L" else names.RIGHT_BROW_BONE)
        eye = eyes[side]
        if brow is None:
            brow = eye.centre + Vector((0.0, 0.0, eye.half_height * 2.2))
        out[f"brow {side}"] = on_skin(brow.x, brow.z + 0.004, brow.y)
        out[f"lid {side}"] = on_skin(eye.centre.x + sign * 0.004, eye.centre.z + eye.half_height * 0.95, eye.front)
        corner = bone(names.LEFT_MOUTH_CORNER_BONE if side == "L" else names.RIGHT_MOUTH_CORNER_BONE)
        if corner is not None:
            # clear of the lips, and of each other when both move in
            out[f"corner {side}"] = on_skin(corner.x + sign * 0.01, corner.z, corner.y)
    out["brow mid"] = on_skin(0.0, (out["brow L"].z + out["brow R"].z) / 2, out["brow L"].y)
    out["emote"] = out["brow mid"] + Vector((0.0, 0.0, 0.02))
    out["lids"] = on_skin(0.0, (eyes["L"].centre.z + eyes["R"].centre.z) / 2, front)
    chin = bone(names.CHIN_BONE)
    if chin is not None:
        out["jaw"] = on_skin(0.0, chin.z + 0.004, chin.y)
    return out


def build(build, keys, eyes, terms, log) -> dict:
    """The face controls and their terms; returns how a preset reaches a Face Key Role through them:
    {role: [(bone, location index, location at full strength)]}."""
    rig, body = build.rig, build.body
    where = places(build, eyes)
    halves = {}
    for role, blend in HALF_BLEND.items():
        if role in keys:
            made = split.halves(body, keys.first(role), blend)
            halves[role] = dict(zip("LR", made))
    wanted = {c for c, _, _, role, _ in TERMS if role in keys} | ({"jaw"} if "vowel_a" in keys else set())
    made = [c for c in CONTROLS if c in wanted and c in where]
    for c in wanted - set(made):
        log.warning(f"The face rig has no place for its {c} control")
    with editing(rig, "EDIT"):
        for c in made:
            shapes.new_bone(rig.data.edit_bones, bone_name(c), where[c], parent=HEAD, length=0.006)
    shapes.collection(rig, names.EMOTIONS_LAYER, row=10)
    for c in made:
        y_range, x_range, kind = CONTROLS[c]
        pose_bone = rig.pose.bones[bone_name(c)]
        shapes.put(rig, pose_bone.name, names.EMOTIONS_LAYER)
        shapes.lock(pose_bone, location=(x_range is None, False, True))
        shapes.limit_location(pose_bone, x=x_range, y=y_range)
        shapes.widget(build, rig, pose_bone.name, _shape(c, kind), color=EMOTE_COLOR if kind == "emote" else COLOR)

    reach, shared = {}, {}
    for c, transform, sign, role, half in TERMS:
        shared.setdefault((c, transform, sign), []).append(role)
    for c, transform, sign, role, half in TERMS:
        if c not in made or role not in keys:
            continue
        pairs = [(halves[role][half], 1.0)] if half else keys.get(role)
        index = 0 if transform == "LOC_X" else 1
        for name, weight in pairs:
            terms.add(name, axis(rig, bone_name(c), transform, TRAVEL, sign), weight)
        # a preset sets a role by the control that moves it alone (not by one side's half)
        if not half and len(shared[c, transform, sign]) == 1:
            reach.setdefault(role, []).append((bone_name(c), index, sign * TRAVEL))
    return reach


def _shape(control, kind):
    r = 0.005
    if kind == "emote":
        r = 0.0065
        return shapes.combine(shapes.diamond(r), shapes.arrows(r * 0.45, r * 1.3))
    if kind == "down":
        r = 0.007 if control == "jaw" else 0.005
        return shapes.combine(shapes.circle(r, 16), shapes.arrows(r * 0.45, r * 1.35, up=False))
    if kind.startswith("corner"):
        r = 0.004
        side = 1 if kind.endswith("L") else -1
        return shapes.combine(shapes.circle(r, 16), shapes.arrows(r * 0.4, r * 1.5, side=side))
    return shapes.combine(shapes.circle(r, 16), shapes.arrows(r * 0.45, r * 1.35))
