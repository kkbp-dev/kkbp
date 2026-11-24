"""Parts of the Rigify Hook on the Golden Samples: what it finds the Character has, and the hands
without the joint-correction bones (the rig fingerprint, run.py fingerprint, checks the rest; the
face rig has its own tests, test_builtin_rigify_face.py)."""

from types import SimpleNamespace

import pytest

from conftest import submodule

build_module = submodule("builtin.rigify.build")
features = submodule("builtin.rigify.metarig.features")

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


# --- the hands without the joint-correction bones (SVS; issues 24 and 26, ADR 0045) ---------------

FINGERS = ("IndexFinger", "MiddleFinger", "RingFinger", "LittleFinger")


def _moved(obj, rig, bone, turn):
    """The indices of `obj`'s vertices that move when the rig's control `bone` turns about its x axis."""
    import bpy

    def positions():
        bpy.context.view_layer.update()
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        return [v.co.copy() for v in evaluated.data.vertices]

    before = positions()
    pose_bone = rig.pose.bones[bone]
    pose_bone.rotation_mode = "XYZ"
    pose_bone.rotation_euler[0] = turn
    after = positions()
    pose_bone.rotation_euler[0] = 0
    return {i for i, (a, b) in enumerate(zip(before, after)) if (a - b).length > 1e-5}


def _in_group(obj, group):
    index = obj.vertex_groups[group].index
    return {v.index for v in obj.data.vertices if any(g.group == index and g.weight > 0 for g in v.groups)}


def _direction(bone):
    return (bone.tail_local - bone.head_local).normalized()


def test_the_svs_wrists_and_fingertips_lie_along_the_hand(golden_import):
    """They came from the Core Import pointing straight up, with nothing to aim them."""
    _, ch = golden_import("svs", hooks=["Rigify"])
    bones = ch.rig.data.bones
    for side, s in (("Left", "L"), ("Right", "R")):
        wrist = bones[f"DEF-{side} wrist"]
        to_fingers = bones[f"MiddleFinger1_{s}"].head_local - wrist.head_local
        assert abs(_direction(wrist).z) < 1e-4 and _direction(wrist).angle(to_fingers) < 0.2, side
        assert 0.02 < wrist.length < 0.08, (side, wrist.length)
        for finger in FINGERS + ("Thumb",):
            second, third = (bones[f"{finger}{n}_{s}"] for n in ((1, 2) if finger == "Thumb" else (2, 3)))
            assert _direction(third).angle(_direction(second)) < 1e-3, third.name
            assert 0.005 < third.length < 0.04, (third.name, third.length)
        for finger in FINGERS:
            assert bones[f"DEF-{finger}1_{s}"].parent.name == f"ORG-{finger}Palm_{s}"
            assert _in_group(ch.body, f"DEF-{finger}Palm_{s}"), finger
        # A thumb bends level, towards the palm, as KK's does: about the vertical.
        assert abs(bones[f"Thumb1_{s}"].matrix_local.col[0].z) > 0.9, side


def test_an_svs_finger_control_bends_its_own_finger(golden_import):
    _, ch = golden_import("svs", hooks=["Rigify"])
    body, rig = ch.body, ch.rig
    moved = _moved(body, rig, "IndexFinger2_L", 0.8)
    assert moved and _in_group(body, "cf_s_index03_L") <= moved
    assert not moved & (_in_group(body, "cf_s_middle03_L") | _in_group(body, "cf_s_index03_R"))
    assert not moved - (_in_group(body, "cf_s_index01_L") | _in_group(body, "cf_s_index02_L")
                        | _in_group(body, "cf_s_index03_L"))
