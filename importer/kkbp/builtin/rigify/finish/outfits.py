"""Each later Outfit's hair and accessory bones go to a hidden collection of their own, "Hair/Accessories
01" and so on, so the first Outfit's are the ones the panel shows. The collections stay out of the
Rigify panel but are in the bone collection list. In Object Mode."""

from __future__ import annotations

from .. import bone_collections, names
from ..bones import outfit_of


def outfit_collections(build):
    rig = build.rig
    parts = list(build.character.outfits) + list(build.character.hairs)
    outfits = sorted({outfit_of(o) for o in parts if outfit_of(o) is not None})
    for bone in rig.data.bones:
        outfit = outfit_of(bone)
        if outfit is None or not outfits or outfit == min(outfits) or not bone.collections:
            continue
        if names.HAIR_LAYER in bone.collections[0].name:
            bone_collections.move(rig, bone.name, bone.collections[0].name + f" {outfit:02d}")
            bone.collections[0].is_visible = False
