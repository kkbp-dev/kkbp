"""The KKBP panel in the 3D Viewport's sidebar."""

from __future__ import annotations

import bpy

from .. import mesh_loader, pillow, settings
from ..translations import CONTEXT, iface
from . import options


class KKBP_PT_import(bpy.types.Panel):
    bl_idname = "KKBP_PT_import"
    bl_label = "KKBP"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"

    def draw(self, context):
        layout = self.layout
        if not pillow.available():
            layout.label(text=pillow.REQUIRED_MESSAGE, icon="ERROR")
            layout.operator("kkbp.install_pillow", icon="IMPORT")
            layout.operator("kkbp.install_pillow_file", icon="FILE")
            return
        for message in mesh_loader.problems():
            layout.label(text=message, icon="ERROR")
        layout.operator("kkbp.import_bundle", text="Import Export Bundle", icon="IMPORT")

        result = settings.last_result
        if result is not None:
            box = layout.box()
            for i, line in enumerate(result.summary()):
                box.label(text=line, icon=("CHECKMARK" if result.ok else "ERROR") if i == 0 else "INFO")
            if result.has_problems() and result.log_path is not None:
                box.operator("kkbp.open_log", icon="TEXT")


class KKBP_PT_import_options(bpy.types.Panel):
    bl_label = "Import Options"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"
    bl_parent_id = "KKBP_PT_import"

    @classmethod
    def poll(cls, context):
        return pillow.available()

    def draw(self, context):
        layout = self.layout
        group = getattr(context.scene, "kkbp_options", None)
        owned = options.owners()
        if group is None or not owned:
            layout.label(text="No Step or Hook declares an option yet.")
            return
        # One line per option: the owner's name beside its first option, the rest below it. A
        # dropdown on the owner's line goes without its label, which the owner's name stands for.
        for owner, declared in owned:
            for i, option in enumerate(declared):
                split = layout.split(factor=0.4)
                name = split.row()
                name.alignment = "RIGHT"
                name.label(text=owner if i == 0 else "")
                split.prop(group, option.name, text="" if i == 0 and option.choices else option.label)
        layout.operator("kkbp.save_option_defaults")


class KKBP_PT_hooks(bpy.types.Panel):
    bl_label = "Hooks"
    bl_translation_context = CONTEXT  # not Blender's own "Hooks", the modifiers
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KKBP"
    bl_parent_id = "KKBP_PT_import"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        prefs = settings.preferences()
        if prefs is not None:
            layout.prop(prefs, "hooks_folder", text="")
        layout.operator("kkbp.reload_hooks", icon="FILE_REFRESH")
        if not settings.loaded_scripts:
            layout.label(text="No hook scripts loaded")
        for script in settings.loaded_scripts:
            if script.error:
                layout.label(text=f"{script.path.name}: {script.error}", icon="ERROR")
            else:
                layout.label(text=f"{script.path.name}: {', '.join(script.hooks) or iface('no Hooks')}", icon="SCRIPT")


classes = (KKBP_PT_import, KKBP_PT_import_options, KKBP_PT_hooks)
