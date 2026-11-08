"""KKBP's public API, the hook interface (docs/hook-interface.md).

Hook scripts in the hooks folder get this module as `kkbp`. Another add-on finds it through
KKBP's entry in `bpy.context.preferences.addons`: `sys.modules[<that name>].api`.
"""

from types import SimpleNamespace

from . import templates as _templates
from .bundle import Bundle, BundleError, open_bundle
from .character import Character, CharacterError
from .editing import editing
from .pipeline import (HOOK_API_VERSION, HookOutcome, ImportContext, ImportResult, Option, OptionError,
                       StepOutcome, hook, import_bundle, unregister_hooks)
from .templates import TemplateError

# The Material Template functions a Hook may use; the rest of kkbp.templates is internal.
TEMPLATE_FUNCTIONS = ("apply", "param", "params", "texture", "slots", "swap", "variant")
templates = SimpleNamespace(**{name: getattr(_templates, name) for name in TEMPLATE_FUNCTIONS})

__all__ = [
    "HOOK_API_VERSION", "Bundle", "BundleError", "Character", "CharacterError", "HookOutcome", "ImportContext",
    "ImportResult", "Option", "OptionError", "StepOutcome", "TemplateError", "editing", "hook", "import_bundle",
    "open_bundle", "templates", "unregister_hooks",
]
