"""Parts of the Rigify Hook on the Golden Samples: what it finds the Character has, and the emotion
grid's behaviour when Body lacks an eye key (the rig fingerprint, run.py fingerprint, checks the
rest against the rig before the rewrite)."""

from types import SimpleNamespace

import pytest

from conftest import submodule

build_module = submodule("builtin.rigify.build")
features = submodule("builtin.rigify.metarig.features")
names = submodule("builtin.rigify.names")

# What each Golden Sample's Character has: KK's has the Better Penetration mod's bones, SVS's
# skirt has no bones of its own, and none is male.
EXPECTED = {
    "kk": dict(skirt=True, rigged_tongue=True, better_penetration=True, head_mod=False, male=False),
    "kks": dict(skirt=True, rigged_tongue=True, better_penetration=False, head_mod=False, male=False),
    "svs": dict(skirt=False, rigged_tongue=True, better_penetration=False, head_mod=False, male=False),
}


@pytest.mark.parametrize("sample", sorted(EXPECTED))
def test_features_found_on_the_core_import(golden_import, sample):
    _, ch = golden_import(sample)
    build = build_module.RigBuild(SimpleNamespace(character=ch), ch.armature, kk_extras=False)
    features.detect(build)
    assert vars(build.features) == EXPECTED[sample]


def _driven(keys):
    return {d.data_path for d in keys.animation_data.drivers} if keys.animation_data else set()


def test_the_emotion_grid_makes_the_custom_keys_on_kk(golden_import):
    _, ch = golden_import("kk", hooks=["Rigify"])
    keys = ch.body.data.shape_keys
    driven = _driven(keys)
    for name in names.CUSTOM_SHAPEKEYS_TO_CREATE:
        assert name in keys.key_blocks and f'key_blocks["{name}"].value' in driven, name


def test_the_emotion_grid_stops_at_a_missing_eye_key_and_says_so(golden_import):
    """SVS's Body has no "Eye Both Eyes Shut Tight": the grid stops there, as it always did (see
    "Found, not fixed" in the pull request), and the log names the key."""
    result, ch = golden_import("svs", hooks=["Rigify"])
    keys = ch.body.data.shape_keys
    missing = names.EYE_SHAPEKEY_CLOSED3
    assert missing not in keys.key_blocks
    assert any(missing in w and "emotion grid stops" in w for w in result.warnings), result.warnings
    driven = _driven(keys)
    for key in (names.EYE_SHAPEKEY_CLOSED1, names.EYE_SHAPEKEY_CLOSED2):
        assert f'key_blocks["{key}{names.EYE_SHAPEKEYS_COPY_SUFFIX}"].value' in driven, key
    assert not any(name in keys.key_blocks for name in names.CUSTOM_SHAPEKEYS_TO_CREATE)
