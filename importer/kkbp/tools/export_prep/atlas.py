"""The atlas, in Blender: a copy of the Character whose meshes each use one atlas per texture kind
(light, dark, normal; with "all_textures" the detail, alpha and colour masks too), or several where
one would be over the size limit. The layout,
the UV maths and the painting are kkbp/atlas, which has no bpy; this module reads the images,
applies the UVs and makes the atlas materials.

An atlas material is a plain Principled BSDF with the light atlas as its colour and alpha and the
normal atlas as its normal map (ADR 0050): Blender's FBX exporter only finds the textures
of such a material, and embeds them. The other atlases are files in the folder only. The materials
of one atlas with the same render method become one material, and the copy has no outlines."""

from __future__ import annotations

import io
from pathlib import Path

import bpy

from ... import templates
from ...character import ID, KEY
from ...collection_colors import color

# The texture slots each atlas mode makes an atlas of.
WITHOUT_EYESHADOW = {"main.light": "main.light_no_eyeshadow", "main.dark": "main.dark_no_eyeshadow"}
SLOTS = {"atlas": ("main.light", "main.dark", "normal"),
         "skip_eyes": ("main.light", "main.dark", "normal"),
         "all_textures": ("main.light", "main.dark", "normal", "detail_normal", "alpha_mask", "color_mask",
                          "detail_mask")}
EYES = ("eye_l", "eye_r")  # "skip_eyes" leaves these with their own textures, so the eyes can still move
UV_MAP = "uv_main"
# The slots an atlas material shows, and so the only atlases loaded into Blender.
SHOWN = ("main.light", "normal")
NORMALS = ("normal", "detail_normal")
FLAT_NORMAL = (128, 128, 255, 255)  # what a material without a normal map gets in a normal atlas
ATLAS_OF = "kkbp_atlas_of"  # on an atlas material: the bundle Ids of the materials it stands in for, one a line
OUTLINE = "kkbp_outline"  # what the Outlines Hook tags its outline materials with


def build(ch, mode: str, folder: Path, log, max_side: int | None = None):
    """The atlas copy of the Character in a "<name> atlas" Collection; returns the Collection. An
    object whose atlas would be wider than `max_side` pixels gets several atlases.
    Pillow is required to import, so it is there; it is imported here, not when the add-on loads,
    because the add-on must load without it to offer installing it."""
    folder.mkdir(parents=True, exist_ok=True)
    collection = color(bpy.data.collections.new(f"{ch.name} atlas"), "atlas")
    bpy.context.scene.collection.children.link(collection)
    copies = _copy(ch, collection)
    for obj in [o for o in copies if o.type == "MESH"]:
        for modifier in [m for m in obj.modifiers if m.type == "SOLIDIFY"]:  # the outlines
            obj.modifiers.remove(modifier)
        _atlas_object(ch, obj, mode, folder, log, max_side)
        _tidy_slots(obj)
    return collection


def sources(material) -> list[str]:
    """The bundle Ids of the Character's materials an atlas material stands in for."""
    return material.get(ATLAS_OF, "").split("\n")


def _tidy_slots(obj):
    """Drops the outline materials' slots and gives each material one slot, moving the faces with
    them. Only the outlines' Solidify modifier used the outline slots."""
    mesh = obj.data
    old = [s.material for s in obj.material_slots]
    kept = list(dict.fromkeys(m for m in old if m is None or not m.get(OUTLINE)))
    if kept == old:
        return
    index = [kept.index(m) if m in kept else 0 for m in old]
    faces = [0] * len(mesh.polygons)
    mesh.polygons.foreach_get("material_index", faces)
    mesh.materials.clear()
    for material in kept:
        mesh.materials.append(material)
    mesh.polygons.foreach_set("material_index", [index[min(i, len(index) - 1)] for i in faces])


def _copy(ch, collection):
    """Copies of the Character's armature and meshes, using each other as the originals did. The Low
    poly Hook's copies are left out: the atlas copy is the Character as another program gets it."""
    originals = [ch.armature] + [o for o in ch.parts() if o.type == "MESH" and o.get("kkbp_role") != "low_poly"]
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


def _atlas_object(ch, obj, mode, folder, log, max_side=None):
    from ... import atlas

    materials = [s.material for s in obj.material_slots
                 if s.material is not None and s.material.get(templates.TEMPLATE) and not s.material.get(OUTLINE)
                 and "main.light" in templates.template_of(s.material).textures]
    materials = [m for m in dict.fromkeys(materials) if _image(m, "main.light") is not None]
    if mode == "skip_eyes":
        eyes = [m for m in materials if m.get("kkbp_role") in EYES]
        materials = [m for m in materials if m not in eyes]
        for slot in obj.material_slots:
            if slot.material in eyes:  # their own texture, in a material the FBX exporter reads too
                own = {"main.light": _image(slot.material, "main.light")}
                slot.material = _simple_material(f"{slot.material.name} Simple", own, [slot.material])
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
    layouts = atlas.plan_split(pieces, max_side=max_side)
    alpha = {m.name: _pil(_image(m, "alpha_mask")) for m in materials}
    alpha = {k: v for k, v in alpha.items() if v is not None}
    for number, layout in enumerate(layouts, 1):
        group = [m for m in materials if m.name in layout.pieces]
        label = f"{_safe(obj.name)} {number}" if len(layouts) > 1 else _safe(obj.name)
        atlas_images = {}
        for slot in SLOTS[mode]:
            pictures = {}
            for mat in group:
                image = _image(mat, slot)
                picture = _pil(image) if image is not None else None
                if picture is not None and slot in ("main.light", "main.dark") and mat.name in alpha \
                        and _keeps_alpha(mat):
                    inverted = templates.template_of(mat).inverted_masks is not None
                    picture = atlas.apply_alpha_mask(picture, alpha[mat.name], inverted)
                blank = FLAT_NORMAL if slot in NORMALS else (0, 0, 0, 0)
                pictures[mat.name] = picture if picture is not None else blank
            if all(isinstance(p, tuple) for p in pictures.values()):
                continue
            path = folder / f"{label} {slot}.png"
            atlas.compose(layout, pictures).save(path)
            if slot not in SHOWN:
                continue
            image = bpy.data.images.load(str(path), check_existing=False)
            if slot in NORMALS:
                image.colorspace_settings.name = "Non-Color"  # a Normal Map node reads the values as they are
            image.pack()
            image[KEY] = ch.key
            atlas_images[slot] = image
        for mat in group:
            for i in loops[mat]:
                u, v = uv.data[i].uv
                uv.data[i].uv = atlas.remap(layout, mat.name, u, v)
        # One material per render method: the materials of one atlas differ in nothing else.
        merged = {}
        for method in dict.fromkeys(m.surface_render_method for m in group):
            name = f"{label} Atlas" + (" Blended" if method == "BLENDED" else "")
            merged[method] = _simple_material(name, atlas_images, [m for m in group if m.surface_render_method == method])
        for slot in obj.material_slots:
            if slot.material in group:
                slot.material = merged[slot.material.surface_render_method]
    sizes = ", ".join(f"{l.size[0]} x {l.size[1]}" for l in layouts)
    if len(layouts) == 1:
        log(f"{obj.name}: {len(materials)} materials in one atlas of {sizes}")
    else:
        log(f"{obj.name}: {len(materials)} materials in {len(layouts)} atlases ({sizes}), split to stay within "
            f"{max_side} px")
    for layout in layouts:
        if max_side is not None and layout.size[0] > max_side:
            log(f"{obj.name}: {next(iter(layout.pieces))} alone is {layout.size[0]} px, over the {max_side} px "
                f"limit; it isn't scaled down, so its atlas is that size")


def _simple_material(name, images, originals):
    """A Principled BSDF material standing in for `originals`, which share a render method:
    `images["main.light"]` is its colour and alpha, `images["normal"]` its normal map. Blender's FBX
    exporter reads textures only from a Principled BSDF in the material's own tree, wired to the
    output (ADR 0050)."""
    simple = bpy.data.materials.new(name)
    simple[ATLAS_OF] = "\n".join(m.get(ID, m.name) for m in originals)
    simple.surface_render_method = originals[0].surface_render_method
    if simple.node_tree is None:
        simple.use_nodes = True
    tree = simple.node_tree
    tree.nodes.clear()
    output = tree.nodes.new("ShaderNodeOutputMaterial")
    output.location = (300, 0)
    bsdf = tree.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 1.0  # matte: the colours are the bake's, not a lit surface's
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    tree.links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    light = images.get("main.light")
    if light is not None:
        node = _image_node(tree, "main.light", light, (-400, 150))
        tree.links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
        tree.links.new(node.outputs["Alpha"], bsdf.inputs["Alpha"])
    normal = images.get("normal")
    if normal is not None:
        node = _image_node(tree, "normal", normal, (-650, -250))
        normal_map = tree.nodes.new("ShaderNodeNormalMap")
        normal_map.location = (-300, -250)
        normal_map.uv_map = UV_MAP
        tree.links.new(node.outputs["Color"], normal_map.inputs["Color"])
        tree.links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    return simple


def _image_node(tree, slot, image, location):
    node = tree.nodes.new("ShaderNodeTexImage")
    node.name = node.label = f"tex.{slot}"
    node.image = image
    node.location = location
    return node


def shown(mat, slot):
    """The image an atlas material shows for `slot` ("main.light" or "normal"), or None."""
    node = mat.node_tree.nodes.get(f"tex.{slot}")
    return node.image if node is not None else None


def _keeps_alpha(mat):
    """The legacy prep left materials whose shader forces them visible (force_visibility 0) alone."""
    try:
        return templates.param(mat, "force_visibility").default_value != 0
    except templates.TemplateError:
        return True


def _image(mat, slot):
    """The material's image for `slot`. A face whose Eyeshadow is below a half gives its bakes without
    eyeshadow as its light and dark (ADR 0046): an atlas holds one of the two."""
    plain = WITHOUT_EYESHADOW.get(slot)
    if plain is not None and "eyeshadow" in templates.params(mat) and templates.param(mat, "eyeshadow").default_value < 0.5:
        slot = plain
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
