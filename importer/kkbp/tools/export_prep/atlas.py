"""The atlas, in Blender: a copy of the Character whose meshes each use one atlas per texture kind
(light, dark, normal; with "all_textures" the detail, alpha and colour masks too). The layout,
the UV maths and the painting are kkbp/atlas, which has no bpy; this module reads the images,
applies the UVs and makes the atlas materials."""

from __future__ import annotations

import io
from pathlib import Path

import bpy

from ... import templates
from ...character import ID, KEY

# The texture slots each atlas mode makes an atlas of.
SLOTS = {"atlas": ("main.light", "main.dark", "normal"),
         "skip_eyes": ("main.light", "main.dark", "normal"),
         "all_textures": ("main.light", "main.dark", "normal", "detail_normal", "alpha_mask", "color_mask",
                          "detail_mask")}
EYES = ("eye_l", "eye_r")  # "skip_eyes" leaves these with their own textures, so the eyes can still move
UV_MAP = "uv_main"


def build(ch, mode: str, folder: Path, log):
    """The atlas copy of the Character in a "<name> atlas" Collection; returns the Collection.
    Pillow is required to import, so it is there; it is imported here, not when the add-on loads,
    because the add-on must load without it to offer installing it."""
    folder.mkdir(parents=True, exist_ok=True)
    collection = bpy.data.collections.new(f"{ch.name} atlas")
    bpy.context.scene.collection.children.link(collection)
    copies = _copy(ch, collection)
    for obj in [o for o in copies if o.type == "MESH"]:
        _atlas_object(ch, obj, mode, folder, log)
        for modifier in obj.modifiers:
            if modifier.type == "SOLIDIFY":  # the outlines
                modifier.show_viewport = modifier.show_render = False
    return collection


def _copy(ch, collection):
    """Copies of the Character's armature and meshes, using each other as the originals did."""
    originals = [ch.armature] + [o for o in ch.parts() if o.type == "MESH"]
    copies = {}
    for obj in originals:
        copy = obj.copy()
        copy.data = obj.data.copy()
        for prop in (KEY, "kkbp_role", "kkbp_outfit"):  # the copy isn't a Part of the Character
            copy.pop(prop, None)
        collection.objects.link(copy)
        copies[obj] = copy
    for obj, copy in copies.items():
        if obj.parent in copies:
            copy.parent = copies[obj.parent]
        for modifier in copy.modifiers:
            if modifier.type == "ARMATURE" and modifier.object in copies:
                modifier.object = copies[modifier.object]
    return list(copies.values())


def _atlas_object(ch, obj, mode, folder, log):
    from ... import atlas

    materials = [s.material for s in obj.material_slots
                 if s.material is not None and s.material.get(templates.TEMPLATE)
                 and "main.light" in templates.template_of(s.material).textures
                 and not (mode == "skip_eyes" and s.material.get("kkbp_role") in EYES)]
    materials = [m for m in dict.fromkeys(materials) if _image(m, "main.light") is not None]
    if not materials:
        return
    uv = obj.data.uv_layers.get(UV_MAP) or obj.data.uv_layers.active
    loops = {m: [] for m in materials}
    for poly in obj.data.polygons:
        mat = obj.material_slots[poly.material_index].material
        if mat in loops:
            loops[mat].extend(poly.loop_indices)
    pieces = []
    for mat in materials:
        coords = [uv.data[i].uv for i in loops[mat]]
        max_uv = (max((c.x for c in coords), default=1.0), max((c.y for c in coords), default=1.0))
        pieces.append(atlas.Piece(mat.name, tuple(_image(mat, "main.light").size), max_uv))
    layout = atlas.plan(pieces)
    alpha = {m.name: _pil(_image(m, "alpha_mask")) for m in materials}
    alpha = {k: v for k, v in alpha.items() if v is not None}
    atlas_images = {}
    for slot in SLOTS[mode]:
        pictures = {}
        for mat in materials:
            image = _image(mat, slot)
            picture = _pil(image) if image is not None else None
            if picture is not None and slot in ("main.light", "main.dark") and mat.name in alpha \
                    and _keeps_alpha(mat):
                picture = atlas.apply_alpha_mask(picture, alpha[mat.name])
            pictures[mat.name] = picture if picture is not None else (0, 0, 0, 0)
        if all(isinstance(p, tuple) for p in pictures.values()):
            continue
        path = folder / f"{_safe(obj.name)} {slot}.png"
        atlas.compose(layout, pictures).save(path)
        image = bpy.data.images.load(str(path), check_existing=False)
        image.pack()
        image[KEY] = ch.key
        atlas_images[slot] = image
    for mat, indices in loops.items():
        for i in indices:
            u, v = uv.data[i].uv
            uv.data[i].uv = atlas.remap(layout, mat.name, u, v)
    for slot in obj.material_slots:
        if slot.material in loops:
            slot.material = _atlas_material(slot.material, atlas_images)
    log(f"{obj.name}: {len(materials)} materials in one atlas of {layout.size[0]} x {layout.size[1]}")


def _atlas_material(mat, atlas_images):
    name = f"{mat.name} Atlas"
    found = bpy.data.materials.get(name)
    if found is not None and found.get("kkbp_atlas_of") == mat.get(ID):
        return found
    copy = mat.copy()
    copy.name = name
    copy.pop(ID, None)
    copy["kkbp_atlas_of"] = mat.get(ID, mat.name)
    for slot in templates.template_of(copy).textures:
        node = templates.texture_node(copy, slot)
        if node is None:
            continue
        if slot in atlas_images:
            node.image = atlas_images[slot]
        elif slot == "alpha_mask":
            node.image = None  # folded into the light and dark atlases
    if "main.dark" not in atlas_images and "main.light" in atlas_images:
        templates.texture_node(copy, "main.dark").image = atlas_images["main.light"]
    # The alpha mask is in the atlases now and its slot is empty, which the shader would read as
    # "hide everything"; force visibility 0 makes it ignore the mask.
    if "force_visibility" in templates.template_of(copy).params:
        templates.param(copy, "force_visibility").default_value = 0
    return copy


def _keeps_alpha(mat):
    """The legacy prep left materials whose shader forces them visible (force_visibility 0) alone."""
    try:
        return templates.param(mat, "force_visibility").default_value != 0
    except templates.TemplateError:
        return True


def _image(mat, slot):
    node = templates.texture_node(mat, slot)
    return node.image if node is not None and node.image is not None and node.image.size[0] else None


def _pil(image):
    from PIL import Image

    if image is None:
        return None
    if image.packed_file is not None:
        return Image.open(io.BytesIO(image.packed_file.data)).convert("RGBA")
    path = bpy.path.abspath(image.filepath)
    return Image.open(path).convert("RGBA") if path and Path(path).is_file() else None


def _safe(name):
    return "".join(c for c in name if c not in '\\`*<>.:?|/"')
