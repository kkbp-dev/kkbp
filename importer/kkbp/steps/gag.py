"""Gag eyes: one `Gag eyes` shape key, and a dropdown on the gag eyes' first material that picks
which gag expression it shows (issue 35, ADR 0042).

Every gag expression of a Game moves the face the same way except one or two (Fiery Eyes, which
leaves the eyes open). `combine_gag_keys` replaces the gag expressions' shape keys with `Gag eyes`,
holding the shape most of them share, and a correction key for each other shape, which turns on
with `Gag eyes` while one of its expressions is picked. Once the materials are made,
`drive_gag_eyes` adds the dropdown and drives from it, and from `Gag eyes`, what each gag
expression's key drove before: the gag mesh that shows, the texture on it and the correction keys.
The material-changes Step hides the pupils and eyelines through `Selection` (ADR 0021).
"""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from .. import templates
from .mesh import _meshes, _part_with_key, _quote, _single_prop_driver, add_driver, drive_param

GAG_KEY = "Gag eyes"
CORRECTIONS = "kkbp_gag_corrections"  # on a Part's shape keys: correction key -> the expressions it is for
TOLERANCE = 1e-5  # metres: two expressions whose shapes differ by less on every vertex share a shape
MAX_NAME = 63  # Blender's longest shape key name


def gag_expressions(bundle) -> list[str]:
    """The targets of the bundle's gag expressions, in the bundle's order, without the gag meshes'
    showing keys (ADR 0010)."""
    found = []
    for e in bundle.expressions.records:
        if e.category == "gag" and e.game_name is not None and e.target not in found:
            found.append(e.target)
    return found


def label(bundle, target: str) -> str:
    """What the dropdown calls a gag expression: its Expression Name without `Gag `, or the game's name."""
    record = next(e for e in bundle.expressions.records if e.target == target)
    if record.name is None:
        return record.game_name
    return record.name[len("Gag "):] if record.name.startswith("Gag ") else record.name


def corrections(obj) -> dict[str, list[str]]:
    """A Part's gag correction keys, each with the gag expressions it is for."""
    keys = obj.data.shape_keys if obj.type == "MESH" else None
    if keys is None or CORRECTIONS not in keys:
        return {}
    return {name: list(targets) for name, targets in keys[CORRECTIONS].items()}


# --- the shape keys --------------------------------------------------------------------------

def combine_gag_keys(ctx):
    """Replaces the gag expressions' shape keys on every Part with `Gag eyes` and its correction keys."""
    ch, bundle = ctx.character, ctx.bundle
    targets = gag_expressions(bundle)
    if not targets:
        return
    if not any(m.role == "gag_eyes" for m in bundle.materials):
        ctx.log.info("The bundle has no gag eye materials to pick a gag expression on, so its gag keys stay apart")
        return
    parts = [obj for obj in _meshes(ch) if obj.data.shape_keys
             and any(t in obj.data.shape_keys.key_blocks for t in targets)]
    deltas = {obj: {t: _delta(obj, t) for t in targets} for obj in parts}
    groups = _same_shapes(targets, parts, deltas)
    base = max(groups, key=len)  # the first of the largest
    for obj in parts:
        found = {}
        shared = deltas[obj][base[0]]
        if np.abs(shared).max(initial=0.0) >= TOLERANCE:
            _add_key(obj, GAG_KEY, shared)
        for group in groups:
            correction = deltas[obj][group[0]] - shared
            if group is base or np.abs(correction).max(initial=0.0) < TOLERANCE:
                continue
            name = _correction_name(bundle, group)
            _add_key(obj, name, correction)
            found[name] = group
        for t in targets:
            key = obj.data.shape_keys.key_blocks.get(t)
            if key is not None:
                obj.shape_key_remove(key)
        obj.data.shape_keys[CORRECTIONS] = found
    shapes = len(groups) - 1
    ctx.log.info(f"{len(targets)} gag expressions are now {GAG_KEY}"
                 + (f" with {shapes} correction key{'s' if shapes != 1 else ''}" if shapes else ""))


def _delta(obj, target):
    """How shape key `target` moves each vertex from its reference key; zeros if `obj` hasn't the key."""
    keys = obj.data.shape_keys.key_blocks
    key = keys.get(target)
    count = len(obj.data.vertices)
    if key is None:
        return np.zeros(count * 3, dtype=np.float32)
    moved, rest = np.empty(count * 3, dtype=np.float32), np.empty(count * 3, dtype=np.float32)
    key.data.foreach_get("co", moved)
    key.relative_key.data.foreach_get("co", rest)
    return moved - rest


def _same_shapes(targets, parts, deltas):
    """The targets grouped by shape, each group and the groups in the bundle's order."""
    groups = []
    for t in targets:
        group = next((g for g in groups if all(np.abs(deltas[o][g[0]] - deltas[o][t]).max(initial=0.0) < TOLERANCE
                                               for o in parts)), None)
        if group is None:
            groups.append([t])
        else:
            group.append(t)
    return groups


def _add_key(obj, name, delta):
    keys = obj.data.shape_keys
    basis = keys.reference_key
    rest = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
    basis.data.foreach_get("co", rest)
    key = obj.shape_key_add(name=name, from_mix=False)
    key.relative_key = basis
    key.value = 0.0  # a new key starts at 1
    key.data.foreach_set("co", rest + delta)
    return key


def _correction_name(bundle, group):
    labels = [label(bundle, t) for t in group]
    name = f"{GAG_KEY} ({', '.join(labels)})"
    if len(name) > MAX_NAME:
        name = f"{GAG_KEY} ({labels[0]} and {len(labels) - 1} more)"
    return name[:MAX_NAME]


# --- the dropdown ----------------------------------------------------------------------------

class Selection:
    """The gag expression the dropdown (or its number) picks, read by drivers. `targets` are the
    driver targets `picked` and `on` take their variable names for, in order."""

    def __init__(self, owner, material, expressions):
        self.owner, self.material, self.expressions = owner, material, list(expressions)
        menu, number = templates.picker_paths(material)
        self.targets = [(owner.data.shape_keys, f'key_blocks["{_quote(GAG_KEY)}"].value'),
                        (material, number), (material, menu)]

    def number(self, target) -> int:
        return self.expressions.index(target) + 1

    def picked(self, names, targets) -> str:
        """A driver expression that is true while one of `targets` is picked. The number wins
        while it is above 0; the dropdown's items count from 0 (ADR 0042)."""
        _, number, menu = names
        wanted = sorted({self.number(t) for t in targets})
        if not wanted:
            return "0"
        if len(wanted) == len(self.expressions):
            return "1"
        others = sorted(set(range(1, len(self.expressions) + 1)) - set(wanted))
        negate = len(others) < len(wanted)
        chosen = others if negate else wanted
        by_number = " or ".join(f"{number} == {n}" for n in chosen)
        by_menu = " or ".join(f"{menu} == {n - 1}" for n in chosen)
        test = f"(({by_number}) if {number} > 0 else ({by_menu}))"
        return f"not {test}" if negate else test

    def on(self, names, targets) -> str:
        """True while `Gag eyes` is up and one of `targets` is picked."""
        return f"({names[0]} > 0 and {self.picked(names, targets)})"

    def chosen(self, names) -> str:
        """The picked expression's number."""
        _, number, menu = names
        return f"{number} if {number} > 0 else {menu} + 1"


def selection(ch, bundle) -> Selection | None:
    """The Character's gag expression selection, once `drive_gag_eyes` has made the dropdown."""
    owner = _owner(ch)
    material = next((m for m in ch.materials(roles="gag_eyes") if templates.picker(m) is not None), None)
    if owner is None or material is None:
        return None
    return Selection(owner, material, gag_expressions(bundle))


def drive_gag_eyes(ctx):
    """Adds the dropdown to the gag eyes' first material and drives from it the gag textures, the
    gag meshes' showing keys and the correction keys."""
    ch, bundle, profile = ctx.character, ctx.bundle, ctx.profile
    targets = gag_expressions(bundle)
    owner = _owner(ch)
    if not targets or owner is None:
        return
    _hide_eyeshadow(ch, owner)
    materials = _gag_materials(ch)
    if not materials:
        ctx.log.warning(f"No gag eye material can show a pattern, so {GAG_KEY} has no dropdown")
        return
    menu_material = materials[0]
    templates.add_picker(ch, menu_material, [label(bundle, t) for t in targets])
    chosen = Selection(owner, menu_material, targets)

    picks = defaultdict(list)  # material -> [(pattern index, expression number)]
    for t in targets:
        effect = bundle.expressions.effect(t)
        for change in (effect.material_changes if effect else ()):
            mat = ch.material(change.material)
            if mat not in materials:
                continue
            names = templates.patterns(mat)
            for texture in change.textures:
                if texture.pattern in names:
                    index = names.index(texture.pattern)
                    picks[mat].append((index, chosen.number(t)))
                    set_pattern_values(mat, index, change, profile)
    for mat in materials:
        templates.pick_by(mat, picks[mat], from_picker=mat is menu_material)
        if mat is not menu_material:
            drive_param(ch, mat, "choice", chosen.targets, chosen.chosen)

    _drive_showing_keys(ctx, chosen, targets)
    for obj in _meshes(ch):
        for name, group in corrections(obj).items():
            key = obj.data.shape_keys.key_blocks.get(name)
            if key is None:
                continue
            add_driver(key, "value", chosen.targets,
                       lambda names, group=group: f"{names[0]} if {chosen.picked(names, group)} else 0")
            _single_prop_driver(key, "mute", owner.data.shape_keys, f'key_blocks["{_quote(GAG_KEY)}"].mute')


def _hide_eyeshadow(ch, owner):
    """Takes the face's eyeshadow away as `Gag eyes` rises, where the face can fade it (ADR 0046):
    the eyeshadow is painted around eyes the gag expressions close or cover. The material's own
    `eyeshadow_hidden` value still hides it by hand."""
    key = [(owner.data.shape_keys, f'key_blocks["{_quote(GAG_KEY)}"].value')]
    for mat in ch.materials(roles="face"):
        if "eyeshadow_hidden" in templates.params(mat):
            drive_param(ch, mat, "eyeshadow_hidden", key, lambda names: names[0], keep=True)


def _drive_showing_keys(ctx, chosen, targets):
    """Shows each gag mesh while `Gag eyes` is up and an expression that `shows` it is picked."""
    ch, bundle = ctx.character, ctx.bundle
    showing_key = {e.mesh: e.target for e in bundle.expressions.records
                   if e.category == "gag" and e.game_name is None}
    shown_by = defaultdict(list)
    for t in targets:
        effect = bundle.expressions.effect(t)
        for mesh in (effect.shows if effect else ()):
            shown_by[mesh].append(t)
    for mesh, group in shown_by.items():
        key_name = showing_key.get(mesh)
        part = _part_with_key(ch, ch.parts(("tears", "gag_eyes")), key_name)
        if part is None:
            ctx.log.warning(f"Mesh {mesh}'s showing key {key_name} wasn't found")
            continue
        key = part.data.shape_keys.key_blocks[key_name]
        add_driver(key, "value", chosen.targets, lambda names, group=group: f"1 if {chosen.on(names, group)} else 0")


def drive_frames(ctx):
    """Gives every object with a chained pattern material the frame property its Attribute node
    reads, driven by the frame (`Chain.frame_property`). The animated patterns turn and pulse with it."""
    for obj in _meshes(ctx.character):
        names = set()
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None or mat.get(templates.TEMPLATE) is None:
                continue
            patterns = templates.template_of(mat).patterns
            if patterns is not None and patterns.chain is not None and patterns.chain.frame_property:
                names.add(patterns.chain.frame_property)
        for name in sorted(names):
            obj[name] = 0.0
            obj.driver_add(f'["{name}"]').driver.expression = "frame"


def set_pattern_values(mat, index, change, profile):
    values = {}
    for raw, value in change.floats.items():
        if raw in profile.pattern_values:
            values[profile.pattern_values[raw]] = value
    for raw, vector in change.vectors.items():
        for component, value in zip("xyzw", vector):
            name = profile.pattern_values.get(f"{raw}.{component}")
            if name:
                values[name] = value
    if templates.template_of(mat).patterns.chain is None:
        return
    for name, value in values.items():
        templates.pattern_param(mat, index, name).default_value = value


def _owner(ch):
    """The Part whose `Gag eyes` key the user moves: Body if it has one."""
    return _part_with_key(ch, [p for p in (ch.body,) if p] + _meshes(ch), GAG_KEY)


def _gag_materials(ch):
    """The gag eyes' materials that pick between patterns, in material slot order."""
    slots = [s.material for obj in ch.parts("gag_eyes") for s in obj.material_slots if s.material]
    found = []
    for mat in slots + ch.materials(roles="gag_eyes"):
        if mat in found or mat.get(templates.TEMPLATE) is None:
            continue
        patterns = templates.template_of(mat).patterns
        if patterns is not None and patterns.chain is not None:
            found.append(mat)
    return found
