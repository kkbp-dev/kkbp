"""The UI translations' tables, checked without Blender: each language module is plain
data, so it is loaded from its file. That every string the UI shows has a translation is looked at
in Blender, by tests/blender/test_translations.py."""

import ast
import importlib.util

import pytest

from conftest import ADDON

TRANSLATIONS = ADDON / "translations"
LANGUAGES = ("de_DE", "es", "fr_FR", "id_ID", "ja_JP", "pt_BR", "ru_RU", "th_TH", "zh_HANS")


def _language(locale):
    spec = importlib.util.spec_from_file_location(f"kkbp_translations_{locale}", TRANSLATIONS / f"{locale}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_strings():
    """Every string in the add-on's code outside the translations. Python joins a string written
    over several lines into one, so a long tooltip is here whole."""
    found = set()
    for path in ADDON.rglob("*.py"):
        if "__pycache__" in path.parts or TRANSLATIONS in path.parents:
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                found.add(node.value)
    return found


def test_every_language_module_is_registered():
    modules = sorted(p.stem for p in TRANSLATIONS.glob("*.py") if p.stem != "__init__")
    assert modules == sorted(LANGUAGES)
    source = (TRANSLATIONS / "__init__.py").read_text(encoding="utf-8")
    assert all(f'": {locale}' in source for locale in LANGUAGES)


@pytest.mark.parametrize("locale", LANGUAGES)
def test_every_translated_string_is_still_in_the_code(locale):
    """A key that is no longer a string in the code translates nothing: the English was reworded, and
    the UI shows the new English until the key follows it."""
    language = _language(locale)
    stale = sorted((set(language.TRANSLATIONS) | set(language.IN_CONTEXT)) - _source_strings())
    assert not stale, f"{locale} translates strings the code no longer has: {stale}"


@pytest.mark.parametrize("locale", LANGUAGES)
def test_every_translation_is_filled_in(locale):
    language = _language(locale)
    for english, translated in {**language.TRANSLATIONS, **language.IN_CONTEXT}.items():
        assert isinstance(translated, str) and translated.strip(), english
        assert ("{version}" in english) == ("{version}" in translated), english


def test_the_languages_translate_the_same_strings():
    first, *others = (_language(locale) for locale in LANGUAGES)
    for other in others:
        assert set(first.TRANSLATIONS) == set(other.TRANSLATIONS)
        assert set(first.IN_CONTEXT) == set(other.IN_CONTEXT)
