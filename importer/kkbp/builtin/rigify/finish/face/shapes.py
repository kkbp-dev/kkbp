"""Small helpers the face rig's parts share: new bones, their widgets, limits and collections.

Control bones point up the world Z with local X = world +X, so a control moves sideways on local X
and up on local Y; widgets are drawn in that plane, in metres (not bone lengths)."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

from ... import bone_collections


def new_bone(edit, name, head, *, parent=None, length=0.01, forward=False):
    """An edit bone at `head`: pointing up (local Z facing the viewer) or, with `forward`, out of the
    face (-Y). It doesn't deform."""
    bone = edit.new(name)
    head = Vector(head)
    bone.head = head
    if forward:
        bone.tail = head + Vector((0.0, -length, 0.0))
        bone.align_roll(Vector((0.0, 0.0, 1.0)))
    else:
        bone.tail = head + Vector((0.0, 0.0, length))
        bone.align_roll(Vector((0.0, -1.0, 0.0)))
    bone.use_deform = False
    if parent is not None:
        bone.parent = edit[parent]
    return bone


def widget(build, rig, bone, shape, *, color=None, wire=1.5):
    """Draws `bone` with `shape`, (points, edges) in the bone's X/Y plane, kept in the Character's
    widget collection."""
    points, edges = shape
    name = f"WGT-{rig.name}_{bone}"
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([(p[0], p[1], 0.0) for p in points], edges, [])
    obj = bpy.data.objects.new(name, mesh)
    build.widgets.objects.link(obj)
    pose_bone = rig.pose.bones[bone]
    pose_bone.custom_shape = obj
    pose_bone.use_custom_shape_bone_size = False
    pose_bone.custom_shape_wire_width = wire
    if color is not None:
        pose_bone.color.palette = "CUSTOM"
        pose_bone.color.custom.normal = color
        pose_bone.color.custom.select = tuple(min(1.0, c + 0.35) for c in color)
        pose_bone.color.custom.active = (1.0, 1.0, 1.0)
    return obj


def lock(pose_bone, location=(True, True, True), rotation=True, scale=True):
    pose_bone.lock_location = location
    pose_bone.lock_rotation = (rotation,) * 3
    pose_bone.lock_rotation_w = rotation
    pose_bone.lock_scale = (scale,) * 3


def limit_location(pose_bone, x=None, y=None):
    """A local limit on x and y, (min, max) each, that also limits moving the bone by hand."""
    c = pose_bone.constraints.new("LIMIT_LOCATION")
    c.owner_space = "LOCAL"
    c.use_transform_limit = True
    for axis, limits in (("x", x), ("y", y)):
        if limits is not None:
            setattr(c, f"use_min_{axis}", True)
            setattr(c, f"use_max_{axis}", True)
            setattr(c, f"min_{axis}", limits[0])
            setattr(c, f"max_{axis}", limits[1])
    return c


def limit_scale(pose_bone, low, high):
    c = pose_bone.constraints.new("LIMIT_SCALE")
    c.owner_space = "LOCAL"
    c.use_transform_limit = True
    for axis in "xyz":
        setattr(c, f"use_min_{axis}", True)
        setattr(c, f"use_max_{axis}", True)
        setattr(c, f"min_{axis}", low)
        setattr(c, f"max_{axis}", high)
    return c


def collection(rig, name, *, row, visible=True):
    """The rig's bone collection `name`, made if missing, in Rigify panel row `row`."""
    found = rig.data.collections_all.get(name) or rig.data.collections.new(name)
    found.rigify_ui_row = row
    found.is_visible = visible
    return found


def put(rig, bone, name):
    bone_collections.move(rig, bone, name)


# --- shapes: (points, edges) ---------------------------------------------------------------------

def loop(points):
    return list(points), [(i, (i + 1) % len(points)) for i in range(len(points))]


def circle(r, n=24):
    return loop([(r * math.cos(2 * math.pi * i / n), r * math.sin(2 * math.pi * i / n)) for i in range(n)])


def rect(x0, y0, x1, y1):
    return loop([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def rounded(w, h, r, n=6):
    points = []
    for cx, cy, start in ((w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                          (w / 2 - r, -h / 2 + r, 270)):
        for i in range(n + 1):
            a = math.radians(start + 90 * i / n)
            points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return loop(points)


def diamond(r):
    return loop([(r, 0.0), (0.0, r), (-r, 0.0), (0.0, -r)])


def star(outer, inner, n=5):
    return loop([((outer if i % 2 == 0 else inner) * math.cos(math.pi / 2 + i * math.pi / n),
                  (outer if i % 2 == 0 else inner) * math.sin(math.pi / 2 + i * math.pi / n)) for i in range(2 * n)])


def arrows(r, gap, up=True, down=True, side=0):
    """Chevrons around a centre for the ways a control moves: up, down, and out to one `side` (+1
    or -1)."""
    points, edges = [], []

    def chevron(a, b, c):
        i = len(points)
        points.extend((a, b, c))
        edges.extend(((i, i + 1), (i + 1, i + 2)))
    if up:
        chevron((-r, gap), (0.0, gap + r), (r, gap))
    if down:
        chevron((-r, -gap), (0.0, -gap - r), (r, -gap))
    if side:
        chevron((side * gap, -r), (side * (gap + r), 0.0), (side * gap, r))
    return points, edges


def combine(*shapes):
    points, edges = [], []
    for p, e in shapes:
        offset = len(points)
        points.extend(p)
        edges.extend((a + offset, b + offset) for a, b in e)
    return points, edges
