"""The panel's operators. Importing goes through kkbp.import_bundle like every other caller."""

from __future__ import annotations

import os

import bpy

from .. import pillow, settings
from ..bundle import BundleError
from ..mesh_loader import MeshLoaderError
from ..pipeline import import_bundle
from ..pipeline.options import OptionError
from . import options

MANIFEST = "manifest.json"
# Blender 5.2 matches the browser's filter_glob against each file's full path, later versions
# against its name alone; the leading * matches both. Other files it lets through are refused.
MANIFEST_GLOB = "*" + MANIFEST


class KKBP_OT_import_bundle(bpy.types.Operator):
    bl_idname = "kkbp.import_bundle"
    bl_label = "Import Export Bundle"
    bl_description = ("Import a Character from an Export Bundle: choose its manifest.json, "
                      "or open its folder and import with no file chosen")
    bl_options = {"REGISTER", "UNDO"}  # the whole import is one undo step

    # The browser fills both. A script may pass either; with no file chosen, the folder is imported.
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    directory: bpy.props.StringProperty(subtype="DIR_PATH")
    filter_glob: bpy.props.StringProperty(default=MANIFEST_GLOB, options={"HIDDEN"})
    filter_folder: bpy.props.BoolProperty(default=True, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        if not pillow.available():
            cls.poll_message_set(pillow.REQUIRED_MESSAGE)
            return False
        return context.mode == "OBJECT"

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        path = self.bundle_path()
        if path is None:
            self.report({"ERROR"}, f"Choose the Export Bundle's {MANIFEST}, or its folder with no file chosen")
            return {"CANCELLED"}
        try:
            result = import_bundle(path, options.scene_values(context.scene))
        except (BundleError, OptionError, MeshLoaderError, pillow.PillowMissing, ValueError) as ex:
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}
        settings.last_result = result
        lines = result.summary()
        self.report({"INFO"} if result.ok else {"ERROR"}, lines[0])
        for line in lines[1:]:
            self.report({"WARNING"}, line)
        # Finished either way, so a failed import's partly built scene is one undo step too.
        return {"FINISHED"}

    def bundle_path(self) -> str | None:
        """The chosen manifest.json or bundle folder, or None if some other file was chosen."""
        filepath = bpy.path.abspath(self.filepath) if self.filepath else ""
        if not filepath:  # a script that passed only the folder
            return bpy.path.abspath(self.directory)
        if os.path.isdir(filepath):  # no file chosen: the folder the browser is in
            return filepath
        return filepath if os.path.basename(filepath) == MANIFEST else None


class KKBP_OT_install_pillow(bpy.types.Operator):
    bl_idname = "kkbp.install_pillow"
    bl_label = "Install Pillow"
    bl_description = f"Download Pillow {pillow.PILLOW_VERSION} from PyPI with Blender's pip and install it into KKBP"

    def invoke(self, context, event):
        if not bpy.app.online_access:
            return context.window_manager.invoke_confirm(
                self, event, message="Online access is turned off in Blender's Preferences. Download Pillow anyway?")
        return self.execute(context)

    def execute(self, context):
        try:
            pillow.use_wheel(pillow.download())
        except (RuntimeError, ValueError, OSError) as ex:
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}
        return _finish_install(self)


class KKBP_OT_install_pillow_file(bpy.types.Operator):
    bl_idname = "kkbp.install_pillow_file"
    bl_label = "Install Pillow from File"
    bl_description = "Install a Pillow wheel (.whl) you downloaded yourself, for this Blender's Python and platform"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filter_glob: bpy.props.StringProperty(default="*.whl", options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        try:
            pillow.use_wheel(bpy.path.abspath(self.filepath))
        except (ValueError, OSError) as ex:
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}
        return _finish_install(self)


def _finish_install(op):
    if pillow.install_from_manifest():
        op.report({"INFO"}, "Pillow is installed")
        return {"FINISHED"}
    op.report({"ERROR"}, "Blender didn't install the Pillow wheel. Restart Blender and try again.")
    return {"CANCELLED"}


class KKBP_OT_reload_hooks(bpy.types.Operator):
    bl_idname = "kkbp.reload_hooks"
    bl_label = "Reload Hooks"
    bl_description = "Load the scripts in the hooks folder again"

    def execute(self, context):
        try:
            reload()
        except OptionError as ex:
            self.report({"ERROR"}, str(ex))
            return {"CANCELLED"}
        failed = [s for s in settings.loaded_scripts if s.error]
        for s in failed:
            self.report({"WARNING"}, f"{s.path.name}: {s.error}")
        return {"FINISHED"}


class KKBP_OT_open_log(bpy.types.Operator):
    bl_idname = "kkbp.open_log"
    bl_label = "Open KKBP Log"
    bl_description = "Open the last import's log (kkbp_cache/log/log.txt in the Export Bundle) in your text editor"

    @classmethod
    def poll(cls, context):
        result = settings.last_result
        return result is not None and result.log_path is not None and result.log_path.is_file()

    def execute(self, context):
        return bpy.ops.wm.path_open(filepath=str(settings.last_result.log_path))


class KKBP_OT_save_option_defaults(bpy.types.Operator):
    bl_idname = "kkbp.save_option_defaults"
    bl_label = "Save as Defaults"
    bl_description = "Use this scene's Import Options as the defaults for new scenes and scripted imports"

    def execute(self, context):
        settings.preferences().set_option_defaults(options.all_values(context.scene))
        options.rebuild()
        return {"FINISHED"}


def reload():
    """Reloads the hooks folder, lists new user Hooks in Preferences and rebuilds the options."""
    settings.reload_hooks()
    prefs = settings.preferences()
    if prefs is not None:
        prefs.sync_user_hooks()
    options.rebuild()


classes = (KKBP_OT_import_bundle, KKBP_OT_install_pillow, KKBP_OT_install_pillow_file, KKBP_OT_reload_hooks,
           KKBP_OT_open_log, KKBP_OT_save_option_defaults)
