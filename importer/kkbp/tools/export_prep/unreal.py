"""Export prep for Unreal: the bones Unreal's Mannequin retargeting recognises get its names, and the
legs face one way so its IK works."""

from __future__ import annotations

from mathutils import Vector

from ...editing import editing
from . import common

# Bone Role -> the Mannequin's bone name.
MANNEQUIN = {
    "hips": "pelvis", "spine": "spine_01", "chest": "spine_02", "upper_chest": "spine_03", "neck": "neck",
    "head": "head",
    **{f"{side}_{part}": f"{name}_{s}" for side, s in (("left", "l"), ("right", "r")) for part, name in (
        ("shoulder", "clavicle"), ("upper_arm", "upperarm"), ("lower_arm", "lowerarm"), ("hand", "hand"),
        ("upper_leg", "thigh"), ("lower_leg", "calf"), ("toes", "ball"))},
}
# The legacy prep made the lower shin the Mannequin's foot; no Bone Role marks it.
FEET = {"cf_j_leg03_L": "foot_l", "cf_j_leg03_R": "foot_r"}


def prepare(ch, skeleton, log):
    armature = ch.armature
    by_role = common.roles(skeleton)
    names = common.readable_names(armature, skeleton)
    names.update({by_role[r]: n for r, n in MANNEQUIN.items() if r in by_role})
    names.update({old: new for old, new in FEET.items() if old in armature.data.bones})
    common.rename(armature, names)
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        for s in "lr":
            calf, ball = bones.get(f"calf_{s}"), bones.get(f"ball_{s}")
            if calf is not None:
                calf.tail.z = calf.head.z + 0.1
                calf.head.y += 0.01
            if ball is not None:
                ball.tail = ball.head + Vector((0.0, -0.05, 0.0))
