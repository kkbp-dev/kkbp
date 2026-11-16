"""Symmetry Step: puts back the exact mirror images the exporter wrote (ADR 0049).

The exporter makes the Body Pass an exact mirror image across X = 0 (ADRs 0047 and 0048), but Blender's
glTF importer skins every vertex into its bind pose through near-identity matrices, which leaves mirror
partners up to a micrometre apart. Where the face, its eyelines and the eye whites lie within a
micrometre of each other in Body, that is enough for Blender's X Mirror to take a vertex of one for
the partner of another. This Step pairs each vertex with the vertex nearest its mirror image, within
SNAP_DISTANCE and when each is the other's nearest, and makes them exact mirror images again; a vertex
that is its own nearest goes onto X = 0. Shape keys move by the same amount.

It runs on each mesh as it was loaded, before `build_parts` joins them, so an eyeline on the face can't
be taken for the face. Then, across the Body Pass's meshes, it pairs the vertices that have no partner
in their own mesh: the left and right eyes are separate meshes. It pairs positions, not vertices: the
vertices at one position (the upper eyeline and its shadow, a copy of it) move together.
"""

from __future__ import annotations

import numpy as np
from mathutils import kdtree

from ..character import OUTFIT
from .mesh import _meshes

# In metres: more than the glTF importer's rounding, far less than any distance the exporter leaves.
SNAP_DISTANCE = 1e-6


def snap_to_symmetry(ctx):
    """Makes each mesh's mirror partners exact again, then the Body Pass's partners across meshes."""
    objs = _meshes(ctx.character)
    within = sum(_snap_within(o.data) for o in objs)
    across = _snap_across([o.data for o in objs if o.get(OUTFIT) is None])
    ctx.log.info(f"Snapped {within} vertices to their mirror image within their mesh, {across} across meshes")


def _positions(mesh) -> np.ndarray:
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    return co.reshape(-1, 3)


def _tree(points) -> kdtree.KDTree:
    tree = kdtree.KDTree(len(points))
    for i, p in enumerate(points):
        tree.insert(p, i)
    tree.balance()
    return tree


def _mirrored(p):
    return (-p[0], p[1], p[2])


def _pairs(points):
    """(i, j) for each pair that are each other's nearest mirror image within SNAP_DISTANCE, i < j, and
    (i, i) for each point that is its own."""
    if len(points) == 0:
        return []
    tree = _tree(points)
    nearest = [tree.find(_mirrored(p)) for p in points]
    pairs = []
    for i, (_, j, distance) in enumerate(nearest):
        if distance <= SNAP_DISTANCE and (j == i or (nearest[j][1] == i and i < j)):
            pairs.append((i, j))
    return pairs


def _mirror_of(a, b):
    """Positions for a and b that are exact mirror images, halfway between where they are."""
    x = (a[0] - b[0]) / 2
    y = (a[1] + b[1]) / 2
    z = (a[2] + b[2]) / 2
    return (x, y, z), (-x, y, z)


def _move(mesh, moves: dict) -> int:
    """Puts the mesh's vertices at `moves` (index -> position); its shape keys move by as much."""
    if not moves:
        return 0
    co = _positions(mesh)
    new = co.copy()
    for v, p in moves.items():
        new[v] = p
    mesh.vertices.foreach_set("co", new.ravel())
    if mesh.shape_keys:
        delta = new - co
        for key in mesh.shape_keys.key_blocks:
            k = np.empty(len(mesh.vertices) * 3)
            key.data.foreach_get("co", k)
            key.data.foreach_set("co", (k.reshape(-1, 3) + delta).ravel())
    mesh.update()
    return len(moves)


def _snap_points(points) -> dict:
    """New places for the points that pair (index -> position)."""
    moves = {}
    for i, j in _pairs(points):
        if i == j:
            moves[i] = (0.0, points[i][1], points[i][2])
        else:
            moves[i], moves[j] = _mirror_of(points[i], points[j])
    return moves


def _snap_within(mesh) -> int:
    co = _positions(mesh)
    if len(co) == 0:
        return 0
    points, at = np.unique(co, axis=0, return_inverse=True)
    at = at.ravel()
    moved = _snap_points(points)
    return _move(mesh, {v: moved[at[v]] for v in range(len(co)) if at[v] in moved})


def _snap_across(meshes) -> int:
    """Pairs, across `meshes`, the vertices with no mirror partner in their own mesh."""
    loose = []  # (mesh, vertex index, position)
    for mesh in meshes:
        co = _positions(mesh)
        if len(co) == 0:
            continue
        tree = _tree(co)
        loose += [(mesh, v, co[v]) for v in range(len(co)) if tree.find(_mirrored(co[v]))[2] > SNAP_DISTANCE]
    if not loose:
        return 0
    points, at = np.unique(np.array([p for _, _, p in loose]), axis=0, return_inverse=True)
    at = at.ravel()
    moved = _snap_points(points)  # none is its own partner: it had none in its own mesh
    moves = {}
    for k, (mesh, v, _) in enumerate(loose):
        if at[k] in moved:
            moves.setdefault(mesh, {})[v] = moved[at[k]]
    return sum(_move(mesh, m) for mesh, m in moves.items())
