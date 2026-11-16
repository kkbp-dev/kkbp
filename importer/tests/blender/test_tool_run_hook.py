"""Running a built-in Hook on a Character imported without it."""

from conftest import kkbp, submodule

character = submodule("character")
run_hook = submodule("tools.run_hook")
settings = submodule("settings")


def test_outlines_on_an_earlier_import(build, monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})
    result = kkbp.api.import_bundle(build(), hooks=[])
    ch = character.Character(result.character_key)
    assert "Outline Modifier" not in ch.hairs[0].modifiers
    log = run_hook.run_hook(ch, "Outlines")
    # The test bundle's Body has no baked materials, which the Hook reports for this Character.
    assert log.warnings == ["hook Outlines: Body has no baked face or body material, so it has no outline"]
