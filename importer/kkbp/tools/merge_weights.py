"""Merge Weights: gives each chosen bone's weights to its parent and deletes the bone (the CATS
add-on's Merge Weights, rewritten; CATS is credited in NOTICE)."""

from __future__ import annotations

from ..editing import editing


def targets(armature, names) -> dict[str, str]:
    """Each bone in `names` -> the bone its weights go to: its nearest ancestor that isn't merged too.
    Bones with no such ancestor are left out (CATS did the same)."""
    names = set(names)
    out = {}
    for name in names:
        bone = armature.data.bones.get(name)
        parent = bone.parent if bone else None
        while parent is not None and parent.name in names:
            parent = parent.parent
        if parent is not None:
            out[name] = parent.name
    return out


def merge_weights(ch, armature, names) -> int:
    """Merges the bones `names` of `armature` (the Character's armature or rig) into their parents on
    every mesh Part and deletes them. Returns how many were merged."""
    merge = targets(armature, names)
    if not merge:
        return 0
    for obj in [o for o in ch.parts() if o.type == "MESH"]:
        groups = obj.vertex_groups
        into = {}
        for bone, parent in merge.items():
            source = groups.get(bone)
            if source is not None:
                into[source.index] = groups.get(parent) or groups.new(name=parent)
        if not into:
            continue
        for v in obj.data.vertices:
            adds = [(into[g.group], g.weight) for g in v.groups if g.group in into and g.weight > 0.0]
            for target, weight in adds:
                target.add([v.index], weight, "ADD")
        for bone in merge:
            source = groups.get(bone)
            if source is not None:
                groups.remove(source)
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        for name in merge:
            if name in bones:
                bones.remove(bones[name])  # its children move to its parent
    return len(merge)
