"""The panel, its operators and Preferences: the UI only. Everything they do goes through
kkbp.import_bundle, Character and the other modules any script can call."""

import bpy

from . import operators, options, panel, preferences, tools

_classes = (preferences.classes + operators.classes + tools.operator_classes + panel.classes
            + tools.panel_classes)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    options.rebuild()


def unregister():
    options.unregister()
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
