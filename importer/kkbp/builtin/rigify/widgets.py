"""Shaping widget meshes on the data API, as the legacy Rigify script did in Edit Mode with Blender's
transform operators: each transform acts on all the widget's vertices in global space, around the
centre of their bounding box (the legacy pivot point, BOUNDING_BOX_CENTER)."""

from mathutils import Matrix, Vector


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


def translate(obj, value):
    offset = Vector(value)
    _set_world(obj, [co + offset for co in _world(obj)])


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
