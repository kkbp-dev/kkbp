"""In-Blender tests. launch.py puts a copy of the add-on in the profile's `user_default`
repository; it is enabled here once per session, and every test starts from an empty scene."""

import importlib
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


@pytest.fixture
def build(tmp_path):
    """build(builder=None) writes a test bundle (the default KK Character if no builder)."""
    from bundle_builder import BundleBuilder

    def _build(builder=None, files=None):
        builder = builder or BundleBuilder()
        return builder.build(tmp_path / f"b{len(list(tmp_path.iterdir()))}", files)
    return _build
