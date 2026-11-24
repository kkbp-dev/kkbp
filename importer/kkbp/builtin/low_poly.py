"""Low poly: a copy of each Outfit's clothes and hair with fewer faces, for smoother playback on slow
computers (issue #129, ADR 0059).

Each copy is made from the finished Part, after every other Hook that changes meshes, so it has the
rig, the SFW cuts and the separated pieces the original has, and no other Hook sees it. Its faces are
cut down once, at the rest pose, by a Collapse decimation that is then applied: a Decimate modifier
left on would run again every frame after the armature, which is the work the copy is there to save.
The copy keeps its vertex weights and shares the original's materials, so Edit Material changes both.
It has no outline. The alternate clothes get no copy.

The copies are Parts with Part Role `low_poly` and their Outfit, in a hidden `Low poly NN` Collection
that carries the Outfit's number like the Outfit's own, so showing it instead of the Outfit's still
gives the body that Outfit's Body Textures.
"""

import bpy

from ..character import OUTFIT
from ..collection_colors import color
from ..pipeline.hooks import hook
from ..pipeline.options import Option
from ..steps.mesh import child_collection, move_to_collection
from .outlines import MODIFIER as OUTLINE_MODIFIER, OUTLINE

# Preset -> the share of faces the copies keep.
RATIOS = {"light": 0.5, "medium": 0.25, "strong": 0.1}
SWITCH = Option(
    "low_poly", str, "off", "Low poly clothes and hair",
    description="Adds a copy of each Outfit's clothes and hair with fewer faces and no outline, in a hidden "
                "Collection beside the Outfit's, for smoother playback",
    choices=(("off", "Off", "No low poly copies"),
             ("light", "Light (50%)", "The copies keep half of the faces"),
             ("medium", "Medium (25%)", "The copies keep a quarter of the faces"),
             ("strong", "Strong (10%)", "The copies keep a tenth of the faces")))
COPIED = ("outfit", "hair")
COLLECTION = "Low poly {index:02d} {name}"
SUFFIX = " low poly"


@hook(name="Low poly", switch=SWITCH)
def low_poly(ctx):
    ch = ctx.character
    ratio = RATIOS[ctx.options.low_poly]
    _remove(ch.parts("low_poly"))  # made again by Run Hook: the new copies replace the old
    before = after = 0
    for index in sorted({o.get(OUTFIT) for o in ch.parts(COPIED)}):
        copies = []
        for obj in [o for o in ch.parts(COPIED, outfit=index) if o.type == "MESH"]:
            copy = _copy(ctx, obj, ratio)
            before += len(obj.data.polygons)
            after += len(copy.data.polygons)
            copies.append(copy)
        if copies:
            name = COLLECTION.format(index=index, name=ch.name)
            collection = color(child_collection(ch.collection, name), "low_poly")
            collection[OUTFIT] = index  # shown, it gives the body this Outfit's textures (outfit_textures.py)
            move_to_collection(copies, collection, hide=True)
    ctx.log.info(f"Made low poly copies of the clothes and hair: {before} faces down to {after}")


def _copy(ctx, obj, ratio):
    """A copy of `obj` with about `ratio` of its faces, its weights and modifiers, and no outline."""
    ch = ctx.character
    copy = obj.copy()
    copy.data = obj.data.copy()
    copy.name = f"{obj.name}{SUFFIX}"
    # The scene's own Collection is always in the view layer, so the copy is evaluated there even when
    # the Character's Collections are hidden (Run Hook); it moves to its own Collection after.
    bpy.context.scene.collection.objects.link(copy)
    ch.add_part(copy, "low_poly", outfit=obj.get(OUTFIT))
    for modifier in [m for m in copy.modifiers if m.type == "SOLIDIFY" and m.name == OUTLINE_MODIFIER]:
        copy.modifiers.remove(modifier)
    if copy.data.shape_keys:
        ctx.log.info(f"{obj.name}'s low poly copy has no shape keys")
    mesh = _decimated(copy, ratio)
    old = copy.data
    copy.data = mesh
    bpy.data.meshes.remove(old)
    mesh.name = f"{obj.data.name}{SUFFIX}"
    _drop_outline_slots(copy)
    return copy


def _decimated(obj, ratio):
    """A new mesh of `obj` at its rest pose, cut down to about `ratio` of its faces: what a Collapse
    Decimate modifier, alone in the stack, makes of it. Vertex groups and UV maps come with it; shape
    keys don't."""
    shown = [(m, m.show_viewport) for m in obj.modifiers]
    for modifier, _ in shown:
        modifier.show_viewport = False
    decimate = obj.modifiers.new("Low poly", "DECIMATE")
    decimate.decimate_type = "COLLAPSE"
    decimate.ratio = ratio
    decimate.use_symmetry = True  # the Character faces -Y, so its sides mirror across X
    decimate.symmetry_axis = "X"
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        return bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph), preserve_all_data_layers=True,
                                               depsgraph=depsgraph)
    finally:
        obj.modifiers.remove(decimate)
        for modifier, was_shown in shown:
            modifier.show_viewport = was_shown


def _remove(copies):
    for obj in copies:
        mesh = obj.data
        bpy.data.objects.remove(obj)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def _drop_outline_slots(obj):
    """Removes the outline materials' slots. The Outlines Hook adds them after the Part's own, and only
    its Solidify modifier, which the copy doesn't have, uses them."""
    materials = obj.data.materials
    while len(materials) and materials[len(materials) - 1] is not None and materials[len(materials) - 1].get(OUTLINE):
        materials.pop(index=len(materials) - 1)
