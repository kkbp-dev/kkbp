"""Export prep: readies a Character for another program (legacy exportprep.py, D26, D28). One module
per target; they share common.py. The atlas (atlas.py) is optional."""

from __future__ import annotations

from ...character import CharacterError
from . import atlas, common, koikatsu, no_change, unreal, vrc, vrm

TARGETS = {
    "vrm": ("VRM", vrm),
    "vrc": ("VRChat", vrc),
    "unreal": ("Unreal", unreal),
    "koikatsu": ("Koikatsu", koikatsu),
    "no_change": ("No change", no_change),
}
SIMPLIFY = (("very_simple", "Very simple", "Merges the deform details, the face and the tongue into their parents"),
            ("simple", "Simple", "Merges the helper bones only"),
            ("none", "No change", "Keeps every bone"))
ATLAS = (("atlas", "Atlas", "One atlas each for the light, dark and normal textures"),
         ("skip_eyes", "Atlas without the eyes", "As Atlas, with the eyes keeping their own textures"),
         ("all_textures", "Atlas of every texture", "As Atlas, with the detail, alpha and colour masks too"),
         ("none", "No atlas", "The textures stay as they are"))


def prep(ch, target: str, simplify: str, atlas_mode: str, log=print):
    """Readies the Character for `target`. With an atlas, the result is a copy in a "<name> atlas"
    Collection, and the atlases are in the bundle's Cache; returns the Collection to export."""
    if ch.rig is not None:
        raise CharacterError(f"{ch.name} has a Rigify rig. Export prep needs a Character imported without Rigify.")
    bundle = ch.bundle()
    skeleton = bundle.skeleton
    _, module = TARGETS[target]
    if target in ("unreal", "koikatsu"):
        module.prepare(ch, skeleton, log)
    merged = common.simplify(ch, skeleton, simplify)
    log(f"Merged {merged} bones")
    if target not in ("unreal", "koikatsu"):
        module.prepare(ch, skeleton, log)
    collection = ch.collection
    folder = bundle.cache_dir("atlas")
    if atlas_mode != "none":
        collection = atlas.build(ch, atlas_mode, folder, log)
    common.fbx_exporter(collection, str(folder / f"{atlas._safe(ch.name)} exported model.fbx"))
    return collection
