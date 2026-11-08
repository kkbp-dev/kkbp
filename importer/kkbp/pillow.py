"""Pillow: required before anything can be imported (docs/design/blender-compat-and-testing.md, "Pillow").

Pillow is installed as a wheel through the extension's blender_manifest.toml:

1. the pinned version is downloaded from PyPI with Blender's own pip into `<add-on>/wheels`
   (emptied first), or the user picks a wheel they downloaded elsewhere;
2. the `#wheel_placeholder` line (or an earlier `wheels = [...]` line) in the manifest names it;
3. Blender is told the extension changed, and installs the wheel.
"""

from __future__ import annotations

import importlib
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

log = logging.getLogger("kkbp")

# Raised only on purpose, so the harness tests what users get.
PILLOW_VERSION = "12.3.0"
REQUIRED_MESSAGE = "Pillow is required. Install it from the KKBP panel."

ADDON_DIR = Path(__file__).resolve().parent
_PLACEHOLDER = re.compile(r"^#wheel_placeholder[ \t]*$", re.MULTILINE)
_WHEELS_LINE = re.compile(r"^wheels[ \t]*=[ \t]*\[.*\][ \t]*$", re.MULTILINE)

_found = False
_warned_version = False


class PillowMissing(RuntimeError):
    def __init__(self):
        super().__init__(REQUIRED_MESSAGE)


def available() -> bool:
    """Whether Pillow loads."""
    global _found
    if not _found:
        importlib.invalidate_caches()
        try:
            importlib.import_module("PIL.Image")
            _found = True
        except ImportError:
            return False
    return True


def require():
    """Raises PillowMissing unless Pillow loads. Another extension may have installed a different
    version into the shared site-packages; that is used, with a warning."""
    global _warned_version
    if not available():
        raise PillowMissing()
    if not _warned_version:
        _warned_version = True
        import PIL
        if PIL.__version__ != PILLOW_VERSION:
            log.warning("Pillow %s is installed; KKBP is tested with %s", PIL.__version__, PILLOW_VERSION)


# --- installing -----------------------------------------------------------------------

def wheels_dir() -> Path:
    return ADDON_DIR / "wheels"


def manifest_path() -> Path:
    return ADDON_DIR / "blender_manifest.toml"


def with_wheel(manifest_text: str, wheel_name: str) -> str:
    """The manifest text with its wheels entry naming `wheels/<wheel_name>`."""
    line = f'wheels = ["./wheels/{wheel_name}"]'
    for pattern in (_PLACEHOLDER, _WHEELS_LINE):
        if pattern.search(manifest_text):
            return pattern.sub(line, manifest_text, count=1)
    raise ValueError("blender_manifest.toml has neither #wheel_placeholder nor a wheels line")


def wheel_problem(path: str | Path) -> str | None:
    """Why the wheel at `path` can't be Pillow for this Blender, or None if it can."""
    tags_module, utils = _packaging()
    name = Path(path).name
    try:
        project, _version, _build, tags = utils.parse_wheel_filename(name)
    except utils.InvalidWheelFilename:
        return f"{name} isn't a wheel file name"
    if project != "pillow":
        return f"{name} isn't a Pillow wheel"
    if not set(tags) & set(tags_module.sys_tags()):
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        return f"{name} isn't for this Blender, which runs Python {version} on {_platform()}"
    return None


def download_command(dest: Path) -> list[str]:
    """Blender's own pip downloading the pinned Pillow for the running Python and platform."""
    return [sys.executable, "-m", "pip", "download", f"pillow=={PILLOW_VERSION}", "--only-binary=:all:",
            "--no-deps", "--disable-pip-version-check", "--dest", str(dest)]


def download() -> Path:
    """Downloads the pinned Pillow into an emptied wheels/ folder and returns the wheel."""
    folder = _empty_wheels_dir()
    run = subprocess.run(download_command(folder), capture_output=True, text=True)
    wheels = sorted(folder.glob("*.whl"))
    if run.returncode != 0 or len(wheels) != 1:
        detail = (run.stderr or run.stdout).strip().splitlines()[-1:] or ["no wheel was downloaded"]
        raise RuntimeError(f"Couldn't download Pillow {PILLOW_VERSION}: {detail[0]}")
    return wheels[0]


def use_wheel(path: str | Path):
    """Makes the manifest name wheel `path`, copying it into wheels/ first if it isn't there."""
    path = Path(path).resolve()
    problem = wheel_problem(path)
    if problem:
        raise ValueError(problem)
    if path.parent != wheels_dir().resolve():
        folder = _empty_wheels_dir()
        shutil.copy2(path, folder / path.name)
    manifest = manifest_path()
    manifest.write_text(with_wheel(manifest.read_text(encoding="utf-8"), path.name), encoding="utf-8")


def install_from_manifest() -> bool:
    """Has Blender install the wheel the manifest names, and returns whether Pillow now loads."""
    import addon_utils

    addon_utils.extensions_refresh()
    if available():
        return True
    # Not picked up by the refresh: have Blender re-read the extension the way enabling it does.
    module = __package__
    addon_utils.disable(module, default_set=False)
    addon_utils.enable(module, default_set=False)
    return available()


def _empty_wheels_dir() -> Path:
    folder = wheels_dir()
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir()
    return folder


def _packaging():
    try:
        from packaging import tags, utils
    except ImportError:  # Blender ships packaging; pip's own copy is the fallback
        from pip._vendor.packaging import tags, utils
    return tags, utils


def _platform():
    import platform
    return f"{platform.system()} {platform.machine()}"
