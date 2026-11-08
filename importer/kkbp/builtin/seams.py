"""Fix body seams: merges the face and body materials' vertices that sit on top of each other, so no
seam shows down the neck and chest (legacy `remove_body_seams`, D16).

It does what Merge by Distance does at 0.00001 with Centroid Merge on: the vertices within the
distance become one at their centroid. A bmesh round trip re-encodes the custom normals against the
merged vertices, which bent them around the mouth; the operator keeps each face corner's normal, so
the Hook puts them back. The weld removes the faces it collapses and keeps every other corner, which takes its normal with it.
"""

import bmesh
import numpy as np

from ..pipeline.hooks import hook
from ..pipeline.options import Option

# In metres, as the legacy importer had it.
MERGE_DISTANCE = 0.00001
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
        verts = list({v for f in bm.faces if f.material_index in slots for v in f.verts})
        targetmap = bmesh.ops.find_doubles(bm, verts=verts, dist=MERGE_DISTANCE)["targetmap"]
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
    ctx.log.info(f"Merged {before - len(body.data.vertices)} vertices on the face and body materials")
