"""Pillow: the installer's steps and the Pillow-required check. conftest has already installed
Pillow into this profile through the offline path, so these tests start with it available."""

import shutil
import sys
from pathlib import Path

import pytest

from conftest import kkbp, submodule

pillow = submodule("pillow")
settings = submodule("settings")

MANIFEST = '''id = "kkbp"
#wheel_placeholder

[permissions]
'''


def test_the_offline_install_put_the_wheel_in_the_manifest():
    import PIL
    assert PIL.__version__ == pillow.PILLOW_VERSION
    (wheel,) = pillow.wheels_dir().glob("*.whl")
    assert f'wheels = ["./wheels/{wheel.name}"]' in pillow.manifest_path().read_text(encoding="utf-8")
    assert "#wheel_placeholder" not in pillow.manifest_path().read_text(encoding="utf-8")


def test_with_wheel_replaces_the_placeholder_or_an_earlier_wheel():
    once = pillow.with_wheel(MANIFEST, "pillow-1-cp313-cp313-x.whl")
    assert once == MANIFEST.replace("#wheel_placeholder", 'wheels = ["./wheels/pillow-1-cp313-cp313-x.whl"]')
    twice = pillow.with_wheel(once, "pillow-2-cp313-cp313-x.whl")
    assert 'wheels = ["./wheels/pillow-2-cp313-cp313-x.whl"]' in twice and "pillow-1" not in twice
    with pytest.raises(ValueError, match="neither #wheel_placeholder nor a wheels line"):
        pillow.with_wheel('id = "kkbp"\n', "x.whl")


def test_wheel_problems():
    (wheel,) = pillow.wheels_dir().glob("*.whl")
    assert pillow.wheel_problem(wheel) is None
    assert pillow.wheel_problem("notes.txt") == "notes.txt isn't a wheel file name"
    assert pillow.wheel_problem("numpy-2.0.0-cp313-cp313-win_amd64.whl") == \
        "numpy-2.0.0-cp313-cp313-win_amd64.whl isn't a Pillow wheel"
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    other_python = f"pillow-{pillow.PILLOW_VERSION}-cp39-cp39-{wheel.name.split('-')[-1]}"
    assert pillow.wheel_problem(other_python).endswith(f"isn't for this Blender, which runs Python {version} on "
                                                       f"{pillow._platform()}")
    other_platform = f"pillow-{pillow.PILLOW_VERSION}-cp{version.replace('.', '')}-cp{version.replace('.', '')}-win32.whl"
    assert "isn't for this Blender" in pillow.wheel_problem(other_platform)


def test_use_wheel_refuses_a_wrong_wheel(tmp_path):
    bad = tmp_path / "pillow-1.0-cp39-cp39-win32.whl"
    bad.write_bytes(b"")
    before = pillow.manifest_path().read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="isn't for this Blender"):
        pillow.use_wheel(bad)
    assert pillow.manifest_path().read_text(encoding="utf-8") == before


def test_use_wheel_empties_the_wheels_folder_first(tmp_path):
    (wheel,) = pillow.wheels_dir().glob("*.whl")
    copy = tmp_path / wheel.name
    shutil.copy2(wheel, copy)
    (pillow.wheels_dir() / "pillow-0.1-cp313-cp313-old.whl").write_bytes(b"")
    pillow.use_wheel(copy)
    assert [p.name for p in pillow.wheels_dir().iterdir()] == [wheel.name]


def test_the_download_uses_blenders_pip_and_the_pin():
    command = pillow.download_command(Path("/tmp/w"))
    assert command[:4] == [sys.executable, "-m", "pip", "download"]
    assert f"pillow=={pillow.PILLOW_VERSION}" in command and "--only-binary=:all:" in command


def test_import_needs_pillow(monkeypatch, build):
    monkeypatch.setattr(pillow, "available", lambda: False)
    with pytest.raises(pillow.PillowMissing, match="Pillow is required. Install it with the buttons below."):
        kkbp.api.import_bundle(build(), hooks=[])
    with pytest.raises(pillow.PillowMissing):
        settings.require_pillow()
