"""The joint corrections Step's drivers against the rules they come from.

importer/tests/data/corrections/<game>.json.gz is what each game's own correction did to its Sample
Card in each of 801 poses (scripts/probe-corrections.sh); the host tests check that the rules
(profiles/corrections.py) give exactly that. Here each test rebuilds that skeleton as an armature
whose bones point every which way, adds the corrections, poses the limbs as the game was posed, and
compares every correction bone with what the rules give for that pose.

Where the rules read a position, Blender's own is used: the game shears a bone turning under a
parent with an uneven scale (the KK Sample Card's forearms), and Blender bones, which carry no scale
(ADR 0008), turn rigidly, so the hand is a few millimetres elsewhere in the two.
"""

import gzip
import json
import math
import random
from pathlib import Path

import bpy
import pytest
from mathutils import Matrix, Quaternion, Vector

from conftest import submodule

corrections = submodule("joint_corrections")
rules_mod = submodule("profiles.corrections")
gm = submodule("profiles.gamemath")
model = submodule("bundle.model")
profiles = submodule("profiles")
editing = submodule("editing").editing

DATA = Path(__file__).resolve().parents[1] / "data" / "corrections"
POSITION, DEGREES, SCALE = 2e-5, 0.05, 2e-4
# An Euler angle this close to ±180° (or a middle angle this close to ±90°) can come out on either
# side in float arithmetic, in the game as in Blender; such poses don't say anything.
EDGE = 0.05


def _data(game):
    path = DATA / f"{game}.json.gz"
    if not path.is_file():
        pytest.skip(f"no recorded corrections for {game}; make them with scripts/probe-corrections.sh {game}")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _game_pose(data):
    names = {b["name"] for b in data["bones"]}
    return rules_mod.Pose({b["name"]: rules_mod.Bone(b["parent"] if b["parent"] in names else None, tuple(b["position"]),
                                                     tuple(b["rotation"]), tuple(b["scale"])) for b in data["bones"]})


def _offset(pose, name):
    """Where the bone is from its parent, along the parent's axes, in world units: what the exporter
    writes (ADR 0008)."""
    parent = pose.bones[name].parent
    here = pose.to_world(name, (0.0, 0.0, 0.0))
    if parent is None:
        return here
    return gm.rotate(gm.qinv(pose.world_rotation(parent)), gm.sub(here, pose.to_world(parent, (0.0, 0.0, 0.0))))


def _skeleton(data):
    pose = _game_pose(data)
    bones = []
    for b in data["bones"]:
        t, q = _offset(pose, b["name"]), b["rotation"]
        bones.append(model.Bone(
            id=b["name"], name=b["name"], parent=pose.bones[b["name"]].parent, role=None, group="deform",
            translation=(-t[0], t[1], t[2]), rotation=(q[0], -q[1], -q[2], q[3]),
            scale=(1.0, 1.0, 1.0), game_scale=tuple(b["lossy_scale"])))
    return model.Skeleton(bones=tuple(bones))


def _armature(skeleton, game):
    """Bones on the game's frames, each turned by its own random rotation: the corrections mustn't
    depend on which way a Blender bone points."""
    obj = bpy.data.objects.new("Armature", bpy.data.armatures.new("Armature"))
    bpy.context.scene.collection.objects.link(obj)
    rng = random.Random(10)
    turn = {}
    with editing(obj, "EDIT"):
        bones = obj.data.edit_bones
        for b in skeleton.bones:
            eb = bones.new(b.id)
            eb.head, eb.tail = (0, 0, 0), (0, 0.05, 0)
            t = Quaternion(Vector([rng.uniform(-1, 1) for _ in range(3)]), rng.uniform(-math.pi, math.pi)).to_matrix().to_4x4()
            eb.matrix = game.frame(b.name) @ t
        for b in skeleton.bones:
            if b.parent:
                bones[b.id].parent = bones[b.parent]
        for eb in bones:
            turn[eb.name] = game.frame(eb.name).inverted() @ eb.matrix
    return obj, turn


def _local(q, t):
    """A local rotation and a world-unit offset in the parent's frame, from Unity's space into a
    Blender frame's."""
    m = Quaternion((q[3], q[0], -q[1], -q[2])).to_matrix().to_4x4()
    m.translation = (-t[0], t[1], t[2])
    return m


@pytest.mark.parametrize("game", ["kk", "kks", "svs"])
def test_the_drivers_move_the_correction_bones_as_the_game_does(game):
    data = _data(game)
    skeleton = _skeleton(data)
    gs = corrections.GameSkeleton(skeleton)
    rules = profiles.get(game.upper()).corrections
    rules = rules.without([n for n in rules.bones() if gs.id(n) is None])
    obj, turn = _armature(skeleton, gs)
    corrections.build(obj, gs, rules)
    rest = {b["name"]: b for b in data["bones"]}
    lossy = {b["name"]: b["lossy_scale"] for b in data["bones"]}
    depth = {b.name: 0 for b in skeleton.bones}
    for b in skeleton.bones:
        n, d = b.name, 0
        while gs.parent(n):
            n, d = gs.parent(n), d + 1
        depth[b.name] = d
    outputs = sorted({o.bone for o in rules.outputs})
    pose = obj.pose.bones
    view = bpy.context.view_layer

    def game_frame(name):
        return pose[name].matrix @ turn[name].inverted()

    rest_pose = _game_pose(data)
    # The importer's model of the rest pose: each position is the exported offset over the parent's
    # game scale, as the Step reads it.
    model_rest = gs.rest_pose([b.name for b in skeleton.bones])
    eulers = [n for n, i in rules.inputs.items() if i.kind == "euler"]

    def game_pose(case, moved=(), base=None):
        p = (base or rest_pose).copy()
        for name, q in case["set"].items():
            if name in p.bones:
                p.bones[name].rotation = tuple(q)
        for m in moved:
            b = p.bones[m["name"]]
            b.position, b.rotation, b.scale = tuple(m["position"]), tuple(m["rotation"]), tuple(m["scale"])
        return p

    def on_an_edge(case):
        p = game_pose(case)
        for name, v in rules_mod.formula_values(rules, p, eulers, rest_pose).items():
            middle = rules.inputs[name].order[1] == "xyz"[rules.inputs[name].axis]
            if abs(abs(v) - (90 if middle else 180)) < EDGE:
                return True
        return False

    worst, skipped = {}, 0
    for index, case in enumerate(data["poses"]):
        if on_an_edge(case):
            skipped += 1
            continue
        for pb in pose:
            if not pb.name.startswith("JC-"):
                pb.matrix_basis = Matrix.Identity(4)
        view.update()
        for name in sorted((n for n in case["set"] if n in rest), key=depth.get):
            parent = gs.parent(name)
            local = _local(case["set"][name], _offset(rest_pose, name))
            pose[name].matrix = game_frame(parent) @ local @ turn[name]
            view.update()
        given = {n: pose[f"JC-R {n}"].location[0] for n, i in rules.inputs.items() if i.kind == "point"}
        expected = rules_mod.evaluate(rules, game_pose(case, base=model_rest), model_rest, given)
        for name in outputs:
            parent = gs.parent(name)
            got = game_frame(parent).inverted() @ game_frame(name)
            loc, rot, scl = got.decompose()
            want = expected.bones[name]
            ps = lossy[parent]
            w = _local(want.rotation, [c * s for c, s in zip(want.position, ps)])
            ratio = [a / b for a, b in zip(want.scale, model_rest.bones[name].scale)]
            turned = math.degrees(rot.rotation_difference(w.to_quaternion()).angle)
            errors = ((loc - w.translation).length, min(turned, 360 - turned),
                      max(abs(a - b) for a, b in zip(scl, ratio)))
            old = worst.setdefault(name, [(0, None), (0, None), (0, None)])
            for k, e in enumerate(errors):
                if e > old[k][0]:
                    old[k] = (e, index)
    assert skipped < len(data["poses"]) / 10
    bad = {n: w for n, w in worst.items() if w[0][0] > POSITION or w[1][0] > DEGREES or w[2][0] > SCALE}
    assert not bad, "\n".join(f"{n}: {w[0][0]:.6f} m (pose {w[0][1]}), {w[1][0]:.3f}° (pose {w[1][1]}), "
                              f"scale {w[2][0]:.5f} (pose {w[2][1]})" for n, w in sorted(bad.items()))


def test_every_driver_is_a_simple_expression():
    data = _data("kk")
    skeleton = _skeleton(data)
    gs = corrections.GameSkeleton(skeleton)
    obj, _ = _armature(skeleton, gs)
    corrections.build(obj, gs, profiles.get("KK").corrections)
    drivers = obj.animation_data.drivers
    assert len(drivers) > 100
    assert all(d.driver.is_simple_expression for d in drivers), [d.driver.expression for d in drivers
                                                                 if not d.driver.is_simple_expression][:3]
    assert not obj.data.collections_all[corrections.COLLECTION].is_visible
