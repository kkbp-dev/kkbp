"""Keeps drivers that read a material's dropdown up to date (ADR 0042).

Blender doesn't re-evaluate a driver when a node socket it reads is edited, only when the socket is
keyframed and the frame changes. So while the add-on is enabled, every edit of a menu or integer
socket (Blender's message bus reports edits from the UI and from Python alike) tags the node trees
of the materials that hold a dropdown (`templates.picker`), and their drivers run again.
"""

import bpy

from . import templates

_OWNER = object()  # the message bus subscriptions' owner
_SOCKETS = ("NodeSocketMenu", "NodeSocketInt")


def register():
    _subscribe()
    if _resubscribe not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_resubscribe)


def unregister():
    if _resubscribe in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_resubscribe)
    bpy.msgbus.clear_by_owner(_OWNER)


def refresh():
    """Tags every material with a dropdown, so the drivers reading it run again."""
    for material in bpy.data.materials:
        if material.node_tree is not None and templates.picker(material) is not None:
            material.node_tree.update_tag()


def _subscribe():
    bpy.msgbus.clear_by_owner(_OWNER)
    for name in _SOCKETS:
        bpy.msgbus.subscribe_rna(key=(getattr(bpy.types, name), "default_value"), owner=_OWNER, args=(),
                                 notify=refresh)


@bpy.app.handlers.persistent
def _resubscribe(*_):
    """Loading a file clears the message bus."""
    _subscribe()
