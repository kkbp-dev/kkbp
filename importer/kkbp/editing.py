"""Switching modes (docs/design/blender-compat-and-testing.md, "Data API over operators").

    with editing(armature, "EDIT"):
        armature.data.edit_bones.new("x")

`editing` is the only place that calls `bpy.ops.object.mode_set`. `switch` is the line-by-line form,
for the scripts ported from the legacy importer that change modes between statements (the Rigify
Hook); new code uses `editing`.
"""

from __future__ import annotations

from contextlib import contextmanager

import bpy


@contextmanager
def editing(objects, mode: str = "EDIT"):
    """Puts `objects` (one object or a list of the same type) into `mode`, with the first one active.

    Afterwards the previous mode, active object and selection come back, even if an error is
    raised inside the block. Objects removed inside the block are skipped when restoring.
    """
    objects = list(objects) if isinstance(objects, (list, tuple)) else [objects]
    if not objects:
        raise ValueError("editing() needs at least one object")
    view_layer = bpy.context.view_layer
    for obj in objects:
        # visible_get also brings the view layer's object list up to date, which `in` and
        # iterating view_layer.objects don't do for newly linked objects.
        if not obj.visible_get(view_layer=view_layer):
            raise ValueError(f"{obj.name} is hidden or not in the view layer, so it can't enter {mode} mode")

    previous_active = view_layer.objects.active
    previous_mode = previous_active.mode if previous_active else "OBJECT"
    previous_selected = [o for o in view_layer.objects if o and o.select_get(view_layer=view_layer)]

    _set_mode(view_layer, previous_active, "OBJECT")
    _select(view_layer, objects, objects[0])
    try:
        _set_mode(view_layer, objects[0], mode, objects)
        yield objects[0] if len(objects) == 1 else objects
    finally:
        _set_mode(view_layer, _alive(objects[0]), "OBJECT")
        _select(view_layer, [o for o in previous_selected if _alive(o)], _alive(previous_active))
        _set_mode(view_layer, _alive(previous_active), previous_mode)


def _set_mode(view_layer, active, mode, objects=None):
    if active is None or active.mode == mode:
        return
    objects = objects or [active]
    with bpy.context.temp_override(view_layer=view_layer, active_object=active, object=active,
                                   selected_objects=objects, selected_editable_objects=objects):
        bpy.ops.object.mode_set(mode=mode)


def _select(view_layer, objects, active):
    for obj in view_layer.objects:
        if obj is not None:  # a removed object's base lingers until the view layer syncs
            obj.select_set(False, view_layer=view_layer)
    for obj in objects:
        if obj.name in view_layer.objects:
            obj.select_set(True, view_layer=view_layer)
    view_layer.objects.active = active if active is not None and active.name in view_layer.objects else None


def _alive(obj):
    """obj, or None if it was removed from Blender."""
    if obj is None:
        return None
    try:
        obj.name
    except ReferenceError:
        return None
    return obj


def reset_state():
    """Object Mode with nothing selected and no active object: the state every Hook starts in."""
    view_layer = bpy.context.view_layer
    _set_mode(view_layer, _alive(view_layer.objects.active), "OBJECT")
    _select(view_layer, [], None)


def object_mode():
    """Back to Object Mode, whatever the active object was doing."""
    view_layer = bpy.context.view_layer
    _set_mode(view_layer, _alive(view_layer.objects.active), "OBJECT")


def switch(obj, mode: str):
    """Makes `obj` the active, only selected object and puts it into `mode`, leaving it there."""
    view_layer = bpy.context.view_layer
    _set_mode(view_layer, _alive(view_layer.objects.active), "OBJECT")
    _select(view_layer, [obj], obj)
    _set_mode(view_layer, obj, mode)
