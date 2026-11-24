"""Game Profiles: every Game in the contract has one and a Sample Card, and every profile's
data names only roles, groups and slots that exist."""

import pytest

import profiles
from bundle import _contract
from conftest import SAMPLE_CARDS


def test_every_game_in_the_schema_has_a_profile_and_a_sample_card():
    """docs/design/game-profile.md, "Adding a Game"."""
    assert sorted(profiles.games()) == sorted(_contract.GAMES)
    for game in _contract.GAMES:
        assert (SAMPLE_CARDS / f"{game.lower()}.png").is_file(), f"{game} has no Sample Card"


def test_a_game_without_a_profile_is_refused():
    with pytest.raises(profiles.ProfileError, match="This importer doesn't support AC. Update KKBP."):
        profiles.get("AC")


@pytest.mark.parametrize("game", _contract.GAMES)
def test_profiles_resolve(game):
    p = profiles.get(game)
    assert p.game == game and p.template_set in ("KK", "SVS")
    assert p.bones.aim_length > 0 and p.bones.upright


def test_kks_extends_kk_and_changes_nothing():
    kk, kks = profiles.get("KK"), profiles.get("KKS")
    assert kks.extends == "KK"
    assert (kks.template_set, dict(kks.raw_textures), kks.bones) == (kk.template_set, dict(kk.raw_textures), kk.bones)


def test_svs_overrides_only_what_differs():
    kk, svs = profiles.get("KK"), profiles.get("SVS")
    assert svs.template_set == "SVS"
    assert dict(svs.raw_textures) == {"_Cloth_alpha_bot": "alpha_mask_bottom"}  # replaces KK's table
    assert svs.pattern_values == kk.pattern_values  # inherited
    assert svs.bones.upright == kk.bones.upright and svs.bones.aim_length != kk.bones.aim_length


@pytest.mark.parametrize("game", _contract.GAMES)
def test_bone_rules_name_known_roles_and_groups(game):
    rules = profiles.get(game).bones
    for rule in rules.upright:
        assert rule.roles or rule.groups, rule
        assert not (rule.roles and rule.groups), "a rule names roles or groups, not both"
        assert rule.roles <= set(_contract.BONE_ROLES), rule.roles - set(_contract.BONE_ROLES)
        assert rule.groups <= set(_contract.BONE_GROUPS), rule.groups - set(_contract.BONE_GROUPS)
        for anchor in (rule.under, rule.outside):
            assert anchor is None or anchor in _contract.BONE_ROLES
    assert set(rules.chains) <= set(_contract.BONE_GROUPS)


@pytest.mark.parametrize("game", _contract.GAMES)
def test_face_keys_name_keys_body_has(game):
    """Every Expression Name the face rig's Face Key Roles name (ADR 0058) is a shape key of the
    Game's Body, as the committed snapshot of its Golden Sample has them."""
    import json
    from pathlib import Path
    snapshot = json.loads((Path(__file__).parents[1] / "snapshots" / f"{game.lower()}.defaults.json").read_text(
        encoding="utf-8"))
    body = next(v for k, v in snapshot["objects"].items() if k.startswith("Body "))
    keys = set(body["mesh"]["shape_keys"])
    face_keys = profiles.get(game).face_keys
    assert set(face_keys) == set(profiles.FACE_KEY_ROLES)
    missing = sorted({name for pairs in face_keys.values() for name, _ in pairs} - keys)
    assert not missing, f"{game}'s Body has no {missing}"


def test_kks_takes_kks_face_keys_from_kk():
    assert profiles.get("KKS").face_keys == profiles.get("KK").face_keys
