"""The snapshot check's physics tolerance (ADR 0031). No bpy: runs on the host and in unit tests.

Every export lets physics settle for two seconds, so the bones it moves rest a little differently in
each Golden Sample: between two exports of the same Sample Card, up to 5.7 mm on KK's skirt, 21.8 mm
on SVS's hair and 13.1 mm on SVS's buttocks. Their heads and tails, and the Rigify bones and widgets
made from them, are compared within PHYSICS_TOLERANCE; everything else keeps the default 1 mm.
"""

import compare

PHYSICS_TOLERANCE = 0.035
PHYSICS_GROUPS = frozenset({"skirt", "hair", "breast"})
# No Bone Group or physics chain marks the buttocks: SVS's physics.json has no chains (its MagicaCloth
# isn't captured) and its buttock bones are `deform` and `helper`, so they are found by the game's name.
BUTTOCK_BONES = ("cf_j_siri_L", "cf_j_siri_R")
METARIG = "Metarig {character}"  # the armature once the Rigify Hook has run (D22)
RIG = "Rig {character}"
# The Rigify Hook's breast and buttock handle bones and widgets, and the bones they are placed from.
HANDLE_BONES = {"Breasts handle": ("cf_j_bust01_L", "cf_j_bust01_R"), "Left Breast handle": ("cf_j_bust01_L",),
                "Right Breast handle": ("cf_j_bust01_R",), "Buttocks": ("cf_j_siri_L", "cf_j_siri_R"),
                "Buttocks handle": ("cf_j_siri_L", "cf_j_siri_R"), "Left Buttock handle": ("cf_j_siri_L",),
                "Right Buttock handle": ("cf_j_siri_R",)}
HANDLE_WIDGETS = {"WidgetButtocks": ("cf_j_siri_L", "cf_j_siri_R"), "WidgetButtockLeft": ("cf_j_siri_L",),
                  "WidgetButtockRight": ("cf_j_siri_R",), "WidgetBreasts": ("cf_j_bust01_L", "cf_j_bust01_R"),
                  "WidgetBreastLeft": ("cf_j_bust01_L",), "WidgetBreastRight": ("cf_j_bust01_R",)}
WIDGET_PREFIX = "WGT-RIG-Armature {character}_"  # a Rigify widget object, named after its bone
_RIG_PREFIXES = (WIDGET_PREFIX, "ORG-", "DEF-", "MCH-", "VIS_", "ROT-", "STR-", "tweak_")
# A joint correction's helper bone is named after the bones it is placed from ("JC-T cf_d_bust00").
JOINT_CORRECTION_PREFIX = "JC-"
_SIDES = ("_L", "_R", ".L", ".R")


def physics_bones(skeleton) -> set[str]:
    """The Ids of the bones physics moves in `skeleton` (skeleton.json): the physics Bone Groups, the
    buttock bones, and every descendant of either."""
    bones = skeleton["bones"]
    children = {}
    for b in bones:
        children.setdefault(b["parent"], []).append(b["id"])
    found = set()
    todo = [b["id"] for b in bones if b.get("group") in PHYSICS_GROUPS or b["id"] in BUTTOCK_BONES]
    while todo:
        bone = todo.pop()
        if bone not in found:
            found.add(bone)
            todo += children.get(bone, [])
    return found


def tolerance_for(skeleton, summary):
    """A function of a summary path that returns its tolerance, for compare.differences. `summary` is
    the expected one; its metarig's bone names tell which rig bones and widgets come from which bone.
    The Rigify Hook's breast and buttock handles count as the bones they are placed from."""
    moved = physics_bones(skeleton)
    moved |= {h for h, bones in HANDLE_BONES.items() if any(b in moved for b in bones)}
    metarig = summary.get("objects", {}).get(METARIG, {}).get("armature", {}).get("bones", {})

    def from_physics(name):
        if name.startswith(JOINT_CORRECTION_PREFIX):
            return any(word in moved for word in name.split()[1:])
        return name in moved or rig_base(name, metarig) in moved

    def tolerance(path):
        parts = path.split("/")  # "", "objects", <object>, ...
        if len(parts) < 4 or parts[1] != "objects":
            return compare.DEFAULT_TOLERANCE
        obj = parts[2]
        if len(parts) == 7 and parts[3:5] == ["armature", "bones"] and parts[6] in ("head", "tail"):
            bone = parts[5]
            physics = bone in moved if obj != RIG else from_physics(bone)
        elif len(parts) == 4 and parts[3] == "location":
            physics = (any(b in moved for b in HANDLE_WIDGETS.get(obj, ())) or
                       obj.startswith(WIDGET_PREFIX) and from_physics(obj))
        else:
            physics = False
        return PHYSICS_TOLERANCE if physics else compare.DEFAULT_TOLERANCE

    return tolerance


def rig_base(name, metarig):
    """The metarig bone a generated rig bone (or its widget) is made from, or None: the longest start
    of its name, cut at a `_` or `.`, that names a metarig bone. Rigify puts its own suffixes before
    the side (IndexFinger1_ik_L from IndexFinger1_L) and lower-cases the spine's names (head and
    MCH-ROT-head from Head), so the side is kept and the case doesn't count."""
    stripped = True
    while stripped:
        stripped = next((p for p in _RIG_PREFIXES if name.startswith(p)), None)
        name = name[len(stripped):] if stripped else name
    side = next((s for s in _SIDES if name.endswith(s)), "")
    stem = name[: len(name) - len(side)]
    lower = {b.lower(): b for b in metarig}
    cuts = [len(stem)] + [i for i in range(len(stem) - 1, 0, -1) if stem[i] in "_."]
    for cut in cuts:
        for candidate in (stem[:cut] + side, stem[:cut]) if side else (stem[:cut],):
            if candidate in metarig:
                return candidate
            if candidate.lower() in lower:
                return lower[candidate.lower()]
    return None
