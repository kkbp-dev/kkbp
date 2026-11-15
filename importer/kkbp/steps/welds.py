"""Weld Steps: the copies of a vertex the exporter wrote become one vertex (ADR 0047).

A UV seam or a hard edge needs two glTF vertices where Blender wants one. The exporter gives each group
of copies one position, one set of weights and one offset per shape key; these Steps weld each group
into one vertex, keeping every face corner's normal and UVs. Copies are vertices within WELD_DISTANCE:
the exporter writes them at one position, and the glTF importer's skinning into the bind pose leaves
them a few nanometres apart.

Copies are welded within each mesh as it was loaded, so an eyeline on the face or a nail on the body
stays its own surface, and on Body between the face and body materials, where the neck meets. Two
vertices of one face are never welded, nor the vertices of two faces that would then be one face (the
back of a double-sided card). The exporter groups copies by the same rules.
"""

from __future__ import annotations

import bmesh
import numpy as np
from mathutils import kdtree

from .mesh import _meshes, _role

# In metres: far more than the glTF importer's rounding, far less than the exporter's 0.01 mm.
WELD_DISTANCE = 1e-6
# The Material Roles whose vertices weld across meshes, at the neck.
NECK = ("face", "body")
NORMALS = "kkbp_corner_normals"  # the attribute the normals cross the weld in, removed after


def weld_copies(ctx):
    """Welds each mesh's copies, before `build_parts` joins the meshes of one Part Role."""
    welded = 0
    for obj in _meshes(ctx.character):
        welded += weld(obj.data, _groups(obj.data))
    ctx.log.info(f"Welded {welded} copies of vertices")


def weld_neck(ctx):
    """Welds Body's face vertices onto the body vertices at the same place."""
    body = ctx.character.body
    if body is None:
        return
    roles = [_role(ctx.bundle, s.material) for s in body.material_slots]
    on = {role: set() for role in NECK}
    for p in body.data.polygons:
        role = roles[p.material_index] if p.material_index < len(roles) else None
        if role in on:
            on[role].update(p.vertices)
    face, other = on["face"] - on["body"], on["body"] - on["face"]
    welded = weld(body.data, _groups(body.data, face, other))
    ctx.log.info(f"Welded {welded} face vertices onto the body at the neck")


def _groups(mesh, first=None, second=None):
    """Groups of vertex indices within WELD_DISTANCE of each other: any two vertices, or with `first`
    and `second`, one of each. No group holds two vertices of one face."""
    count = len(mesh.vertices)
    co = np.empty(count * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    targets = range(count) if second is None else sorted(second)
    if not targets:
        return []
    tree = kdtree.KDTree(len(targets))
    for i in targets:
        tree.insert(co[i], i)
    tree.balance()
    neighbours = [set() for _ in range(count)]
    for p in mesh.polygons:
        vs = list(p.vertices)
        for v in vs:
            neighbours[v].update(vs)
    parent = list(range(count))
    members = {}

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    def unite(a, b):
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        ma, mb = members.get(ra, [ra]), members.get(rb, [rb])
        if any(find(n) == rb for v in ma for n in neighbours[v]):
            return  # it would collapse a face
        parent[rb] = ra
        members[ra] = ma + mb
        members.pop(rb, None)

    for v in (range(count) if first is None else sorted(first)):
        for _, other, _ in tree.find_range(co[v], WELD_DISTANCE):
            if other != v:
                unite(v, other)

    apart = set()
    changed = True
    while changed:
        changed = False
        seen = {}
        for p in mesh.polygons:
            key = tuple(sorted(v if v in apart else find(v) for v in p.vertices))
            if key not in seen:
                seen[key] = tuple(p.vertices)
                continue
            for v in (*seen[key], *p.vertices):
                if v not in apart and len(members.get(find(v), ())) > 1:
                    apart.add(v)
                    changed = True
    groups = {}
    for v in range(count):
        if v not in apart:
            groups.setdefault(find(v), []).append(v)
    return [g for g in groups.values() if len(g) > 1]


def weld(mesh, groups) -> int:
    """Welds each group onto its first vertex, keeping each face corner's normal. Returns how many
    vertices went."""
    if not groups:
        return 0
    # A bmesh round trip re-encodes custom normals against the welded vertices, so they ride along as a
    # corner attribute and are put back.
    normals = np.empty(len(mesh.loops) * 3, dtype=np.float32)
    mesh.corner_normals.foreach_get("vector", normals)
    carried = mesh.attributes.new(NORMALS, "FLOAT_VECTOR", "CORNER")
    carried.data.foreach_set("vector", normals)
    before = len(mesh.vertices)
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        targetmap = {bm.verts[v]: bm.verts[g[0]] for g in groups for v in g[1:]}
        bmesh.ops.weld_verts(bm, targetmap=targetmap)
        bm.to_mesh(mesh)
    finally:
        bm.free()
    carried = mesh.attributes[NORMALS]
    normals = np.empty(len(mesh.loops) * 3, dtype=np.float32)
    carried.data.foreach_get("vector", normals)
    mesh.attributes.remove(carried)
    mesh.normals_split_custom_set(normals.reshape(-1, 3))
    mesh.update()
    return before - len(mesh.vertices)
