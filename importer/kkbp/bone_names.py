"""The legacy importer's readable names for the bones with a Bone Role (D23). The Core Import names
bones by Id (D9); the Rigify Hook and export prep give these names to the bones they hand on, so the
rig's controls and the exported skeletons keep the names the legacy importer, its documentation and
the animation retargeting lists use."""

_SIDES = (("left", "Left", "L"), ("right", "Right", "R"))
_FINGERS = (("index", "IndexFinger"), ("middle", "MiddleFinger"), ("ring", "RingFinger"), ("little", "LittleFinger"))
_JOINTS = ("proximal", "intermediate", "distal")
ROLE_NAMES = {
    "body_root": "Center", "hips": "Hips", "spine": "Spine", "chest": "Chest", "upper_chest": "Upper Chest",
    "neck": "Neck", "head": "Head",
    **{f"{side}_{part}": f"{word} {name}" for side, word, _ in _SIDES for part, name in (
        ("shoulder", "shoulder"), ("upper_arm", "arm"), ("lower_arm", "elbow"), ("hand", "wrist"),
        ("upper_leg", "leg"), ("lower_leg", "knee"), ("foot", "ankle"), ("toes", "toe"), ("eye", "Eye"))},
    **{f"{side}_thumb_{joint}": f"Thumb{i}_{s}" for side, _, s in _SIDES for i, joint in enumerate(_JOINTS)},
    **{f"{side}_{finger}_{joint}": f"{name}{i + 1}_{s}" for side, _, s in _SIDES for finger, name in _FINGERS
       for i, joint in enumerate(_JOINTS)},
}
# No Bone Role marks the pelvis, which the legacy importer renamed too.
EXACT_NAMES = {"cf_j_waist01": "Pelvis"}

