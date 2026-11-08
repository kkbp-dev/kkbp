"""The Golden Samples are local (ADR 0031): a test of a Game with none is skipped, not failed."""

import pytest

from conftest import golden


def test_a_missing_golden_sample_skips_with_how_to_make_it():
    with pytest.raises(pytest.skip.Exception, match=r"no Golden Sample for nope; make it with scripts/export-sample.sh nope"):
        golden("nope")


def test_a_golden_sample_is_its_folder(tmp_path, monkeypatch):
    import conftest
    (tmp_path / "kk").mkdir()
    (tmp_path / "kk" / "manifest.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(conftest, "SAMPLES", tmp_path)
    assert golden("kk") == tmp_path / "kk"
