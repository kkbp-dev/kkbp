"""KKBP's Preferences: the hooks folder, the user Hooks' order and switches, and option defaults."""

from __future__ import annotations

import json

import bpy

from .. import settings
from ..pipeline import hooks


class KKBP_PG_user_hook(bpy.types.PropertyGroup):
    key: bpy.props.StringProperty()
    enabled: bpy.props.BoolProperty(name="On", default=True, description="Run this Hook after each import")


class KKBP_UL_user_hooks(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_property, index=0):
        loaded = hooks.find(item.key) if ":" in item.key else None
        row = layout.row()
        row.prop(item, "enabled", text="")
        row.label(text=item.key.rpartition(":")[2], icon="SCRIPT" if loaded else "ERROR")
        if not loaded:
            row.label(text="not loaded")


class KKBP_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = settings.ADDON

    hooks_folder: bpy.props.StringProperty(
        name="Hooks folder", subtype="DIR_PATH",
        description="Every .py file in this folder is loaded as a Hook script. There is no default folder")
    user_hooks: bpy.props.CollectionProperty(type=KKBP_PG_user_hook)
    user_hooks_index: bpy.props.IntProperty()
    # The Import Option defaults, by name, as JSON. Set from the panel's "Save as defaults".
    option_defaults_json: bpy.props.StringProperty(default="{}")

    def option_defaults(self) -> dict:
        try:
            value = json.loads(self.option_defaults_json or "{}")
        except ValueError:
            return {}
        return value if isinstance(value, dict) else {}

    def set_option_defaults(self, values: dict):
        self.option_defaults_json = json.dumps(values, sort_keys=True)

    def user_hook_order(self) -> list[tuple[str, bool]]:
        return [(h.key, h.enabled) for h in self.user_hooks]

    def sync_user_hooks(self):
        """Adds newly loaded user Hooks at the end, switched on. Hooks that aren't loaded now keep
        their place, so they come back where they were."""
        known = {h.key for h in self.user_hooks}
        for h in hooks.registered():
            if not h.builtin and h.key not in known:
                self.user_hooks.add().key = h.key

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "hooks_folder")
        layout.label(text="User Hooks run after the built-in Hooks, in this order:")
        row = layout.row()
        row.template_list("KKBP_UL_user_hooks", "", self, "user_hooks", self, "user_hooks_index", rows=3)
        col = row.column(align=True)
        col.operator("kkbp.move_user_hook", text="", icon="TRIA_UP").direction = "UP"
        col.operator("kkbp.move_user_hook", text="", icon="TRIA_DOWN").direction = "DOWN"
        col.operator("kkbp.remove_user_hook", text="", icon="X")
        defaults = self.option_defaults()
        box = layout.box()
        box.label(text="Import Option defaults" + ("" if defaults else ": the built-in ones"))
        for name, value in sorted(defaults.items()):
            box.label(text=f"{name} = {value!r}")
        if defaults:
            box.operator("kkbp.reset_option_defaults")


class KKBP_OT_move_user_hook(bpy.types.Operator):
    bl_idname = "kkbp.move_user_hook"
    bl_label = "Move Hook"
    bl_description = "Move the selected Hook up or down the running order"
    bl_options = {"INTERNAL"}
    direction: bpy.props.EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")])

    def execute(self, context):
        prefs = settings.preferences()
        i = prefs.user_hooks_index
        j = i - 1 if self.direction == "UP" else i + 1
        if 0 <= i < len(prefs.user_hooks) and 0 <= j < len(prefs.user_hooks):
            prefs.user_hooks.move(i, j)
            prefs.user_hooks_index = j
        return {"FINISHED"}


class KKBP_OT_remove_user_hook(bpy.types.Operator):
    bl_idname = "kkbp.remove_user_hook"
    bl_label = "Forget Hook"
    bl_description = "Remove the selected Hook from the list. It comes back, at the end, if it is loaded again"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        prefs = settings.preferences()
        if 0 <= prefs.user_hooks_index < len(prefs.user_hooks):
            prefs.user_hooks.remove(prefs.user_hooks_index)
            prefs.user_hooks_index = max(0, prefs.user_hooks_index - 1)
        return {"FINISHED"}


class KKBP_OT_reset_option_defaults(bpy.types.Operator):
    bl_idname = "kkbp.reset_option_defaults"
    bl_label = "Use the built-in defaults"
    bl_description = "Forget the saved Import Option defaults"
    bl_options = {"INTERNAL"}

    def execute(self, context):
        settings.preferences().set_option_defaults({})
        from . import options
        options.rebuild()
        return {"FINISHED"}


classes = (KKBP_PG_user_hook, KKBP_UL_user_hooks, KKBP_AP_preferences, KKBP_OT_move_user_hook,
           KKBP_OT_remove_user_hook, KKBP_OT_reset_option_defaults)
