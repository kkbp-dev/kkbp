"""The panel's operators, the scene's Import Options and Preferences."""

import bpy
import pytest

from conftest import submodule

hooks = submodule("pipeline.hooks")
settings = submodule("settings")
pillow = submodule("pillow")
ui_options = submodule("ui.options")
character = submodule("character")
Option = submodule("pipeline").Option


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    saved = dict(hooks._registry)
    hooks._registry.clear()
    prefs = settings.preferences()
    prefs.hooks_folder = ""
    prefs.user_hooks.clear()
    prefs.set_option_defaults({})
    settings.last_result = None
    ui_options.rebuild()
    yield prefs
    hooks._registry.clear()
    hooks._registry.update(saved)
    prefs.hooks_folder = ""
    prefs.user_hooks.clear()
    prefs.set_option_defaults({})
    ui_options.rebuild()


def _tint_hook(ran=None, default=0.5):
    def after(ctx):
        if ran is not None:
            ran.append(ctx.options.tint)
    return hooks.register_hook(after, name="Tinter", source="tests",
                               options=[Option("tint", float, default, "Tint")])


def test_the_ui_is_registered():
    assert hasattr(bpy.ops.kkbp, "import_bundle") and hasattr(bpy.ops.kkbp, "install_pillow")
    assert "KKBP_PT_import" in dir(bpy.types)
    assert settings.preferences() is not None


def test_import_from_the_operator(build):
    path = build()
    assert bpy.ops.kkbp.import_bundle(directory=str(path)) == {"FINISHED"}
    result = settings.last_result
    assert result.ok and result.character_name == "Test Chara"
    assert character.Character(result.character_key).collection is not None


def test_the_log_opens_when_the_import_warns(build):
    path = build()
    bpy.ops.kkbp.import_bundle(directory=str(path))
    assert not settings.last_result.has_problems()
    hooks.register_hook(lambda ctx: ctx.log.warning("Something to look at"), name="Warner", source="tests")
    bpy.ops.kkbp.import_bundle(directory=str(build()))
    result = settings.last_result
    assert result.has_problems() and "see the KKBP log" in result.summary()[1]
    assert result.log_path.is_file() and bpy.ops.kkbp.open_log.poll()


def test_a_bad_bundle_is_reported_not_raised(build):
    path = build()
    (path / "skeleton.json").unlink()
    with pytest.raises(RuntimeError, match="skeleton.json is missing"):  # how bpy.ops reports an ERROR
        bpy.ops.kkbp.import_bundle(directory=str(path))
    assert settings.last_result is None


def test_the_import_button_needs_pillow(monkeypatch):
    assert bpy.ops.kkbp.import_bundle.poll()
    monkeypatch.setattr(pillow, "available", lambda: False)
    assert not bpy.ops.kkbp.import_bundle.poll()


class _Layout:
    """Records what a panel draws: each split is one line of (left label, right prop texts)."""

    def __init__(self, lines=None):
        self.lines = [] if lines is None else lines
        self.texts = []

    def split(self, factor):
        line = _Layout(self.lines)
        self.lines.append(line.texts)
        return line

    def row(self):
        return self

    def label(self, text):
        self.texts.append(text)

    def prop(self, group, name, text=None):
        self.texts.append((name, text))

    def operator(self, *args, **kwargs):
        pass


def test_each_option_is_one_line_beside_its_owner():
    hooks.register_hook(lambda ctx: None, name="One", source="tests",
                        options=[Option("one", bool, True, "Use one")])
    hooks.register_hook(lambda ctx: None, name="Two", source="tests",
                        options=[Option("mode", str, "a", "Mode", choices=("a", "b")), Option("amount", float, 0.5, "Amount")])
    ui_options.rebuild()
    layout = _Layout()
    panel = submodule("ui.panel").KKBP_PT_import_options
    panel.draw(type("Panel", (), {"layout": layout})(), bpy.context)
    assert layout.lines == [["One", ("one", "Use one")], ["Two", ("mode", "")], ["", ("amount", "Amount")]]


def test_scene_options_follow_the_declarations():
    _tint_hook()
    ui_options.rebuild()
    group = bpy.context.scene.kkbp_options
    assert group.tint == pytest.approx(0.5)
    assert ui_options.scene_values(bpy.context.scene) == {}
    group.tint = 0.75
    assert ui_options.scene_values(bpy.context.scene) == {"tint": pytest.approx(0.75)}
    hooks.register_hook(lambda ctx: None, name="Other", source="tests2",
                        options=[Option("shader", str, "off", "Shader", choices=["off", "eevee"])])
    ui_options.rebuild()
    group = bpy.context.scene.kkbp_options
    assert group.tint == pytest.approx(0.75)  # kept across the rebuild
    assert group.shader == "off"
    assert [owner for owner, _ in ui_options.owners()] == ["Tinter", "Other"]


def test_the_operator_passes_the_scene_options(build):
    ran = []
    _tint_hook(ran)
    ui_options.rebuild()
    bpy.context.scene.kkbp_options.tint = 0.25
    bpy.ops.kkbp.import_bundle(directory=str(build()))
    assert ran == [pytest.approx(0.25)]


def test_saved_defaults_apply_to_scripted_imports(build, clean):
    ran = []
    _tint_hook(ran)
    ui_options.rebuild()
    bpy.context.scene.kkbp_options.tint = 0.9
    assert bpy.ops.kkbp.save_option_defaults() == {"FINISHED"}
    assert clean.option_defaults() == {"tint": pytest.approx(0.9)}
    bpy.ops.wm.read_homefile(use_empty=True)
    assert bpy.context.scene.kkbp_options.tint == pytest.approx(0.9)  # a new scene starts from them
    submodule("api").import_bundle(build())
    assert ran == [pytest.approx(0.9)]


def test_reload_lists_user_hooks_in_preferences(build, tmp_path, clean):
    folder = tmp_path / "hooks"
    folder.mkdir()
    for name in ("a", "b"):
        (folder / f"{name}.py").write_text(
            f'@kkbp.hook(name="{name}")\ndef run(ctx):\n    ctx.log.info("ran {name}")\n', encoding="utf-8")
    clean.hooks_folder = str(folder)
    assert bpy.ops.kkbp.reload_hooks() == {"FINISHED"}
    assert [h.key for h in clean.user_hooks] == ["kkbp_user_hooks.a:a", "kkbp_user_hooks.b:b"]
    clean.user_hooks_index = 1
    bpy.ops.kkbp.move_user_hook(direction="UP")
    clean.user_hooks[1].enabled = False
    result = submodule("api").import_bundle(build())
    assert [(h.name, h.status) for h in result.hooks] == [("b", "ran"), ("a", "off")]
    assert [s.path.name for s in settings.loaded_scripts] == ["a.py", "b.py"]


def test_the_startup_check_runs_cleanly(tmp_path, clean):
    clean.hooks_folder = str(tmp_path / "nowhere")
    from conftest import kkbp
    assert kkbp._after_startup() is None  # run once
    assert settings.loaded_scripts[0].error == "the hooks folder doesn't exist"
