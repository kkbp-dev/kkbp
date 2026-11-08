"""Export prep for Koikatsu (making game mods): the bones keep the game's names, which are their Ids,
and the bones above the body root go back under one another as in the game."""

from __future__ import annotations

from . import common


def prepare(ch, skeleton, log):
    root = skeleton.by_role("body_root")
    if root is None:
        return
    parent = {b.id: b.parent for b in skeleton.bones}
    chain, bone = {}, root.id
    while parent.get(bone) is not None:
        chain[bone] = parent[bone]
        bone = parent[bone]
    chain[bone] = None
    common.reparent(ch.armature, chain)
