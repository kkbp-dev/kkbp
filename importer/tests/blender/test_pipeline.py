"""The pipeline skeleton: Steps with Game lists, Import Options, Hooks, ImportResult and the log."""

import os

import bpy
import pytest

from bundle_builder import BundleBuilder
from bundle_copy import copy_bundle
from conftest import kkbp, submodule

pipeline = submodule("pipeline")
hooks = submodule("pipeline.hooks")
run = submodule("pipeline.run")
settings = submodule("settings")
character = submodule("character")
Option, Step = pipeline.Option, pipeline.Step


@pytest.fixture(autouse=True)
def clean_registry(monkeypatch):
    monkeypatch.setattr(hooks, "_registry", {})
    monkeypatch.setattr(settings, "hooks_folder", lambda: None)
    monkeypatch.setattr(settings, "option_defaults", lambda: {})
    monkeypatch.setattr(settings, "user_hook_order", lambda: [])


def _run(path, steps=(), hook_list=(), options=None, declared=()):
    bundle = kkbp.bundle.open_bundle(path)
    resolved = pipeline.options.resolve(list(declared) + [o for s in steps for o in s.options], {}, options)
    return run.run_pipeline(bundle, list(steps), [(h, True) if not isinstance(h, tuple) else h for h in hook_list],
                            resolved)


# --- import_bundle --------------------------------------------------------------------

def test_import_bundle_with_no_steps(build, monkeypatch):
    monkeypatch.setattr(run, "STEPS", [])
    path = build()
    result = kkbp.api.import_bundle(path, hooks=[])
    assert result.ok and result.failed_step is None and result.steps == [] and result.hooks == []
    assert (result.character_name, result.game) == ("Test Chara", "KK")
    ch = character.Character(result.character_key)
    assert ch.collection.name == "Test Chara"
    assert ch.collection.name in bpy.context.scene.collection.children
    assert result.log_path == path / "kkbp_cache" / "log" / "log.txt"
    assert "Importing Test Chara (KK, Schema Version 1.2)" in result.log_path.read_text(encoding="utf-8")
    assert result.summary()[0].startswith("Imported Test Chara")


def test_every_import_makes_a_new_character(build):
    path = build()
    first = kkbp.api.import_bundle(path, hooks=[])
    second = kkbp.api.import_bundle(path, hooks=[])
    assert first.character_key != second.character_key
    assert len([c for c in bpy.data.collections if c.name.startswith("Test Chara")]) == 2


def test_a_bad_bundle_raises_before_anything_is_built(build):
    path = build()
    (path / "skeleton.json").unlink()
    with pytest.raises(kkbp.api.BundleError, match="skeleton.json is missing"):
        kkbp.api.import_bundle(path, hooks=[])
    assert len(bpy.data.collections) == 0


def test_unknown_options_raise_before_anything_is_built(build):
    with pytest.raises(kkbp.api.OptionError, match="unknown Import Option: use_magic"):
        kkbp.api.import_bundle(build(), options={"use_magic": True}, hooks=[])
    assert len(bpy.data.collections) == 0


def test_newer_minor_bundle_warnings_reach_the_result(build):
    b = BundleBuilder()
    b.schema_version = "1.3"
    result = kkbp.api.import_bundle(build(b), hooks=[])
    assert result.ok and len(result.warnings) == 1 and "newer than this importer's" in result.warnings[0]


# --- Steps ----------------------------------------------------------------------------

def test_steps_run_in_order_with_their_game_lists(build):
    ran = []

    def everywhere(ctx):
        ran.append("everywhere")

    def kk_only(ctx):
        ran.append("kk_only")

    def svs_only(ctx):
        ran.append("svs_only")

    steps = [Step(everywhere), Step(svs_only, games=["SVS"]), Step(kk_only, games=["KK", "KKS"])]
    result = _run(build(), steps)
    assert ran == ["everywhere", "kk_only"]
    assert [(s.name, s.status) for s in result.steps] == [
        ("everywhere", "ran"), ("svs_only", "skipped"), ("kk_only", "ran")]
    assert result.steps[1].reason == "not for KK"
    assert all(s.seconds >= 0 for s in result.steps)


def test_game_lists_name_exact_games():
    with pytest.raises(ValueError, match="unknown Game AC"):
        Step(lambda ctx: None, games=["AC"])


def test_what_a_step_gets(build):
    seen = {}

    def look(ctx):
        seen.update(bundle=ctx.bundle, character=ctx.character, game=ctx.game, tint=ctx.options.tint)
        ctx.log.warning("a warning")
        with pytest.raises(AttributeError):
            ctx.options.tint = 2.0

    path = build()
    result = _run(path, [Step(look, options=[Option("tint", float, 0.5, "Tint")])], options={"tint": 1})
    assert seen["bundle"].path == path and seen["game"] == "KK" and seen["tint"] == 1.0
    assert seen["character"].key == result.character_key
    assert result.warnings == ["look: a warning"]


def test_steps_get_the_game_profile_and_hooks_dont(build):
    seen = {}

    def step(ctx):
        seen["step"] = ctx.profile

    def after(ctx):
        seen["hook_has_profile"] = hasattr(ctx, "profile")

    h = hooks.register_hook(after, name="Look", source="tests", builtin=False)
    b = BundleBuilder("SVS")
    _run(build(b), [Step(step)], [h])
    assert seen["step"].game == "SVS" and seen["step"].template_set == "SVS"
    assert seen["hook_has_profile"] is False


def test_a_game_without_a_profile_is_refused_before_anything_is_built(build, monkeypatch):
    profiles = submodule("profiles")
    monkeypatch.delitem(profiles._MODULES, "KKS")
    with pytest.raises(kkbp.api.BundleError, match="This importer doesn't support KKS. Update KKBP."):
        kkbp.api.import_bundle(build(BundleBuilder("KKS")), hooks=[])
    assert len(bpy.data.collections) == 0


def test_a_failed_step_stops_the_import_and_leaves_the_scene(build):
    ran = []

    def makes_something(ctx):
        obj = bpy.data.objects.new("half built", None)
        ctx.character.collection.objects.link(obj)

    def breaks(ctx):
        raise KeyError("cf_j_head")

    def never(ctx):
        ran.append("never")

    hook = hooks.register_hook(lambda ctx: ran.append("hook"), name="after", source="tests")
    result = _run(build(), [Step(makes_something), Step(breaks), Step(never)], [hook])
    assert not result.ok
    assert result.failed_step == "breaks" and result.error == "KeyError: 'cf_j_head'"
    assert [s.status for s in result.steps] == ["ran", "failed"]
    assert ran == [] and result.hooks == []
    assert "half built" in bpy.data.objects
    assert result.summary()[0] == "Import failed in Step breaks: KeyError: 'cf_j_head'"
    assert "Traceback" in result.log_path.read_text(encoding="utf-8")


# --- progress --------------------------------------------------------------------------

class _Counter:
    """Stands in for the window manager's progress counter, which a test can't read back."""
    seen = None

    def __init__(self, total):
        type(self).seen = self.calls = [("begin", total)]

    def advance(self):
        self.calls.append("advance")

    def end(self):
        self.calls.append("end")


def test_progress_counts_every_step_and_hook(build, monkeypatch):
    """Issue 66: the counter reaches its total whatever ran, so skipped Steps and Hooks count too."""
    monkeypatch.setattr(run, "Progress", _Counter)
    hook = hooks.register_hook(lambda ctx: None, name="on", source="tests")
    off = hooks.register_hook(lambda ctx: None, name="off", source="tests")
    result = _run(build(), [Step(lambda ctx: None), Step(lambda ctx: None, games=["SVS"])], [hook, (off, False)])
    assert result.ok
    assert _Counter.seen == [("begin", 4)] + ["advance"] * 4 + ["end"]


def test_progress_ends_when_a_step_fails(build, monkeypatch):
    monkeypatch.setattr(run, "Progress", _Counter)

    def breaks(ctx):
        raise KeyError("cf_j_head")

    hook = hooks.register_hook(lambda ctx: None, name="after", source="tests")
    result = _run(build(), [Step(breaks), Step(lambda ctx: None)], [hook])
    assert not result.ok
    assert _Counter.seen == [("begin", 3), "end"]  # the cursor comes back, without counting on


def test_the_real_counter_runs_headless(build):
    assert _run(build(), [Step(lambda ctx: None)]).ok


# --- Import Options -------------------------------------------------------------------

def test_option_declarations():
    assert Option("use_outlines", bool, True, "Outlines").kind == "bool"
    assert Option("size", int, 2, "Size", min=1, max=4).kind == "int"
    shader = Option("shader", str, "off", "Convert shaders", choices=["off", ("eevee", "Eevee"), ("cycles", "Cycles", "")])
    assert shader.kind == "choice" and shader.choice_ids == ("off", "eevee", "cycles")
    assert Option("prefix", str, "", "Prefix").kind == "text"
    for bad in (lambda: Option("Fix", bool, True, "x"), lambda: Option("x", list, [], "x"),
                lambda: Option("x", int, 1, "x", choices=["a"]), lambda: Option("x", bool, 1, "x"),
                lambda: Option("x", str, "z", "x", choices=["a", "b"]), lambda: Option("x", int, 9, "x", max=4)):
        with pytest.raises(pipeline.OptionError):
            bad()


def test_option_values_come_from_defaults_then_preferences_then_the_call():
    declared = [Option("a", bool, True, "A"), Option("b", int, 1, "B"), Option("c", str, "x", "C")]
    o = pipeline.options.resolve(declared, {"b": 2, "c": 5}, {"c": "y"})
    assert (o.a, o.b, o.c) == (True, 2, "y")  # the stale Preferences value for c is ignored
    assert o.as_dict() == {"a": True, "b": 2, "c": "y"}
    with pytest.raises(pipeline.OptionError, match="option b should be int"):
        pipeline.options.resolve(declared, {}, {"b": "2"})


def test_option_names_are_unique_across_steps_and_hooks():
    step = Step(lambda ctx: None, options=[Option("tint", float, 0.5, "Tint")])
    hook = hooks.register_hook(lambda ctx: None, name="Tinter", source="tests",
                               options=[Option("tint", float, 0.1, "Tint")])
    with pytest.raises(pipeline.OptionError, match="option tint is declared by both Step <lambda> and Hook Tinter"):
        run.declared_options([step], [hook])


# --- Hooks ----------------------------------------------------------------------------

def test_hooks_run_after_the_steps_and_failures_are_warnings(build):
    ran = []
    first = hooks.register_hook(lambda ctx: ran.append("first"), name="first", source="tests")

    def broken(ctx):
        raise RuntimeError("no eyebrows")

    second = hooks.register_hook(broken, name="broken", source="tests")
    third = hooks.register_hook(lambda ctx: ran.append("third"), name="third", source="tests")
    result = _run(build(), [Step(lambda ctx: ran.append("step"))], [first, second, third])
    assert ran == ["step", "first", "third"]
    assert result.ok
    assert [(h.name, h.status) for h in result.hooks] == [("first", "ran"), ("broken", "failed"), ("third", "ran")]
    assert result.hooks[1].reason == "RuntimeError: no eyebrows"
    assert result.warnings == ["Hook broken failed: RuntimeError: no eyebrows"]
    assert "Hook broken failed: RuntimeError: no eyebrows" in result.summary()


def test_every_hook_starts_in_object_mode_with_nothing_selected(build):
    states = []

    def leaves_edit_mode(ctx):
        obj = bpy.data.objects.new("m", bpy.data.meshes.new("m"))
        ctx.character.collection.objects.link(obj)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        with bpy.context.temp_override(active_object=obj, object=obj):
            bpy.ops.object.mode_set(mode="EDIT")

    def look(ctx):
        vl = bpy.context.view_layer
        states.append((bpy.context.mode, vl.objects.active, [o for o in vl.objects if o.select_get()]))

    a = hooks.register_hook(leaves_edit_mode, name="a", source="tests")
    b = hooks.register_hook(look, name="b", source="tests")
    _run(build(), [], [a, b])
    assert states == [("OBJECT", None, [])]
    assert bpy.context.mode == "OBJECT"


def test_hook_interface_version(build):
    ran = []
    ok = hooks.register_hook(lambda ctx: ran.append("ok"), name="ok", source="tests", requires_api="2.0")
    major = hooks.register_hook(lambda ctx: ran.append("major"), name="major", source="tests", requires_api="3.0")
    minor = hooks.register_hook(lambda ctx: ran.append("minor"), name="minor", source="tests", requires_api="2.9")
    old = hooks.register_hook(lambda ctx: ran.append("old"), name="old", source="tests", requires_api="1.0")
    result = _run(build(), [], [ok, major, minor, old])
    assert ran == ["ok"]
    assert [h.status for h in result.hooks] == ["ran", "skipped", "skipped", "skipped"]
    assert result.hooks[1].reason == "it needs hook interface 3.0; this KKBP has 2.0"
    assert result.hooks[3].reason == "it needs hook interface 1.0; this KKBP has 2.0"
    with pytest.raises(ValueError, match="should be major.minor"):
        hooks.register_hook(lambda ctx: None, name="bad", source="tests", requires_api="1")


def test_built_in_switches(build):
    ran = []
    outlines = Option("use_outlines", bool, True, "Outlines")
    shader = Option("convert_shaders", str, "off", "Convert shaders", choices=["off", "eevee"])
    a = hooks.register_hook(lambda ctx: ran.append("outlines"), name="Outlines", source="kkbp.hooks.outlines",
                            switch=outlines, builtin=True)
    b = hooks.register_hook(lambda ctx: ran.append("shaders"), name="Convert shaders", source="kkbp.hooks.shaders",
                            switch=shader, builtin=True)
    result = _run(build(), [], [a, b], options={"use_outlines": False, "convert_shaders": "eevee"}, declared=[outlines, shader])
    assert ran == ["shaders"]
    assert (result.hooks[0].status, result.hooks[0].reason) == ("off", "use_outlines is off")
    with pytest.raises(ValueError, match="only built-in Hooks have a switch"):
        hooks.register_hook(lambda ctx: None, name="mine", source="tests", switch=outlines)
    with pytest.raises(ValueError, match="only built-in Hooks have a switch"):
        kkbp.api.hook(name="mine", switch=outlines)(lambda ctx: None)


def test_hooks_switched_off_in_preferences(build):
    h = hooks.register_hook(lambda ctx: None, name="mine", source="tests")
    result = _run(build(), [], [(h, False)])
    assert (result.hooks[0].status, result.hooks[0].reason) == ("off", "switched off in Preferences")


def test_hook_order(monkeypatch):
    b1 = hooks.register_hook(lambda ctx: None, name="Rigify", source="kkbp.hooks.rigify", builtin=True)
    b2 = hooks.register_hook(lambda ctx: None, name="Convert shaders", source="kkbp.hooks.shaders", builtin=True)
    u1 = hooks.register_hook(lambda ctx: None, name="one", source="a")
    u2 = hooks.register_hook(lambda ctx: None, name="two", source="b")
    u3 = hooks.register_hook(lambda ctx: None, name="new", source="c")
    assert hooks.builtin_in_order(["Convert shaders", "Rigify"]) == [b2, b1]
    with pytest.raises(RuntimeError, match="missing from BUILTIN_HOOKS: Rigify"):
        hooks.builtin_in_order(["Convert shaders"])
    assert hooks.user_in_order([("b:two", False), ("a:one", True), ("gone:old", True)]) == [
        (u2, False), (u1, True), (u3, True)]


def test_the_decorator_and_unregistering():
    @kkbp.api.hook(name="Decorated", requires_api="2.0", options=[Option("strength", float, 1.0, "Strength")])
    def after_import(ctx):
        pass

    (h,) = hooks.registered()
    assert (h.name, h.source, h.builtin, h.fn) == ("Decorated", __name__, False, after_import)
    kkbp.api.unregister_hooks(__name__)
    assert hooks.registered() == []


def test_import_bundle_runs_the_named_hooks(build):
    ran = []
    hooks.register_hook(lambda ctx: ran.append("a"), name="a", source="tests")
    hooks.register_hook(lambda ctx: ran.append("b"), name="b", source="tests")
    result = kkbp.api.import_bundle(build(), hooks=["b"])
    assert ran == ["b"] and [h.name for h in result.hooks] == ["b"]
    with pytest.raises(ValueError, match="no registered Hook 'c'"):
        kkbp.api.import_bundle(build(), hooks=["c"])


# --- the hooks folder -----------------------------------------------------------------

def _folder(tmp_path, scripts):
    folder = tmp_path / "hooks"
    folder.mkdir(exist_ok=True)
    for name, text in scripts.items():
        (folder / name).write_text(text, encoding="utf-8")
    return folder


GOOD = '''
@kkbp.hook(name="Fix eyebrow color", requires_api="2.0",
           options=[kkbp.Option("tint", float, default=0.5, label="Tint")])
def after_import(ctx):
    ctx.log.info(f"tint {ctx.options.tint} on {ctx.character.name} from {ctx.game}")
'''


def test_folder_scripts_get_kkbp_and_run_on_import(build, tmp_path, monkeypatch):
    folder = _folder(tmp_path, {"eyebrows.py": GOOD, "broken.py": "def broken(:\n",
                                "notes.txt": "ignored"})
    monkeypatch.setattr(settings, "hooks_folder", lambda: str(folder))
    result = kkbp.api.import_bundle(build(), options={"tint": 0.25})
    assert [(h.name, h.status) for h in result.hooks] == [("Fix eyebrow color", "ran")]
    assert "tint 0.25 on Test Chara from KK" in result.log_path.read_text(encoding="utf-8")
    loaded = {s.path.name: s for s in settings.loaded_scripts}
    assert sorted(loaded) == ["broken.py", "eyebrows.py"]
    assert loaded["eyebrows.py"].hooks == ["Fix eyebrow color"] and loaded["eyebrows.py"].error is None
    assert loaded["broken.py"].error.startswith("SyntaxError")
    assert "kkbp" not in __import__("sys").modules


def test_the_hook_interface_docs_first_hook_runs_on_a_sample(tmp_path, monkeypatch):
    """The example in docs/hook-interface.md, run from a hooks folder on a copy of the KK sample."""
    from conftest import REPO, golden

    doc = (REPO / "docs" / "hook-interface.md").read_text(encoding="utf-8")
    example = doc.split("## A first Hook", 1)[1].split("```python\n", 1)[1].split("```", 1)[0]
    monkeypatch.setattr(settings, "hooks_folder", lambda: str(_folder(tmp_path, {"example.py": example})))
    settings.reload_hooks()
    copy = tmp_path / "kk"
    copy_bundle(golden("kk"), copy)
    result = kkbp.api.import_bundle(copy, options={"portrait_camera_framing": "face", "portrait_camera_lens": 50.0},
                                    hooks=["Portrait camera"])
    assert [(h.name, h.status) for h in result.hooks] == [("Portrait camera", "ran")]

    from bpy_extras.object_utils import world_to_camera_view

    ch = character.Character(result.character_key)
    cameras = [o for o in ch.collection.objects if o.type == "CAMERA"]
    assert len(cameras) == 1 and cameras[0].data.lens == 50.0
    camera, armature, skeleton = cameras[0], ch.armature, kkbp.bundle.open_bundle(copy).skeleton
    bpy.context.view_layer.update()

    def point(role):
        return armature.matrix_world @ armature.pose.bones[skeleton.by_role(role).id].head

    head, eyes = point("head"), (point("left_eye") + point("right_eye")) / 2
    x, y, depth = world_to_camera_view(bpy.context.scene, camera, head)
    assert (round(x, 3), round(y, 3)) == (0.5, 0.5) and depth > 0, "the camera aims at the head"
    assert (camera.matrix_world.translation - head).dot(eyes - head) > 0, "from in front of the face"
    for role in ("left_eye", "right_eye"):
        assert 0 < world_to_camera_view(bpy.context.scene, camera, point(role)).y < 1, "the eyes are in the frame"


def test_reloading_the_folder_replaces_its_hooks(build, tmp_path, monkeypatch):
    folder = _folder(tmp_path, {"eyebrows.py": GOOD})
    monkeypatch.setattr(settings, "hooks_folder", lambda: str(folder))
    settings.reload_hooks()
    assert [h.name for h in hooks.registered()] == ["Fix eyebrow color"]
    (folder / "eyebrows.py").write_text(GOOD.replace("Fix eyebrow color", "Fix eyebrow colour"), encoding="utf-8")
    settings.reload_hooks()
    assert [h.name for h in hooks.registered()] == ["Fix eyebrow colour"]
    os.remove(folder / "eyebrows.py")
    settings.reload_hooks()
    assert hooks.registered() == []


def test_a_folder_hook_with_a_clashing_option_isnt_loaded(build, tmp_path, monkeypatch):
    hooks.register_hook(lambda ctx: None, name="Tinter", source="some_addon",
                        options=[Option("tint", float, 0.1, "Tint")])
    folder = _folder(tmp_path, {"eyebrows.py": GOOD})
    monkeypatch.setattr(settings, "hooks_folder", lambda: str(folder))
    (script,) = settings.reload_hooks()
    assert script.hooks == []
    assert script.error == "Hook Fix eyebrow color wasn't loaded: option tint is already declared by Hook Tinter"


def test_a_missing_folder_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "hooks_folder", lambda: str(tmp_path / "nowhere"))
    (script,) = settings.reload_hooks()
    assert script.error == "the hooks folder doesn't exist"


# --- the log --------------------------------------------------------------------------

def test_the_log_is_replaced_by_each_import(build):
    path = build()
    first = kkbp.api.import_bundle(path, hooks=[])
    second = kkbp.api.import_bundle(path, hooks=[])
    assert first.log_path == second.log_path
    assert first.log_path.read_text(encoding="utf-8").count("Importing Test Chara") == 1


def test_an_unwritable_bundle_keeps_the_log_on_the_console(build):
    path = build()
    (path / "kkbp_cache").write_text("in the way", encoding="utf-8")  # a file where the folder would go
    result = kkbp.api.import_bundle(path, hooks=[])
    assert result.ok and result.log_path is None
    assert len(result.warnings) == 1 and "couldn't be written into the bundle" in result.warnings[0]
