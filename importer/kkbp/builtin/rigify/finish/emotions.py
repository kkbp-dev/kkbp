"""The emotion grid: four controllers beside the face, each over a guide widget, that drive copies of
Body's expression shape keys (Expression Names, ADR 0004). The mouth controller blends the A, I,
U, E and O keys around a circle; the eye controller closes or squeezes the eyes; the two custom
controllers drive four empty keys the animator can sculpt. The copies are what the grid drives,
so the original keys stay free to animate. A key Body lacks is left out and logged; the rest of the
grid is still made (issue #64).

Body holds the mouth and the tongue (ADR 0039), so the tongue follows the mouth keys.
"""

from __future__ import annotations

import math

from mathutils import Vector

from .. import drivers, names
from ..drivers import Variable
from ....editing import editing

# (controller, guide, offset from the Eyes handle, guide widget, moves only up and down)
CONTROLLERS = (
    (names.MOUTH_WIDGET_CONTROLLER_BONE, names.FACE_WIDGET_MOUTH_GUIDE_BONE, (0.2, 0.1, 0), "Mouth Grid", False),
    (names.EYE_WIDGET_CONTROLLER_BONE, names.FACE_WIDGET_EYES_GUIDE_BONE, (-0.2, 0.1, 0), "Eye Grid", True),
    (names.CUSTOM1_WIDGET_CONTROLLER_BONE, names.CUSTOM1_GUIDE_BONE, (-0.25, 0.1, 0), "Custom1 Grid", True),
    (names.CUSTOM2_WIDGET_CONTROLLER_BONE, names.CUSTOM2_GUIDE_BONE, (-0.3, 0.1, 0), "Custom2 Grid", True),
)
CONTROLLER_WIDGET = "WidgetSpine"
# The bones the Emotions collection shows: the grid, the eye handles and the eyebrows.
EMOTIONS = (
    names.MOUTH_WIDGET_CONTROLLER_BONE, names.FACE_WIDGET_MOUTH_GUIDE_BONE, names.EYE_WIDGET_CONTROLLER_BONE,
    names.FACE_WIDGET_EYES_GUIDE_BONE, names.CUSTOM1_GUIDE_BONE, names.CUSTOM1_WIDGET_CONTROLLER_BONE,
    names.CUSTOM2_GUIDE_BONE, names.CUSTOM2_WIDGET_CONTROLLER_BONE, names.EYES_HANDLE_BONE,
    names.LEFT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_BONE,
    "cf_J_Mayu_R", "cf_J_MayuTip_s_R", "cf_J_MayuMid_s_R", "cf_J_Mayu_L", "cf_J_MayuTip_s_L", "cf_J_MayuMid_s_L",
)
# The mouth keys around the circle, by the last letter of the base key's name: each pair's first
# key ramps up to MOUTH_INNER, then crossfades into the second by MOUTH_OUTER.
MOUTH_DIRECTIONS = {"A": math.radians(90), "O": math.radians(18), "U": math.radians(-54), "E": math.radians(-126),
                    "I": math.radians(162)}
MOUTH_PAIRS = ((names.MOUTH_SHAPEKEY_A, names.MOUTH_SHAPEKEY_A2), (names.MOUTH_SHAPEKEY_I, names.MOUTH_SHAPEKEY_I2),
               (names.MOUTH_SHAPEKEY_U, names.MOUTH_SHAPEKEY_U2), (names.MOUTH_SHAPEKEY_E, names.MOUTH_SHAPEKEY_E2),
               (names.MOUTH_SHAPEKEY_O, names.MOUTH_SHAPEKEY_O2))
MOUTH_INNER, MOUTH_OUTER = 0.045, 0.09
REACH = 0.09  # how far a controller moves for a key to reach its full value
# (eye key, its expression of the controller's height z): down closes, up squeezes.
EYE_DRIVERS = (
    (names.EYE_SHAPEKEY_CLOSED1, f"max(0,min(0.35,-z/{REACH}))"),
    (names.EYE_SHAPEKEY_CLOSED2, f"max(0,min(0.7,-z/{REACH}))"),
    (names.EYE_SHAPEKEY_CLOSED3, f"max(0,min(1,z/{REACH}))"),
    (names.EYE_SHAPEKEY_CLOSED4, f"max(0,min(0.5,z/{(REACH * 2)}))"),
)
# (custom key, controller, expression), in the order they are driven.
CUSTOM_DRIVERS = (
    (names.CUSTOM_SHAPEKEYS_TO_CREATE[1], names.CUSTOM1_WIDGET_CONTROLLER_BONE, f"max(0,min(1,-z/{REACH}))"),
    (names.CUSTOM_SHAPEKEYS_TO_CREATE[3], names.CUSTOM2_WIDGET_CONTROLLER_BONE, f"max(0,min(1,-z/{REACH}))"),
    (names.CUSTOM_SHAPEKEYS_TO_CREATE[0], names.CUSTOM1_WIDGET_CONTROLLER_BONE, f"max(0,min(1,z/{REACH}))"),
    (names.CUSTOM_SHAPEKEYS_TO_CREATE[2], names.CUSTOM2_WIDGET_CONTROLLER_BONE, f"max(0,min(1,z/{REACH}))"),
)


def emotion_grid(build):
    rig = build.rig
    with editing(rig, "EDIT"):
        edit = rig.data.edit_bones
        eyes = edit[names.EYES_HANDLE_BONE].head
        for controller, guide, offset, _shape, _ in CONTROLLERS:
            place = eyes + Vector(offset)
            for name in (controller, guide):
                bone = edit.new(name)
                bone.head = place
                bone.tail = bone.head + Vector((0, 0.1, 0))
                bone.parent = edit[names.HEAD_TWEAK_BONE]
                bone.use_deform = False
    for controller, guide, _offset, shape, up_and_down in CONTROLLERS:
        c, g = rig.pose.bones[controller], rig.pose.bones[guide]
        c.lock_location = (up_and_down, True, False)
        c.custom_shape_scale_xyz = (2, 2, 2)
        c.custom_shape = build.widget(CONTROLLER_WIDGET)
        g.lock_location = g.lock_rotation = g.lock_scale = (True, True, True)
        g.custom_shape = build.widget(shape)
    emotions = rig.data.collections[names.EMOTIONS_LAYER]
    for name in EMOTIONS:
        if bone := rig.data.bones.get(name):
            bone.collections.clear()
            emotions.assign(bone)

    body = build.body
    if body.data.shape_keys is None:
        build.log.warning("Body has no shape keys, so the emotion grid drives nothing")
        return
    _mouth(rig, body, build.log)
    keys = body.data.shape_keys
    _copy_keys(body, names.EYE_SHAPEKEYS_TO_COPY, names.EYE_SHAPEKEYS_COPY_SUFFIX)
    missing = []
    for key, expression in EYE_DRIVERS:
        name = key + names.EYE_SHAPEKEYS_COPY_SUFFIX
        if name not in keys.key_blocks:  # each Game has its own eye expressions (issue #64)
            missing.append(key)
            continue
        _height_driver(keys, name, rig, names.EYE_WIDGET_CONTROLLER_BONE, expression)
    if missing:
        build.log.info(f"Body has no {', '.join(repr(k) for k in missing)} shape key, so the emotion grid's eye "
                       "controller doesn't drive it")
    for name in names.CUSTOM_SHAPEKEYS_TO_CREATE:
        body.shape_key_add(name=name).value = 0
    for name, controller, expression in CUSTOM_DRIVERS:
        _height_driver(keys, name, rig, controller, expression)


def _copy_keys(body, originals, suffix):
    """A copy of each of `originals` Body has, as `<name><suffix>`, at 0."""
    blocks = body.data.shape_keys.key_blocks
    for key in [k for k in blocks if k.name in originals]:
        copy = blocks.get(key.name + suffix) or body.shape_key_add(name=key.name + suffix)
        copy.value = 0
        for i in range(len(key.data)):
            copy.data[i].co = key.data[i].co


def _location(rig, controller, axis):
    return Variable(axis, "SINGLE_PROP", rig, data_path=f'pose.bones["{controller}"].location.{axis}')


def _height_driver(keys, name, rig, controller, expression):
    path = f'key_blocks["{name}"].value'
    keys.driver_remove(path)
    drivers.add(keys, path, type="SCRIPTED", variables=[_location(rig, controller, "z")], expression=expression)


def _mouth(rig, body, log):
    """Each mouth key pair blends in as the controller moves towards its direction: the first key by
    MOUTH_INNER, crossfading into the second by MOUTH_OUTER. A pair whose second key Body lacks keeps
    its first key at full all the way out; a first key goes by its other name if Body has that one."""
    blocks = body.data.shape_keys.key_blocks
    pairs = []
    for base, second in MOUTH_PAIRS:
        alternate = dict(names.MOUTH_SHAPEKEY_ALTERNATES)[base]
        first = base if base in blocks or alternate not in blocks else alternate
        pairs.append((MOUTH_DIRECTIONS[base[-1]], first, second))
    _copy_keys(body, [name for _, first, second in pairs for name in (first, second)], names.MOUTH_SHAPEKEYS_COPY_SUFFIX)
    keys = body.data.shape_keys
    controller = names.MOUTH_WIDGET_CONTROLLER_BONE
    radius = "sqrt(x*x+z*z)"
    missing = []
    for direction, first, second in pairs:
        angle = (f"max(0,1-acos((x*{math.cos(direction):.4f}+z*{math.sin(direction):.4f})/"
                 f"({radius}+.0001))/1.2566)")
        ramp = f"max(0,min(1,{radius}/{MOUTH_INNER}))"
        crossfade = f"max(0,min(1,({radius}-{MOUTH_INNER})/{MOUTH_OUTER - MOUTH_INNER}))"
        has_second = second + names.MOUTH_SHAPEKEYS_COPY_SUFFIX in keys.key_blocks
        for name, expression in ((first, f"(1-{crossfade})*{ramp}*{angle}" if has_second else f"{ramp}*{angle}"),
                                 (second, f"{crossfade}*{angle}")):
            key = keys.key_blocks.get(name + names.MOUTH_SHAPEKEYS_COPY_SUFFIX)
            if key is None:
                missing.append(name)
                continue
            path = f'key_blocks["{key.name}"].value'
            keys.driver_remove(path)
            drivers.add(keys, path, type="SCRIPTED",
                        variables=[_location(rig, controller, "x"), _location(rig, controller, "z")],
                        expression=expression)
    if missing:
        log.info(f"Body has no {', '.join(repr(k) for k in missing)} shape key, so the emotion grid's mouth "
                 "controller doesn't drive it")
