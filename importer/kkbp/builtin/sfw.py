"""SFW: removes the genitals and nipples and their bones (legacy `apply_sfw`, D21).

The genital and Better Penetration bones are Bone Group `nsfw`. Nothing in the bundle marks the
nipples (the `breast` Group also holds the bust), so their bones are named here, as the legacy
importer named them; they are KK's and KKS's, and SVS's nipple bones have other names. Runs before
Rigify, so the rig is built without these bones.
"""

import bmesh

from ..editing import editing
from ..pipeline.hooks import hook
from ..pipeline.options import Option

SWITCH = Option("sfw_mode", bool, False, "SFW mode", description="Attempts to cover up some NSFW things")

NSFW_GROUP = "nsfw"
# KK's nipple bones: their vertices go from every mesh.
NIPPLES = ("cf_s_bnip025_L", "cf_s_bnip025_R", "cf_s_bnip02_L", "cf_s_bnip02_R")
# The crotch bones in Group nsfw whose vertices go from the body only: clothes are weighted to them too.
CROTCH = ("cf_j_kokan", "cf_j_ana", "cf_d_ana", "cf_d_kokan", "cf_s_ana")
# KK's nipple and breast bones that go with the nsfw ones (the legacy list).
BONES = ("cf_s_bnip025_L", "cf_s_bnip025_R", "cf_j_bnip02root_L", "cf_j_bnip02_L", "cf_s_bnip01_L", "cf_s_bust02_L",
         "cf_j_bnip02root_R", "cf_j_bnip02_R", "cf_s_bnip01_R", "cf_s_bust02_R")
# The genital shape key, by the game's name (it has no Expression Name).
SHAPE_KEYS = ("vagina.open",)


@hook(name="SFW", switch=SWITCH)
def sfw(ctx):
    ch = ctx.character
    nsfw = {b.id for b in ctx.bundle.skeleton.bones if b.group == NSFW_GROUP}
    body = ch.body
    removed = 0
    for obj in [o for o in ch.parts() if o.type == "MESH"]:
        groups = (nsfw | set(NIPPLES)) if obj == body else (nsfw - set(CROTCH)) | set(NIPPLES)
        removed += _delete_vertices(obj, groups)
        for name in SHAPE_KEYS:
            keys = obj.data.shape_keys
            if keys is not None and name in keys.key_blocks:
                obj.shape_key_remove(keys.key_blocks[name])
    bones = _delete_bones(ch.armature, nsfw | set(BONES))
    ctx.log.info(f"Removed {removed} vertices and {bones} bones")


def _members(obj, names):
    """The indices of the vertices in any of the vertex groups `names`, whatever their weight."""
    groups = {g.index for g in obj.vertex_groups if g.name in names}
    if not groups:
        return set()
    return {v.index for v in obj.data.vertices if any(g.group in groups for g in v.groups)}


def _delete_vertices(obj, names) -> int:
    doomed = _members(obj, names)
    if doomed:
        bm = bmesh.new()
        try:
            bm.from_mesh(obj.data)
            bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in doomed], context="VERTS")
            bm.to_mesh(obj.data)
        finally:
            bm.free()
        obj.data.update()
    for group in [g for g in obj.vertex_groups if g.name in names]:
        obj.vertex_groups.remove(group)
    return len(doomed)


def _delete_bones(armature, names) -> int:
    if armature is None:
        return 0
    doomed = [b.name for b in armature.data.bones if b.name in names]
    if doomed:
        with editing(armature, "EDIT"):
            bones = armature.data.edit_bones
            for name in doomed:
                bones.remove(bones[name])  # its children move to its parent
    return len(doomed)
