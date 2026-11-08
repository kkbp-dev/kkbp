"""Export prep for VRM: the readable bone names, a hierarchy VRM's humanoid detection takes (the
pelvis as Hips over the spine and legs), and the waist and hand helpers merged."""

from __future__ import annotations

from ...editing import editing
from .. import merge_weights
from . import common

# No Bone Role marks these helpers, which VRM's humanoid detection trips over.
MERGED = ("cf_j_waist02", "cf_s_waist01", "cf_s_hand_L", "cf_s_hand_R")


def prepare(ch, skeleton, log, extra_merged=()):
    armature = ch.armature
    common.nudge_eyelines(ch)
    by_role = common.roles(skeleton)
    names = common.readable_names(armature, skeleton)
    common.rename(armature, names)
    name = {r: names.get(by_role[r], by_role[r]) for r in by_role}
    pelvis = names.get("cf_j_waist01", "cf_j_waist01")
    if pelvis in armature.data.bones and "hips" in name:
        parents = {pelvis: None, name.get("spine"): pelvis}
        parents.update({name[f"{s}_upper_leg"]: pelvis for s in ("left", "right") if f"{s}_upper_leg" in name})
        parents.update({name[f"{s}_foot"]: name[f"{s}_lower_leg"] for s in ("left", "right")
                        if f"{s}_foot" in name and f"{s}_lower_leg" in name})
        if "upper_chest" in name:
            parents.update({name[f"{s}_shoulder"]: name["upper_chest"] for s in ("left", "right")
                            if f"{s}_shoulder" in name})
        common.reparent(armature, {k: v for k, v in parents.items() if k})
        with editing(armature, "EDIT"):
            armature.data.edit_bones.remove(armature.data.edit_bones[name["hips"]])
        armature.data.bones[pelvis].name = "Hips"
    merged = [n for n in MERGED + tuple(extra_merged) if n in armature.data.bones]
    merge_weights.merge_weights(ch, armature, merged)
    common.hide_eye_uv_warps(ch)
