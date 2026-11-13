"""The joint corrections on imported Characters: the Core Import's armature, and the rig the Rigify
Hook generates, where the Hook has put them back. Each test bends the limbs (through the rig's FK
controls with Rigify) and checks every correction bone against the rules for the pose the armature
is in."""

import json
import math

import bpy
import pytest
from mathutils import Euler, Quaternion

from bundle_copy import copy_bundle
from conftest import golden, kkbp, submodule

character = submodule("character")
jc = submodule("joint_corrections")
rules_mod = submodule("profiles.corrections")
gm = submodule("profiles.gamemath")

POSITION, DEGREES, SCALE = 5e-5, 0.1, 5e-4
# (x, y, z) degrees for each limb's bones; moderate, so no angle sits on an Euler edge.
BEND = {"upper_arm": (20, 15, -35), "lower_arm": (5, -60, 10), "hand": (25, 10, 30),
        "upper_leg": (-40, 10, 15), "lower_leg": (55, 0, 0), "foot": (15, 20, -10)}
RIG_FK = {"upper_arm": "arm_fk", "lower_arm": "elbow_fk", "hand": "wrist_fk",
          "upper_leg": "leg_fk", "lower_leg": "knee_fk", "foot": "ankle_fk"}


def _import(tmp_path_factory, game, rigify):
    copy = tmp_path_factory.mktemp(f"jc-{game}") / game
    copy_bundle(golden(game), copy)
    bpy.ops.wm.read_homefile(use_empty=True)
    hooks = ["Rigify"] if rigify else []
    result = kkbp.api.import_bundle(copy, hooks=hooks, options={"use_rigify": rigify})
    assert result.ok
    ch = character.Character(result.character_key)
    with open(copy / "skeleton.json", encoding="utf-8") as f:
        roles = {b["role"]: b["id"] for b in json.load(f)["bones"] if b.get("role")}
    return (ch.rig if rigify else ch.armature), roles


@pytest.fixture(autouse=True)
def empty_scene():
    """Each test imports for itself."""
    yield


def _bend(armature, rigify, roles):
    pose = armature.pose.bones
    if rigify:
        for pb in pose:
            if "IK_FK" in pb.keys():
                pb["IK_FK"] = 1.0  # FK
        for side in ("Left", "Right"):
            for part, control in RIG_FK.items():
                pb = pose.get(f"{side} {control}")
                assert pb is not None, f"the rig has no {side} {control}"
                pb.matrix_basis = Euler([math.radians(a) for a in BEND[part]]).to_matrix().to_4x4()
    else:
        for side in ("left", "right"):
            for part, angles in BEND.items():
                name = roles[f"{side}_{part}"]
                pose[name].matrix_basis = Euler([math.radians(a) for a in angles]).to_matrix().to_4x4()
    bpy.context.view_layer.update()


def _check(armature):
    data = json.loads(armature[jc.STASH])
    rules = rules_mod.parse("stash", data["rules"])
    model = submodule("bundle.model")
    skeleton = model.Skeleton(bones=tuple(
        model.Bone(id=b["name"], name=b["name"], parent=b["parent"], role=None, group="deform",
                   translation=tuple(b["translation"]), rotation=tuple(b["rotation"]), scale=(1.0, 1.0, 1.0),
                   game_scale=tuple(b["game_scale"])) for b in data["bones"]))
    gs = jc.GameSkeleton(skeleton)
    bone_of = jc.tagged_bones(armature)
    for name, child in data["stand_ins"].items():
        if name not in bone_of and child in bone_of:
            bone_of[name] = bone_of[child]
    outputs = sorted({o.bone for o in rules.outputs if f"JC-H {o.bone}" in armature.pose.bones})
    assert outputs, "no correction bone has its corrections"
    pose, bones = armature.pose.bones, armature.data.bones

    def frame(name):
        """The game frame of a bone as the armature has it posed."""
        b = bone_of[name]
        return pose[b].matrix @ (bones[b].matrix_local.inverted() @ gs.frame(name))

    rest = gs.rest_pose([b.name for b in skeleton.bones])
    posed = rest.copy()
    for n, i in rules.inputs.items():
        if i.kind == "euler" and i.bone in bone_of and gs.parent(i.bone) in bone_of:
            q = (frame(gs.parent(i.bone)).inverted() @ frame(i.bone)).to_quaternion()
            posed.bones[i.bone].rotation = (q.x, -q.y, -q.z, q.w)
    given = {n: pose[f"JC-R {n}"].location[0] for n, i in rules.inputs.items()
             if i.kind == "point" and f"JC-R {n}" in pose}
    used = rules.without([n for n in rules.bones() if n not in bone_of])
    expected = rules_mod.evaluate(used, posed, rest, given)
    worst = {}
    for name in outputs:
        parent = gs.parent(name)
        loc, rot, scl = (frame(parent).inverted() @ frame(name)).decompose()
        w = expected.bones[name]
        ps = gs.game_scale(parent)
        want_loc = (-w.position[0] * ps[0], w.position[1] * ps[1], w.position[2] * ps[2])
        want_rot = Quaternion((w.rotation[3], w.rotation[0], -w.rotation[1], -w.rotation[2]))
        turned = math.degrees(rot.rotation_difference(want_rot).angle)
        ratio = [a / b for a, b in zip(w.scale, rest.bones[name].scale)]
        worst[name] = (max(abs(a - b) for a, b in zip(loc, want_loc)), min(turned, 360 - turned),
                       max(abs(a - b) for a, b in zip(scl, ratio)))
    return outputs, {n: e for n, e in worst.items() if e[0] > POSITION or e[1] > DEGREES or e[2] > SCALE}


@pytest.mark.parametrize("game", ["kk", "svs"])
@pytest.mark.parametrize("rigify", [False, True], ids=["fk", "rigify"])
def test_bent_limbs_move_the_correction_bones_by_the_rules(tmp_path_factory, game, rigify):
    armature, roles = _import(tmp_path_factory, game, rigify)
    _bend(armature, rigify, roles)
    # the game's own reading of the knee: the drivers saw the limbs bend
    assert abs(armature.pose.bones["JC-R knee_L"].location[0]) > 20
    assert abs(armature.pose.bones["JC-R knee_R"].location[0]) > 20
    outputs, bad = _check(armature)
    assert len(outputs) > 30
    assert not bad, bad
    drivers = armature.animation_data.drivers
    assert all(d.driver.is_valid and d.driver.is_simple_expression for d in drivers
               if d.data_path.startswith('pose.bones["JC-'))


def test_the_option_off_leaves_no_corrections(tmp_path_factory):
    copy = tmp_path_factory.mktemp("jc-off") / "kk"
    copy_bundle(golden("kk"), copy)
    bpy.ops.wm.read_homefile(use_empty=True)
    result = kkbp.api.import_bundle(copy, hooks=[], options={"joint_corrections": False})
    assert result.ok
    armature = character.Character(result.character_key).armature
    assert jc.STASH not in armature
    assert not [b for b in armature.data.bones if b.name.startswith(jc.PREFIX)]
