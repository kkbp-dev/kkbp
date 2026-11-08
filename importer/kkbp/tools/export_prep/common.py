"""What the export prep targets share: bone names, simplifying the skeleton, and the FBX exporter."""

from __future__ import annotations

from collections import defaultdict

import bpy

from ... import compat
from ...bone_names import EXACT_NAMES, ROLE_NAMES
from ...editing import editing
from .. import merge_weights

# Simplifying merges the weights of bones without a Bone Role in these Bone Groups into their
# parents, as the legacy option did with its bone collections. "very_simple" merges the deform
# details, the face and the tongue; "simple" only the helpers.
SIMPLIFY = {
    "very_simple": ("deform", "breast", "nsfw", "face", "eye", "eyebrow", "mouth", "helper"),
    "simple": ("helper",),
    "none": (),
}
EYELINE_NUDGE = 0.0001  # metres forward, so the eyeline's UVs don't fight the face's in an FBX


def roles(skeleton) -> dict[str, str]:
    """Bone Role -> bone Id."""
    return {b.role: b.id for b in skeleton.bones if b.role}


def rename(armature, names: dict[str, str]):
    """Renames bones (and with them their vertex groups, constraints and drivers)."""
    for old, new in names.items():
        bone = armature.data.bones.get(old)
        if bone is not None:
            bone.name = new


def readable_names(armature, skeleton) -> dict[str, str]:
    """The legacy readable names (D23) for the bones with a Bone Role and the pelvis: Id -> name."""
    by_role = roles(skeleton)
    names = {by_role[r]: n for r, n in ROLE_NAMES.items() if r in by_role}
    names.update({old: new for old, new in EXACT_NAMES.items() if old in armature.data.bones})
    return names


def simplify(ch, skeleton, level: str) -> int:
    groups = SIMPLIFY[level]
    if not groups:
        return 0
    armature = ch.armature
    root = skeleton.by_role("tongue_root")
    tongue = _subtree(skeleton, root.id) if root and level == "very_simple" else set()
    # the pelvis has no Bone Role but is a body bone (the legacy Torso collection kept it)
    doomed = [b.id for b in skeleton.bones
              if ((b.role is None and b.group in groups) or b.id in tongue) and b.id not in EXACT_NAMES]
    return merge_weights.merge_weights(ch, armature, [n for n in doomed if n in armature.data.bones])


def nudge_eyelines(ch):
    """Moves the upper eyeline's faces forward a little (legacy separate_eye_meshes)."""
    body = ch.body
    if body is None:
        return
    slots = {i for i, s in enumerate(body.material_slots) if s.material and s.material.get("kkbp_role") == "eyeline_upper"}
    verts = {v for p in body.data.polygons if p.material_index in slots for v in p.vertices}
    layers = [body.data.vertices] + ([k.data for k in body.data.shape_keys.key_blocks] if body.data.shape_keys else [])
    for layer in layers:
        for v in verts:
            layer[v].co.y -= EYELINE_NUDGE


def hide_eye_uv_warps(ch):
    """The eye UV warp modifiers export badly; they are switched off, as the legacy prep did."""
    for obj in [o for o in ch.parts() if o.type == "MESH"]:
        for modifier in obj.modifiers:
            if modifier.type == "UV_WARP":
                modifier.show_viewport = False


def reparent(armature, parents: dict[str, str | None]):
    with editing(armature, "EDIT"):
        bones = armature.data.edit_bones
        for name, parent in parents.items():
            if name in bones and (parent is None or parent in bones):
                bones[name].parent = bones[parent] if parent else None


def fbx_exporter(collection, filepath):
    """A collection exporter for FBX on `collection`, with the legacy prep's settings."""
    compat.add_collection_exporter(collection, "IO_FH_fbx", filepath, {
        "object_types": {"EMPTY", "ARMATURE", "MESH", "OTHER"}, "use_mesh_modifiers": False,
        "add_leaf_bones": False, "bake_anim": False, "apply_scale_options": "FBX_SCALE_ALL", "path_mode": "COPY",
        "embed_textures": False, "mesh_smooth_type": "OFF"})


def _subtree(skeleton, root_id):
    children = defaultdict(list)
    for b in skeleton.bones:
        children[b.parent].append(b.id)
    found, todo = set(), [root_id]
    while todo:
        bone = todo.pop()
        found.add(bone)
        todo.extend(children[bone])
    return found
