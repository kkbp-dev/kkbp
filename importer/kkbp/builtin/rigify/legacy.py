"""What the legacy importer's `common` module gave the Rigify scripts, for the Character being rigged.

The scripts in before.py, after.py and commons.py are the legacy importer's own, ported with as few
changes as possible (D23): they find bones by the legacy names the Hook gives them, and everything
they asked `common` for comes from here instead, through Character. `begin` is called before each
run.
"""

from __future__ import annotations

import bpy

from ... import appending
from ...character import OUTFIT
from ...editing import editing
from ...editing import switch as _switch
from ...library import hook_assets

_state: dict = {}


def begin(ctx, kk_extras: bool):
    """Binds this module to the Character being rigged. `kk_extras`: whether the skeleton has the
    joint-correction bones the KK-only parts need (ADR 0022)."""
    _state.clear()
    _state.update(ctx=ctx, character=ctx.character, kk_extras=kk_extras)


def character():
    return _state["character"]


# --- what `common` gave --------------------------------------------------------------------

def get_body():
    return character().body


def get_name():
    return character().name


def get_armature():
    return character().armature


def get_rig():
    return character().rig


def get_outfits():
    return list(character().outfits)


def get_hairs():
    return list(character().hairs)


def is_kk():
    """Not a Game check: whether the KK-only parts run, from the skeleton (ADR 0022)."""
    return _state["kk_extras"]


def kklog(message, type="info"):
    log = _state["ctx"].log
    {"warn": log.warning, "error": log.warning}.get(type, log.info)(str(message))


def switch(obj, mode):
    _switch(obj, mode.upper())


def mode(mode):
    """`bpy.ops.object.mode_set` for the active object, as the legacy scripts used it."""
    obj = bpy.context.view_layer.objects.active
    _switch(obj, mode.upper())


def get_layer_collection_from_name(layer, name):
    if layer.name == name:
        return layer
    for child in layer.children:
        found = get_layer_collection_from_name(child, name)
        if found is not None:
            return found
    return None


def import_from_library_file(category, names, use_fake_user=False):
    """The Bone Widgets collection, from rigify.blend into the Character's Collection."""
    assert category == "Collection" and list(names) == [hook_assets.RIGIFY.collection], (category, names)
    added = appending.append(hook_assets.RIGIFY.path, "collections", hook_assets.RIGIFY.collection,
                             hook_assets.VERSION_PROP)
    widgets = next(c for c in added if appending.base_name(c.name) == hook_assets.RIGIFY.collection)
    character().collection.children.link(widgets)
    _state["widgets"] = widgets
    return widgets


def widget_collection():
    """The Character's copy of the Bone Widgets collection."""
    return _state["widgets"]


def widget(name):
    """The Character's widget object `name` (the scripts looked widgets up by name)."""
    return next(o for o in widget_collection().all_objects if appending.base_name(o.name) == name)


# --- what the scripts found by scanning the scene ------------------------------------------

def mesh_objects():
    """The Character's meshes: the scripts scanned `bpy.context.scene.objects`, which would reach
    other Characters."""
    return [o for o in character().parts() if o.type == "MESH"]


def outfit_of(idblock):
    """The Outfit index of a Part or bone (D29), or None."""
    value = idblock.get(OUTFIT)
    return value if isinstance(value, int) else None


def face_bone_names():
    """The face bones whose widgets the rig turns: the legacy importer listed KK's by name; they are
    the bones of the face Bone Groups outside the tongue."""
    skeleton = _state["ctx"].bundle.skeleton
    root = skeleton.by_role("tongue_root")
    tongue = _subtree(skeleton, root.id) if root else set()
    return [b.id for b in skeleton.bones if b.group in ("face", "eye", "eyebrow", "mouth") and b.id not in tongue]


def _subtree(skeleton, root_id):
    children = {}
    for b in skeleton.bones:
        children.setdefault(b.parent, []).append(b.id)
    found, todo = set(), [root_id]
    while todo:
        bone = todo.pop()
        found.add(bone)
        todo.extend(children.get(bone, ()))
    return found


def copy_tags(source, target):
    """The bundle Id and Outfit a generated rig bone takes from its ORG- bone."""
    for prop in ("id", OUTFIT):
        if prop in source:
            target[prop] = source[prop]


def lowest_point(rig):
    """The lowest world Z of the visible meshes parented to the rig (the Character's Parts; hidden
    Outfits don't count), or 0 if there are none."""
    import numpy as np

    bpy.context.view_layer.update()
    lowest = None
    for obj in rig.children:
        if obj.type != "MESH" or not obj.visible_get() or not obj.data.vertices:
            continue
        co = np.empty(len(obj.data.vertices) * 3, dtype=np.float64)
        obj.data.vertices.foreach_get("co", co)
        world = np.array(obj.matrix_world)
        z = float((co.reshape(-1, 3) @ world[2, :3] + world[2, 3]).min())
        lowest = z if lowest is None else min(lowest, z)
    return lowest if lowest is not None else 0.0


def move_rig(rig, offset):
    """Moves the rig's bones and everything parented to the rig by `offset` (world space), keeping
    the rig object and each child's own location where they are: what the legacy origin_set and
    location reset did, the children following through their parent inverse.

    The bones move as edit bones, so leaving Edit Mode rebuilds the pose; moved with
    `rig.data.transform`, the pose stayed where the bones had been until the next mode change."""
    from mathutils import Matrix

    local = rig.matrix_world.to_3x3().inverted() @ offset
    with editing(rig):
        # Read first: setting a bone's tail moves its connected children's heads too.
        moved = [(bone, bone.head + local, bone.tail + local) for bone in rig.data.edit_bones]
        for bone, head, tail in moved:
            bone.head, bone.tail = head, tail
    for child in rig.children:
        if child.parent_type == "OBJECT":
            child.matrix_parent_inverse = Matrix.Translation(local) @ child.matrix_parent_inverse
