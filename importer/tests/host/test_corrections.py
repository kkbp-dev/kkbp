"""The Game Profiles' joint corrections (profiles/corrections.py) against what each game's own
correction did (importer/tests/data/corrections, recorded by scripts/probe-corrections.sh)."""

import gzip
import json
import math
import random
from pathlib import Path

import pytest

import profiles
from profiles import corrections, gamemath as gm

DATA = Path(__file__).resolve().parents[1] / "data" / "corrections"
GAMES = ["kk", "kks", "svs"]


def _data(game):
    path = DATA / f"{game}.json.gz"
    if not path.is_file():
        pytest.skip(f"no recorded corrections for {game}; make them with scripts/probe-corrections.sh {game}")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _pose(bones):
    names = {b["name"] for b in bones}
    return corrections.Pose({b["name"]: corrections.Bone(b["parent"] if b["parent"] in names else None,
                                                         tuple(b["position"]), tuple(b["rotation"]), tuple(b["scale"]))
                             for b in bones})


@pytest.mark.parametrize("game", GAMES)
def test_the_rules_do_what_the_game_did(game):
    data = _data(game)
    rest = _pose(data["bones"])
    rules = profiles.get(game.upper()).corrections
    assert not [b for b in rules.bones() if b not in rest.bones], "the Sample Card lacks bones the rules name"
    outputs = {o.bone for o in rules.outputs}
    worst = {}
    for case in data["poses"]:
        pose = rest.copy()
        for name, q in case["set"].items():
            if name in pose.bones:
                pose.bones[name].rotation = tuple(q)
        got = corrections.evaluate(rules, pose, rest)
        moved = {m["name"]: m for m in case["moved"]}
        for name in outputs:
            want = moved.get(name)
            w = (tuple(want["position"]), tuple(want["rotation"]), tuple(want["scale"])) if want else (
                rest.bones[name].position, rest.bones[name].rotation, rest.bones[name].scale)
            g = got.bones[name]
            dot = min(1.0, abs(sum(a * b for a, b in zip(gm.qnorm(g.rotation), gm.qnorm(w[1])))))
            errors = (max(abs(a - b) for a, b in zip(g.position, w[0])), math.degrees(2 * math.acos(dot)),
                      max(abs(a - b) for a, b in zip(g.scale, w[2])))
            worst[name] = tuple(max(e, o) for e, o in zip(errors, worst.get(name, (0, 0, 0))))
    # The game works in float32: positions to a micrometre, angles to a few hundredths of a degree.
    bad = {n: w for n, w in worst.items() if w[0] > 2e-6 or w[1] > 0.06 or w[2] > 2e-6}
    assert not bad, bad


@pytest.mark.parametrize("game", GAMES)
def test_every_correction_bone_the_game_moved_is_in_the_rules(game):
    """Except what the rules leave out on purpose: KK's breast colliders and finger tip, which only
    follow the bones they hang from, and SVS's skirt corrections."""
    data = _data(game)
    rules = profiles.get(game.upper()).corrections
    outputs = {o.bone for o in rules.outputs}
    moved = {m["name"] for case in data["poses"] for m in case["moved"]}
    kept = {b["name"] for b in data["bones"]}
    left_out = {n for n in moved - outputs if n in kept and not n.startswith(("cf_d_sk_", "cf_s_sk_"))}
    # bones that move only because a bone above them was set or corrected
    above = {}
    for b in data["bones"]:
        above[b["name"]] = b["parent"]

    def under_something_moved(name):
        p = above.get(name)
        while p is not None:
            if p in outputs or any(p in c["set"] for c in data["poses"]):
                return True
            p = above.get(p)
        return False

    assert not {n for n in left_out if not under_something_moved(n)}


@pytest.mark.parametrize("order", ["yzx", "zxy", "zyx", "yxz"])
def test_the_driver_euler_formula_is_the_games(order):
    names = {"atan2": math.atan2, "asin": math.asin, "degrees": math.degrees, "max": max, "min": min}
    rng = random.Random(order)
    for _ in range(2000):
        q = gm.qnorm(tuple(rng.uniform(-1, 1) for _ in range(4)))
        want = gm.to_euler(order, q)
        # a glTF-space frame's components: the game's y and z are their negatives
        given = {"w": q[3], "x": q[0], "y": -q[1], "z": -q[2]}
        for axis in range(3):
            expression = gm.euler_expression(order, axis)
            assert len(expression) < 256
            got = eval(expression, dict(names), given)  # noqa: S307
            assert abs((got - want[axis] + 180) % 360 - 180) < 1e-9


def test_kks_takes_its_rules_from_kk():
    """KKS's ExpressionBone decompiles to KK's, constant for constant."""
    assert profiles.get("KKS").corrections == profiles.get("KK").corrections


def test_a_formula_naming_something_unknown_is_refused():
    with pytest.raises(corrections.CorrectionError, match="uses unknown nope"):
        corrections.parse("KK", {"inputs": {}, "values": {}, "outputs": [("position", "b", {"x": "nope * 2"})]})


def test_rules_without_a_bone_drop_what_needs_it():
    rules = corrections.parse("KK", {
        "inputs": {"a": ("euler", "limb", "zyx", "x"), "b": ("euler", "other", "zyx", "y")},
        "values": {"twice": "a * 2"},
        "outputs": [("rotation", "c1", "zyx", {"x": "twice"}), ("rotation", "c2", "zyx", {"y": "b"})]})
    trimmed = rules.without(["limb"])
    assert [o.bone for o in trimmed.outputs] == ["c2"]
    assert set(trimmed.inputs) == {"b"} and not trimmed.values
