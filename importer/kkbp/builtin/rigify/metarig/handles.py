"""The handles: control bones in front of the eyes, breasts and buttocks that the bones themselves
copy, each drawn with a widget sized from the vertex groups it moves. In Object Mode; the handle
bones are made in Edit Mode inside `_arrange`."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

import bpy

from .. import bones, constraints, meshes, names, widget_shapes, widgets
from ....editing import editing


@dataclass(frozen=True)
class HandleSet:
    """A middle handle and a left and right one under it."""
    bones: tuple  # the middle, left and right bones the handles move
    handles: tuple  # their handle bones
    groups: tuple  # the left and right vertex groups the widgets and handles are placed from
    snap: bool  # the widgets' geometry is centred on their origin first
    rotate: tuple  # degrees about x, y and z, or None
    move: tuple  # the handles' offset: (along the groups' middle x, their front y, their middle z)
    size: tuple  # the middle widget's scale on x, y and z; the side ones scale towards their own group


EYES = HandleSet((names.EYES_BONE, names.LEFT_EYE_BONE, names.RIGHT_EYE_BONE),
                 (names.EYES_HANDLE_BONE, names.LEFT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_BONE),
                 (names.LEFT_EYE_DEFORM_BONE, names.RIGHT_EYE_DEFORM_BONE),
                 snap=False, rotate=(90, 0, 90), move=(0.93, 1.66427, 1), size=(1.16, 1, 1.65))
BREASTS = HandleSet((names.BREASTS_BONE, names.LEFT_BREAST_BONE1, names.RIGHT_BREAST_BONE1),
                    (names.BREASTS_HANDLE_BONE, names.LEFT_BREAST_HANDLE_BONE, names.RIGHT_BREAST_HANDLE_BONE),
                    (names.LEFT_NIPPLE_DEFORM_BONE1, names.RIGHT_NIPPLE_DEFORM_BONE1),
                    snap=True, rotate=None, move=(0.3, 1.66427, 0.9955), size=(21, 1, 19))
BUTTOCKS = HandleSet((names.BUTTOCKS_BONE, names.LEFT_BUTTOCK_BONE, names.RIGHT_BUTTOCK_BONE),
                     (names.BUTTOCKS_HANDLE_BONE, names.LEFT_BUTTOCK_HANDLE_BONE, names.RIGHT_BUTTOCK_HANDLE_BONE),
                     (names.LEFT_BUTTOCK_DEFORM_BONE, names.RIGHT_BUTTOCK_DEFORM_BONE),
                     snap=True, rotate=None, move=(0, -3.6, 1), size=(30, 1, 25))
# Used when an eye's vertex group reaches no higher than 0 (cf_J_Eye07_s is the lower eyelid's).
EYE_FALLBACK = ("cf_J_Eye07_s_L", "cf_J_Eye07_s_R")
# rigify.blend's breast widgets, which the buttock handles draw too.
BREAST_WIDGETS = (names.ORIGINAL_WIDGET_BREASTS, names.ORIGINAL_WIDGET_BREAST_LEFT, names.ORIGINAL_WIDGET_BREAST_RIGHT)


def widgets_and_handles(build):
    metarig = build.metarig
    widgets.append_library(build)
    eyes = (widgets.make(build, names.WIDGET_EYES, metarig, names.EYES_BONE, widget_shapes.EYES_VERTICES, widget_shapes.EYES_EDGES),
            widgets.make(build, names.WIDGET_EYE_LEFT, metarig, names.LEFT_EYE_BONE, widget_shapes.EYE_VERTICES, widget_shapes.EYE_EDGES),
            widgets.make(build, names.WIDGET_EYE_RIGHT, metarig, names.RIGHT_EYE_BONE, widget_shapes.EYE_VERTICES, widget_shapes.EYE_EDGES))
    _arrange(build, EYES, eyes)
    breasts = _copies(build, (names.WIDGET_BREASTS, names.WIDGET_BREAST_LEFT, names.WIDGET_BREAST_RIGHT), names.BREASTS_BONE)
    if not build.features.male:
        _arrange(build, BREASTS, breasts)
    buttocks = _copies(build, (names.WIDGET_BUTTOCKS, names.WIDGET_BUTTOCK_LEFT, names.WIDGET_BUTTOCK_RIGHT), names.BUTTOCKS_BONE)
    _arrange(build, BUTTOCKS, buttocks)

    _finish(metarig, EYES, eyes, eye=True)
    if not build.features.male:
        _finish(metarig, BREASTS, breasts, eye=False)
    _finish(metarig, BUTTOCKS, buttocks, eye=False)
    # The buttock handles also follow the game's buttock joint corrections.
    name = names.COPY_TRANSFORMS_CONSTRAINT_BASE + names.JOINT_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX
    for handle, correction in ((names.LEFT_BUTTOCK_HANDLE_BONE, names.LEFT_BUTTOCK_JOINT_CORRECTION_BONE),
                               (names.RIGHT_BUTTOCK_HANDLE_BONE, names.RIGHT_BUTTOCK_JOINT_CORRECTION_BONE)):
        constraints.copy_transforms(metarig, handle, correction, name=name, mix="AFTER", space="LOCAL")


def _copies(build, new_names, bone):
    out = []
    for source, name in zip(BREAST_WIDGETS, new_names):
        widget = widgets.copy(build, source, name)
        widgets.place(widget, build.metarig, bone)
        out.append(widget)
    return tuple(out)


def _shape(widget, handle_set):
    if handle_set.snap:
        widgets.geometry_to_origin(widget)
    if handle_set.rotate:
        for axis, degrees in zip("XYZ", handle_set.rotate):
            if degrees:
                widgets.rotate(widget, axis, math.radians(degrees))


def _arrange(build, handle_set, shapes):
    """Shapes the three widgets from the two vertex groups and makes the handle bones, in front of
    the bones they move."""
    bpy.context.view_layer.update()
    middle, left, right = shapes
    body = build.body
    _shape(middle, handle_set)
    lb, rb = (meshes.group_bounds(body, g) for g in handle_set.groups)
    if not lb.max_z or not rb.max_z:
        lb, rb = (meshes.group_bounds(body, g) for g in EYE_FALLBACK)
    mid_z = {"left": (lb.max_z + lb.min_z) / 2, "right": (rb.max_z + rb.min_z) / 2}
    average_mid_z = statistics.mean([mid_z["left"], mid_z["right"]])
    average_min_y = statistics.mean([lb.min_y, rb.min_y])
    mid_x = {"left": (lb.max_x + lb.min_x) / 2, "right": (rb.max_x + rb.min_x) / 2}
    sx, sy, sz = handle_set.size
    widgets.resize(middle, (sx, sy, sz))

    lengths = {side: (b.max_x - b.min_x, b.max_y - b.min_y, b.max_z - b.min_z) for side, b in (("left", lb), ("right", rb))}
    averages = [statistics.mean([lengths["left"][i], lengths["right"][i]]) for i in range(3)]
    for side, widget in (("left", left), ("right", right)):
        _shape(widget, handle_set)
        factors = [statistics.mean([s, s * (lengths[side][i] / averages[i])]) for i, s in enumerate(handle_set.size)]
        widgets.resize(widget, tuple(factors))

    along_x, along_y, along_z = handle_set.move
    bounds = {"left": lb, "right": rb}
    with editing(build.metarig, "EDIT"):
        parent = bones.copy_bone(build.metarig, handle_set.bones[0], handle_set.handles[0])
        parent.tail.y = parent.tail.y + average_min_y * along_y
        parent.head.y = parent.head.y + average_min_y * along_y
        drop = middle.location[2] - average_mid_z * along_z
        parent.tail.z = parent.tail.z - drop
        parent.head.z = parent.head.z - drop
        for side, bone, handle, widget in (("left", handle_set.bones[1], handle_set.handles[1], left),
                                           ("right", handle_set.bones[2], handle_set.handles[2], right)):
            child = bones.copy_bone(build.metarig, bone, handle)
            child.tail.x = child.tail.x + mid_x[side] * along_x
            child.head.x = child.head.x + mid_x[side] * along_x
            child.tail.y = child.tail.y + bounds[side].min_y * along_y
            child.head.y = child.head.y + bounds[side].min_y * along_y
            drop = widget.location[2] - mid_z[side] * along_z
            child.tail.z = child.tail.z - drop
            child.head.z = child.head.z - drop
            child.parent = parent


def _finish(rig, handle_set, shapes, eye):
    """Each handle draws its widget, and its bone copies it. An eye handle moves only across the face."""
    for bone, handle, widget in zip(handle_set.bones, handle_set.handles, shapes):
        pose_bone = rig.pose.bones[handle]
        pose_bone.custom_shape = widget
        if eye:
            pose_bone.lock_location[1] = True
            pose_bone.lock_rotation[0] = True
            pose_bone.lock_rotation[2] = True
            pose_bone.lock_scale[1] = True
        constraints.copy_transforms(rig, bone, handle, name=names.COPY_TRANSFORMS_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX,
                                    mix="REPLACE", space="LOCAL")
