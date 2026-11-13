"""What the Rigify Hook reads from and changes on the Character's meshes: vertex groups and their
extent, and a shape key copy."""

from __future__ import annotations

from dataclasses import dataclass, field

import bmesh


@dataclass
class Bounds:
    """The world-space extent of a vertex group's vertices; each bound is None if it has none.
    `coordinates` holds every vertex of the mesh in world space, by index."""
    vertices: list = field(default_factory=list)
    coordinates: list = field(default_factory=list)
    min_x: float = None
    min_y: float = None
    min_z: float = None
    max_x: float = None
    max_y: float = None
    max_z: float = None


def group_bounds(obj, group) -> Bounds:
    """The extent of the vertices in `obj`'s vertex group `group`, whatever their weight."""
    coordinates = [obj.matrix_world @ v.co for v in obj.data.vertices]
    index = obj.vertex_groups[group].index
    vertices = [v for v in obj.data.vertices if index in [g.group for g in v.groups]]
    bounds = Bounds(vertices=vertices, coordinates=coordinates)
    for vertex in vertices:
        co = coordinates[vertex.index]
        bounds.min_x = _lower(bounds.min_x, co[0])
        bounds.min_y = _lower(bounds.min_y, co[1])
        bounds.min_z = _lower(bounds.min_z, co[2])
        bounds.max_x = _higher(bounds.max_x, co[0])
        bounds.max_y = _higher(bounds.max_y, co[1])
        bounds.max_z = _higher(bounds.max_z, co[2])
    return bounds


def _lower(current, value):
    return value if current is None or value < current else current


def _higher(current, value):
    return value if current is None or value > current else current


def is_group_empty(obj, group) -> bool:
    """Whether `obj` has no vertex group `group`, or no vertex in it."""
    vertex_group = obj.vertex_groups.get(group)
    if not vertex_group:
        return True
    return not any(vertex_group.index in [g.group for g in v.groups] for v in obj.data.vertices)


def rename_group(meshes, old, new):
    """Renames the vertex group `old` to `new` on each of `meshes` that has it."""
    for obj in meshes:
        group = obj.vertex_groups.get(old)
        if group is not None:
            group.name = new


def weighted_bones(rig, meshes) -> list:
    """The bones of `rig` that a vertex of `meshes` has a nonzero weight for, in the order found."""
    found = []
    for obj in meshes:
        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            layer = bm.verts.layers.deform.active
            seen = []
            if layer is not None:
                for vert in bm.verts:
                    for group, weight in vert[layer].items():
                        if weight != 0 and group not in seen:
                            seen.append(group)
                            bone = rig.pose.bones.get(obj.vertex_groups[group].name)
                            if bone is not None and bone.name not in found:
                                found.append(bone.name)
        finally:
            bm.free()
    return found


def duplicate_shape_key(obj, name, copy_name):
    """A copy of the shape key `name`, at full strength alone, as the new key `copy_name` at 0,
    replacing an earlier copy and the drivers on it."""
    keys = obj.data.shape_keys
    for key in keys.key_blocks:
        if key.name == name:
            key.mute = False
            old_value = key.value
            key.value = 1
        elif key.name == copy_name:
            if keys.animation_data:
                for fcurve in keys.animation_data.drivers:
                    if fcurve.data_path.startswith("key_blocks") and fcurve.data_path.split('"')[1] == key.name:
                        keys.animation_data.drivers.remove(fcurve)
            obj.shape_key_remove(key=key)
        else:
            key.mute = True
    copy = obj.shape_key_add(name=copy_name, from_mix=True)
    copy.value = 0
    for key in obj.data.shape_keys.key_blocks:
        key.mute = False
        if key.name == name:
            key.value = old_value
    return copy
