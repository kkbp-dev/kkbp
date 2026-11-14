"""The UI in Japanese and Simplified Chinese (issue #37), through Blender's own translation API: the
UI follows Blender's language setting, and the strings in the code stay English.

Each language is a module named by Blender's locale, holding `TRANSLATIONS`: English string ->
translation. A string with no entry shows in English. What is translated is what the user reads in
panels, dialogs, Preferences and tooltips. Log lines, reports and errors stay English, so a bug
report reads the same in every language, and so do names from the game (ADR 0004).

Blender looks a string up here before its own catalogue, for every part of its UI, so the tables
leave out words Blender already translates ("Save", "Cancel", "Bones"...): those keep Blender's
wording, here and everywhere else.
"""

import bpy

from .. import pillow
from . import ja_JP, zh_HANS

LANGUAGES = {"ja_JP": ja_JP, "zh_HANS": zh_HANS}
# Blender looks a property's name, a tooltip and a label up in "*", and an operator's name in "Operator".
CONTEXTS = ("*", "Operator")
# The context of the few strings a language's IN_CONTEXT translates: a panel or property says it is in
# this one (`bl_translation_context`, `translation_context`), so Blender's own entry for the same
# English word isn't used for it and isn't replaced anywhere else.
CONTEXT = "KKBP"
# What a string with {version} in it is filled with, as the code that shows it does.
FILLED = {"version": pillow.PILLOW_VERSION}


def table() -> dict:
    """{locale: {(context, English): translation}}, as `bpy.app.translations.register` takes it."""
    out = {}
    for locale, language in LANGUAGES.items():
        entries = out[locale] = {}
        for english, translated in language.TRANSLATIONS.items():
            if "{version}" in english:
                english, translated = english.format(**FILLED), translated.format(**FILLED)
            for context in CONTEXTS:
                entries[context, english] = translated
        for english, translated in language.IN_CONTEXT.items():
            entries[CONTEXT, english] = translated
    return out


def iface(text: str, context: str = "*") -> str:
    """`text` in Blender's UI language. For text put together when it is drawn; Blender translates a
    whole label, button, property name or tooltip by itself."""
    return bpy.app.translations.pgettext_iface(text, context)


def register():
    bpy.app.translations.register(__name__, table())


def unregister():
    bpy.app.translations.unregister(__name__)
