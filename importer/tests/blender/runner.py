"""Runs pytest on importer/tests/blender/ inside Blender. Started by launch.py:

    blender --background --factory-startup --python-exit-code 1 --python runner.py -- \
        --site <importer/.venv site-packages> -- [pytest arguments]
"""

import importlib.abc
import importlib.machinery
import sys
from pathlib import Path

argv = sys.argv[sys.argv.index("--") + 1:]
site = argv[argv.index("--site") + 1]
pytest_args = argv[argv.index("--", argv.index("--site")) + 1:] if argv.count("--") else []
HERE = Path(__file__).resolve().parent
sys.path[:0] = [site, str(HERE), str(HERE.parent)]


class _HideVenvPackages(importlib.abc.MetaPathFinder):
    """The venv has Pillow and numpy for the host tests of kkbp/atlas and kkbp/shading. Inside
    Blender, Pillow must come only through the add-on's installer and numpy only from Blender, as
    they do for users, so the venv's copies are out of sight."""

    HIDDEN = ("PIL", "numpy")

    def find_spec(self, name, path=None, target=None):
        if name not in self.HIDDEN:
            return None
        spec = importlib.machinery.PathFinder.find_spec(name, [p for p in sys.path if p != site])
        if spec is None:
            raise ModuleNotFoundError(f"No module named '{name}'", name=name)
        return spec


sys.meta_path.insert(0, _HideVenvPackages())

import pytest  # noqa: E402

code = pytest.main([str(HERE), "-q", "-p", "no:cacheprovider", "--rootdir", str(HERE), *pytest_args])
sys.exit(int(code))
