"""Teeth bones (issue #42): five controls along each row of teeth, when the Hook's `teeth_bones`
option is on.

The teeth are the faces with the `teeth` Material Role. Their two rows are told apart by which
piece of the mesh a vertex is in, not by height, because the rows overlap in height. Each row gets a
control at its middle, at each end and halfway between, placed by the angle around the row's arch.

A game weights the teeth to its mouth bones (KK to six of them, SVS to one). Those weights stay
true: under each mouth bone a control's vertices follow, the control gets a hidden bone that copies
the control's own movement, and the vertices' weight for the mouth bone moves to it, shared between
the two nearest controls. So with the controls at rest the teeth move exactly as they did.

`add_bones` runs in Edit Mode and `rig` in Object Mode.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mathutils import Vector

from ....character import ROLE
from .. import bone_collections, constraints, names

TEETH = "teeth"  # the Material Role
LENGTH = 0.004  # of each new bone, which points up as the mouth bones do; its sphere widget is half as wide
MERGE = 5  # vertices at the same place to this many decimals are one, across UV and normal seams
MIN_VERTICES = 3  # a row with fewer can't be laid along an arch
CONSTRAINT = "Teeth control"
# The collection of the mouth's own controls, where the lists phase gives each bone a sphere widget.
COLLECTION = names.ORIGINAL_LOWER_FACE_LAYER_INDEX


@dataclass
class Vertex:
    obj: object
    index: int
    position: Vector  # in the metarig's space, at rest
    weights: dict  # mouth bone -> weight
    along: float = 0.0  # 0 at the row's left end, 1 at its right end


@dataclass
class Plan:
    """What `add_bones` made, for `rig`."""
    controls: list = field(default_factory=list)
    mechanism: dict = field(default_factory=dict)  # (control, mouth bone) -> hidden bone
    shares: list = field(default_factory=list)  # (Vertex, {control: share})


def add_bones(build) -> Plan | None:
    """Makes the controls and their hidden bones on the metarig. In Edit Mode."""
    metarig = build.metarig
    edit = metarig.data.edit_bones
    plan = Plan()
    for row, vertices in zip(names.TEETH_ROWS, _rows(build)):
        vertices = [v for v in vertices if v.weights]
        if len(vertices) < MIN_VERTICES or not _lay_along(vertices):
            build.log.warning(f"Found no {row} row of teeth weighted to bones, so it gets no teeth bones")
            continue
        totals = {}
        for vertex in vertices:
            for bone, weight in vertex.weights.items():
                totals[bone] = totals.get(bone, 0.0) + weight
        parent = max(totals, key=totals.get)  # the mouth bone that moves the row most
        controls = []
        for i, place in enumerate(names.TEETH_PLACES):
            near = [v.position for v in vertices if _share(v.along, i) > 0.5]
            if not near:
                near = [max(vertices, key=lambda v: _share(v.along, i)).position]
            head = sum(near, Vector()) / len(near)
            control = _bone(edit, names.teeth_bone(row, place), head, parent)
            controls.append(control)
            plan.controls.append(control)
        for vertex in vertices:
            shares = {c: _share(vertex.along, i) for i, c in enumerate(controls)}
            shares = {c: s for c, s in shares.items() if s > 0}
            plan.shares.append((vertex, shares))
            for control in shares:
                for bone in vertex.weights:
                    if (control, bone) not in plan.mechanism:
                        plan.mechanism[control, bone] = _bone(
                            edit, names.teeth_mechanism_bone(control, bone), edit[control].head, bone)
    if not plan.controls:
        return None
    build.log.info(f"Teeth bones: {len(plan.controls)} controls, with {len(plan.mechanism)} hidden bones under "
                   f"the mouth bones that move {len(plan.shares)} teeth vertices")
    return plan


def rig(build, plan):
    """Puts the controls with the mouth's, has each hidden bone copy its control, and moves the teeth
    vertices' weights onto the hidden bones. In Object Mode."""
    if plan is None:
        return
    metarig = build.metarig
    for control in plan.controls:
        bone_collections.move(metarig, control, COLLECTION)
    for (control, _), bone in plan.mechanism.items():
        constraints.copy_transforms(metarig, bone, control, name=CONSTRAINT, mix="REPLACE", space="LOCAL")
    for vertex, shares in plan.shares:
        groups = vertex.obj.vertex_groups
        for bone, weight in vertex.weights.items():
            groups[bone].remove([vertex.index])
            for control, share in shares.items():
                name = plan.mechanism[control, bone]
                (groups.get(name) or groups.new(name=name)).add([vertex.index], weight * share, "REPLACE")


def _bone(edit, name, head, parent):
    bone = edit.new(name)
    bone.head = head
    bone.tail = head + Vector((0.0, 0.0, LENGTH))
    bone.roll = 0.0
    bone.parent = edit[parent]
    bone.use_connect = False
    return bone.name


def _share(along, place) -> float:
    """How much of a vertex `along` its row the control at `place` moves: all of it at the control,
    none at the next one."""
    gaps = len(names.TEETH_PLACES) - 1
    return max(0.0, 1.0 - abs(along * gaps - place))


def _lay_along(vertices) -> bool:
    """Sets each vertex's `along` from its angle around the arch, seen from the middle of the arch's
    open end at the back. False if the row has no width to measure."""
    xs = [v.position.x for v in vertices]
    middle, back = (min(xs) + max(xs)) / 2, max(v.position.y for v in vertices)
    # The Character faces -y with its left at +x: 0 at the left end, pi at the right.
    angles = [math.atan2(back - v.position.y, v.position.x - middle) for v in vertices]
    low, high = min(angles), max(angles)
    if high - low < 1e-6:
        return False
    for vertex, angle in zip(vertices, angles):
        vertex.along = (angle - low) / (high - low)
    return True


def _rows(build) -> tuple:
    """The teeth vertices of the upper and of the lower row: each connected piece goes to the row its
    middle is in."""
    bones = build.metarig.data.bones
    to_metarig = build.metarig.matrix_world.inverted()
    pieces = []
    for obj in build.meshes():
        slots = {i for i, s in enumerate(obj.material_slots) if s.material is not None and s.material.get(ROLE) == TEETH}
        if not slots:
            continue
        matrix = to_metarig @ obj.matrix_world
        group_names = {g.index: g.name for g in obj.vertex_groups}
        pieces += _pieces(obj, slots, matrix, {i: n for i, n in group_names.items() if n in bones})
    if not pieces:
        return [], []
    heights = [v.position.z for piece in pieces for v in piece]
    middle = (min(heights) + max(heights)) / 2
    upper, lower = [], []
    for piece in pieces:
        height = sum(v.position.z for v in piece) / len(piece)
        (upper if height >= middle else lower).extend(piece)
    return upper, lower


def _pieces(obj, slots, matrix, bone_groups) -> list:
    """`obj`'s vertices in the faces of `slots`, as one list of Vertex per connected piece."""
    mesh = obj.data
    place, joined = {}, {}

    def root(key):
        while joined.setdefault(key, key) != key:
            joined[key] = joined[joined[key]]
            key = joined[key]
        return key

    for polygon in mesh.polygons:
        if polygon.material_index not in slots:
            continue
        keys = []
        for index in polygon.vertices:
            if index not in place:
                place[index] = tuple(round(c, MERGE) for c in mesh.vertices[index].co)
            keys.append(place[index])
        for key in keys[1:]:
            joined[root(key)] = root(keys[0])
    pieces = {}
    for index, key in place.items():
        vertex = mesh.vertices[index]
        weights = {bone_groups[g.group]: g.weight for g in vertex.groups if g.group in bone_groups and g.weight > 0}
        pieces.setdefault(root(key), []).append(Vertex(obj, index, matrix @ vertex.co, weights))
    return list(pieces.values())
