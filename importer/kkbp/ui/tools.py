"""The Tools panel and its operators: each picks the Character (docs/design/character.md, "Which
Character a tool works on"), calls its tool in kkbp/tools/ and reports."""

from __future__ import annotations

import bpy

from ..character import Character, CharacterError
from ..editing import switch
from ..bundle import BundleError
from ..pipeline import hooks as hook_registry
from ..translations import CONTEXT
from ..tools import (animation, bulk_import, edit_material, export_prep, link_hair,
                     merge_weights, run_hook)


def _character(op, context):
    try:
        return Character.for_tool(context)
    except CharacterError as ex:
        op.report({"ERROR"}, str(ex))
        return None


class KKBP_OT_merge_weights(bpy.types.Operator):
    bl_idname = "kkbp.merge_weights"
    bl_label = "Merge Weights"
    bl_description = "Gives the selected bones' weights to their parents and deletes the bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE" and obj.mode in ("EDIT", "POSE") and \
            Character.of(obj) is not None

    def execute(self, context):
        armature = context.active_object
        ch = _character(self, context)
        if ch is None:
            return {"CANCELLED"}
        if armature.mode == "EDIT":
            names = [b.name for b in armature.data.edit_bones if b.select]
        else:
            names = [b.name for b in context.selected_pose_bones or ()]
        mode = armature.mode
        switch(armature, "OBJECT")
        count = merge_weights.merge_weights(ch, armature, names)
        switch(armature, mode)
        self.report({"INFO"}, f"Merged {count} bones")
        return {"FINISHED"}


class KKBP_OT_export_prep(bpy.types.Operator):
    bl_idname = "kkbp.export_prep"
    bl_label = "Export Prep"
    bl_description = ("Readies the Character for another program: bone names, a simpler skeleton, an atlas, and "
                      "an FBX exporter on its Collection")
    bl_options = {"REGISTER", "UNDO"}

    target: bpy.props.EnumProperty(name="Target", items=[(k, label, "") for k, (label, _) in export_prep.TARGETS.items()])
    simplify: bpy.props.EnumProperty(name="Bones", items=export_prep.SIMPLIFY)
    atlas: bpy.props.EnumProperty(name="Atlas", items=export_prep.ATLAS)
    atlas_size: bpy.props.EnumProperty(
        name="Largest atlas", default=str(export_prep.DEFAULT_ATLAS_SIZE),
        description="An object whose atlas would be wider than this gets several atlases. Nothing is scaled down",
        items=[(str(n), f"{n} px", "") for n in export_prep.ATLAS_SIZES])

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        for name in ("target", "simplify", "atlas"):
            layout.prop(self, name)
        if self.atlas != "none":
            layout.prop(self, "atlas_size")

    def execute(self, context):
        ch = _character(self, context)
        if ch is None:
            return {"CANCELLED"}
        try:
            collection = export_prep.prep(ch, self.target, self.simplify, self.atlas,
                                          log=lambda m: self.report({"INFO"}, m), max_atlas=int(self.atlas_size))
        except (CharacterError, BundleError) as ex:
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Ready to export {collection.name} (its Collection's FBX exporter)")
        return {"FINISHED"}


def _hook_items(self, context):
    return [(h.key, h.name, "Built in" if h.builtin else h.source) for h in hook_registry.registered()]


class KKBP_OT_run_hook(bpy.types.Operator):
    bl_idname = "kkbp.run_hook"
    bl_label = "Run Hook"
    bl_description = "Runs a Hook, such as Rigify, on a Character imported without it"
    bl_options = {"REGISTER", "UNDO"}

    hook: bpy.props.EnumProperty(name="Hook", items=_hook_items, translation_context=CONTEXT)

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        ch = _character(self, context)
        if ch is None:
            return {"CANCELLED"}
        try:
            log = run_hook.run_hook(ch, self.hook)
        except Exception as ex:  # a Hook can raise anything; report it, as a failed Hook is reported on import
            self.report({"ERROR"}, f"{type(ex).__name__}: {ex}")
            return {"CANCELLED"}
        for warning in log.warnings:
            self.report({"WARNING"}, warning)
        return {"FINISHED"}


class KKBP_OT_bulk_import(bpy.types.Operator):
    bl_idname = "kkbp.bulk_import"
    bl_label = "Bulk Import"
    bl_description = ("Imports every Export Bundle in a folder, each in its own Blender in the background, and "
                      "saves a .blend beside each bundle folder")

    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    filter_folder: bpy.props.BoolProperty(default=True, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        module = __package__.rpartition(".")[0]
        done = bulk_import.run(bpy.path.abspath(self.directory), bpy.app.binary_path, module,
                               log=lambda m: self.report({"INFO"}, m))
        failed = [f for f, saved in done if saved is None or saved.name.startswith("Error - ")]
        self.report({"WARNING"} if failed else {"INFO"}, f"Imported {len(done) - len(failed)} of {len(done)} bundles")
        return {"FINISHED"}


class KKBP_OT_import_animation(bpy.types.Operator):
    bl_idname = "kkbp.import_animation"
    bl_label = "Import Animation"
    bl_description = "Puts a Koikatsu .fbx animation on the Character's Rigify rig as a new action"
    bl_options = {"REGISTER", "UNDO"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.fbx", options={"HIDDEN"})
    stretch_arms: bpy.props.BoolProperty(
        name="Lengthen arms", default=True,
        description="Makes the arms 5% longer, which looks closer to the game in some poses")

    @classmethod
    def poll(cls, context):
        return context.mode in ("OBJECT", "POSE")

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        ch = _character(self, context)
        if ch is None:
            return {"CANCELLED"}
        try:
            action = animation.import_animation(ch, bpy.path.abspath(self.filepath), self.stretch_arms,
                                                log=lambda m: self.report({"INFO"}, m))
        except (ValueError, RuntimeError, BundleError) as ex:
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}
        self.report({"INFO"}, f"Imported {action.name}")
        return {"FINISHED"}


class KKBP_OT_ik_snap(bpy.types.Operator):
    bl_idname = "kkbp.ik_snap"
    bl_label = "Snap IKs"
    bl_description = "Snaps the rig's IK controls to their FK pose and switches the limbs to IK"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        ch = Character.of(context.active_object)
        return ch is not None and ch.rig is not None

    def execute(self, context):
        animation.ik_snap(Character.of(context.active_object).rig)
        return {"FINISHED"}


def _active_material(context):
    obj = context.active_object
    return obj.active_material if obj is not None and context.mode == "OBJECT" else None


# Edit Material's Saturate option (ADR 0026; Shown Colours for a graded template, ADR 0056), on the operator and, for the material panel to show
# beside the button, on the scene (`scene.kkbp_edit_saturate`).
_SATURATE = dict(
    name="Saturate",
    description="Whether the textures and colours go through the game's colour grade, as the legacy importer did",
    items=[("DEFAULT", "Default", "Hair and eyebrows saturate, everything else doesn't"),
           ("ON", "On", "Saturate. A material that follows the game's shaders takes its colours as they show "
                        "instead, so the eyedropper can pick them"),
           ("OFF", "Off", "Don't saturate")])


def register_properties():
    bpy.types.Scene.kkbp_edit_saturate = bpy.props.EnumProperty(**_SATURATE, default="DEFAULT")


def unregister_properties():
    del bpy.types.Scene.kkbp_edit_saturate


class _MaterialOperator:
    """Works on the active object's active material."""

    bl_options = {"REGISTER", "UNDO"}
    wants_edit = True  # poll: the active material is an edit material, or isn't one

    @classmethod
    def poll(cls, context):
        mat = _active_material(context)
        return mat is not None and edit_material.is_edit(mat) == cls.wants_edit and \
            Character.of(context.active_object) is not None

    def execute(self, context):
        ch = _character(self, context)
        if ch is None:
            return {"CANCELLED"}
        try:
            self.run(ch, _active_material(context))
        except (edit_material.EditError, BundleError, RuntimeError, ValueError) as ex:
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}
        return {"FINISHED"}

    def log(self, message):
        self.report({"INFO"}, message)


class KKBP_OT_edit_material(_MaterialOperator, bpy.types.Operator):
    bl_idname = "kkbp.edit_material"
    bl_label = "Edit Material"
    bl_description = ("Swaps the active material for an editable one that rebuilds the game's colouring, so its "
                      "colours can be changed and saved")
    wants_edit = False

    # SKIP_SAVE: the panel passes the scene's choice, so a value from an earlier run never sticks.
    saturate: bpy.props.EnumProperty(**_SATURATE, default="DEFAULT", options={"SKIP_SAVE"})

    def run(self, ch, mat):
        saturate = {"DEFAULT": None, "ON": True, "OFF": False}[self.saturate]
        edit = edit_material.edit(ch, mat, saturate=saturate, log=self.log)
        self.report({"INFO"}, f"Editing {edit.name}")


class KKBP_OT_cancel_material(_MaterialOperator, bpy.types.Operator):
    bl_idname = "kkbp.cancel_material"
    bl_label = "Cancel"
    bl_description = "Puts the original material back and drops the changes"

    def run(self, ch, mat):
        edit_material.cancel(mat)


class KKBP_OT_reset_material(_MaterialOperator, bpy.types.Operator):
    bl_idname = "kkbp.reset_material"
    bl_label = "Reset"
    bl_description = "Starts the edit again from the Export Bundle"

    def run(self, ch, mat):
        edit_material.reset(ch, mat, log=self.log)


class KKBP_OT_save_material(_MaterialOperator, bpy.types.Operator):
    bl_idname = "kkbp.save_material"
    bl_label = "Save"
    bl_description = "Bakes the edited colours into the original material's light and dark textures"

    def run(self, ch, mat):
        saved = edit_material.save(ch, mat, log=self.log)
        self.report({"INFO"}, f"Saved {saved.name}")


class KKBP_OT_link_hair(_MaterialOperator, bpy.types.Operator):
    bl_idname = "kkbp.link_hair"
    bl_label = "Link Hair"
    bl_description = "Puts every hair material into edit with the active hair material's settings"

    def run(self, ch, mat):
        link_hair.link_hair(ch, mat, log=self.log)


class KKBP_PT_tools(bpy.types.Panel):
    bl_label = "Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"
    bl_parent_id = "KKBP_PT_import"

    def draw(self, context):
        layout = self.layout
        layout.operator("kkbp.bulk_import", icon="FILE_FOLDER")
        layout.operator("kkbp.run_hook", icon="SCRIPT")
        layout.operator("kkbp.export_prep", icon="EXPORT")
        layout.operator("kkbp.import_animation", icon="ARMATURE_DATA")
        layout.operator("kkbp.ik_snap", icon="LINKED")


class KKBP_PT_material(bpy.types.Panel):
    """The edit material buttons in Properties > Material, under the material list, as the legacy
    importer had them (its EDIT_PT_panel and HAIR_PT_panel)."""

    bl_label = "KKBP"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat is not None and Character.of(context.active_object) is not None and \
            (edit_material.is_edit(mat) or "kkbp_id" in mat)

    def draw(self, context):
        layout = self.layout
        if edit_material.is_edit(context.material):
            row = layout.row(align=True)
            row.operator("kkbp.reset_material", icon="LOOP_BACK")
            row.operator("kkbp.cancel_material", icon="X")
            row.operator("kkbp.save_material", icon="CHECKMARK")
            if link_hair.can_link(context.material):
                layout.operator("kkbp.link_hair", icon="LINKED")
        else:
            row = layout.row(align=True)
            row.operator("kkbp.edit_material", icon="MATERIAL").saturate = context.scene.kkbp_edit_saturate
            row.prop(context.scene, "kkbp_edit_saturate")


operator_classes = (KKBP_OT_merge_weights, KKBP_OT_export_prep, KKBP_OT_run_hook, KKBP_OT_bulk_import,
                    KKBP_OT_import_animation, KKBP_OT_ik_snap, KKBP_OT_edit_material,
                    KKBP_OT_cancel_material, KKBP_OT_reset_material, KKBP_OT_save_material, KKBP_OT_link_hair)
panel_classes = (KKBP_PT_tools, KKBP_PT_material)
