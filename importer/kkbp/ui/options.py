"""The Import Options on the scene: a property group generated from the declarations.

Current values live on the scene (`scene.kkbp_options`), so a .blend remembers how it was imported.
The group is rebuilt only when the declared options change, for example after the hooks folder is
reloaded. Blender keeps scene values as ID properties under each option's name, so values for
options whose names haven't changed survive a rebuild.
"""

from __future__ import annotations

import bpy

from .. import settings
from ..pipeline import hooks
from ..pipeline.options import resolve
from ..pipeline.run import declared_options
from ..pipeline.steps import BUILTIN_HOOKS, STEPS

_registered = None  # (signature, class)


def owners() -> list[tuple[str, list]]:
    """[(owner, [Option, ...]), ...]: each Step's and Hook's options, for the panel. The built-in Hooks
    come in the order they run (BUILTIN_HOOKS), then the user Hooks in the order they registered."""
    ordered = hooks.builtin_in_order(BUILTIN_HOOKS) + [h for h in hooks.registered() if not h.builtin]
    out = [(s.label or f"Step {s.name}", list(s.options)) for s in STEPS if s.options]
    out += [(h.name, list(h.all_options)) for h in ordered if h.all_options]
    return out


def rebuild(force=False):
    """(Re)registers `Scene.kkbp_options` for the options declared now, with Preferences defaults."""
    global _registered
    declared = declared_options(STEPS, hooks.registered())
    defaults = resolve(declared, settings.option_defaults())
    signature = tuple((o.name, o.kind, o.label, o.description, o.choices, o.min, o.max, defaults[o.name])
                      for o in declared)
    if _registered and _registered[0] == signature and not force:
        return
    unregister()
    cls = type("KKBP_PG_import_options", (bpy.types.PropertyGroup,),
               {"__annotations__": {o.name: _property(o, defaults[o.name]) for o in declared}})
    bpy.utils.register_class(cls)
    bpy.types.Scene.kkbp_options = bpy.props.PointerProperty(type=cls)
    _registered = (signature, cls)


def unregister():
    global _registered
    if _registered:
        del bpy.types.Scene.kkbp_options
        bpy.utils.unregister_class(_registered[1])
        _registered = None


def scene_values(scene) -> dict:
    """The options the user has set on this scene; the rest come from Preferences at import."""
    group = getattr(scene, "kkbp_options", None)
    return {n: getattr(group, n) for n in _names() if group is not None and group.is_property_set(n)}


def all_values(scene) -> dict:
    group = getattr(scene, "kkbp_options", None)
    return {n: getattr(group, n) for n in _names()} if group is not None else {}


def _names():
    return [entry[0] for entry in _registered[0]] if _registered else []


def _property(option, default):
    common = {"name": option.label, "description": option.description, "default": default}
    if option.kind == "bool":
        return bpy.props.BoolProperty(**common)
    if option.kind == "int":
        return bpy.props.IntProperty(**common, **_limits(option))
    if option.kind == "float":
        return bpy.props.FloatProperty(**common, **_limits(option))
    if option.kind == "choice":
        return bpy.props.EnumProperty(items=[(i, label, desc) for i, label, desc in option.choices], **common)
    return bpy.props.StringProperty(**common)


def _limits(option):
    out = {}
    if option.min is not None:
        out["min"] = option.min
    if option.max is not None:
        out["max"] = option.max
    return out
