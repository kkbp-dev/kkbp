"""Scene summary: a JSON-ready description of an imported Character.

Runs inside Blender. The summary is what the old and new importers are compared on,
so it records only what a Character is made of, never how it was built:
Parts and their roles, materials with their template and texture images, shape keys,
bones with rounded positions, and vertex counts.

Everything is sorted so the output is stable from run to run. The Character's name is
replaced by "{character}" and random ids by "{random}" in every string,
so summaries of different runs and Characters line up.
"""

import re

import bpy

SUMMARY_VERSION = 2
CHARACTER = "{character}"

# The new importer's tags (importer/kkbp/character.py and templates.py). A summary of a legacy import
# has none of them, so its output is unchanged.
PART_ROLE = "kkbp_role"
BUNDLE_ID = "kkbp_id"
TEMPLATE = "kkbp_template"
CHARACTER_KEY = "kkbp_key"

# Custom properties the legacy importer sets to True to mark what an object or material is for.
LEGACY_ROLE_TAGS = (
    "armature", "body", "outfit", "hair", "alt", "hitbox", "tongue", "tears",
    "gag", "glasses", "rig", "useless", "bake",
)

POSITION_DIGITS = 4

# Blender's ".001" suffix on duplicated datablocks; it depends on creation order, not content.
DUPLICATE_SUFFIX = re.compile(r"\.\d{3}$")

# The legacy Rigify scripts name a bone "Metarig_ID:" plus 16 random characters.
RANDOM_ID = re.compile(r"(Metarig_ID:)[A-Za-z0-9]{16}")
RANDOM_ID_REPLACEMENT = r"\1{random}"


def summarize(character_name):
    def clean(text):
        if character_name:
            text = text.replace(character_name, CHARACTER)
        return RANDOM_ID.sub(RANDOM_ID_REPLACEMENT, text)

    objects = sorted(bpy.data.objects, key=lambda o: o.name)
    return {
        "summary_version": SUMMARY_VERSION,
        "collections": _collections(bpy.context.scene.collection, clean),
        "objects": {clean(o.name): _object(o, clean) for o in objects},
        "materials": {
            clean(m.name): _material(m, clean)
            for m in sorted(bpy.data.materials, key=lambda m: m.name)
            if m.users > (1 if m.use_fake_user else 0)
        },
        "images": sorted({clean(_image_name(i)) for i in bpy.data.images if i.users and i.source == "FILE"}),
        "counts": {
            "objects": len(bpy.data.objects),
            "meshes": len(bpy.data.meshes),
            "armatures": len(bpy.data.armatures),
            "materials": len(bpy.data.materials),
            "node_groups": len(bpy.data.node_groups),
            "images": len(bpy.data.images),
            "actions": len(bpy.data.actions),
        },
    }


def _collections(collection, clean):
    out = {
        "objects": sorted(clean(o.name) for o in collection.objects),
        "children": {clean(c.name): _collections(c, clean) for c in sorted(collection.children, key=lambda c: c.name)},
    }
    if getattr(collection, "color_tag", "NONE") != "NONE":  # the scene's own Collection has none
        out["color"] = collection.color_tag
    if getattr(collection, "asset_data", None) is not None:
        preview = collection.preview
        out["asset"] = {"tags": sorted(t.name for t in collection.asset_data.tags),
                        "preview": list(preview.image_size) if preview else None}
    return out


def _object(obj, clean):
    out = {
        "type": obj.type,
        "parent": clean(obj.parent.name) if obj.parent else None,
        "roles": _roles(obj),
        "id": _plain(obj.get("id"), clean),
        "hidden": {"viewport": obj.hide_viewport, "render": obj.hide_render, "hide_get": _hide_get(obj)},
        "location": _rounded(obj.location),
        "modifiers": [{"name": clean(m.name), "type": m.type} for m in obj.modifiers],
        "constraints": len(obj.constraints),
    }
    if obj.type == "MESH":
        out["mesh"] = _mesh(obj, clean)
    elif obj.type == "ARMATURE":
        out["armature"] = _armature(obj, clean)
    return out


def _roles(idblock):
    """The legacy importer's role tags, or the new importer's Part Role or Material Role."""
    role = idblock.get(PART_ROLE)
    if isinstance(role, str):
        return [role]
    return sorted(tag for tag in LEGACY_ROLE_TAGS if idblock.get(tag) is True)


def _hide_get(obj):
    try:
        return obj.hide_get()
    except RuntimeError:
        # Not in the active view layer.
        return None


def _mesh(obj, clean):
    mesh = obj.data
    keys = mesh.shape_keys.key_blocks if mesh.shape_keys else []
    return {
        "vertices": len(mesh.vertices),
        "edges": len(mesh.edges),
        "faces": len(mesh.polygons),
        "uv_maps": [uv.name for uv in mesh.uv_layers],
        "color_attributes": sorted(a.name for a in mesh.color_attributes),
        "vertex_groups": len(obj.vertex_groups),
        "material_slots": [clean(s.material.name) if s.material else None for s in obj.material_slots],
        "shape_keys": [clean(k.name) for k in keys],
        "shape_key_drivers": _driver_count(mesh.shape_keys) if mesh.shape_keys else 0,
    }


def _armature(obj, clean):
    bones = obj.data.bones
    return {
        "bone_count": len(bones),
        "bone_collections": sorted(
            (clean(c.name), len(c.bones)) for c in obj.data.collections_all
        ),
        "drivers": _driver_count(obj),
        "pose_constraints": sum(len(pb.constraints) for pb in obj.pose.bones),
        "bones": {
            clean(b.name): {
                "parent": clean(b.parent.name) if b.parent else None,
                "head": _rounded(b.head_local),
                "tail": _rounded(b.tail_local),
                "deform": b.use_deform,
            }
            for b in sorted(bones, key=lambda b: b.name)
        },
    }


def _material(mat, clean):
    out = {
        "roles": _roles(mat),
        "id": _plain(mat.get(BUNDLE_ID, mat.get("id")), clean),
        "surface_render_method": getattr(mat, "surface_render_method", None),
        "node_groups": [],
        "images": [],
    }
    if TEMPLATE in mat:
        out["template"] = mat[TEMPLATE]
    if mat.node_tree:
        groups, images = set(), set()
        _walk_nodes(mat.node_tree, groups, images, set())
        out["node_groups"] = sorted({clean(DUPLICATE_SUFFIX.sub("", g)) for g in groups})
        out["images"] = sorted(clean(i) for i in images)
    return out


def _walk_nodes(tree, groups, images, seen):
    if tree.name in seen:
        return
    seen.add(tree.name)
    for node in tree.nodes:
        if node.type == "GROUP" and node.node_tree:
            groups.add(node.node_tree.name)
            _walk_nodes(node.node_tree, groups, images, seen)
        elif node.type == "TEX_IMAGE" and node.image:
            images.add(_image_name(node.image))


def _image_name(image):
    # The legacy importer's images are named by file; bundle files have no meaning
    # (textures/0001.png), so a new import's image is known by the name it gives it
    # ("<material Id> <slot>"). Either way without Blender's .001 suffix.
    if CHARACTER_KEY in image:
        return DUPLICATE_SUFFIX.sub("", image.name)
    return bpy.path.basename(image.filepath) or image.name


def _driver_count(idblock):
    anim = idblock.animation_data
    return len(anim.drivers) if anim else 0


def _rounded(vector):
    return [round(v, POSITION_DIGITS) + 0.0 for v in vector]


def _plain(value, clean):
    """Convert an ID property value to plain JSON, or None."""
    if value is None:
        return None
    if isinstance(value, str):
        return clean(value)
    if hasattr(value, "to_list"):
        return [_plain(v, clean) for v in value.to_list()]
    if hasattr(value, "to_dict"):
        return {k: _plain(v, clean) for k, v in value.to_dict().items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v, clean) for v in value]
    return value
