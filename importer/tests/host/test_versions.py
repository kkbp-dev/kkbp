"""Schema Version and Game: what a bundle from a newer or different importer gets."""

import pytest

import bundle
from bundle_builder import BundleBuilder


def _files(version="1.0", game="KK"):
    b = BundleBuilder()
    b.schema_version, b.game = version, game
    return b.files()


def test_newer_minor_opens_with_a_warning(build):
    b = bundle.open_bundle(build(files=_files("1.4")))
    assert b.warnings == ("The bundle's Schema Version 1.4 is newer than this importer's 1.0; "
                          "anything new in it is ignored.",)


def test_newer_minor_keeps_unknown_set_values_with_a_warning(build):
    files = _files("1.1")
    bones = files["skeleton.json"]["bones"]
    bones[1]["group"] = "tail"
    bones[2]["group"] = "tail"
    files["materials.json"]["materials"][0]["role"] = "nails"
    b = bundle.open_bundle(build(files=files))
    assert b.skeleton.bones[1].group == "tail"
    assert b.material("cf_m_body").role == "nails"
    assert len(b.warnings) == 3  # the version, and each unknown value once
    assert any("'tail' isn't a Bone Group this importer knows" in w for w in b.warnings)
    assert any("'nails' isn't a Material Role this importer knows" in w for w in b.warnings)


@pytest.mark.parametrize("version", ["2.0", "0.9"])
def test_other_major_is_rejected(build, version):
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(build(files=_files(version)))
    assert caught.value.problems == [f"manifest.json: Schema Version {version} isn't supported; "
                                     "this importer reads 1.x. Update KKBP."]


def test_bad_version_string(build):
    with pytest.raises(bundle.BundleError, match="'1.0.0' isn't a major.minor version"):
        bundle.open_bundle(build(files=_files("1.0.0")))


@pytest.mark.parametrize("version", ["1.0", "1.3"])
def test_unknown_game_is_rejected(build, version):
    with pytest.raises(bundle.BundleError) as caught:
        bundle.open_bundle(build(files=_files(version, game="AC")))
    assert caught.value.problems == ["This importer doesn't support AC. Update KKBP."]
