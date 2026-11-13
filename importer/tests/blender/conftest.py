"""In-Blender tests. launch.py puts a copy of the add-on in the profile's `user_default`
repository; it is enabled here once per session, and every test starts from an empty scene."""

import importlib
import json
import os
from pathlib import Path

import addon_utils
import bpy
import pytest

MODULE = "bl_ext.user_default.kkbp"
REPO = Path(__file__).resolve().parents[3]
SAMPLES = REPO / "contract" / "samples"  # the Golden Samples (ignored by git)


def golden(sample):
    """The Golden Sample of `sample` (kk, kks or svs), or skips the test when this working copy has
    none: each developer exports their own with scripts/export-sample.sh (ADR 0031)."""
    path = SAMPLES / sample
    if not (path / "manifest.json").is_file():
        pytest.skip(f"no Golden Sample for {sample}; make it with scripts/export-sample.sh {sample}")
    return path


def _raise(ex):
    raise ex


if addon_utils.enable(MODULE, default_set=True, handle_error=_raise) is None:
    raise RuntimeError(f"Could not enable {MODULE}")

kkbp = importlib.import_module(MODULE)


def _install_pillow():
    """Installs Pillow into this test profile through the installer's offline path, as a user would."""
    pillow = importlib.import_module(f"{MODULE}.pillow")
    assert not pillow.available(), "Pillow is already importable in a fresh test profile"
    pillow.use_wheel(os.environ["KKBP_TEST_PILLOW_WHEEL"])
    assert pillow.install_from_manifest(), "Blender didn't install the Pillow wheel the manifest names"


_install_pillow()


def submodule(name):
    """An add-on module, such as submodule('character')."""
    return importlib.import_module(f"{MODULE}.{name}")


@pytest.fixture(autouse=True)
def empty_scene():
    bpy.ops.wm.read_homefile(use_empty=True)
    assert MODULE in bpy.context.preferences.addons, "reading the empty file disabled the add-on"
    yield


class SceneCache:
    """Scenes that take a while to make (a Golden Sample import, say), made once per session and
    saved; every later request opens the saved file. Each request, the first included, gets a
    freshly opened file, so a test may change the scene as it likes and every test sees the same
    starting point, however the tests are ordered."""

    def __init__(self, tmp_path_factory):
        self._factory = tmp_path_factory
        self._saved = {}  # key -> (scene.blend, what make returned)

    def get(self, key, make):
        """Opens the scene for `key`, making it the first time with `make(folder)`, which builds it
        in an empty file (files it needs, such as a bundle copy, go into `folder` and must outlive the
        session) and returns a value that holds no Blender data. Returns that value."""
        if key not in self._saved:
            folder = self._factory.mktemp("scene")
            bpy.ops.wm.read_homefile(use_empty=True)
            value = make(folder)
            path = folder / "scene.blend"
            # Paths stay as they are, so the images still point into the bundle copy beside it.
            bpy.ops.wm.save_as_mainfile(filepath=str(path), relative_remap=False, compress=False)
            self._saved[key] = (path, value)
        path, value = self._saved[key]
        filepaths = bpy.context.preferences.filepaths
        trusted = filepaths.use_scripts_auto_execute
        # As the scene was in the session that made it: Python drivers, and Rigify's rig UI script.
        filepaths.use_scripts_auto_execute = True
        try:
            bpy.ops.wm.open_mainfile(filepath=str(path), load_ui=False)
        finally:
            filepaths.use_scripts_auto_execute = trusted
        assert MODULE in bpy.context.preferences.addons, "opening a saved scene disabled the add-on"
        return value


@pytest.fixture(scope="session")
def scenes(tmp_path_factory):
    return SceneCache(tmp_path_factory)


@pytest.fixture(scope="session")
def golden_import(scenes):
    """golden_import(sample, hooks=(), options=None) -> (ImportResult, Character): the Golden Sample
    imported into an empty file, with the Import Options' own defaults (not Preferences'), from a
    saved copy after the first time (SceneCache). The result is the first, real import's."""
    from bundle_copy import copy_bundle

    character = importlib.import_module(f"{MODULE}.character")
    settings = importlib.import_module(f"{MODULE}.settings")

    def _import(sample, hooks=(), options=None):
        key = ("golden", sample, tuple(hooks), json.dumps(options or {}, sort_keys=True))

        def make(folder):
            copy = copy_bundle(golden(sample), folder / sample)
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(settings, "option_defaults", lambda: {})
                result = kkbp.api.import_bundle(copy, hooks=list(hooks), options=dict(options or {}))
            assert result.ok, f"{result.failed_step}: {result.error}"
            return result

        result = scenes.get(key, make)
        return result, character.Character(result.character_key)
    return _import


@pytest.fixture
def build(tmp_path):
    """build(builder=None) writes a test bundle (the default KK Character if no builder)."""
    from bundle_builder import BundleBuilder

    def _build(builder=None, files=None):
        builder = builder or BundleBuilder()
        return builder.build(tmp_path / f"b{len(list(tmp_path.iterdir()))}", files)
    return _build
