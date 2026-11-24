"""The face rig's presets and resets (the Rigify Hook's finish/face, ADR 0058), for the Face panel and
for scripts. Everything is read from what the Hook wrote on the rig, so a rig from an older import
simply has no face data."""

from __future__ import annotations

import json

from ..builtin.rigify import names

STRENGTH = "preset_strength"
GRID_BONES = (names.BOARD_CONTROL_PREFIX + "shape", names.BOARD_CONTROL_PREFIX + "open")  # placed, not scaled


def data(rig) -> dict | None:
    """What the face rig wrote on `rig`: presets, the Face Properties sliders by category and the
    controls; None for a rig without a face rig."""
    text = rig.get(names.FACE_DATA_PROPERTY) if rig is not None else None
    return json.loads(text) if text else None


def presets(rig) -> list:
    found = data(rig)
    return list(found["presets"]) if found else []


def reset(rig):
    """Every face control back to rest, and every Face Properties slider to 0."""
    found = data(rig)
    if not found:
        return
    for name in found["controls"]:
        if bone := rig.pose.bones.get(name):
            bone.location = (0.0, 0.0, 0.0)
            bone.scale = (1.0, 1.0, 1.0)
    properties = rig.pose.bones.get(names.FACE_PROPERTIES_BONE)
    if properties is not None:
        for _, keys in found["panel"]:
            for key in keys:
                properties[key] = 0.0
    rig.update_tag()


def apply_preset(rig, preset, *, add=False):
    """Poses the face as `preset`, at the Face Properties bone's preset strength; with `add`, on top
    of the face as it is."""
    found = data(rig)
    if not found or preset not in found["presets"]:
        raise KeyError(f"The rig has no face preset {preset!r}")
    if not add:
        reset(rig)
    properties = rig.pose.bones[names.FACE_PROPERTIES_BONE]
    strength = properties.get(STRENGTH, 1.0)
    for kind, target, *rest in found["presets"][preset]:
        if kind == "loc":
            index, value = rest
            rig.pose.bones[target].location[index] += value * (1.0 if target in GRID_BONES else strength)
        else:
            properties[target] = min(1.0, properties.get(target, 0.0) + rest[0] * strength)
    rig.update_tag()


def key(rig, frame):
    """Keys every face control and Face Properties slider at `frame`."""
    found = data(rig)
    if not found:
        return
    for name in found["controls"]:
        if bone := rig.pose.bones.get(name):
            bone.keyframe_insert("location", frame=frame, group=names.FACE_LAYER)
            bone.keyframe_insert("scale", frame=frame, group=names.FACE_LAYER)
    for _, keys in found["panel"]:
        for k in keys:
            rig.keyframe_insert(f'pose.bones["{names.FACE_PROPERTIES_BONE}"]["{k}"]', frame=frame,
                                group=names.FACE_PROPERTIES_BONE)
