"""KKBP: rebuilds a Character in Blender from an Export Bundle.

Other add-ons and hook scripts use the public API in `api` (docs/design/import-pipeline.md).
"""

import bpy

from . import api, builtin, dropdowns, mesh_loader, translations, ui  # noqa: F401  (api: other add-ons reach it as
#                                         <module>.api; builtin: importing it registers the built-in Hooks)
from .pipeline import hooks


def register():
    translations.register()
    ui.register()
    dropdowns.register()
    # Blender's own glTF add-on may register after this one, and Preferences are only readable
    # once registering is over, so these run a moment later. Every import reloads the hooks too.
    bpy.app.timers.register(_after_startup, first_interval=1.0)


def unregister():
    if bpy.app.timers.is_registered(_after_startup):
        bpy.app.timers.unregister(_after_startup)
    hooks.unregister_hooks(hooks.FOLDER_MODULE)
    dropdowns.unregister()
    ui.unregister()
    translations.unregister()


def _after_startup():
    mesh_loader.check_at_startup()
    try:
        ui.operators.reload()
    except Exception as ex:  # a broken hook setup must never stop Blender starting
        mesh_loader.log.error("Couldn't load the hooks folder: %s", ex)
