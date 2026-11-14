"""Fix body seams: merges the face and body materials' vertices that sit on top of each other, so no
seam shows down the neck and chest (legacy `remove_body_seams`, D16).

It does what Merge by Distance does at 0.00001 with Centroid Merge on: the vertices within the
distance become one at their centroid. A bmesh round trip re-encodes the custom normals against the
merged vertices, which bent them around the mouth; the operator keeps each face corner's normal, so
the Hook puts them back. The weld removes the faces it collapses and keeps every other corner, which takes its normal with it.

Where the face meets the body, around the neck, a vertex of one is also merged with the nearest of the
other within SEAM_DISTANCE: SVS writes 16 of the neck's 26 pairs 0.010 to 0.026 mm apart, more than
MERGE_DISTANCE, which left a seam there (issue 85).
"""

import bmesh
import numpy as np
from mathutils import kdtree

from ..pipeline.hooks import hook
from ..pipeline.options import Option

# In metres, as the legacy importer had it.
MERGE_DISTANCE = 0.00001
# How far apart a face vertex and a body vertex may be and still be merged. Ten times MERGE_DISTANCE:
# at that distance the Golden Samples merge the neck's pairs and nothing else between the two.
SEAM_DISTANCE = 0.0001
# The materials whose vertices are merged, by Material Role: only the face and the body. The legacy
# importer took every material of the game's face and body meshes, the eyes and eye whites too.
ROLES = ("face", "body")
NORMALS = "kkbp_corner_normals"  # the attribute the normals cross the merge in, removed after

SWITCH = Option(
    "fix_seams", bool, True, "Fix body seams",
    description="Merges the vertices of the face and body materials that sit on top of each other (Merge by "
                "Distance). It can change the weights around the neck; without it, seams may show around the "
                "neck and down the chest when outlines are on")


@hook(name="Fix body seams", switch=SWITCH)
def fix_body_seams(ctx):
    body = ctx.character.body
    if body is None:
        ctx.log.warning("The Character has no body, so no seams were fixed")
        return
    materials = set(ctx.character.materials(roles=ROLES))
    slots = {i for i, s in enumerate(body.material_slots) if s.material in materials}
    if not slots:
        ctx.log.warning("Body has no face or body material, so no seams were fixed")
        return
    mesh = body.data
    before = len(mesh.vertices)
    # The weld can collapse a few faces (KKS, SVS), so the normals ride along as a corner attribute.
    normals = np.empty(len(mesh.loops) * 3, dtype=np.float32)
    mesh.corner_normals.foreach_get("vector", normals)
    carried = mesh.attributes.new(NORMALS, "FLOAT_VECTOR", "CORNER")
    carried.data.foreach_set("vector", normals)
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        roles = {i: next(r for r in ROLES if body.material_slots[i].material in ctx.character.materials(roles=r))
                 for i in slots}
        used = {}  # vertex -> the Material Roles of its faces
        for f in bm.faces:
            if f.material_index in slots:
                for v in f.verts:
                    used.setdefault(v, set()).add(roles[f.material_index])
        targetmap = bmesh.ops.find_doubles(bm, verts=list(used), dist=MERGE_DISTANCE)["targetmap"]
        across = _join_across(targetmap, used)
        bmesh.ops.weld_verts(bm, targetmap=targetmap, use_centroid=True)
        bm.to_mesh(mesh)
    finally:
        bm.free()
    carried = mesh.attributes[NORMALS]
    normals = np.empty(len(mesh.loops) * 3, dtype=np.float32)
    carried.data.foreach_get("vector", normals)
    mesh.attributes.remove(carried)
    mesh.normals_split_custom_set(normals.reshape(-1, 3))
    mesh.update()
    ctx.log.info(f"Merged {before - len(body.data.vertices)} vertices on the face and body materials, "
                 f"{across} of them where the two meet")


def _join_across(targetmap, used):
    """Adds to `targetmap` each face-only vertex whose nearest body-only vertex is within SEAM_DISTANCE
    and isn't merged with it yet, and returns how many pairs now cross from one to the other."""
    first, second = ROLES
    theirs = [v for v, roles in used.items() if roles == {second}]
    if not theirs:
        return 0
    tree = kdtree.KDTree(len(theirs))
    for i, v in enumerate(theirs):
        tree.insert(v.co, i)
    tree.balance()

    def kept(v):
        return targetmap.get(v, v)

    for v, roles in used.items():
        if roles != {first}:
            continue
        _, index, distance = tree.find(v.co)
        if distance > SEAM_DISTANCE:
            continue
        mine, other = kept(v), kept(theirs[index])
        if mine is other:
            continue
        for merged, target in list(targetmap.items()):
            if target is mine:
                targetmap[merged] = other
        targetmap[mine] = other
    return sum(1 for v, target in targetmap.items() if used[v] != used[target])
