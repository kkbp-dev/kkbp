"""The Rigify Hook on a copy of the KK golden sample: what the legacy scripts left that the port
must keep (bugs found by hand in the UI)."""

import shutil

import bpy
import pytest

from conftest import golden, kkbp, submodule

character = submodule("character")
rigify = submodule("builtin.rigify")
prepare = submodule("builtin.rigify.prepare")
commons = submodule("builtin.rigify.commons")
legacy = submodule("builtin.rigify.legacy")


@pytest.fixture(scope="module")
def ch(tmp_path_factory):
    copy = tmp_path_factory.mktemp("rigify") / "kk"
    shutil.copytree(golden("kk"), copy, ignore=shutil.ignore_patterns("kkbp_cache"))
    bpy.ops.wm.read_homefile(use_empty=True)
    result = kkbp.api.import_bundle(copy, hooks=["Rigify"], options={"use_rigify": True})
    assert result.ok
    return character.Character(result.character_key)


@pytest.fixture(autouse=True)
def empty_scene():
    """One import for the module; the scene isn't reset between tests."""
    yield


def _layer(layer, collection):
    if layer.collection == collection:
        return layer
    return next((f for f in (_layer(c, collection) for c in layer.children) if f), None)


def test_the_eye_bones_point_forward_from_the_nose_bridge(ch):
    bones = ch.armature.data.bones
    nose = bones[prepare.NOSE_BRIDGE].head_local
    for name in (prepare.EYES_X, prepare.EYE_CONTROLLER, commons.eyesHandleBoneName):
        b = bones[name]
        assert b.tail_local.y < b.head_local.y, name  # forward is -Y
        assert b.tail_local.z == pytest.approx(b.head_local.z, abs=1e-5), name
    assert bones[prepare.EYES_X].head_local.y == pytest.approx(nose.y, abs=1e-5)


def test_the_eye_uv_warps_move_only_the_eyes(ch):
    body = ch.body
    warps = {m.name: m for m in body.modifiers if m.type == "UV_WARP"}
    for role, name in prepare.UV_WARPS.items():
        group = prepare.EYE_GROUPS[role]
        assert warps[name].vertex_group == group and group in body.vertex_groups


def test_the_lowest_visible_vertex_stands_on_the_floor(ch):
    """ADR 0027: legacy's root 4 cm under the ankle sank the KK sample's shoes 1.9 cm."""
    assert legacy.lowest_point(ch.rig) == pytest.approx(0.0, abs=1e-5)
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


def test_junk_holds_the_widgets_and_the_metarig_and_is_hidden(ch):
    junk = bpy.data.collections[rigify.JUNK.format(name=ch.name)]
    assert junk.name in ch.collection.children
    assert ch.armature.name in junk.objects and list(ch.armature.users_collection) == [junk]
    assert any(c.name.startswith("WGTS_") for c in junk.children)
    assert not any(c.name.startswith("WGTS_") for c in bpy.context.scene.collection.children)
    assert _layer(bpy.context.view_layer.layer_collection, junk).exclude
    assert "Bone Widgets" not in bpy.data.collections


def test_the_mouth_grid_drives_body_and_its_tongue(ch):
    for obj in (ch.body,):
        keys = obj.data.shape_keys
        copies = [k.name for k in keys.key_blocks if k.name.endswith(commons.mouthShapekeysCopySuffix)]
        assert copies, obj.name
        driven = {d.data_path for d in keys.animation_data.drivers}
        assert any(f'key_blocks["{name}"].value' in driven for name in copies), obj.name


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
    torso = ch.rig.data.collections_all[commons.torsoLayerName]
    row = [c.name for c in ch.rig.data.collections_all if c.rigify_ui_row == torso.rigify_ui_row]
    assert sorted(row) == sorted([commons.torsoLayerName, commons.torsoLayerName + commons.fkLayerSuffix])


def test_an_empty_hidden_custom_collection_sits_right_of_nsfw(ch):
    """Issue #7: somewhere for the user's own bones, drawn beside NSFW in the Rig Layers panel."""
    collections = ch.rig.data.collections_all
    custom, nsfw = collections[rigify.CUSTOM_COLLECTION], collections[rigify.NSFW_COLLECTION]
    assert len(custom.bones) == 0 and not custom.is_visible
    assert custom.rigify_ui_row == nsfw.rigify_ui_row > 0
    row = [c.name for c in _panel_order(ch.rig.data.collections) if c.rigify_ui_row == nsfw.rigify_ui_row]
    assert row[row.index(nsfw.name) + 1] == custom.name
