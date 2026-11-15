"""What the pipeline needs from Preferences and the rest of the add-on, in one place, so the
pipeline itself never reads Blender UI state."""

from __future__ import annotations

import bpy

ADDON = __package__  # this add-on's module name, such as bl_ext.user_default.kkbp

# Set by the hooks folder loader each time it runs: [LoadedScript, ...], for the panel.
loaded_scripts: list = []
# The last ImportResult from the panel's Import button, for its summary. Not saved in the .blend.
last_result = None


def preferences():
    addon = bpy.context.preferences.addons.get(ADDON)
    return addon.preferences if addon else None


def option_defaults() -> dict:
    """The Import Option defaults set in Preferences, by name."""
    prefs = preferences()
    return prefs.option_defaults() if prefs is not None and hasattr(prefs, "option_defaults") else {}


def hooks_folder() -> str | None:
    prefs = preferences()
    folder = getattr(prefs, "hooks_folder", "") if prefs is not None else ""
    return bpy.path.abspath(folder) if folder else None


def user_hook_order() -> list[tuple[str, bool]]:
    """The user Hooks' order and on/off state from Preferences, as (key, switched on)."""
    prefs = preferences()
    return prefs.user_hook_order() if prefs is not None and hasattr(prefs, "user_hook_order") else []


def reload_hooks():
    """Loads the hooks folder again (it is loaded at startup, from Reload hooks and before each import)."""
    from . import api
    from .pipeline import hooks
    from .pipeline.run import declared_options
    from .pipeline.steps import STEPS

    taken = {o.name: f"Step {s.name}" for s in STEPS for o in s.options}
    for h in hooks.registered():
        if h.source != hooks.FOLDER_MODULE and not h.source.startswith(hooks.FOLDER_MODULE + "."):
            taken.update({o.name: f"Hook {h.name}" for o in h.all_options})
    loaded_scripts[:] = hooks.load_folder(hooks_folder(), api, taken)
    declared_options(STEPS, hooks.registered())  # a clash among add-on Hooks is an error here, not mid-import
    return loaded_scripts


def require_pillow():
    """Raises PillowMissing ("Pillow is required. Install it with the buttons below.") until it loads."""
    from . import pillow
    pillow.require()
