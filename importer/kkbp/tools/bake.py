"""Bakes an edit material into light and dark textures (D44), as the legacy importer did: the meshes
that use it are laid flat in UV space over a plane that fills the rest, and an orthographic camera
renders them with Eevee at the size of the material's largest texture, once with its toon shading
fully lit and once fully dark. Normals are off, and the alpha mask is left to the Light Dark material. Everything is made in a scene of its own, which
goes afterwards; the images are written into the Cache (`kkbp_cache/baked/`) and packed.
"""

from __future__ import annotations

import re

import bpy
import numpy as np

from .. import compat, templates
from ..character import ROLE

CACHE = "baked"
SCENE = "KKBP bake"
FALLBACK_SIZE = 64  # for a material with no images: a solid colour or fully transparent
PASSES = (("light", 1.0), ("dark", 0.0))
# Slots the original Light Dark material applies itself, so the bake shows them neutral (white):
# an Outfit's body alpha mask would otherwise cut holes into the body's texture.
NEUTRAL_SLOTS = ("alpha_mask",)


def bake(ch, material, name: str, *, at_least=(0, 0), log=print):
    """(light image, dark image) for `material`, rendered from the Character's meshes that use it, at
    the size of its largest texture or `at_least` (the light texture being replaced), if larger."""
    # not the Low poly Hook's copies: their faces would draw over the original's in the bake
    objects = [o for o in ch.parts() if o.type == "MESH" and o.get(ROLE) != "low_poly"
               and material.name in o.data.materials]
    if not objects:
        raise ValueError(f"no mesh of {ch.name} uses {material.name}")
    width, height = max(_size(material), tuple(at_least), key=lambda size: size[0] * size[1])
    folder = ch.bundle().cache_dir(CACHE)
    scene = _scene(width, height)
    made = []
    toon, normals = templates.param(material, "toon_shading"), templates.param(material, "use_normals")
    links = [(l.from_socket, l.to_socket) for l in material.node_tree.links if l.to_socket == toon]
    saved = (toon.default_value, normals.default_value, material.surface_render_method)
    white = bpy.data.images.new(f"{SCENE} white", 4, 4, alpha=True)
    white.generated_color = (1.0, 1.0, 1.0, 1.0)
    neutral = [(node, node.image) for node in (templates.texture_node(material, slot) for slot in NEUTRAL_SLOTS)
               if node is not None]
    try:
        for node, _ in neutral:
            node.image = white
        aspect = height / width
        for obj in objects:
            made.append(_flat(scene, obj, material, aspect))
        made.append(_filler(scene, objects[0], material, aspect))
        made.append(_camera(scene, aspect))
        for link in [l for l in material.node_tree.links if l.to_socket == toon]:
            material.node_tree.links.remove(link)
        normals.default_value = 0.0
        material.surface_render_method = "BLENDED"  # no dithering noise in the alpha
        images = []
        for kind, value in PASSES:
            toon.default_value = value
            path = folder / f"{_safe(name)} {kind}.png"
            compat.render_still(scene, path)
            images.append(_load(ch, path, f"{CACHE}/{path.name}"))
            log(f"Baked {path.name} ({width} x {height})")
        return tuple(images)
    finally:
        toon.default_value, normals.default_value, material.surface_render_method = saved
        for node, image in neutral:
            node.image = image
        bpy.data.images.remove(white)
        for from_socket, to_socket in links:
            material.node_tree.links.new(from_socket, to_socket)
        for obj in made:
            data = obj.data
            bpy.data.objects.remove(obj)
            if data is not None and data.users == 0:
                (bpy.data.cameras if isinstance(data, bpy.types.Camera) else bpy.data.meshes).remove(data)
        bpy.data.scenes.remove(scene)


def _size(material):
    """The largest image size in the material, its groups included."""
    best = (0, 0)
    for node in _image_nodes(material.node_tree, set()):
        size = tuple(node.image.size)
        if size[0] * size[1] > best[0] * best[1]:
            best = size
    return best if best[0] and best[1] else (FALLBACK_SIZE, FALLBACK_SIZE)


def _image_nodes(tree, seen):
    if tree is None or tree in seen:
        return
    seen.add(tree)
    for node in tree.nodes:
        if node.type == "TEX_IMAGE" and node.image is not None:
            yield node
        elif node.type == "GROUP":
            yield from _image_nodes(node.node_tree, seen)


def _scene(width, height):
    scene = bpy.data.scenes.new(SCENE)
    r = scene.render
    r.engine = "BLENDER_EEVEE"
    r.resolution_x, r.resolution_y, r.resolution_percentage = width, height, 100
    r.film_transparent = True
    r.filter_size = 0.0
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "RGBA"
    r.image_settings.color_depth = "8"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.eevee.taa_render_samples = 1
    return scene


def _flat(scene, obj, material, aspect):
    """A mesh of `obj`'s faces that use `material`, each loop at its uv_main position, with every
    UV map and face-corner colour attribute of `obj` (main_skin's overlays read the vertex colour)."""
    src = obj.data
    index = list(src.materials).index(material)
    n_polys = len(src.polygons)
    mat_index = np.empty(n_polys, dtype=np.int32)
    src.polygons.foreach_get("material_index", mat_index)
    starts = np.empty(n_polys, dtype=np.int32)
    totals = np.empty(n_polys, dtype=np.int32)
    src.polygons.foreach_get("loop_start", starts)
    src.polygons.foreach_get("loop_total", totals)
    keep = mat_index == index
    loops = np.concatenate([np.arange(s, s + t) for s, t in zip(starts[keep], totals[keep])]) \
        if keep.any() else np.empty(0, dtype=np.int64)
    uv_layers = {}
    for layer in src.uv_layers:
        uv = np.empty(len(src.loops) * 2, dtype=np.float32)
        layer.data.foreach_get("uv", uv)
        uv_layers[layer.name] = uv.reshape(-1, 2)[loops]
    render_uv = next((l.name for l in src.uv_layers if l.active_render), src.uv_layers[0].name)
    coords = np.zeros((len(loops), 3), dtype=np.float32)
    coords[:, 0] = uv_layers[render_uv][:, 0]
    coords[:, 1] = uv_layers[render_uv][:, 1] * aspect

    mesh = bpy.data.meshes.new(f"{SCENE} {obj.name}")
    mesh.vertices.add(len(loops))
    mesh.vertices.foreach_set("co", coords.ravel())
    mesh.loops.add(len(loops))
    mesh.loops.foreach_set("vertex_index", np.arange(len(loops), dtype=np.int32))
    mesh.polygons.add(int(keep.sum()))
    totals = totals[keep]
    mesh.polygons.foreach_set("loop_start", (np.cumsum(totals) - totals).astype(np.int32))
    mesh.polygons.foreach_set("loop_total", totals)
    for layer_name, uv in uv_layers.items():
        layer = mesh.uv_layers.new(name=layer_name)
        layer.data.foreach_set("uv", uv.ravel())
    mesh.uv_layers[render_uv].active_render = True
    for attribute in src.color_attributes:
        if attribute.domain != "CORNER":
            continue
        values = np.empty(len(src.loops) * 4, dtype=np.float32)
        attribute.data.foreach_get("color", values)
        copy = mesh.color_attributes.new(attribute.name, attribute.data_type, "CORNER")
        copy.data.foreach_set("color", values.reshape(-1, 4)[loops].ravel())
    mesh.update()
    mesh.materials.append(material)
    return _link(scene, mesh)


def _filler(scene, obj, material, aspect):
    """A plane under the flat mesh covering all of UV space, so the texture has no empty gaps."""
    mesh = bpy.data.meshes.new(f"{SCENE} filler")
    mesh.from_pydata([(0, 0, -0.01), (1, 0, -0.01), (1, aspect, -0.01), (0, aspect, -0.01)], [], [(0, 1, 2, 3)])
    corners = np.array([(0, 0), (1, 0), (1, 1), (0, 1)], dtype=np.float32)
    for layer in obj.data.uv_layers:
        mesh.uv_layers.new(name=layer.name).data.foreach_set("uv", corners.ravel())
    render_uv = next((l.name for l in obj.data.uv_layers if l.active_render), None)
    if render_uv:
        mesh.uv_layers[render_uv].active_render = True
    mesh.materials.append(material)
    return _link(scene, mesh)


def _camera(scene, aspect):
    data = bpy.data.cameras.new(f"{SCENE} camera")
    data.type = "ORTHO"
    data.ortho_scale = max(1.0, aspect)
    data.clip_start, data.clip_end = 0.001, 10.0
    camera = bpy.data.objects.new(data.name, data)
    camera.location = (0.5, aspect / 2, 1.0)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


def _link(scene, mesh):
    obj = bpy.data.objects.new(mesh.name, mesh)
    scene.collection.objects.link(obj)
    return obj


def _load(ch, path, id):
    """The Character's image `id`, (re)loaded from `path` and packed."""
    image = ch.image(id)
    if image is None:
        image = bpy.data.images.load(str(path), check_existing=False)
        image.name = path.name
        ch.tag_image(image, id)
    else:  # an earlier bake of the same material
        if image.packed_file:
            image.unpack(method="REMOVE")
        image.filepath = str(path)
        image.reload()
    image.pack()
    return image


def _safe(name):
    return re.sub(r'[<>:"/\\|?*]', "_", name)
