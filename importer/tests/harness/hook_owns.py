"""What each built-in Hook may change, for `run.py hooks --each` (D32). No bpy: runs on the host.

Each Hook runs on its own (`hooks=[that one]`, its switch on) and its scene summary is compared with
the Core Import's from the same build. Every difference must be one the Hook owns, by the rules
below; any other is reported, and fails the run, because a Hook should change only its own part of
the Character. A rule is a path pattern into the summary (`*` is one key, a trailing `**` anything
below), or a function of the difference.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

BODY = "Body {character}"
DEFAULT_OBJECTS = ("Cube", "Camera", "Light")


@dataclass(frozen=True)
class Run:
    hook: str  # its name in BUILTIN_HOOKS
    options: dict = field(default_factory=dict)  # its switch, set on
    choice: str | None = None  # for a choice switch: which choice this run is

    @property
    def variant(self) -> str:
        """The run's folder name under .work/runs/<build>/<sample>.<variant>."""
        slug = self.hook.lower().replace(" ", "_")
        return f"hook.{slug}" + (f".{self.choice}" if self.choice else "")

    @property
    def label(self) -> str:
        return self.hook + (f" ({self.choice})" if self.choice else "")


# One run per Hook, and one per choice of a choice switch. Each Hook adds its runs and its rules
# when it is written.
RUNS: list[Run] = [
    Run("Delete default scene", {"delete_default_scene": True}),
    *[Run("Convert shaders", {"convert_shaders": c}, c) for c in ("eevee_mod", "cycles", "cycles_classic", "principled")],
    Run("Separate meshes", {"separation_type": "by_material"}, "by_material"),
    Run("Outlines", {"use_outlines": True}),
    Run("Face cards", {"use_face_cards": True}),
    Run("SFW", {"sfw_mode": True}),
    Run("Rigify", {"use_rigify": True}),
    Run("Separate Eyes", {"separate_eyes": True}),
]

# Hook name -> the parts of the summary it may change.
OWNS: dict[str, tuple] = {
    # Blender's startup objects and their data (the harness imports into an empty file, so nothing).
    "Delete default scene": (lambda d: d.path[0] == "objects" and len(d.path) >= 2 and d.path[1] in DEFAULT_OBJECTS,
                             ("counts", "objects"), ("counts", "meshes"), ("counts", "cameras"), ("counts", "lights")),
    # The shader groups and the images the variants bring, and Eevee+'s geometry-nodes modifier on Body.
    "Convert shaders": (("materials", "*", "node_groups", "**"), ("materials", "*", "images", "**"),
                        ("images", "**"), ("counts", "node_groups"), ("counts", "images"),
                        ("objects", BODY, "modifiers", "**")),
    # The Outfits' clothes become one object each: the Outfit objects go, the pieces come, and the
    # Collections list them.
    "Separate meshes": (lambda d: d.path[0] == "objects" and len(d.path) == 2 and _role(d) == ["outfit"],
                        ("collections", "**"), ("counts", "objects"), ("counts", "meshes")),
    # The Solidify modifiers, the outline materials and their slots (textured materials move first),
    # and Body's vertex group that thins the outline where the face mask hides it.
    "Outlines": (("objects", "*", "modifiers", "**"), ("objects", "*", "mesh", "material_slots", "**"),
                 ("objects", BODY, "mesh", "vertex_groups"),
                 lambda d: d.path[0] == "materials" and d.path[1].startswith("Outline "),
                 ("images", "**"), ("counts", "materials"), ("counts", "images")),
    # The cards, their rig and bone shapes, their materials and images, and their Collection.
    "Face cards": (lambda d: d.path[0] == "objects" and len(d.path) == 2 and str(d.path[1]).startswith(FACE_CARDS),
                   lambda d: d.path[0] == "materials" and str(d.path[1]).startswith(CARD_MATERIALS),
                   ("images", "**"), ("collections", "**"), ("counts", "**")),
    # Vertices, vertex groups and shape keys of the meshes, and bones of the armature.
    "SFW": (("objects", "*", "mesh", "**"), ("objects", "*", "armature", "**")),
    # The metarig and the rig, their widgets, and what moves onto the rig: parents, modifiers, vertex
    # groups (DEF- names, the eye and palm groups), and the face rig's shape key halves, drivers and
    # board labels (ADR 0058). Not materials.
    "Rigify": (("objects", "**"), ("collections", "**"), ("counts", "objects"), ("counts", "meshes"),
               ("counts", "armatures"), ("counts", "actions")),
    # Body loses the eye and eyebrow faces, their slots and its UV-warp modifiers; the new Parts and their
    # Collection come, with keys driven from Body's.
    "Separate Eyes": (("objects", "**"), ("collections", "**"), ("counts", "objects"), ("counts", "meshes")),
}
FACE_CARDS = ("Face card", "Facecard-bone")
CARD_MATERIALS = ("Eyeline card", "Eyewhite card", "Pupil L card", "Pupil R card", "Gag Mouth")


# --- differences between two summaries of the same bundle ---------------------------------------

TOLERANCE = 1e-3
_DUPLICATE = re.compile(r"\.\d{3}$")
# Texture file suffixes a card template's own images keep, as template slots (`_unowned_image`).
_IMAGE_SUFFIXES = (
    ("_light.png", "main.light"), ("_dark.png", "main.dark"), ("_NMPD_CNV.png", "detail_normal"),
    ("_NMP_CNV.png", "normal"), ("_AM.png", "alpha_mask"), ("_AMB.png", "alpha_mask_bottom"),
    ("_Cloth_alpha_bot.png", "alpha_mask_bottom"), ("_Cloth_alpha.png", "alpha_mask"),
    ("_EXPR.png", "expression"), ("_MT_CT.png", "main"), ("_Normal_map.png", "normal"),
)


@dataclass
class Difference:
    path: tuple  # keys from the summary's top
    kind: str  # missing, unexpected, changed, order
    expected: object = None
    actual: object = None

    def text(self):
        where = "/".join(str(p) for p in self.path)
        if self.kind == "missing":
            return f"{where}: only in the Core Import" + (f": {_short(self.expected)}" if self.expected is not None else "")
        if self.kind == "unexpected":
            return f"{where}: only with the Hook" + (f": {_short(self.actual)}" if self.actual is not None else "")
        if self.kind == "order":
            return f"{where}: same items, different order"
        return f"{where}: {_short(self.expected)} -> {_short(self.actual)}"


def _short(value, limit=120):
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summary_differences(core, hooked):
    """Every difference between the Core Import's summary and a Hook run's, item by item, after
    both are put into one form: material names lose Blender's `.001` duplicate number, and images
    are known by material Id and texture slot."""
    return differences(normalize(core), normalize(hooked))


def normalize(summary):
    out = {"collections": summary["collections"], "objects": {}, "materials": {}, "images": [], "counts": summary["counts"]}
    for name, obj in summary["objects"].items():
        o = {k: v for k, v in obj.items() if k != "id"}
        o["roles"] = obj.get("roles", [])
        if "mesh" in obj:
            mesh = dict(obj["mesh"])
            if "material_slots" in mesh:
                mesh["material_slots"] = [_DUPLICATE.sub("", m) if m else None for m in mesh["material_slots"]]
            o["mesh"] = mesh
        out["objects"][name] = o
    for name, mat in summary["materials"].items():
        m = {k: v for k, v in mat.items() if k not in ("roles", "id", "template")}
        owned = bool(mat.get("id"))
        m["images"] = sorted(i if owned else _unowned_image(i) for i in mat["images"])
        out["materials"][_DUPLICATE.sub("", name)] = m
    owners = {i for mat in summary["materials"].values() if mat.get("id") for i in mat["images"]}
    out["images"] = sorted({i if i in owners else _unowned_image(i) for i in summary["images"]})
    return out


def _unowned_image(image):
    """An image file named after a material, in a material with no bundle Id (a face card, which
    can leave showing the card template's own `cf_m_..._light.png`)."""
    for suffix, slot in _IMAGE_SUFFIXES:
        if image.endswith(suffix) and image.startswith("cf_m_"):
            return f"{image[: -len(suffix)]} {slot}"
    return image


def differences(expected, actual, path=()):
    """Every difference, item by item: list items that are strings are compared as sets."""
    out = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(set(expected) | set(actual), key=str):
            if key not in actual:
                out.append(Difference(path + (key,), "missing", expected[key]))
            elif key not in expected:
                out.append(Difference(path + (key,), "unexpected", None, actual[key]))
            else:
                out += differences(expected[key], actual[key], path + (key,))
    elif isinstance(expected, list) and isinstance(actual, list):
        if all(isinstance(v, str) for v in expected + actual):
            missing = [v for v in expected if v not in actual]
            extra = [v for v in actual if v not in expected]
            out += [Difference(path + (v,), "missing") for v in missing]
            out += [Difference(path + (v,), "unexpected") for v in extra]
            if not missing and not extra and expected != actual:
                out.append(Difference(path, "order", expected, actual))
        elif _vector(expected) and _vector(actual) and len(expected) == len(actual):
            if any(not math.isclose(e, a, abs_tol=TOLERANCE) for e, a in zip(expected, actual)):
                out.append(Difference(path, "changed", expected, actual))
        elif len(expected) != len(actual):
            out.append(Difference(path, "changed", expected, actual))
        else:
            for i, (e, a) in enumerate(zip(expected, actual)):
                out += differences(e, a, path + (i,))
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)) and not isinstance(expected, bool):
        if not math.isclose(expected, actual, abs_tol=TOLERANCE if isinstance(expected, float) else 0):
            out.append(Difference(path, "changed", expected, actual))
    elif expected != actual:
        out.append(Difference(path, "changed", expected, actual))
    return out


def _vector(values):
    return bool(values) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in values)


# --- what each Hook owns --------------------------------------------------------------------

def _role(d):
    value = d.expected if d.kind == "missing" else d.actual
    return value.get("roles") if isinstance(value, dict) else None


def _matches(pattern, d) -> bool:
    if callable(pattern):
        return bool(pattern(d))
    path = d.path
    if pattern and pattern[-1] == "**":
        head = pattern[:-1]
        return len(path) >= len(head) and all(p == "*" or p == k for p, k in zip(head, path))
    return len(path) == len(pattern) and all(p == "*" or p == k for p, k in zip(pattern, path))


def split(run: Run, diffs) -> tuple[list, list]:
    """(owned, unowned) differences for one Hook run."""
    rules = OWNS.get(run.hook, ())
    owned, unowned = [], []
    for d in diffs:
        (owned if any(_matches(r, d) for r in rules) else unowned).append(d)
    return owned, unowned


def markdown(sample, run: Run, owned, unowned, limit=80) -> str:
    lines = [f"# {sample}: {run.label} on its own, against the Core Import", "",
             f"{len(owned)} change(s) it owns, {len(unowned)} it doesn't.", ""]
    if unowned:
        lines += ["## Changes outside what it owns", ""] + [f"- `{d.text()}`" for d in unowned[:limit]]
        if len(unowned) > limit:
            lines.append(f"- … and {len(unowned) - limit} more")
        lines.append("")
    lines += ["## Changes it owns", ""] + [f"- `{d.text()}`" for d in owned[:limit]]
    if len(owned) > limit:
        lines.append(f"- … and {len(owned) - limit} more")
    return "\n".join(lines) + "\n"
