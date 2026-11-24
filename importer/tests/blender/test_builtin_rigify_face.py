"""The Rigify Hook's face rig (finish/face, ADR 0058) on the KK and SVS Golden Samples: every control
drives what its Face Key Role names, the jaw opens one open key at a time, the halves move one side,
the presets pose what they say, and the eyes follow their target."""

import json

import bpy
import numpy as np
import pytest

from conftest import submodule

names = submodule("builtin.rigify.names")
controls = submodule("builtin.rigify.finish.face.controls")
board = submodule("builtin.rigify.finish.face.board")
face_tool = submodule("tools.face")
prepare = submodule("builtin.rigify.prepare")

SAMPLES = ("kk", "svs")
T = controls.TRAVEL


@pytest.fixture(scope="module", params=SAMPLES)
def ch(request, golden_import):
    return golden_import(request.param, hooks=["Rigify"])[1]


@pytest.fixture(autouse=True)
def empty_scene():
    """One import per sample for the module; each test puts the face back."""
    yield


def _roles(ch):
    return {role: [(n, w) for n, w in pairs]
            for role, pairs in json.loads(ch.body.data.shape_keys[names.FACE_KEYS_PROPERTY]).items()}


def _update(ch):
    ch.rig.update_tag()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)


def _rest(ch):
    face_tool.reset(ch.rig)
    for bone in (names.EYE_TARGET_BONE, names.LEFT_EYE_TARGET_BONE, names.RIGHT_EYE_TARGET_BONE):
        ch.rig.pose.bones[bone].location = (0, 0, 0)
        ch.rig.pose.bones[bone].scale = (1, 1, 1)
    _update(ch)


def _values(ch, moves):
    _rest(ch)
    for bone, index, value in moves:
        ch.rig.pose.bones[bone].location[index] = value
    _update(ch)
    return {k.name: k.value for k in ch.body.data.shape_keys.key_blocks}


def _driven(ch):
    """The face rig's drivers: the value of every key it drives (the gag code drives its correction keys)."""
    return [d for d in ch.body.data.shape_keys.animation_data.drivers
            if d.data_path.startswith("key_blocks") and d.data_path.endswith(".value") and "Gag eyes (" not in d.data_path]


def test_every_face_driver_is_valid_and_simple(ch):
    """Simple expressions run with auto-run Python off."""
    drivers = _driven(ch)
    assert len(drivers) > 60
    for d in drivers:
        assert d.driver.is_valid and d.driver.is_simple_expression, (d.data_path, d.driver.expression)
    for name in prepare.UV_WARPS.values():
        on = [d for d in ch.body.animation_data.drivers if d.data_path.startswith(f'modifiers["{name}"]')]
        assert len(on) == 4 and all(d.driver.is_simple_expression for d in on), name


def test_the_face_is_at_rest_with_every_control_at_rest(ch):
    values = _values(ch, [])
    busy = {k: v for k, v in values.items() if v > 1e-4 and k != "Basis"}
    assert not busy


@pytest.mark.parametrize("row", controls.TERMS, ids=lambda r: f"{r[0]}-{r[1]}-{r[2]}-{r[3]}")
def test_each_face_control_drives_its_role(ch, row):
    control, transform, sign, role, half = row
    roles = _roles(ch)
    if role not in roles:
        pytest.skip(f"no {role}")
    values = _values(ch, [(controls.bone_name(control), 0 if transform == "LOC_X" else 1, sign * T * 3)])  # past the limit
    if half:
        name = f"{roles[role][0][0]} ({half})"
        assert values[name] == pytest.approx(1.0, abs=0.02), name
    else:
        for name, weight in roles[role]:
            assert values[name] == pytest.approx(weight, abs=0.02), name


def test_the_jaw_opens_one_open_key_at_a_time(ch):
    roles = _roles(ch)
    jaw = controls.bone_name("jaw")
    vowel_at = {"vowel_a": (0, 0), "vowel_i": (0, 1), "vowel_o": (0, -1), "vowel_e": (-1, 0), "vowel_u": (1, 0)}
    half = {g[0]: g[2] for g in board.GRIDS}
    open_keys = [roles[r][0][0] for r in list(vowel_at) + [f"open_mood_{d}" for d in ("up", "down", "left", "right")]
                 if r in roles]
    for role, (x, y) in vowel_at.items():
        values = _values(ch, [(jaw, 1, -2 * T), (board.bone_name("shape"), 0, x * half["shape"]),
                              (board.bone_name("shape"), 1, y * half["shape"])])
        assert {k: round(values[k], 2) for k in open_keys} == {k: (1.0 if k == roles[role][0][0] else 0.0)
                                                              for k in open_keys}, role
    # the open mood grid takes over from the vowel the shape grid points at
    values = _values(ch, [(jaw, 1, -2 * T), (board.bone_name("shape"), 1, half["shape"]),
                          (board.bone_name("open"), 1, half["open"])])
    up = roles["open_mood_up"][0][0]
    assert {k: round(values[k], 2) for k in open_keys} == {k: (1.0 if k == up else 0.0) for k in open_keys}
    assert _values(ch, [(jaw, 1, -T)])[roles["vowel_a"][0][0]] == pytest.approx(0.5, abs=0.02)


def test_each_board_slider_and_lip_mood_drives_its_role(ch):
    roles = _roles(ch)
    found = 0
    for gid, _, half, _, directions in board.GRIDS:
        if gid in board.JAW_GRIDS:
            continue
        for direction, (role, _) in directions.items():
            transform, sign, index = board.DIRECTIONS[direction]
            values = _values(ch, [(board.bone_name(gid), index, sign * half)])
            for name, weight in roles.get(role, ()):
                assert values[name] == pytest.approx(weight, abs=0.02), (gid, direction, name)
                found += 1
    for bone in [b for b in ch.rig.pose.bones if b.name.startswith(names.BOARD_CONTROL_PREFIX)
                 and b.name[len(names.BOARD_CONTROL_PREFIX):] in ch.body.data.shape_keys.key_blocks]:
        key = bone.name[len(names.BOARD_CONTROL_PREFIX):]
        assert _values(ch, [(bone.name, 0, board.SLIDE)])[key] == pytest.approx(1.0, abs=0.02), key
        found += 1
    assert found > 30


def test_the_gag_type_slider_steps_through_the_gags(ch):
    bone = board.bone_name(board.GAG_TYPE)
    templates = submodule("templates")
    material = next(m for m in ch.materials(roles="gag_eyes") if templates.picker(m) is not None)
    _, number = templates.picker_paths(material)
    got = []
    for x in (0.0, board.SLIDE / 2, board.SLIDE):
        _values(ch, [(bone, 0, x)])
        got.append(material.node_tree.path_resolve(number.removeprefix("node_tree.")))
    assert got[0] == 0 and 1 < got[1] < got[2]


def test_a_half_moves_only_its_side(ch):
    keys = ch.body.data.shape_keys.key_blocks
    n = len(ch.body.data.vertices)
    basis = np.empty(n * 3)
    keys[0].data.foreach_get("co", basis)
    basis = basis.reshape(n, 3)
    halves = [k for k in keys if k.name.endswith((" (L)", " (R)"))]
    assert len(halves) >= 8
    for key in halves:
        co = np.empty(n * 3)
        key.data.foreach_get("co", co)
        moved = np.linalg.norm(co.reshape(n, 3) - basis, axis=1)
        other = basis[:, 0] < -0.01 if key.name.endswith("(L)") else basis[:, 0] > 0.01
        assert moved.max() > 1e-4 and moved[other].max() < 1e-6, key.name


def test_every_preset_poses_what_it_says(ch):
    data = face_tool.data(ch.rig)
    ch.rig.pose.bones[names.FACE_PROPERTIES_BONE][face_tool.STRENGTH] = 1.0
    for preset, expect in data["expect"].items():
        _rest(ch)
        face_tool.apply_preset(ch.rig, preset)
        _update(ch)
        values = {k.name: k.value for k in ch.body.data.shape_keys.key_blocks}
        wrong = {k: (round(values[k], 3), w) for k, w in expect.items() if abs(values[k] - min(1.0, w)) > 0.02}
        extra = {k: round(v, 3) for k, v in values.items() if v > 0.02 and k not in expect and k != "Basis"}
        assert not wrong and not extra, preset
    _rest(ch)
    face_tool.apply_preset(ch.rig, "Happy")
    face_tool.apply_preset(ch.rig, "Angry", add=True)
    _update(ch)
    values = {k.name: k.value for k in ch.body.data.shape_keys.key_blocks}
    assert all(values[k] > 0.9 for k in list(data["expect"]["Happy"]) + list(data["expect"]["Angry"]))
    _rest(ch)


def test_the_eyes_follow_the_target(ch):
    warps = [ch.body.modifiers[n] for n in prepare.UV_WARPS.values()]
    target = ch.rig.pose.bones[names.EYE_TARGET_BONE]
    _rest(ch)
    target.location.x = 0.1
    _update(ch)
    assert all(abs(w.offset[0]) + abs(w.offset[1]) > 0.02 for w in warps)
    _rest(ch)
    target.location.y = -0.12  # down: the lids close a little
    _update(ch)
    blink = _roles(ch)["blink"]
    assert ch.body.data.shape_keys.key_blocks[blink[0][0]].value > 0.05
    _rest(ch)
    target.scale = (1.4,) * 3
    _update(ch)
    assert warps[0].scale[0] == pytest.approx(1 / 1.4, abs=0.01)
    _rest(ch)
    ch.rig.pose.bones[names.LEFT_EYE_TARGET_BONE].location.x = 0.05
    _update(ch)
    left, right = warps
    assert abs(left.offset[0]) + abs(left.offset[1]) > 0.005 and abs(right.offset[0]) + abs(right.offset[1]) < 0.002
    _rest(ch)


def test_the_look_joystick_moves_the_eyes(ch):
    _rest(ch)
    ch.rig.pose.bones[board.bone_name("look")].location.x = 0.02
    _update(ch)
    warp = ch.body.modifiers[prepare.UV_WARPS["eye_l"]]
    assert abs(warp.offset[0]) + abs(warp.offset[1]) > 0.01
    _rest(ch)


def test_the_layers_and_the_board(ch):
    collections = ch.rig.data.collections_all
    for name in (names.FACE_LAYER, names.EYES_LAYER, names.EMOTIONS_LAYER):
        assert collections[name].is_visible and len(collections[name].bones) > 0, name
    tweak = collections[names.FACE_TWEAK_LAYER]
    assert not tweak.is_visible and "cf_J_Mayu_L" in [b.name for b in tweak.bones]
    assert ch.rig.data.bones[names.FACE_BOARD_BONE].hide_select
    labels = [o for o in bpy.data.objects if o.parent == ch.rig and o.type == "FONT"]
    assert len(labels) > 30 and all(o.hide_select and o.hide_render for o in labels)
    for old in ("Eyes handle", "Mouth Widget Controller", "Eyesx", "Eyeballs"):
        assert old not in ch.rig.data.bones, old
    keys = ch.body.data.shape_keys.key_blocks
    assert not [k.name for k in keys if k.name.endswith("(Copy)") or k.name.startswith("Custom Key")]


def test_face_properties_hold_only_keys_no_control_reaches(ch):
    data = face_tool.data(ch.rig)
    raw = {k for _, keys in data["panel"] for k in keys}
    driven = {d.data_path.split('"')[1]: d for d in _driven(ch)}
    for key in raw:
        assert driven[key].driver.expression == "r", key
    assert raw and not any(k.endswith((" (L)", " (R)")) for k in raw)


def test_head_tracking_still_turns_the_head(ch):
    """Head tracking was part of the old eye rig (metarig/head_track.py)."""
    target = ch.rig.pose.bones[names.HEAD_TRACK_TARGET_BONE]
    target["02A) Track target"] = 1.0
    head = ch.rig.pose.bones[names.ORIGINAL_BONE_PREFIX + names.HEAD_BONE]
    _update(ch)
    before = head.matrix.to_quaternion()
    target.location.x = 0.3
    _update(ch)
    turned = before.rotation_difference(head.matrix.to_quaternion()).angle
    target.location.x = 0.0
    target["02A) Track target"] = 0.0
    _update(ch)
    assert turned > 0.1
