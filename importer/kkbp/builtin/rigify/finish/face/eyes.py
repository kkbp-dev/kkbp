"""The Eyes layer: one look-at target with a per-eye offset under it. The eyes stay texture-based: the
two UV warp modifiers prepare.py put on Body get drivers on their offset (from where each eye aims)
and scale (from the targets' scale: the iris size). Looking down closes the lids a little.

The gain is measured from the mesh: a least-squares fit of `uv_main` against world X and Z over
each eye's vertices says which UV offset moves the iris a given distance across the face, so an
eye looking half a radian to the side moves its iris about half the eye's width.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from mathutils import Vector

from .....editing import editing
from ... import constraints, drivers, names, prepare
from . import shapes
from .terms import Term, channel, driver, prop

HEAD = names.ORIGINAL_BONE_PREFIX + names.HEAD_BONE
DISTANCE = 0.35  # metres from the eyes' front to the target
COLOR = (0.95, 0.75, 0.2)
SIDES = (("L", "eye_l", names.LEFT_EYE_TARGET_BONE, names.LEFT_EYE_AIM_BONE),
         ("R", "eye_r", names.RIGHT_EYE_TARGET_BONE, names.RIGHT_EYE_AIM_BONE))
FOLLOW_HEAD, LID_FOLLOW = "follow_head", "lid_follow"


@dataclass
class Eye:
    centre: Vector
    front: float  # the eye's frontmost y
    half_width: float
    half_height: float
    uv_fit: np.ndarray  # 2x2: d(u, v) / d(x, z)
    uv_centre: tuple


def measure(body) -> dict:
    """Each eye's shape and UV gradient, from the vertices of its vertex group, by side."""
    mesh = body.data
    uv = mesh.uv_layers[prepare.UV_MAP].data
    out = {}
    for side, role, _, _ in SIDES:
        group = body.vertex_groups.get(prepare.EYE_GROUPS[role])
        if group is None:
            return {}
        members = {v.index for v in mesh.vertices if any(g.group == group.index and g.weight > 0.5 for g in v.groups)}
        if not members:
            return {}
        world = body.matrix_world
        co = np.array([tuple(world @ mesh.vertices[i].co) for i in sorted(members)])
        rows, uvs = [], []
        for loop in mesh.loops:
            if loop.vertex_index in members:
                p = world @ mesh.vertices[loop.vertex_index].co
                rows.append((p.x, p.z, 1.0))
                uvs.append(tuple(uv[loop.index].uv))
        fit, *_ = np.linalg.lstsq(np.array(rows), np.array(uvs), rcond=None)
        out[side] = Eye(Vector(co.mean(axis=0)), float(co[:, 1].min()), float(np.ptp(co[:, 0]) / 2),
                        float(np.ptp(co[:, 2]) / 2), fit[:2].T, tuple(np.array(uvs).mean(axis=0)))
    return out


def build(build, eyes) -> list:
    """The eye targets, the aim bones and the UV warp drivers; returns the lid-follow terms for the
    blink keys."""
    rig, body = build.rig, build.body
    z = (eyes["L"].centre.z + eyes["R"].centre.z) / 2
    y = min(eyes["L"].front, eyes["R"].front) - DISTANCE
    with editing(rig, "EDIT"):
        edit = rig.data.edit_bones
        # no bone parent: its Armature constraint is the parent, so root moves it once
        shapes.new_bone(edit, names.EYE_TARGET_PARENT_BONE, (0, y, z), length=0.02)
        shapes.new_bone(edit, names.EYE_TARGET_BONE, (0, y, z), parent=names.EYE_TARGET_PARENT_BONE, length=0.02)
        for side, _, target, aim in SIDES:
            c = eyes[side].centre
            child = shapes.new_bone(edit, target, (c.x, y, c.z), parent=names.EYE_TARGET_BONE, length=0.015)
            child.inherit_scale = "NONE"  # the main target's scale sizes the irises, not the eyes' spacing
            shapes.new_bone(edit, aim, tuple(c), parent=HEAD, length=0.02, forward=True)
    shapes.collection(rig, names.EYES_LAYER, row=10)
    for bone in (names.EYE_TARGET_BONE, names.LEFT_EYE_TARGET_BONE, names.RIGHT_EYE_TARGET_BONE):
        shapes.put(rig, bone, names.EYES_LAYER)
    for bone in (names.EYE_TARGET_PARENT_BONE, names.LEFT_EYE_AIM_BONE, names.RIGHT_EYE_AIM_BONE):
        shapes.put(rig, bone, names.MCH_LAYER_INDEX)

    follow = drivers.bone_property(rig, names.EYE_TARGET_BONE, FOLLOW_HEAD, default=1.0, min=0.0, max=1.0,
                                   description="1: the eye target moves with the head. 0: it stays where it is")
    lids = drivers.bone_property(rig, names.EYE_TARGET_BONE, LID_FOLLOW, default=0.4, min=0.0, max=1.0,
                                 description="How much the eyelids close as the eyes look down")
    # The parent follows root, or the head as `follow_head` goes to 1: a blend of the two, not the
    # head on top of root, which moved the target twice as far as root.
    parent = constraints.armature(rig, names.EYE_TARGET_PARENT_BONE, [names.ROOT_BONE, HEAD],
                                  name=names.ARMATURE_CONSTRAINT_BASE + names.PARENT_CONSTRAINT_SUFFIX)
    driver(parent.targets[0], "weight", "1-f", [("f", prop(rig, follow))])
    driver(parent.targets[1], "weight", "f", [("f", prop(rig, follow))])

    main = rig.pose.bones[names.EYE_TARGET_BONE]
    shapes.lock(main, location=(False, False, False), scale=False)
    shapes.limit_scale(main, 0.5, 1.6)
    width = eyes["L"].centre.x - eyes["R"].centre.x
    shapes.widget(build, rig, main.name, shapes.rounded(width + 0.06, 0.05, 0.02), color=COLOR, wire=2.0)
    for side, _, target, aim in SIDES:
        pose_bone = rig.pose.bones[target]
        shapes.lock(pose_bone, location=(False, False, True), scale=False)
        shapes.limit_scale(pose_bone, 0.5, 1.6)
        shapes.widget(build, rig, target, shapes.combine(shapes.circle(0.014), shapes.circle(0.004)), color=COLOR)
        track = rig.pose.bones[aim].constraints.new("DAMPED_TRACK")
        track.target, track.subtarget, track.track_axis = rig, target, "TRACK_Y"

    lid_terms = []
    warps = {m.name: m for m in body.modifiers if m.type == "UV_WARP"}
    for side, role, target, aim in SIDES:
        eye = eyes[side]
        warp = warps.get(prepare.UV_WARPS[role])
        if warp is None:
            continue
        warp.center = eye.uv_centre
        m = rig.data.bones[aim].matrix_local.to_3x3()
        # how the look direction moves per radian of swing about the aim's local X and Z
        d_rx, d_rz = m.col[2], -m.col[0]
        travel = np.array([[eye.half_width * d_rx.x, eye.half_width * d_rz.x],
                           [eye.half_height * d_rx.z, eye.half_height * d_rz.z]])
        gain = -eye.uv_fit @ travel  # uv offset per (rx, rz)
        swing = [("rx", channel(rig, aim, "ROT_X", rotation_mode="SWING_TWIST_Y")),
                 ("rz", channel(rig, aim, "ROT_Z", rotation_mode="SWING_TWIST_Y"))]
        for i in range(2):
            driver(warp, "offset", f"{round(float(gain[i, 0]), 5)}*rx+{round(float(gain[i, 1]), 5)}*rz", swing,
                   index=i)
        size = [("s", channel(rig, target, "SCALE_AVG")), ("t", channel(rig, names.EYE_TARGET_BONE, "SCALE_AVG"))]
        for i in range(2):
            driver(warp, "scale", "1/max(0.1,s*t)", size, index=i)
        if side == "L":
            # looking down by half a radian closes the lids by `lid_follow`
            down = (-round(d_rx.z, 5), -round(d_rz.z, 5))
            lid_terms.append(Term(f"{{f}}*max(0,({down[0]}*{{rx}}+{down[1]}*{{rz}})*2)",
                                  {"f": prop(rig, lids), "rx": swing[0][1], "rz": swing[1][1]}))
    return lid_terms
