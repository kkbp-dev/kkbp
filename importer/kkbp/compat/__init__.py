"""Everything that depends on the Blender version, and the few operators the importer still needs,
as functions named for what they do (docs/design/blender-compat-and-testing.md).

`bpy.app.version` appears only here, as a tuple comparison (`bpy.app.version >= (5, 3)`). Each
branch records the Blender version, a link to the release notes, and "remove when the minimum is X
or later". Prefer feature detection (`hasattr`). The minimum is 5.2 LTS, so there are no version
branches yet.

Operators are used only where the data API has no equivalent, each with an explicit context
through `bpy.context.temp_override`, so they never depend on what the user has selected.
"""

from __future__ import annotations

import bpy

from ..editing import editing


def join_meshes(target, others):
    """Joins the mesh objects `others` into `target` (Blender's Join, which merges vertex groups,
    UV maps and shape keys by name). `others` are removed. Returns `target`."""
    others = [o for o in others if o != target]
    if not others:
        return target
    objects = [target, *others]
    with bpy.context.temp_override(active_object=target, object=target, selected_objects=objects,
                                   selected_editable_objects=objects, view_layer=bpy.context.view_layer):
        result = bpy.ops.object.join()
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender couldn't join {', '.join(o.name for o in others)} into {target.name}")
    return target


def move_shape_key(obj, index: int, to: str):
    """Moves shape key `index` of `obj` to the `TOP` (just below the basis) or the `BOTTOM`.
    The data API has no way to reorder shape keys."""
    obj.active_shape_key_index = index
    with bpy.context.temp_override(active_object=obj, object=obj, selected_objects=[obj],
                                   selected_editable_objects=[obj]):
        bpy.ops.object.shape_key_move(type=to)
    obj.active_shape_key_index = 0


def separate_by_material(obj) -> list:
    """Splits mesh object `obj` into one object per material its faces use (Blender's Separate by
    Material). `obj` keeps one of them. Returns the new objects; none if its faces use one material
    (Blender cancels then). The data API has no split."""
    if len({p.material_index for p in obj.data.polygons}) < 2:
        return []
    before = set(bpy.data.objects)
    with editing(obj, "EDIT"):
        with bpy.context.temp_override(active_object=obj, object=obj, edit_object=obj, selected_objects=[obj],
                                       selected_editable_objects=[obj]):
            result = bpy.ops.mesh.separate(type="MATERIAL")
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender couldn't separate {obj.name} by material")
    return [o for o in bpy.data.objects if o not in before]


def enable_rigify() -> bool:
    """Enables Blender's Rigify add-on for this session if it isn't on; never saves Preferences
    (D22). True if Rigify was off."""
    import addon_utils

    preferences = bpy.context.preferences
    if "rigify" in preferences.addons:
        return False
    # Rigify's register() reads its own entry in Preferences, so it is enabled there for the session;
    # the unsaved-changes flag goes back to what it was, so auto-save doesn't store it.
    dirty = preferences.is_dirty
    addon_utils.enable("rigify", default_set=True, persistent=False, handle_error=_raise)
    preferences.is_dirty = dirty
    return True


def _raise(ex):
    raise ex


def add_rigify_color_sets(obj):
    """Rigify's standard bone colour sets on armature object `obj` (Rigify keeps the colours in its
    operator, with no function to call)."""
    with bpy.context.temp_override(active_object=obj, object=obj, selected_objects=[obj]):
        bpy.ops.armature.rigify_add_color_sets()


def generate_rigify(metarig):
    """Generates the Rigify rig from `metarig` (Rigify has no function for it outside its operator)
    and returns the rig."""
    from ..editing import switch

    before = set(bpy.data.objects)
    # Rigify changes the active object while it generates and checks context.active_object, so the
    # metarig is made the real active object instead of overriding the context.
    switch(metarig, "OBJECT")
    result = bpy.ops.pose.rigify_generate()
    if "FINISHED" not in result:
        raise RuntimeError(f"Rigify couldn't generate a rig from {metarig.name}")
    target = getattr(metarig.data, "rigify_target_rig", None)
    if target is not None:
        return target
    return next(o for o in bpy.data.objects if o not in before and o.type == "ARMATURE")


def add_collection_exporter(collection, kind: str, filepath: str, settings: dict):
    """A collection exporter (`kind`, such as IO_FH_fbx) on `collection` with these export settings.
    The data API can't add one (Blender 5.2)."""
    layer = _layer_collection(bpy.context.view_layer.layer_collection, collection)
    with bpy.context.temp_override(collection=collection):
        if layer is not None:
            bpy.context.view_layer.active_layer_collection = layer
        bpy.ops.collection.exporter_add(name=kind)
    exporter = collection.exporters[-1]
    for key, value in settings.items():
        setattr(exporter.export_properties, key, value)
    exporter.export_properties.filepath = filepath
    return exporter


def _layer_collection(layer, collection):
    if layer.collection == collection:
        return layer
    for child in layer.children:
        found = _layer_collection(child, collection)
        if found is not None:
            return found
    return None


def import_fbx(path, scale: float) -> list:
    """Imports an FBX file with Blender's FBX importer and returns the objects it made."""
    before = set(bpy.data.objects)
    with bpy.context.temp_override(view_layer=bpy.context.view_layer):
        result = bpy.ops.import_scene.fbx(filepath=str(path), global_scale=scale)
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender couldn't import {path}")
    return [o for o in bpy.data.objects if o not in before]


def rigify_ik_to_fk(rig, **limb):
    """Rigify's "IK -> FK" snap for one limb of `rig`. Rigify registers the operator per rig, under
    its rig_id, and has no function for it."""
    from ..editing import switch

    switch(rig, "POSE")
    operator = getattr(bpy.ops.pose, f"rigify_limb_ik2fk_{rig.data['rig_id']}")
    operator(**limb)


def render_still(scene, path):
    """Renders `scene` with its own settings and writes the image to `path`. The data API can't
    render."""
    scene.render.filepath = str(path)
    with bpy.context.temp_override(scene=scene):
        result = bpy.ops.render.render(write_still=True, scene=scene.name)
    if "FINISHED" not in result:
        raise RuntimeError(f"Blender couldn't render {scene.name}")
