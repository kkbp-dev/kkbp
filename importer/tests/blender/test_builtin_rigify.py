"""The Rigify Hook on a copy of the KK golden sample: what the legacy scripts left that the port
must keep (bugs found by hand in the UI)."""

import bpy
import pytest

from conftest import submodule

rigify = submodule("builtin.rigify")
prepare = submodule("builtin.rigify.prepare")
names = submodule("builtin.rigify.names")
ground = submodule("builtin.rigify.finish.ground")
board = submodule("builtin.rigify.finish.face.board")


@pytest.fixture(scope="module")
def ch(golden_import):
    return golden_import("kk", hooks=["Rigify"])[1]


@pytest.fixture(autouse=True)
def empty_scene():
    """One import for the module; the scene isn't reset between tests."""
    yield


def _layer(layer, collection):
    if layer.collection == collection:
        return layer
    return next((f for f in (_layer(c, collection) for c in layer.children) if f), None)


def test_the_eye_controller_points_forward_from_the_nose_bridge(ch):
    """The metarig-only bone the head track target is placed from (metarig/head_track.py)."""
    bones = ch.armature.data.bones
    nose = bones[prepare.NOSE_BRIDGE].head_local
    b = bones[prepare.EYE_CONTROLLER]
    assert b.tail_local.y < b.head_local.y  # forward is -Y
    assert b.tail_local.z == pytest.approx(b.head_local.z, abs=1e-5)
    assert b.head_local.y == pytest.approx(nose.y, abs=1e-5)
    assert prepare.EYE_CONTROLLER not in ch.rig.data.bones


def test_the_eye_uv_warps_move_only_the_eyes(ch):
    body = ch.body
    warps = {m.name: m for m in body.modifiers if m.type == "UV_WARP"}
    for role, name in prepare.UV_WARPS.items():
        group = prepare.EYE_GROUPS[role]
        assert warps[name].vertex_group == group and group in body.vertex_groups


def test_the_lowest_visible_vertex_stands_on_the_floor(ch):
    """ADR 0027: legacy's root 4 cm under the ankle sank the KK sample's shoes 1.9 cm."""
    assert ground.lowest_point(ch.rig) == pytest.approx(0.0, abs=1e-5)
    assert ch.rig.data.bones["root"].head_local.z == pytest.approx(0.0, abs=1e-5)


def test_the_pose_follows_the_bones_moved_to_the_ground(ch):
    """Moved with data.transform, the pose stayed 0.019 above the bones until a mode change."""
    bpy.context.view_layer.update()
    # The joint corrections move their bones, and what hangs from them, off the rest pose, as
    # Studio would (ADR 0038).
    def corrected(pb):
        for p in [pb, *pb.parent_recursive]:
            if p.name.startswith("JC-") or "Joint correction" in p.constraints:
                return True
        return False

    for pb in [p for p in ch.rig.pose.bones if not corrected(p)]:
        assert (pb.matrix.translation - pb.bone.matrix_local.translation).length < 1e-4, pb.name


def test_the_rig_is_in_front(ch):
    assert ch.rig.show_in_front and ch.rig.display_type == "TEXTURED"


def test_junk_holds_the_board_labels_and_the_hidden_widgets_and_metarig(ch):
    junk = bpy.data.collections[rigify.JUNK.format(name=ch.name)]
    hidden = bpy.data.collections[rigify.WIDGETS.format(name=ch.name)]
    labels = bpy.data.collections[board.LABELS.format(name=ch.name)]
    assert junk.name in ch.collection.children
    assert set(junk.children) == {hidden, labels} and not junk.objects
    assert ch.armature.name in hidden.objects and list(ch.armature.users_collection) == [hidden]
    assert any(c.name.startswith("WGTS_") for c in hidden.children)
    assert not any(c.name.startswith("WGTS_") for c in bpy.context.scene.collection.children)
    view_layer = bpy.context.view_layer.layer_collection
    assert not _layer(view_layer, junk).exclude and not _layer(view_layer, labels).exclude
    assert _layer(view_layer, hidden).exclude
    assert "Bone Widgets" not in bpy.data.collections


def test_hair_chains_keep_their_unweighted_root(ch):
    """cf_J_hairF_s has no weights but is the front hair chain's root, as in legacy."""
    bones = ch.rig.data.bones
    assert "DEF-cf_J_hairF_s" in bones and "cf_J_hairF_s_master" in bones
    assert bones["DEF-cf_J_hairF_00"].parent.name == "DEF-cf_J_hairF_s"


def _panel_order(collections):
    """The order Rigify's Rig Layers panel draws the collections in."""
    for c in collections:
        yield c
        yield from _panel_order(c.children)


def test_junk_is_a_bone_collection_but_not_in_the_panel(ch):
    """Issue #25: legacy put whichever collection came third on row 1, which was Junk, beside Torso."""
    junk = ch.rig.data.collections_all[prepare.JUNK]
    assert junk.rigify_ui_row == 0
    torso = ch.rig.data.collections_all[names.TORSO_LAYER]
    row = [c.name for c in ch.rig.data.collections_all if c.rigify_ui_row == torso.rigify_ui_row]
    assert sorted(row) == sorted([names.TORSO_LAYER, names.TORSO_LAYER + names.FK_LAYER_SUFFIX])


def test_an_empty_hidden_custom_collection_sits_right_of_nsfw(ch):
    """Issue #7: somewhere for the user's own bones, drawn beside NSFW in the Rig Layers panel."""
    collections = ch.rig.data.collections_all
    custom, nsfw = collections[rigify.CUSTOM_COLLECTION], collections[rigify.NSFW_COLLECTION]
    assert len(custom.bones) == 0 and not custom.is_visible
    assert custom.rigify_ui_row == nsfw.rigify_ui_row > 0
    row = [c.name for c in _panel_order(ch.rig.data.collections) if c.rigify_ui_row == nsfw.rigify_ui_row]
    assert row[row.index(nsfw.name) + 1] == custom.name


def test_bone_finds_every_bundle_bone_where_the_metarig_has_it(ch):
    """ch.bone (ADR 0054) gives each bundle bone the rig has a bone that starts where the metarig's
    bone with that Id does, and the Role bones Rigify's ORG- copies."""
    skeleton, rig, metarig = ch.bundle().skeleton, ch.rig, ch.armature
    found = 0
    for bone in skeleton.bones:
        name = ch.bone(bone.id)  # raises if it can't pick one
        source = next((b for b in metarig.data.bones if b.get("id") == bone.id), None)
        if name is None or source is None:
            continue
        found += 1
        # within 1 mm: grounding the rig moves it a little (finish/ground.py)
        assert (rig.data.bones[name].head_local - source.head_local).length < 1e-3, (bone.id, name)
    assert found > 300
    for bone in skeleton.bones:
        if bone.role in ("head", "neck", "hips", "left_upper_arm"):
            assert ch.bone(bone.id).startswith("ORG-"), bone.role
