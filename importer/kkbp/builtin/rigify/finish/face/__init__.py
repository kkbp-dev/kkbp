"""The face rig (ADR 0058): controls on the face for what has a place there, a board beside the head
for the rest, a look-at target for the eyes, and the emotion presets. Every control drives the
Game's baked expression keys (ADR 0003), through the Face Key Roles the Core Import wrote on Body
(keys.py); a key no control reaches gets a 0-1 slider on the Face Properties bone, which the KKBP
sidebar's Face panel shows with the presets (ui/face.py).

The game face bones stay in the hidden Face Tweak collection, for bone-level tweaks.
"""

from __future__ import annotations

import json

from .....editing import editing
from ... import drivers, names
from . import board, controls, eyes, presets, shapes
from .keys import FaceKeys
from .terms import Terms, build_drivers

CATEGORIES = (("Eyes", "Eye "), ("Brows", "Eyebrow "), ("Mouth", "Mouth "), ("Tears", "Tears "))
HALF = (" (L)", " (R)")
STAR_COLOR = (1.0, 0.45, 0.65)
STRENGTH = "preset_strength"


def face_rig(build):
    body, log = build.body, build.log
    keys = FaceKeys(body)
    if body is None or body.data.shape_keys is None or not keys.get("blink"):
        log.warning("Body has no expression keys the face rig knows, so the rig has no face controls")
        return
    measured = eyes.measure(body)
    if not measured:
        log.warning("Body has no eye vertex groups, so the face rig has no eyes or face controls")
        return
    terms = Terms()
    for term in eyes.build(build, measured):
        for name, weight in keys.get("blink"):
            terms.add(name, term, weight)
    reach = controls.build(build, keys, measured, terms, log)
    reach.update(board.build(build, keys, measured, terms, log))

    controlled = set(terms.keys())
    names_ = [k.name for k in body.data.shape_keys.key_blocks]
    panel = []
    for title, prefix in CATEGORIES:
        listed = [n for n in names_ if n.startswith(prefix) and n not in controlled and not n.endswith(HALF)]
        if listed:
            panel.append([title, listed])
    raw = [n for _, listed in panel for n in listed]
    _properties(build, raw)
    build_drivers(build.rig, body, terms, raw, log)

    resolved = presets.resolve(keys, reach, set(raw))
    controls_ = [b.name for b in build.rig.data.bones
                 if b.collections.get(names.FACE_LAYER) and b.name != names.FACE_BOARD_BONE]
    build.rig[names.FACE_DATA_PROPERTY] = json.dumps(
        {"presets": {p: r["ops"] for p, r in resolved.items()}, "expect": {p: r["expect"] for p, r in resolved.items()},
         "panel": panel, "controls": controls_ + [names.EYE_TARGET_BONE, names.LEFT_EYE_TARGET_BONE,
                                                  names.RIGHT_EYE_TARGET_BONE]}, ensure_ascii=False)
    _no_relationship_lines(build.rig)
    for name in (names.FACE_LAYER, names.EYES_LAYER, names.EMOTIONS_LAYER):
        build.rig.data.collections_all[name].is_visible = True
    log.info(f"The face rig drives {len(controlled)} expression keys from its controls; "
             f"{len(raw)} more have Face Properties sliders")


def _no_relationship_lines(rig):
    """Each control the face layers show hangs from a hidden pivot whose tail is the control's head,
    so its dashed relationship line has no length. The pivot sits at rest, so the control moves as
    before."""
    shown = {b.name for name in (names.FACE_LAYER, names.EYES_LAYER, names.EMOTIONS_LAYER)
             for b in rig.data.collections_all[name].bones if b.parent is not None}
    with editing(rig, "EDIT"):
        edit = rig.data.edit_bones
        for name in sorted(shown):
            bone = edit[name]
            pivot = edit.new(names.FACE_PIVOT_PREFIX + name)
            pivot.head = bone.head - bone.vector.normalized() * 0.002
            pivot.tail = bone.head.copy()
            pivot.roll = bone.roll
            pivot.use_deform = False
            pivot.parent = bone.parent
            bone.parent = pivot
    for name in shown:
        shapes.put(rig, names.FACE_PIVOT_PREFIX + name, names.MCH_LAYER_INDEX)


def _properties(build, raw):
    """The Face Properties bone above the head: a 0-1 property per key no control reaches, and the
    presets' strength."""
    rig = build.rig
    head = rig.data.bones[names.ORIGINAL_BONE_PREFIX + names.HEAD_BONE]
    at = head.tail_local.copy()
    at.y -= 0.12
    at.z += 0.06
    with editing(rig, "EDIT"):
        shapes.new_bone(rig.data.edit_bones, names.FACE_PROPERTIES_BONE, at, parent=head.name, length=0.02)
    pose_bone = rig.pose.bones[names.FACE_PROPERTIES_BONE]
    shapes.lock(pose_bone)
    shapes.widget(build, rig, pose_bone.name, shapes.star(0.022, 0.009), color=STAR_COLOR, wire=2.0)
    shapes.collection(rig, names.EMOTIONS_LAYER, row=6)
    shapes.put(rig, pose_bone.name, names.EMOTIONS_LAYER)
    for name in raw:
        drivers.bone_property(rig, names.FACE_PROPERTIES_BONE, name, default=0.0, min=0.0, max=1.0,
                              description="How much of this expression (keys no face control reaches)")
    drivers.bone_property(rig, names.FACE_PROPERTIES_BONE, STRENGTH, default=1.0, min=0.0, max=1.0,
                          description="How strongly the Face panel's presets apply")
