"""Shaping widget meshes on the data API, as the legacy Rigify script did in Edit Mode with Blender's
transform operators: each transform acts on all the widget's vertices in global space, around the
centre of their bounding box (the legacy pivot point, BOUNDING_BOX_CENTER). Also where the widgets
come from: rigify.blend's Bone Widgets collection, appended into the Character's Collection."""

import bpy
from mathutils import Euler, Matrix, Vector

from ... import appending
from ...library import hook_assets


def append_library(build):
    """Appends the Bone Widgets collection from rigify.blend into the Character's Collection and
    keeps it as `build.widgets`."""
    added = appending.append(hook_assets.RIGIFY.path, "collections", hook_assets.RIGIFY.collection,
                             hook_assets.VERSION_PROP)
    widgets = next(c for c in added if appending.base_name(c.name) == hook_assets.RIGIFY.collection)
    build.character.collection.children.link(widgets)
    build.widgets = widgets
    return widgets


def _world(obj):
    matrix = obj.matrix_world
    return [matrix @ v.co for v in obj.data.vertices]


def _set_world(obj, cos):
    inverse = obj.matrix_world.inverted()
    for v, co in zip(obj.data.vertices, cos):
        v.co = inverse @ co
    obj.data.update()


def _centre(cos):
    if not cos:
        return Vector((0.0, 0.0, 0.0))
    return Vector([(min(co[i] for co in cos) + max(co[i] for co in cos)) / 2 for i in range(3)])


def rotate(obj, axis, radians):
    cos = _world(obj)
    centre, rotation = _centre(cos), Matrix.Rotation(radians, 3, axis)
    _set_world(obj, [centre + rotation @ (co - centre) for co in cos])


def resize(obj, factors):
    cos = _world(obj)
    centre = _centre(cos)
    _set_world(obj, [centre + Vector([(co[i] - centre[i]) * factors[i] for i in range(3)]) for co in cos])


def geometry_to_origin(obj):
    """Moves the mesh so the centre of its bounds is the object's origin (Origin > Geometry to Origin)."""
    cos = [v.co.copy() for v in obj.data.vertices]
    centre = _centre(cos)
    for v in obj.data.vertices:
        v.co -= centre
    obj.data.update()


def place(obj, rig, bone):
    """Puts `obj` where the pose bone `bone` draws its custom shape, in Object Mode."""
    pose_bone = rig.pose.bones[bone]
    scale = Vector(pose_bone.custom_shape_scale_xyz)
    if pose_bone.use_custom_shape_bone_size:
        scale *= pose_bone.length
    obj.rotation_mode = "XYZ"
    shape = Matrix.LocRotScale(pose_bone.custom_shape_translation, Euler(pose_bone.custom_shape_rotation_euler), scale)
    obj.matrix_basis = rig.matrix_world @ pose_bone.bone.matrix_local @ shape


def make(build, name, rig, bone, vertices, edges):
    """A new widget object `name` of `vertices` and `edges`, in the Character's widget collection,
    placed at `bone`. Another Character's widget of the same name is left alone (Blender adds .001)."""
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    build.widgets.objects.link(obj)
    place(obj, rig, bone)
    mesh.from_pydata(vertices, edges, [])
    mesh.update()
    return obj


def copy(build, source, name):
    """A copy, with its own mesh, of the Character's widget `source`, as `name`."""
    original = build.widget(source)
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = name
    build.widgets.objects.link(obj)
    return obj
