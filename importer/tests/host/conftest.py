"""Host tests: run on importer/.venv's Python (Blender's own interpreter), without Blender.

The bundle package is imported directly, as `bundle`, so the add-on's bpy-using __init__ never runs.
"""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
ADDON = REPO / "importer" / "kkbp"
SAMPLES = REPO / "contract" / "samples"  # the Golden Samples (ignored by git)
SCHEMAS = REPO / "contract" / "schema"
SAMPLE_CARDS = REPO / "contract" / "sample-cards"


def golden(sample):
    """The Golden Sample of `sample` (kk, kks or svs), or skips the test when this working copy has
    none: each developer exports their own with scripts/export-sample.sh (ADR 0031)."""
    path = SAMPLES / sample
    if not (path / "manifest.json").is_file():
        pytest.skip(f"no Golden Sample for {sample}; make it with scripts/export-sample.sh {sample}")
    return path


for path in (ADDON, REPO / "importer" / "tests", REPO / "importer" / "tools"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from bundle_builder import BundleBuilder  # noqa: E402


@pytest.fixture
def build(tmp_path):
    """build(builder=None, files=None) writes a bundle (the default KK Character if no builder)."""
    def _build(builder=None, files=None):
        builder = builder or BundleBuilder()
        return builder.build(tmp_path / f"b{len(list(tmp_path.iterdir()))}", files)
    return _build
