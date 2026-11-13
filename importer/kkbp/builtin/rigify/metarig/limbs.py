"""The limbs: the arms', legs' and feet's bones placed from the joint-correction bones and the meshes,
the heels, and with the joint-correction bones (KK and KKS, ADR 0022) the palms and fingers. In Edit
Mode.

Each side is described by a Limb of names. The right side mirrors the left along x; where a value
isn't a mirror (the thumbs' rolls, the elbow joint-correction rolls) both are written out.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from math import radians

from .. import bones, meshes, names
from . import accessories


@dataclass(frozen=True)
class Limb:
    left: bool
    shoulder_correction: str
    elbow_correction_mid: str
    elbow_correction_back: str
    elbow_correction_front: str
    shoulder_deform: str
    arm: str
    elbow: str
    wrist: str
    wrist_deform: str
    toe: str
    toe_deform: str
    ankle: str
    ankle_deform: str
    knee_correction_mid: str
    knee_correction_back: str
    leg: str
    leg_deform3: str
    heel_original: str
    heel: str


LEFT = Limb(True, names.LEFT_SHOULDER_JOINT_CORRECTION_BONE, names.MID_LEFT_ELBOW_JOINT_CORRECTION_BONE,
            names.BACK_LEFT_ELBOW_JOINT_CORRECTION_BONE, names.FRONT_LEFT_ELBOW_JOINT_CORRECTION_BONE,
            names.LEFT_SHOULDER_DEFORM_BONE, names.LEFT_ARM_BONE, names.LEFT_ELBOW_BONE, names.LEFT_WRIST_BONE,
            names.LEFT_WRIST_DEFORM_BONE, names.LEFT_TOE_BONE, names.LEFT_TOE_DEFORM_BONE, names.LEFT_ANKLE_BONE,
            names.LEFT_ANKLE_DEFORM_BONE, names.MID_LEFT_KNEE_JOINT_CORRECTION_BONE,
            names.BACK_LEFT_KNEE_JOINT_CORRECTION_BONE, names.LEFT_LEG_BONE, names.ORIGINAL_LEFT_LEG_DEFORM_BONE3,
            names.ORIGINAL_LEFT_HEEL_BONE, names.LEFT_HEEL_BONE)
RIGHT = Limb(False, names.RIGHT_SHOULDER_JOINT_CORRECTION_BONE, names.MID_RIGHT_ELBOW_JOINT_CORRECTION_BONE,
             names.BACK_RIGHT_ELBOW_JOINT_CORRECTION_BONE, names.FRONT_RIGHT_ELBOW_JOINT_CORRECTION_BONE,
             names.RIGHT_SHOULDER_DEFORM_BONE, names.RIGHT_ARM_BONE, names.RIGHT_ELBOW_BONE, names.RIGHT_WRIST_BONE,
             names.RIGHT_WRIST_DEFORM_BONE, names.RIGHT_TOE_BONE, names.RIGHT_TOE_DEFORM_BONE, names.RIGHT_ANKLE_BONE,
             names.RIGHT_ANKLE_DEFORM_BONE, names.MID_RIGHT_KNEE_JOINT_CORRECTION_BONE,
             names.BACK_RIGHT_KNEE_JOINT_CORRECTION_BONE, names.RIGHT_LEG_BONE, names.ORIGINAL_RIGHT_LEG_DEFORM_BONE3,
             names.ORIGINAL_RIGHT_HEEL_BONE, names.RIGHT_HEEL_BONE)
SIDES = (LEFT, RIGHT)


@dataclass(frozen=True)
class Finger:
    """One finger of one side. `palm` is its palm bone (the index finger's for a thumb); `rolls` its
    three bones' rolls in degrees."""
    palm: str
    bones: tuple
    deforms: tuple
    palm_deform: str
    rolls: tuple
    middle: bool = False
    thumb: bool = False


def _finger(side, finger, rolls, **kw):
    s = "LEFT" if side is LEFT else "RIGHT"
    n = lambda suffix: getattr(names, f"{s}_{finger}_{suffix}")  # noqa: E731
    palm_finger = "INDEX_FINGER" if finger == "THUMB" else finger
    return Finger(palm=getattr(names, f"{s}_{palm_finger}_PALM_BONE"),
                  bones=(n("BONE1"), n("BONE2"), n("BONE3")),
                  deforms=(n("DEFORM_BONE1"), n("DEFORM_BONE2"), n("DEFORM_BONE3")),
                  palm_deform=None if finger == "THUMB" else getattr(names, f"{s}_{finger}_PALM_DEFORM_BONE"),
                  rolls=rolls, **kw)


# In the order they are made: each finger, left then right.
FINGERS = (
    (_finger(LEFT, "INDEX_FINGER", (0, 5, 10)), _finger(RIGHT, "INDEX_FINGER", (0, -5, -10))),
    (_finger(LEFT, "MIDDLE_FINGER", (-10, -2, 6), middle=True), _finger(RIGHT, "MIDDLE_FINGER", (10, 2, -6), middle=True)),
    (_finger(LEFT, "RING_FINGER", (-15, -10, -5)), _finger(RIGHT, "RING_FINGER", (15, 10, 5))),
    (_finger(LEFT, "LITTLE_FINGER", (-20, -18, -16)), _finger(RIGHT, "LITTLE_FINGER", (20, 18, 16))),
    (_finger(LEFT, "THUMB", (-257, -260, -263), thumb=True), _finger(RIGHT, "THUMB", (-103, -106, -109), thumb=True)),
)


def _along(low, high, factor):
    return low + math.dist([low], [high]) * factor


def _back(low, high, factor):
    """`_along` from the other end, for the right side's mirror of a left-side x."""
    return high - math.dist([low], [high]) * factor


def limbs(build):
    metarig, edit = build.metarig, build.metarig.data.edit_bones
    if build.kk_extras:
        for side in SIDES:
            _arm(build, side)
    for side in SIDES:
        edit[side.toe].tail.z = edit[side.toe].head.z
    for side in SIDES:
        edit[side.toe].tail.y = meshes.group_bounds(build.body, side.toe_deform).min_y
    ankles = {side: meshes.group_bounds(build.body, side.ankle_deform) for side in SIDES}
    if build.kk_extras:
        for side in SIDES:
            mid, back = edit[side.knee_correction_mid], edit[side.knee_correction_back]
            edit[side.leg].head.y = _along(mid.head.y, back.head.y, 0.33)
    for side in SIDES:
        _heel_and_ankle(metarig, side, ankles[side])
    if build.kk_extras:
        _palms_and_fingers(build)


def _arm(build, side):
    """The elbow between its joint-correction bones, the shoulder bones along the arm, and the wrist
    just short of the elbow's back correction, pointing across the hand."""
    edit = build.metarig.data.edit_bones
    mid, back, front = edit[side.elbow_correction_mid], edit[side.elbow_correction_back], edit[side.elbow_correction_front]
    arm, elbow = edit[side.arm], edit[side.elbow]
    elbow.head.y = _along(mid.head.y, front.head.y, 0.33)
    elbow.roll = radians(0)
    if side.left:  # legacy turned only the left elbow's front and back correction bones
        front.roll = radians(180)
        back.roll = radians(180)
    for name in (side.shoulder_correction, side.shoulder_deform):
        edit[name].tail = arm.tail
        edit[name].roll = radians(90 if side.left else -90)
    wrist = edit[side.wrist]
    wrist.head.y = mid.head.y - math.dist([mid.head.y], [back.head.y]) * 0.15
    if wrist.tail.z != wrist.head.z:
        wrist.tail.y = wrist.head.y
        wrist.tail.z = wrist.head.z
        b = meshes.group_bounds(build.body, side.wrist_deform)
        wrist.tail.x = (_along if side.left else _back)(b.min_x, b.max_x, 0.66)


def _heel_and_ankle(metarig, side, ankle_bounds):
    """A heel bone across the bottom of the ankle's vertices, and the ankle's head 70% of the way up
    to the shin's lowest deform bone."""
    edit = metarig.data.edit_bones
    heel = bones.copy_bone(metarig, side.heel_original, side.heel)
    b = ankle_bounds
    heel.head.x, heel.tail.x = (b.min_x, b.max_x) if side.left else (b.max_x, b.min_x)
    heel.head.y = heel.tail.y = b.max_y
    heel.head.z = heel.tail.z = b.min_z
    heel.parent = edit[side.ankle]
    ankle, shin = edit[side.ankle], edit[side.leg_deform3]
    ankle.head.z = _along(ankle.tail.z, shin.head.z, 0.7)
    ankle.head.y = _along(shin.head.y, heel.head.y, 0.2)


def _palms_and_fingers(build):
    """Each finger's share of the wrist's vertices becomes its palm bone's group, then the fingers and
    palm bones are placed from their groups."""
    edit = build.metarig.data.edit_bones
    first_bones = {f.palm_deform: edit[f.bones[0]] for pair in FINGERS[:4] for f in pair}
    limits = {}
    for side in SIDES:
        wrist = edit[side.wrist]
        reach = math.dist([wrist.head.x], [wrist.tail.x]) * 0.85
        limits[side] = wrist.tail.x - reach if side.left else wrist.tail.x + reach
    for i, pair in enumerate(FINGERS[:4]):
        for side, finger in zip(SIDES, pair):
            lower = None if i == 3 else edit[FINGERS[i + 1][SIDES.index(side)].bones[0]].head.y
            _palm_group(build, side, finger.palm_deform, limits[side], first_bones[finger.palm_deform].head.y, lower)
    for pair in FINGERS:
        for side, finger in zip(SIDES, pair):
            _finger_bones(build, side, finger)


def _palm_group(build, side, palm_group, limit, mid_y, next_mid_y):
    """Moves the wrist group's vertices past `limit` (towards the fingers) that are nearer this
    finger's base than the next finger's into the palm group, with their weights."""
    for obj in build.meshes():
        wrist = obj.vertex_groups.get(side.wrist_deform)
        if wrist is None:
            continue
        b = meshes.group_bounds(obj, side.wrist_deform)
        palm = obj.vertex_groups.get(palm_group) or obj.vertex_groups.new(name=palm_group)
        for vertex in b.vertices:
            x, y = b.coordinates[vertex.index][0], b.coordinates[vertex.index][1]
            if (x > limit) if side.left else (x < limit):
                if next_mid_y is None or math.dist([y], [mid_y]) < math.dist([y], [next_mid_y]):
                    palm.add([vertex.index], wrist.weight(vertex.index), "REPLACE")
                    wrist.remove([vertex.index])


def _finger_bones(build, side, finger):
    metarig = build.metarig
    edit = metarig.data.edit_bones
    one, two, three = (edit[n] for n in finger.bones)
    b1, b2, b3 = (meshes.group_bounds(build.body, n) for n in finger.deforms)
    x = _along if side.left else _back
    if not finger.thumb:
        one.head.z = _along(b1.min_z, b1.max_z, 0.5 if finger.middle else 0.4)
        two.head.z = _along(b2.min_z, b2.max_z, 0.6)
        three.head.z = _along(b3.min_z, b3.max_z, 0.6)
        three.tail.x = x(b3.min_x, b3.max_x, 0.95)
        three.tail.y = three.head.y + (two.tail.y - two.head.y)
        three.tail.z = _along(b3.min_z, b3.max_z, 0.4)
        wrist = edit[side.wrist]
        palm = bones.copy_bone(metarig, finger.bones[0], finger.palm)
        palm.parent = edit[side.wrist]
        accessories.connect(metarig, finger.bones[0], finger.palm, False)
        palm.head.z = palm.tail.z
        reach = math.dist([wrist.tail.x], [wrist.head.x]) * 0.6
        palm.head.x = wrist.tail.x - reach if side.left else wrist.tail.x + reach
        palm.head.y = palm.head.y + (one.head.y - one.tail.y)
        palm.roll = radians(0)
    else:
        one.head.x = x(b1.min_x, b1.max_x, 0.2)
        two.head.x = x(b2.min_x, b2.max_x, 0.5)
        three.head.x = x(b3.min_x, b3.max_x, 0.4)
        three.tail.x = x(b3.min_x, b3.max_x, 0.95)
        one.head.y = _along(b1.min_y, b1.max_y, 0.45)
        one.head.z = _along(b1.min_z, b1.max_z, 0.35)
        two.head.y = _along(b2.min_y, b2.max_y, 0.35)
        two.head.z = _along(b2.min_z, b2.max_z, 0.3)
        three.head.y = _along(b3.min_y, b3.max_y, 0.4)
        three.head.z = _along(b3.min_z, b3.max_z, 0.45)
        three.tail.y = _along(b3.min_y, b3.max_y, 0.1)
        three.tail.z = _along(b3.min_z, b3.max_z, 0.25)
        one.parent = edit[finger.palm]
    for bone, roll in zip((one, two, three), finger.rolls):
        bone.roll = radians(roll)
