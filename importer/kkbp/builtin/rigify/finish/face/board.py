"""The face board: a labelled panel beside the head, following it, for what has no place on the face.

- Look: a joystick that adds to the eye target.
- Mouth shape: which open shape the jaw opens, A in its middle and I, O, E, U at its edges.
- Mood and Mood 2: lip-only shapes that layer over any open shape.
- Open mood: four more open shapes, which take over from the mouth shape when pushed; the jaw opens
  them too, so only one open key is ever on and the teeth and tongue never move twice.
- Sliders: the other eye, brow and open-mouth keys, the gag eyes (how much, and which gag) and the
  tears.

The board's frame can't be selected; only its knobs and sliders move. Labels are text objects
parented to the frame, in their own Collection, hidden in renders. Nothing on the board draws a
relationship line: each control hangs from a pivot (face/__init__.py), and each label sits on the
frame bone's tail.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Matrix, Vector

from ..... import templates
from .....editing import editing
from .....steps import gag
from ... import names
from . import controls, shapes
from .terms import Term, axis, channel, driver, prop

HEAD = names.ORIGINAL_BONE_PREFIX + names.HEAD_BONE
SLIDE = 0.03  # a slider's travel
ROW, COLUMN, LABEL = 0.0115, 0.088, 0.04
TEXT = 0.0052
LOOK_GAIN = (0.07, 0.05)  # how far the look joystick moves the eye target, sideways and up
FRAME_COLOR = (0.55, 0.55, 0.6)
COLORS = {"eyes": (0.95, 0.75, 0.2), "brows": (0.45, 0.8, 1.0), "mouth": (1.0, 0.45, 0.55),
          "mood": (0.6, 1.0, 0.55)}
LABELS = "Face board labels {name}"
GAG_TYPE = "gag type"
# grid id, title, half size, colour, {direction: (Face Key Role, label)}
GRIDS = (
    ("look", "LOOK", 0.022, "eyes", {}),
    ("shape", "MOUTH SHAPE", 0.016, "mouth", {"up": ("vowel_i", "I"), "down": ("vowel_o", "O"),
                                             "left": ("vowel_e", "E"), "right": ("vowel_u", "U")}),
    ("mood", "MOOD", 0.016, "mood", {"up": ("mood_up", "smile"), "down": ("mood_down", "frown"),
                                     "left": ("mood_left", "pout"), "right": ("mood_right", "smirk")}),
    ("mood2", "MOOD 2", 0.016, "mood", {"up": ("mood2_up", ":3"), "down": ("mood2_down", "press"),
                                        "left": ("mood2_left", "grit"), "right": ("mood2_right", "tight")}),
    ("open", "OPEN MOOD", 0.016, "mouth", {"up": ("open_mood_up", "gape"), "down": ("open_mood_down", "sad"),
                                           "left": ("open_mood_left", "pout"),
                                           "right": ("open_mood_right", "huff")}),
)
JAW_GRIDS = ("shape", "open")
DIRECTIONS = {"up": ("LOC_Y", 1, 1), "down": ("LOC_Y", -1, 1), "left": ("LOC_X", -1, 0), "right": ("LOC_X", 1, 0)}
# column title, colour, rows: a Face Key Role, (None, subtitle), or (role, label) for a set label
COLUMNS = (
    ("EYES", "eyes", ("eyes_smiling", "eyes_happy_closed", "eyes_half_lid", "eyes_smug", "eyes_doubt", "eyes_angry",
                      "eyes_sad", (None, "GAG EYES"), ("gag_eyes", "Amount"), (GAG_TYPE, "Type"))),
    ("BROWS", "brows", ("brows_amazed", "brows_doubt", "brows_smiling", "brows_worried", "brows_angry",
                        (None, "TEARS"), ("tears_small", "Small"), ("tears_med", "Medium"), ("tears_big", "Big"))),
    ("OPEN MOUTH", "mouth", ("open_smile", "open_cartoony", "open_excited", "open_angry", "open_hate", "open_serious",
                             "open_triangle", "open_kiss", "open_catlike", "open_tongue", "open_playful")),
)
PREFIXES = ("Eyebrow ", "Eye ", "Mouth ")


def bone_name(item):
    return names.BOARD_CONTROL_PREFIX + item


def build(build, keys, eyes, terms, log) -> dict:
    """The board, its terms and labels; returns how a preset reaches a Face Key Role through it,
    as controls.build does."""
    rig = build.rig
    selection = gag.selection(build.character, build.ctx.bundle)
    rows = []  # (column, row, kind, role or None, text)
    for ci, (_, colour, items) in enumerate(COLUMNS):
        r = 0
        for item in items:
            role, text = item if isinstance(item, tuple) else (item, None)
            if role is None:
                rows.append((ci, r, "subtitle", None, text))
            elif role == GAG_TYPE:
                if selection is None:
                    continue
                rows.append((ci, r, "slider", role, text))
            elif role in keys:
                rows.append((ci, r, "slider", role, text or _label(keys.first(role))))
            else:
                continue
            r += 1

    face_x = max(eyes["L"].centre.x + eyes["L"].half_width, 0.05)
    x0 = face_x + 0.06
    y = min(eyes["L"].front, eyes["R"].front) - 0.01
    top = eyes["L"].centre.z + 0.1
    biggest = max(g[2] for g in GRIDS)
    grid_height = 0.02 + 2 * biggest + 0.014
    height = grid_height + 0.014 + max(r for _, r, *_ in rows) * ROW + ROW + 0.008
    width = max(sum(2 * g[2] + 0.022 for g in GRIDS), len(COLUMNS) * COLUMN) + 0.006
    centres, sliders = {}, []
    with editing(rig, "EDIT"):
        edit = rig.data.edit_bones
        shapes.new_bone(edit, names.FACE_BOARD_BONE, (x0, y, top - height), parent=HEAD, length=0.02)
        gx = x0 + 0.006
        for gid, _, half, _, _ in GRIDS:
            centre = Vector((gx + half + 0.008, y - 0.001, top - 0.022 - biggest))
            shapes.new_bone(edit, bone_name(gid), centre, parent=names.FACE_BOARD_BONE, length=0.006)
            centres[gid] = centre
            gx += 2 * half + 0.022
        for ci, r, kind, role, text in rows:
            cx = x0 + 0.006 + ci * COLUMN
            z = top - grid_height - 0.014 - (r + 1) * ROW + 0.004
            at = Vector((cx + LABEL, y - 0.001, z))
            if kind == "slider":
                name = bone_name(role if role == GAG_TYPE else keys.first(role))
                shapes.new_bone(edit, name, at, parent=names.FACE_BOARD_BONE, length=0.006)
                sliders.append((name, role, text, COLUMNS[ci][1], at, cx))
            else:
                sliders.append((None, None, text, None, Vector((cx, y - 0.0015, z - 0.002)), cx))
    rig.data.bones[names.FACE_BOARD_BONE].hide_select = True  # scenery: only its knobs and sliders move
    shapes.lock(rig.pose.bones[names.FACE_BOARD_BONE])
    shapes.put(rig, names.FACE_BOARD_BONE, names.EMOTIONS_LAYER)

    labels = _Labels(build, rig)
    reach = {}
    rest = rig.data.bones[names.FACE_BOARD_BONE].matrix_local.inverted()
    frame = [shapes.rect(-0.002, -0.002, width, height)]
    for gid, title, half, colour, directions in GRIDS:
        bone, centre = bone_name(gid), centres[gid]
        local = rest @ centre
        frame.append(shapes.rect(local.x - half, local.y - half, local.x + half, local.y + half))
        frame.append(([(local.x - half, local.y), (local.x + half, local.y), (local.x, local.y - half),
                       (local.x, local.y + half)], [(0, 1), (2, 3)]))
        pose_bone = rig.pose.bones[bone]
        shapes.put(rig, bone, names.EMOTIONS_LAYER)
        shapes.lock(pose_bone, location=(False, False, True))
        shapes.limit_location(pose_bone, x=(-half, half), y=(-half, half))
        shapes.widget(build, rig, bone, shapes.combine(shapes.circle(half * 0.28), shapes.circle(half * 0.09)),
                      color=COLORS[colour])
        labels.add(title, centre + Vector((-half, -0.0005, half + 0.0095)), size=0.0048)
        for direction, (role, text) in directions.items():
            offset = {"up": (0, half + 0.0032), "down": (0, -half - 0.0032), "left": (-half - 0.0012, 0),
                      "right": (half + 0.0012, 0)}[direction]
            labels.add(text, centre + Vector((offset[0], -0.0005, offset[1])), size=0.0036,
                       align={"left": "RIGHT", "right": "LEFT"}.get(direction, "CENTER"))
            if gid in JAW_GRIDS or role not in keys:
                continue
            transform, sign, index = DIRECTIONS[direction]
            for name, weight in keys.get(role):
                terms.add(name, axis(rig, bone, transform, half, sign), weight)
            reach[role] = [(bone, index, sign * half)]
    if "vowel_a" in keys:
        labels.add("A", centres["shape"] + Vector((0.0, -0.0005, -0.0072)), size=0.0034, align="CENTER")
    _look(rig, centres)
    reach.update(_jaw_terms(rig, keys, centres, terms))

    for name, role, text, colour, at, cx in sliders:
        if name is None:
            labels.add(text, at, size=0.0042)
            continue
        local = rest @ at
        frame.append(([(local.x, local.y), (local.x + SLIDE, local.y), (local.x, local.y - 0.002),
                       (local.x, local.y + 0.002), (local.x + SLIDE, local.y - 0.002), (local.x + SLIDE, local.y + 0.002)],
                      [(0, 1), (2, 3), (4, 5)]))
        pose_bone = rig.pose.bones[name]
        shapes.put(rig, name, names.EMOTIONS_LAYER)
        shapes.lock(pose_bone, location=(False, True, True))
        shapes.limit_location(pose_bone, x=(0.0, SLIDE))
        shapes.widget(build, rig, name, shapes.rect(-0.0022, -0.0038, 0.0022, 0.0038), color=COLORS[colour])
        labels.add(text, at + Vector((-LABEL + 0.002, -0.0005, 0.0)))
        if role == GAG_TYPE:
            count = len(selection.expressions)
            frame.append(([(local.x + SLIDE * (i + 0.5) / count, local.y + d) for i in range(count)
                           for d in (-0.0012, 0.0012)], [(2 * i, 2 * i + 1) for i in range(count)]))
            _gag_type(rig, name, selection, count)
            continue
        for key, weight in keys.get(role):
            terms.add(key, axis(rig, name, "LOC_X", SLIDE), weight)
        reach[role] = [(name, 0, SLIDE)]
    for ci, (title, _, _) in enumerate(COLUMNS):
        labels.add(title, Vector((x0 + 0.006 + ci * COLUMN, y - 0.0015, top - grid_height - 0.006)), size=0.0055)
    labels.add("FACE", Vector((x0 + width - 0.004, y - 0.0015, top + 0.007)), size=0.0072, align="RIGHT")
    shapes.widget(build, rig, names.FACE_BOARD_BONE, shapes.combine(*frame), color=FRAME_COLOR, wire=1.0)
    log.info(f"The face board has {len(GRIDS)} grids and {sum(1 for s in sliders if s[0])} sliders")
    return reach


def _label(name):
    for prefix in PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _look(rig, centres):
    """The look joystick adds to the eye target's location."""
    transform = rig.pose.bones[names.EYE_TARGET_BONE].constraints.new("TRANSFORM")
    transform.target, transform.subtarget = rig, bone_name("look")
    transform.owner_space = transform.target_space = "LOCAL"
    transform.map_from = transform.map_to = "LOCATION"
    transform.mix_mode = "ADD"
    half = GRIDS[0][2]
    transform.from_min_x, transform.from_max_x, transform.from_min_y, transform.from_max_y = -half, half, -half, half
    transform.to_min_x, transform.to_max_x = -LOOK_GAIN[0], LOOK_GAIN[0]
    transform.to_min_y, transform.to_max_y = -LOOK_GAIN[1], LOOK_GAIN[1]


def _jaw_terms(rig, keys, centres, terms) -> dict:
    """The jaw opens one open key at a time: the vowel the mouth shape grid points at (A in its
    middle), or the open mood its grid is pushed towards, which takes over from the vowels."""
    half = {g[0]: g[2] for g in GRIDS}
    k_jaw = round(-1 / (2 * controls.TRAVEL), 4)
    k1, k2 = round(1 / half["shape"], 4), round(1 / half["open"], 4)
    jaw = controls.bone_name("jaw")
    v = {"j": channel(rig, jaw, "LOC_Y"),
         "x": channel(rig, bone_name("shape"), "LOC_X"), "y": channel(rig, bone_name("shape"), "LOC_Y"),
         "a": channel(rig, bone_name("open"), "LOC_X"), "b": channel(rig, bone_name("open"), "LOC_Y")}
    opened = f"min(1,max(0,{{j}}*{k_jaw}))"
    free = f"max(0,1-abs({{a}}*{k2})-abs({{b}}*{k2}))"  # 1 while the open mood grid is in its middle
    n1 = f"max(1,abs({{x}}*{k1})+abs({{y}}*{k1}))"
    n2 = f"max(1,abs({{a}}*{k2})+abs({{b}}*{k2}))"
    vowels = {"vowel_a": f"max(0,1-abs({{x}}*{k1})-abs({{y}}*{k1}))", "vowel_i": f"max(0,{{y}}*{k1})/{n1}",
              "vowel_o": f"max(0,{{y}}*{-k1})/{n1}", "vowel_e": f"max(0,{{x}}*{-k1})/{n1}",
              "vowel_u": f"max(0,{{x}}*{k1})/{n1}"}
    moods = {"up": f"max(0,{{b}}*{k2})/{n2}", "down": f"max(0,{{b}}*{-k2})/{n2}",
             "left": f"max(0,{{a}}*{-k2})/{n2}", "right": f"max(0,{{a}}*{k2})/{n2}"}
    at = {"vowel_a": (0, 0), "vowel_i": (0, half["shape"]), "vowel_o": (0, -half["shape"]),
          "vowel_e": (-half["shape"], 0), "vowel_u": (half["shape"], 0)}
    reach = {}
    if jaw not in rig.pose.bones:
        return reach
    for role, weight_expr in vowels.items():
        for name, weight in keys.get(role):
            terms.add(name, Term(f"{opened}*{free}*{weight_expr}", v), weight)
        if role in keys:
            reach[role] = [(jaw, 1, -2 * controls.TRAVEL), (bone_name("shape"), 0, at[role][0]),
                           (bone_name("shape"), 1, at[role][1])]
    for direction, (role, _) in next(g for g in GRIDS if g[0] == "open")[4].items():
        transform, sign, index = DIRECTIONS[direction]
        for name, weight in keys.get(role):
            terms.add(name, Term(f"{opened}*{moods[direction]}", {k: v[k] for k in "jab"}), weight)
        if role in keys:
            reach[role] = [(jaw, 1, -2 * controls.TRAVEL), (bone_name("open"), index, sign * half["open"])]
    return reach


def _gag_type(rig, bone, selection, count):
    """At 0 the gag eyes' own dropdown picks; moved right, the slider steps through the gags, which
    sets the dropdown's number (ADR 0042)."""
    _, number = templates.picker_paths(selection.material)
    k = round((count - 1) / SLIDE, 3)
    # the node tree is its own datablock: the driver goes on it
    driver(selection.material.node_tree, number.removeprefix("node_tree."),
           f"0 if x<0.0004 else 1+min({count - 1},x*{k})", [("x", channel(rig, bone, "LOC_X"))])


class _Labels:
    def __init__(self, build, rig):
        ch = build.character
        name = LABELS.format(name=ch.name)
        self.collection = next((c for c in ch.collection.children if c.name == name), None)
        if self.collection is None:
            self.collection = bpy.data.collections.new(name)
            ch.collection.children.link(self.collection)
        self.rig, self.count = rig, 0

    def add(self, text, world, size=TEXT, align="LEFT"):
        self.count += 1
        curve = bpy.data.curves.new(f"Face board label {self.count}", "FONT")
        curve.body, curve.size, curve.align_x, curve.align_y = text, size, align, "CENTER"
        obj = bpy.data.objects.new(f"Face board label {self.count}", curve)
        self.collection.objects.link(obj)
        obj.parent, obj.parent_type, obj.parent_bone = self.rig, "BONE", names.FACE_BOARD_BONE
        obj.hide_select = True
        obj.hide_render = True
        obj.show_in_front = True
        # hidden with the board's bone collection
        driver(obj, "hide_viewport", "not shown",
               [("shown", prop(self.rig, f'data.collections_all["{names.EMOTIONS_LAYER}"].is_visible'))])
        # The object sits on the frame bone's tail, where its relationship line goes, so the line has
        # no length; the text moves to its place by its own offset (in the text's plane: x across, y up).
        anchor = self.rig.matrix_world @ self.rig.data.bones[names.FACE_BOARD_BONE].tail_local
        curve.offset_x, curve.offset_y = world.x - anchor.x, world.z - anchor.z
        bpy.context.view_layer.update()
        obj.matrix_world = Matrix.Translation(anchor) @ Matrix.Rotation(math.radians(90), 4, "X")
        return obj
