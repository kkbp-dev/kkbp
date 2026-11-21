"""Keeps drivers that read a material's dropdown up to date (ADR 0042).

Blender doesn't re-evaluate a driver when a node socket it reads is edited, only when the socket is
keyframed and the frame changes. So while the add-on is enabled, every edit of a menu or integer
socket (Blender's message bus reports edits from the UI and from Python alike) tags the node trees
of the materials that hold a dropdown (`templates.picker`), and their drivers run again.

With several threads, Blender sometimes runs such a driver before the material's new value is in, in
the same update, and then counts it as done: a correction key such as `Gag eyes (Fiery Eyes)` keeps
the old expression's value. So after an update in which a dropdown's values changed, the drivers that
read that material are tagged once more, without the material, and the next update runs them with
the value settled.
"""

import bpy

from . import templates

_OWNER = object()  # the message bus subscriptions' owner
_SOCKETS = ("NodeSocketMenu", "NodeSocketInt")

_seen: dict[int, tuple] = {}  # material pointer -> its dropdown's values when its drivers last ran again


def register():
    _subscribe()
    for handlers, handler in _HANDLERS:
        if handler not in handlers:
            handlers.append(handler)


def unregister():
    for handlers, handler in _HANDLERS:
        if handler in handlers:
            handlers.remove(handler)
    bpy.msgbus.clear_by_owner(_OWNER)
    _seen.clear()


def refresh():
    """Tags every material with a dropdown, so the drivers reading it run again."""
    for material in bpy.data.materials:
        if material.node_tree is not None and templates.picker(material) is not None:
            material.node_tree.update_tag()


def values(material) -> tuple:
    """The material's dropdown's menu and number values."""
    node = templates.picker(material)
    names = templates.template_of(material).patterns.picker
    return node.inputs[names.menu].default_value, node.inputs[names.number].default_value


def readers(material) -> list:
    """The shape keys, objects and node trees with a driver that reads the material."""
    owners = [*bpy.data.shape_keys, *bpy.data.objects,
              *(m.node_tree for m in bpy.data.materials if m.node_tree is not None)]
    return [owner for owner in owners
            if owner.animation_data is not None
            and any(target.id == material for fcurve in owner.animation_data.drivers
                    for variable in fcurve.driver.variables for target in variable.targets)]


def run_again():
    """Tags what reads each dropdown whose values changed since the last time, so its drivers run again
    in the next update. Returns how many dropdowns changed."""
    changed = 0
    for material in bpy.data.materials:
        if material.node_tree is None or templates.picker(material) is None:
            continue
        now = values(material)
        if _seen.get(material.as_pointer()) == now:
            continue
        _seen[material.as_pointer()] = now
        changed += 1
        for owner in readers(material):
            owner.update_tag()
    return changed


def _subscribe():
    bpy.msgbus.clear_by_owner(_OWNER)
    for name in _SOCKETS:
        bpy.msgbus.subscribe_rna(key=(getattr(bpy.types, name), "default_value"), owner=_OWNER, args=(),
                                 notify=refresh)


@bpy.app.handlers.persistent
def _after_update(scene, depsgraph):
    # Runs after every update, including the one its tags make, which changes no material.
    if any(isinstance(u.id, (bpy.types.Material, bpy.types.ShaderNodeTree)) for u in depsgraph.updates):
        run_again()


@bpy.app.handlers.persistent
def _after_load(*_):
    """Loading a file clears the message bus, and the materials are new."""
    _seen.clear()
    _subscribe()


_HANDLERS = ((bpy.app.handlers.depsgraph_update_post, _after_update),
             (bpy.app.handlers.load_post, _after_load))
