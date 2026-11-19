"""Everything that depends on the Blender version, and the few operators the importer still needs,
as functions named for what they do (docs/design/blender-compat-and-testing.md).

`bpy.app.version` appears only here, as a tuple comparison (`bpy.app.version >= (5, 3)`). Each
branch records the Blender version, a link to the release notes, and "remove when the minimum is X
or later". Prefer feature detection (`hasattr`). The minimum is 5.2 LTS, so there are no version
branches yet; NEWER_GLTF_OPTIONS detects its options instead.

Operators are used only where the data API has no equivalent, each with an explicit context
through `bpy.context.temp_override`, so they never depend on what the user has selected.
"""

from __future__ import annotations

import bpy

from ..editing import editing


# glTF importer options that Blenders newer than the minimum have, set when the importer has them,
# with the value the Mesh Loader wants. Each moves into mesh_loader.GLTF_OPTIONS when the minimum
# Blender has it.
NEWER_GLTF_OPTIONS = {
    # New in Blender 5.3's glTF importer: load a texture's KTX version instead of its PNG. Bundles
    # have no KTX textures. Move into GLTF_OPTIONS when the minimum is 5.3 or later.
    "import_ktx_texture": False,
}


def gltf_options(base: dict, available) -> dict:
    """The Mesh Loader's options `base`, plus each NEWER_GLTF_OPTIONS option this importer has."""
    return {**base, **{k: v for k, v in NEWER_GLTF_OPTIONS.items() if k in available}}


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


# Blender's C++ FBX importer (`wm.fbx_import`), with every option it has set here. The Python one
# (`import_scene.fbx`, "Legacy" in Blender 5.3's menu) switches modes with `object.mode_set`, which acts
# on the context's active object: called under a context override that names another object (a
# script's `temp_override(active_object=rig)`), it left its armature in Edit Mode with no pose bones
# and raised (ADR 0053). The C++ one builds the armature through the data API. Both give the game's
# animation FBXs the same bones, rest and pose.
FBX_OPTIONS = {
    "use_anim": True,
    "anim_offset": 1.0,  # the first key on frame 1, as the game's clips are numbered
    "ignore_leaf_bones": False,
    "use_custom_props": False,  # the retarget reads only the pose
    "use_custom_props_enum_as_string": True,
    "use_custom_normals": True,
    "import_subdivision": False,
    "validate_meshes": True,
    "mtl_name_collision_mode": "MAKE_UNIQUE",
    "import_colors": "SRGB",
}
# The operator's file-browser properties (and its `filter_` ones) and the scale, which import_fbx
# passes itself: not import options.
FBX_UI_PROPERTIES = {"rna_type", "filepath", "directory", "files", "check_existing", "filemode", "display_type",
                     "sort_method", "global_scale"}


def import_fbx(path, scale: float) -> list:
    """Imports an FBX file with Blender's FBX importer and returns the objects it made. If the import
    fails, what it made is removed and Blender is back in Object Mode before the error is raised."""
    before = set(bpy.data.objects)
    try:
        result = _run_fbx_importer(str(path), scale)
        if "FINISHED" not in result:
            raise RuntimeError(f"Blender couldn't import {path}")
    except BaseException:
        remove_imported([o for o in bpy.data.objects if o not in before])
        raise
    return [o for o in bpy.data.objects if o not in before]


def _run_fbx_importer(path: str, scale: float):
    with bpy.context.temp_override(view_layer=bpy.context.view_layer):
        return bpy.ops.wm.fbx_import(filepath=path, global_scale=scale, **FBX_OPTIONS)


def remove_imported(objects):
    """Removes `objects` (what import_fbx made) with their data and actions, once nothing else uses
    them, leaving Object Mode first if one of them is in another mode."""
    from ..editing import object_mode, switch

    if any(o.mode != "OBJECT" for o in objects):
        object_mode()
        for obj in (o for o in objects if o.mode != "OBJECT"):  # in a mode but not the active object
            switch(obj, "OBJECT")
    for obj in objects:
        data = obj.data
        action = obj.animation_data.action if obj.animation_data else None
        bpy.data.objects.remove(obj)
        if data is not None and data.users == 0:
            bpy.data.batch_remove([data])
        # The C++ importer gives its action a fake user.
        if action is not None and action.users == int(action.use_fake_user):
            bpy.data.actions.remove(action)


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
