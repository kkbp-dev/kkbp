"""Separate meshes: one object per piece of clothing (legacy `separate_meshes`, D17).

"One object per outfit" is what the Core Import makes, so it is this Hook's `off`. "Separate all
clothing" splits each Outfit's clothes into one Part per material, named by the material's bundle Id.
Hair and alternate clothes stay as they are, as in the legacy importer.
"""

from contextlib import contextmanager

import bpy

from .. import compat
from ..character import ID
from ..pipeline.hooks import hook
from ..pipeline.options import Option

SWITCH = Option(
    "separation_type", str, "off", "Separation type",
    description="How the clothes are split into objects",
    choices=(("off", "One object per outfit", "Each Outfit's clothes are one object"),
             ("by_material", "Separate all clothing", "Each piece of clothing is its own object, named by its "
                                                      "material")))


@hook(name="Separate meshes", switch=SWITCH)
def separate_meshes(ctx):
    count = 0
    for outfit in ctx.character.outfits:
        with _shown(outfit):
            pieces = [outfit] + compat.separate_by_material(outfit)
        for piece in pieces:
            remove_unused_slots(piece)
            material = next((s.material for s in piece.material_slots if s.material), None)
            if material is not None:
                piece.name = piece.data.name = material.get(ID, material.name)
        count += len(pieces)
    ctx.log.info(f"Separated the clothes into {count} objects")


def remove_unused_slots(obj):
    """Keeps only the material slots the object's faces use, in their order."""
    mesh = obj.data
    indices = [0] * len(mesh.polygons)
    mesh.polygons.foreach_get("material_index", indices)
    used = sorted(set(indices))
    if used == list(range(len(mesh.materials))):
        return
    materials = [mesh.materials[i] for i in used]
    new_index = {old: new for new, old in enumerate(used)}
    mesh.materials.clear()
    for mat in materials:
        mesh.materials.append(mat)
    mesh.polygons.foreach_set("material_index", [new_index[i] for i in indices])
    mesh.update()


@contextmanager
def _shown(obj):
    """Shows the Collections that hide `obj` (later Outfits are hidden) while Blender edits it."""
    hidden = [layer for layer in _layers(bpy.context.view_layer.layer_collection, obj) if layer.hide_viewport]
    for layer in hidden:
        layer.hide_viewport = False
    try:
        yield
    finally:
        for layer in hidden:
            layer.hide_viewport = True


def _layers(layer, obj, path=()):
    """The layer collections on the way to each Collection that holds `obj`."""
    path = path + (layer,)
    found = list(path) if obj.name in layer.collection.objects else []
    for child in layer.children:
        found += [lc for lc in _layers(child, obj, path) if lc not in found]
    return found
