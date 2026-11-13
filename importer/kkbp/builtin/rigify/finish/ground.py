"""Feet on the ground (ADR 0027): the rig moves so the lowest vertex of the visible meshes on it is at
z = 0. The legacy script put the root 4 cm under the left ankle instead, which sank the KK sample's
shoes 1.9 cm under the floor."""

from __future__ import annotations

import bpy
import numpy as np
from mathutils import Matrix

from ....editing import editing


def lowest_point(rig):
    """The lowest world Z of the visible meshes parented to the rig (the Character's Parts; hidden
    Outfits don't count), or 0 if there are none."""
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
    local = rig.matrix_world.to_3x3().inverted() @ offset
    with editing(rig):
        # Read first: setting a bone's tail moves its connected children's heads too.
        moved = [(bone, bone.head + local, bone.tail + local) for bone in rig.data.edit_bones]
        for bone, head, tail in moved:
            bone.head, bone.tail = head, tail
    for child in rig.children:
        if child.parent_type == "OBJECT":
            child.matrix_parent_inverse = Matrix.Translation(local) @ child.matrix_parent_inverse
