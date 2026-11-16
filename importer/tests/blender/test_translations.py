"""The UI in other languages than English (issue #37): Blender's language setting translates it."""

import warnings

import bpy
import pytest

from conftest import MODULE, submodule

translations = submodule("translations")
hooks = submodule("pipeline.hooks")
steps = submodule("pipeline.steps")
pillow = submodule("pillow")

LANGUAGES = tuple(translations.LANGUAGES)
CONTEXTS = translations.CONTEXTS + (translations.CONTEXT,)
# Names, which read the same in every language.
NAMES = {"KKBP", "Eevee", "Eevee+", "Rigify", "SFW", "VRM", "VRChat", "Unreal"}


@pytest.fixture
def language():
    view = bpy.context.preferences.view
    before = view.language

    def use(locale):
        view.language = locale
    yield use
    view.language = before


def _translated(text, table) -> bool:
    """Whether `text` has a translation: its own (which may read the same as the English), or Blender's."""
    if text in table.TRANSLATIONS or text in table.IN_CONTEXT:
        return True
    return any(bpy.app.translations.pgettext_iface(text, context) != text for context in CONTEXTS)


def _properties(cls):
    """The properties the registered class declares. `bl_rna` of an operator's or a panel's class is
    Blender's plain Operator or Panel, with Blender's own properties."""
    if issubclass(cls, bpy.types.Operator):
        return _operator(cls).get_rna_type().properties
    if issubclass(cls, (bpy.types.PropertyGroup, bpy.types.AddonPreferences)):
        return cls.bl_rna.properties
    return ()


def _operator(cls):
    category, _, name = cls.bl_idname.partition(".")
    return getattr(getattr(bpy.ops, category), name)


def _shown() -> set:
    """Every string the add-on's registered classes, options, Steps and Hooks show."""
    found = set()
    classes = [getattr(bpy.types, name) for name in dir(bpy.types) if name.startswith("KKBP_")]
    assert any(cls.__module__.startswith(MODULE) for cls in classes)
    # The Import Options' group is made from the declared options, and isn't among bpy.types by name.
    options = bpy.context.scene.kkbp_options.bl_rna.properties
    for cls in classes:
        found |= {getattr(cls, "bl_label", ""), getattr(cls, "bl_description", "")}
    for properties in [_properties(cls) for cls in classes] + [options]:
        for prop in properties:
            if prop.identifier == "name" or prop.is_hidden or prop.name in ("", prop.identifier):  # a property with no name of its own
                continue
            found |= {prop.name, prop.description}
            if prop.type == "ENUM":
                for item in prop.enum_items_static:
                    found |= {item.name, item.description}
    for h in hooks.registered():
        if h.builtin:
            found.add(h.name)
    found |= {s.label for s in steps.STEPS if s.label}
    return {text for text in found if text and text not in NAMES and not text.endswith(" px")}


@pytest.mark.parametrize("locale", LANGUAGES)
def test_the_ui_follows_blenders_language(language, locale):
    table = translations.LANGUAGES[locale]
    gettext = bpy.app.translations.pgettext_iface
    assert gettext("Import Options") == "Import Options"  # English until the language is set
    assert table.TRANSLATIONS["Import Options"] != "Import Options"
    language(locale)
    assert gettext("Import Options") == table.TRANSLATIONS["Import Options"]  # a panel's title
    assert gettext("Delete default scene") == table.TRANSLATIONS["Delete default scene"]  # an Import Option
    assert gettext("Export Prep", "Operator") == table.TRANSLATIONS["Export Prep"]  # a button
    assert translations.iface("no Hooks") == table.TRANSLATIONS["no Hooks"]
    tooltip = bpy.types.KKBP_OT_export_prep.bl_description
    assert bpy.app.translations.pgettext_tip(tooltip) == table.TRANSLATIONS[tooltip]


@pytest.mark.parametrize("locale", LANGUAGES)
def test_the_pillow_tooltip_is_translated_with_its_version(language, locale):
    language(locale)
    tooltip = bpy.types.KKBP_OT_install_pillow.bl_description
    translated = bpy.app.translations.pgettext_tip(tooltip)
    assert pillow.PILLOW_VERSION in tooltip and pillow.PILLOW_VERSION in translated and translated != tooltip


def test_a_word_blender_uses_for_something_else_has_its_own_context(language):
    """Blender's "Hooks" are the modifiers. The panel's title is looked up in KKBP's context, and
    Blender's own entry stays as it was."""
    assert bpy.types.KKBP_PT_hooks.bl_translation_context == translations.CONTEXT
    assert bpy.ops.kkbp.run_hook.get_rna_type().properties["hook"].translation_context == translations.CONTEXT
    language("zh_HANS")
    gettext = bpy.app.translations.pgettext_iface
    ours, blenders = gettext("Hooks", translations.CONTEXT), gettext("Hooks")
    assert ours == translations.LANGUAGES["zh_HANS"].IN_CONTEXT["Hooks"]
    assert blenders not in ("Hooks", ours)


@pytest.mark.parametrize("locale", LANGUAGES)
def test_blenders_own_words_keep_blenders_translation(language, locale):
    """Blender looks a string up in the add-on's table first, everywhere in its UI. So the table
    holds no string that Blender's catalogue translates differently."""
    language(locale)
    gettext = bpy.app.translations.pgettext_iface
    translations.unregister()
    try:
        blenders = {(context, english): gettext(english, context)
                    for english in translations.LANGUAGES[locale].TRANSLATIONS for context in translations.CONTEXTS}
    finally:
        translations.register()
    changed = {key: (own, gettext(key[1], key[0])) for key, own in blenders.items()
               if own != key[1] and own != gettext(key[1], key[0])}
    assert not changed


@pytest.mark.parametrize("locale", LANGUAGES)
def test_what_the_ui_shows_is_translated(language, locale):
    """Tells of the strings with no translation yet, which show in English. A warning, not a failure:
    new English text mustn't wait for someone who can write the other languages."""
    shown = _shown()
    assert "Import Options" in shown and "Use Rigify armature" in shown and "Separate all clothing" in shown
    language(locale)
    missing = sorted(text for text in shown if not _translated(text, translations.LANGUAGES[locale]))
    if missing:
        warnings.warn(f"{locale}: {len(missing)} UI strings have no translation: {missing}")
    assert len(missing) < len(shown) / 10
