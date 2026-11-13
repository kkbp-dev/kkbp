"""The eye rig: the Eyes target bones, the tracking bones, and the eye mechanism's custom properties,
constraints and drivers, with which the eye handles move the eye textures (through the Eye
Controller's UV warps) and the eyelids.

Each eye is an Eye of names and measured constants. The right eye mirrors the left along x: in an
expression, an eye's x term is its value minus its head distance on the left and plus it on the
right; its y terms subtract on both sides. Everything else is written once.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from math import radians

from .. import bones, constraints, drivers, meshes, names
from ..drivers import Variable

SIZE = 100.0  # the eyes size factor's default, which many ranges scale with
EPSILON = "0.000001"


@dataclass(frozen=True)
class Eye:
    s: str  # the suffix of the driver variables' names
    handle: str
    eyeball: str
    marker: str
    marker_x: str
    marker_z: str
    head_marker_x: str
    head_marker_z: str
    track: str
    track_correction: str
    target: str  # the eye's target bone, under Eyes target
    deform: str  # the eye's deform bone, whose head is the eyeball's depth
    x_sign: str  # how the head distance enters the eye's x terms
    head_x_variable: str
    # Measured on the reference character, at whose proportions the location defaults are right.
    head_x_reference: float
    head_z_reference: float
    x_limits: tuple  # the default min and max x locations
    outward: str  # the x limit that points away from the face's middle
    turn: int  # degrees the track correction starts from


LEFT = Eye("L", names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYEBALL_BONE, names.LEFT_EYE_HANDLE_MARKER_BONE,
           names.LEFT_EYE_HANDLE_MARKER_X_BONE, names.LEFT_EYE_HANDLE_MARKER_Z_BONE, names.LEFT_HEAD_MARKER_X_BONE,
           names.LEFT_HEAD_MARKER_Z_BONE, names.LEFT_EYEBALL_TRACK_BONE, names.LEFT_EYEBALL_TRACK_CORRECTION_BONE,
           names.LEFT_EYE_BONE, names.LEFT_EYE_DEFORM_BONE, "-", "headDistX_L",
           0.031159714929090754, 0.053977131843566895, (-0.075, 0.25), "max", -45)
RIGHT = Eye("R", names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYEBALL_BONE, names.RIGHT_EYE_HANDLE_MARKER_BONE,
            names.RIGHT_EYE_HANDLE_MARKER_X_BONE, names.RIGHT_EYE_HANDLE_MARKER_Z_BONE, names.RIGHT_HEAD_MARKER_X_BONE,
            names.RIGHT_HEAD_MARKER_Z_BONE, names.RIGHT_EYEBALL_TRACK_BONE, names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE,
            names.RIGHT_EYE_BONE, names.RIGHT_EYE_DEFORM_BONE, "+",
            "headdDistX_R",  # sic: animators' drivers may read it by this name
            -0.031183381431473478, 0.05397462844848633, (-0.25, 0.075), "min", 45)
EYES = (LEFT, RIGHT)
# The right eye's distance from its handle marker to its track correction bone, on the reference character.
TRACK_REFERENCE = 0.0917946808040142


@dataclass
class Measures:
    """What the tracking bones measure, for the properties' defaults."""
    head_x: dict
    head_z: dict
    track_y: float  # the right eye's track correction distance
    placeholders: tuple  # the head tweak, torso and root placeholders' names


def eye_bones(build):
    """The Eyes target bone, and the left and right eye targets under it, where the Eye Controller is.
    In Edit Mode."""
    metarig = build.metarig
    eyes = bones.copy_bone(metarig, names.ORIGINAL_EYES_BONE, names.EYES_BONE)
    for eye in EYES:
        bones.copy_bone(metarig, names.ORIGINAL_EYES_BONE, eye.target)
    for eye in EYES:
        metarig.data.edit_bones[eye.target].parent = eyes


def tracking_bones(build) -> Measures:
    """The markers the drivers measure the handles' and head's movement by, the eyeballs and their
    tracking bones, the head's tracking bones and the placeholders the generated rig's controls
    replace. In Edit Mode."""
    metarig = build.metarig
    edit = metarig.data.edit_bones
    copy = lambda source, name: bones.copy_bone(metarig, source, name)  # noqa: E731
    target = copy(names.EYES_HANDLE_BONE, names.EYES_TRACK_TARGET_BONE)
    target_parent = copy(names.EYES_HANDLE_BONE, names.EYES_TRACK_TARGET_PARENT_BONE)
    eyes_marker = copy(names.EYES_HANDLE_BONE, names.EYES_HANDLE_MARKER_BONE)
    for eye in EYES:
        copy(eye.handle, eye.marker)
    for eye in EYES:
        marker = copy(eye.handle, eye.marker_x)
        marker.head.z = marker.tail.z = eyes_marker.head.z
    for eye in EYES:
        marker = copy(eye.handle, eye.marker_z)
        marker.head.x = marker.tail.x = eyes_marker.head.x
    target.parent = target_parent
    target_parent.parent = None
    head = edit[names.HEAD_BONE]
    for eye in EYES:
        for name in (eye.marker, eye.marker_x, eye.marker_z):
            edit[name].parent = head

    eyeballs = copy(names.EYES_HANDLE_BONE, names.EYEBALLS_BONE)
    eyeballs.roll = radians(0)
    for eye in EYES:
        eyeball = copy(eye.handle, eye.eyeball)
        eyeball.parent = head
        eyeball.roll = radians(0)
        eyeball.head.y = edit[eye.deform].head.y
    eyeballs.head.y = statistics.mean([edit[eye.eyeball].head.y for eye in EYES])
    eyeballs.length = edit[names.EYES_HANDLE_BONE].length
    for eye in EYES:
        edit[eye.eyeball].length = edit[eye.handle].length
    copy(names.EYEBALLS_BONE, names.EYEBALLS_TRACK_BONE)
    for eye in EYES:
        copy(eye.eyeball, eye.track)
    for eye in EYES:
        copy(eye.track, eye.track_correction)
    for eye in EYES:
        marker = copy(eye.handle, eye.head_marker_x)
        marker.parent = head
        marker.head.y = head.head.y
        marker.length = edit[eye.handle].length
        marker.head.z = marker.tail.z = head.head.z
    for eye in EYES:
        marker = copy(eye.handle, eye.head_marker_z)
        marker.parent = head
        marker.head.y = head.head.y
        marker.length = edit[eye.handle].length
        marker.head.x = marker.tail.x = head.head.x

    head_target = copy(names.EYES_HANDLE_BONE, names.HEAD_TRACK_TARGET_BONE)
    head_target.length = head.length
    head_target_parent = copy(names.HEAD_TRACK_TARGET_BONE, names.HEAD_TRACK_TARGET_PARENT_BONE)
    head_target.parent = head_target_parent
    head_target_parent.parent = None
    head_track = copy(names.EYEBALLS_BONE, names.HEAD_TRACK_BONE)
    head_track.parent = None
    head_track.head.y = head.head.y
    placeholders = tuple(bones.new_bone(metarig, name + names.PLACEHOLDER_BONE_SUFFIX).name
                         for name in (names.HEAD_TWEAK_BONE, names.TORSO_BONE, names.ROOT_BONE))
    return Measures(
        head_x={eye: edit[eye.head_marker_x].head.x - head.head.x for eye in EYES},
        head_z={eye: edit[eye.head_marker_z].head.z - head.head.z for eye in EYES},
        track_y=edit[RIGHT.track_correction].head.y - edit[RIGHT.marker].head.y,
        placeholders=placeholders)


# --- the mechanism -----------------------------------------------------------------------------

def _prop(build, bone, name, description, default, low, high):
    return drivers.bone_property(build.metarig, bone, name, description=description, default=default, min=low, max=high)


def _properties(build, m):
    """The settings the animator sees on the handle, track target and eyeball bones; returns their
    data paths, by bone and name."""
    paths = {}
    eyes_handle = (
        ("01A) Limit location", "Limits the maximum reachable X and Y locations based on the left and right eye handles settings", 0.0, 0.0, 1.0),
        ("02A) Eyelids automation", "Enables eyelids shape key automation when both eyes move up and down", 0.0, 0.0, 1.0),
        ("02B) Default eyelids value", "Eyelids shape key automation value when both eyes are at their default position", 0.05, 0.0, 1.0),
        ("02C) Min eyelids value", "Minimum reachable eyelids shape key automation value when both eyes move down", 0.0, 0.0, 1.0),
        ("02D) Max eyelids value", "Maximum reachable eyelids shape key automation value when both eyes move up", 0.25, 0.0, 1.0),
        ("02E) Eyelids speed factor", "Determines how fast the eyelids shape key automation value will change when both eyes move up and down", 2.0, 0.0, SIZE * 10),
        ("03A) Eyes size factor", "Factors into many constraints and drivers for the eyes mechanics; it's better not to change this value", SIZE, 0, SIZE * 10),
    )
    for name, *rest in eyes_handle:
        paths[names.EYES_HANDLE_BONE, name] = _prop(build, names.EYES_HANDLE_BONE, name, *rest)
    for eye in EYES:
        for name, description, default, low, high in (
            ("01A) Limit location", "Limits the maximum reachable X and Y locations based on the settings below", 0.0, 0.0, 1.0),
            ("01B) Min X location", "Minimum reachable X location limit", eye.x_limits[0] - eye.head_x_reference + m.head_x[eye], SIZE * -10, SIZE * 10),
            ("01C) Max X location", "Maximum reachable X location limit", eye.x_limits[1] - eye.head_x_reference + m.head_x[eye], SIZE * -10, SIZE * 10),
            ("01D) Min Y location", "Minimum reachable Y location limit", -0.1 - eye.head_z_reference + m.head_z[eye], SIZE * -10, SIZE * 10),
            ("01E) Max Y location", "Maximum reachable Y location limit", 0.13 - eye.head_z_reference + m.head_z[eye], SIZE * -10, SIZE * 10),
            ("02A) Speed correction", "Increases the speed at which the eye moves when not controlled directly in order to reach its maximum location limits at the same time as the other eye", 0.0, 0.0, 1.0),
        ):
            paths[eye.handle, name] = _prop(build, eye.handle, name, description, default, low, high)
    for name, description, default in (
        ("01A) Parent to head", "The bone will act as if it was parented to the head bone", 1),
        ("01B) Parent to torso", "The bone will act as if it was parented to the torso bone", 0),
        ("01C) Parent to root", "The bone will act as if it was parented to the root bone", 0),
    ):
        paths[names.EYES_TRACK_TARGET_BONE, name] = _prop(build, names.EYES_TRACK_TARGET_BONE, name, description, default, 0, 1)
    for name, description, default, low, high in (
        ("01A) Eyeballs speed factor", "Determines how fast the eyes will move when rotating the eyeball bones manually", 0.26, 0.0, 1.0),
        ("02A) Track target", "Enables tracking of the eyeballs track target bone", 0.0, 0.0, 1.0),
        ("02B) Eyeballs track speed factor", "Determines how fast the eyes will move when the eyeballs are tracking their target", 0.04, 0.0, 1.0),
        ("02C) Nearby target track correction", "When tracking a target that moves closer to the middle of the face than its original location, the individual eyes will gradually point towards it instead of keeping the original distance between them", 0.0, 0.0, 1.0),
        ("02D) Nearby target track size factor", "Factors into the nearby target track correction, if the character is scaled up or down after running the first Rigify script this value should be changed proportionally", m.track_y / TRACK_REFERENCE, SIZE * -10, SIZE * 10),
    ):
        paths[names.EYEBALLS_BONE, name] = _prop(build, names.EYEBALLS_BONE, name, description, default, low, high)
    for name, description, default, low, high in (
        ("01A) Limit rotation", "Limits the maximum reachable rotation of the head based on the settings below", 0.0, 0.0, 1.0),
        ("01B) Min X rotation", "Minimum reachable X angle limit", -40.0, -180.0, 0.0),
        ("01C) Max X rotation", "Maximum reachable X angle limit", 50.0, 0.0, 180.0),
        ("01D) Min Y rotation", "Minimum reachable Y angle limit", -80.0, -180.0, 0.0),
        ("01E) Max Y rotation", "Maximum reachable Y angle limit", 80.0, 0.0, 180.0),
        ("01F) Min Z rotation", "Minimum reachable Z angle limit", -50.0, -180.0, 0.0),
        ("01G) Max Z rotation", "Maximum reachable Z angle limit", 50.0, 0.0, 180.0),
        ("02A) Track target", "Enables tracking of the head track target bone", 0.0, 0.0, 1.0),
        ("03A) Parent to head", "The bone will act as if it was parented to the head bone", 1, 0, 1),
        ("03B) Parent to torso", "The bone will act as if it was parented to the torso bone", 0, 0, 1),
        ("03C) Parent to root", "The bone will act as if it was parented to the root bone", 0, 0, 1),
    ):
        paths[names.HEAD_TRACK_TARGET_BONE, name] = _prop(build, names.HEAD_TRACK_TARGET_BONE, name, description, default, low, high)
    return paths


_TRANSFORMATION = names.TRANSFORMATION_CONSTRAINT_BASE
_EYEBALL_LOCATION = _TRANSFORMATION + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX
_HANDLE_LOCATION = _TRANSFORMATION + names.HANDLE_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX
_CORRECTION = {"min": names.CORRECTION_CONSTRAINT_SUFFIX + names.MIN_CONSTRAINT_SUFFIX,
               "max": names.CORRECTION_CONSTRAINT_SUFFIX + names.MAX_CONSTRAINT_SUFFIX}
_FULL_TURN = ((radians(-180), radians(180)), (radians(0), radians(0)), (radians(-180), radians(180)))
_NONE = ((radians(0), radians(0)),) * 3
_ZERO = ((0, 0),) * 3
_SCALE = ((0.0, 100.0), (1.0, 1.0), (0.0, 100.0))


def _handle_constraints(rig, handle, eyeball, corrections):
    """A handle's constraints, in stack order: it follows its eyeball's rotation as location (with,
    for an eye, the min and max corrections), its eyeball's Y rotation and scale, and (for an eye)
    the Eyes handle's location corrections; and a limit on its location."""
    out = {"location": constraints.transformation(
        rig, handle, eyeball, name=_EYEBALL_LOCATION, mix="ADD", space="LOCAL", map_from="ROTATION",
        from_range=_FULL_TURN, map_to="LOCATION", to_range=((SIZE / -10, SIZE / 10), (0, 0), (SIZE / -10, SIZE / 10)),
        from_rotation_mode="AUTO")}
    if corrections:
        for limit in ("min", "max"):
            out["eyeball", limit] = constraints.transformation(
                rig, handle, eyeball, name=_EYEBALL_LOCATION + _CORRECTION[limit], mix="ADD", space="LOCAL",
                map_from="ROTATION", from_range=_NONE, map_to="LOCATION", to_range=_ZERO, from_rotation_mode="AUTO")
    constraints.copy_rotation(rig, handle, eyeball, name=names.COPY_ROTATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX,
                              mix="AFTER", space="LOCAL", use=(False, True, False), invert=(False, False, False))
    constraints.transformation(rig, handle, eyeball, name=_TRANSFORMATION + names.EYEBALL_CONSTRAINT_SUFFIX + names.SCALE_CONSTRAINT_SUFFIX,
                               mix="MULTIPLY", space="LOCAL", map_from="SCALE", from_range=_SCALE, map_to="SCALE", to_range=_SCALE)
    if corrections:
        for limit in ("min", "max"):
            out["handle", limit] = constraints.transformation(
                rig, handle, names.EYES_HANDLE_BONE, name=_HANDLE_LOCATION + _CORRECTION[limit], mix="ADD", space="LOCAL",
                map_from="LOCATION", from_range=_ZERO, map_to="LOCATION", to_range=_ZERO)
    out["limit"] = constraints.limit_location(
        rig, handle, name=names.LIMIT_LOCATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX, space="CUSTOM",
        space_bone=names.HEAD_BONE, min=(-SIZE, -SIZE, None), max=(SIZE, SIZE, None))
    return out


def _constraints(build, m):
    rig = build.metarig
    handles = {None: _handle_constraints(rig, names.EYES_HANDLE_BONE, names.EYEBALLS_BONE, corrections=False)}
    for eye in EYES:
        handles[eye] = _handle_constraints(rig, eye.handle, eye.eyeball, corrections=True)
    head_tweak, torso, root = m.placeholders
    track = names.COPY_ROTATION_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX
    damped = names.DAMPED_TRACK_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX
    parent = names.ARMATURE_CONSTRAINT_BASE + names.PARENT_CONSTRAINT_SUFFIX
    out = {"handles": handles}
    out["eyes_target_parent"] = constraints.armature(rig, names.EYES_TRACK_TARGET_PARENT_BONE, [names.HEAD_BONE, torso, root], name=parent)
    out["eyeballs_track"] = constraints.copy_rotation(rig, names.EYEBALLS_BONE, names.EYEBALLS_TRACK_BONE, name=track, mix="REPLACE",
                                                      space="LOCAL", use=(True, False, True), invert=(False, False, False))
    for eye in EYES:
        out["eyeball_track", eye] = constraints.copy_rotation(
            rig, eye.eyeball, eye.track_correction, name=track + names.CORRECTION_CONSTRAINT_SUFFIX, mix="REPLACE",
            space="LOCAL", use=(True, False, True), invert=(False, False, False))
    constraints.damped_track(rig, names.EYEBALLS_TRACK_BONE, names.EYES_TRACK_TARGET_BONE, name=damped)
    for eye in EYES:
        constraints.damped_track(rig, eye.track, names.EYES_TRACK_TARGET_BONE, name=damped)
    out["head_rotation"] = constraints.transformation(
        rig, names.HEAD_BONE, names.HEAD_TRACK_BONE, name=_TRANSFORMATION + names.HEAD_CONSTRAINT_SUFFIX + names.ROTATION_CONSTRAINT_SUFFIX,
        mix="REPLACE", space="LOCAL_WITH_PARENT", map_from="ROTATION",
        from_range=((math.radians(-180), math.radians(180)),) * 3, map_to="ROTATION",
        to_range=((math.radians(180), math.radians(-180)), (math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180))),
        from_rotation_mode="QUATERNION", to_euler_order="AUTO", map_to_from=("X", "Z", "Y"))
    out["head_limit"] = constraints.limit_rotation(
        rig, names.HEAD_BONE, name=names.LIMIT_ROTATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX, space="LOCAL",
        limits=((math.radians(-180), math.radians(180)),) * 3)
    out["head_target_parent"] = constraints.armature(rig, names.HEAD_TRACK_TARGET_PARENT_BONE, [head_tweak, torso, root], name=parent)
    constraints.damped_track(rig, names.HEAD_TRACK_BONE, names.HEAD_TRACK_TARGET_BONE, name=damped)
    return out


class _Vars:
    """The driver variables, by the name the drivers know them by."""

    def __init__(self, rig, paths):
        prop = lambda name, bone, key: Variable(name, "SINGLE_PROP", rig, data_path=paths[bone, key])  # noqa: E731
        dist = lambda name, a, b: Variable(name, "LOC_DIFF", rig, bone=a, space="WORLD_SPACE",  # noqa: E731
                                           target2=rig, bone2=b, space2="WORLD_SPACE")
        h = names.EYES_HANDLE_BONE
        self.locX = Variable("locX", "TRANSFORMS", rig, bone=h, space="LOCAL_SPACE", transform="LOC_X")
        self.default = prop("default", h, "02B) Default eyelids value")
        self.min = prop("min", h, "02C) Min eyelids value")
        self.max = prop("max", h, "02D) Max eyelids value")
        self.speed = prop("speed", h, "02E) Eyelids speed factor")
        self.enabled = prop("enabled", h, "02A) Eyelids automation")
        self.limit = prop("limit", h, "01A) Limit location")
        self.size = prop("sizeFactor", h, "03A) Eyes size factor")
        self.eye = {}
        for eye in EYES:
            s = eye.s
            self.eye[eye] = {
                "limit": prop(f"limit_{s}", eye.handle, "01A) Limit location"),
                "minX": prop(f"minX_{s}", eye.handle, "01B) Min X location"),
                "maxX": prop(f"maxX_{s}", eye.handle, "01C) Max X location"),
                "minY": prop(f"minY_{s}", eye.handle, "01D) Min Y location"),
                "maxY": prop(f"maxY_{s}", eye.handle, "01E) Max Y location"),
                "corr": prop(f"corr_{s}", eye.handle, "02A) Speed correction"),
                "distX": dist(f"distX_{s}", names.EYES_HANDLE_MARKER_BONE, eye.marker_x),
                "distY": dist(f"distY_{s}", names.EYES_HANDLE_MARKER_BONE, eye.marker_z),
                "headX": dist(eye.head_x_variable, names.HEAD_BONE, eye.head_marker_x),
                "headY": dist(f"headDistY_{s}", names.HEAD_BONE, eye.head_marker_z),
                "orgDist": dist(f"orgDist_{s}", eye.track_correction, eye.marker),
                "currDist": dist(f"currDist_{s}", eye.track_correction, names.EYES_TRACK_TARGET_BONE),
                "rotZ": Variable(f"rotZ_{s}", "TRANSFORMS", rig, bone=eye.track, space="LOCAL_SPACE", transform="ROT_Z",
                                 rotation_mode="QUATERNION"),
            }
        t = names.EYES_TRACK_TARGET_BONE
        self.target_parent = [prop("parentHead", t, "01A) Parent to head"), prop("parentTorso", t, "01B) Parent to torso"),
                              prop("parentRoot", t, "01C) Parent to root")]
        b = names.EYEBALLS_BONE
        self.rotSpeed = prop("rotSpeed", b, "01A) Eyeballs speed factor")
        self.track = prop("track", b, "02A) Track target")
        self.trackSpeed = prop("trackSpeed", b, "02B) Eyeballs track speed factor")
        self.trackCorr = prop("trackCorr", b, "02C) Nearby target track correction")
        self.factor = prop("factor", b, "02D) Nearby target track size factor")
        self.rotZ = Variable("rotZ", "TRANSFORMS", rig, bone=names.EYEBALLS_TRACK_BONE, space="LOCAL_SPACE", transform="ROT_Z",
                             rotation_mode="QUATERNION")
        ht = names.HEAD_TRACK_TARGET_BONE
        self.head_limit = prop("limit", ht, "01A) Limit rotation")
        self.head_rotation = [prop(n, ht, key) for n, key in (
            ("minX", "01B) Min X rotation"), ("maxX", "01C) Max X rotation"), ("minY", "01D) Min Y rotation"),
            ("maxY", "01E) Max Y rotation"), ("minZ", "01F) Min Z rotation"), ("maxZ", "01G) Max Z rotation"))]
        self.head_parent = [prop("parentHead", ht, "03A) Parent to head"), prop("parentTorso", ht, "03B) Parent to torso"),
                            prop("parentRoot", ht, "03C) Parent to root")]
        self.head_track = prop("track", ht, "02A) Track target")


def _term(v, eye, limit, axis, compact=False):
    """An eye's limit on `axis` less (or plus, for the right eye's x) its head distance."""
    value, head = v.eye[eye][f"{limit}{axis}"].name, v.eye[eye][f"head{axis}"].name
    sign = eye.x_sign if axis == "X" else "-"
    return f"({value}{sign}{head})" if compact else f"({value} {sign} {head})"


def _correction_drivers(cons, v, eye, other):
    """The min and max corrections that let an eye reach its limit at the same time as the other."""
    size = v.size.name
    for limit in ("max", "min"):
        compare = f"<= {EPSILON} * {size}" if limit == "max" else f">= -{EPSILON} * {size}"
        handle, eyeball = cons["handle", limit], cons["eyeball", limit]
        drivers.add(handle, "influence", type="AVERAGE", variables=[v.eye[eye]["corr"]])
        drivers.add(eyeball, "influence", type="SCRIPTED", variables=[v.rotSpeed, v.track, v.eye[eye]["corr"]],
                    expression=f"{v.eye[eye]['corr'].name} * (1 - {v.track.name}) * {v.rotSpeed.name}")
        for axis, channel in (("X", "z"), ("Y", "x")):
            own, theirs = _term(v, eye, limit, axis), _term(v, other, limit, axis)
            cond = f"{own} - {theirs} {compare}"
            variables = [v.eye[eye][f"{limit}{axis}"], v.eye[other][f"{limit}{axis}"], v.eye[eye][f"head{axis}"],
                         v.eye[other][f"head{axis}"], v.size]
            if limit == "max":
                to = f"{own} * {size} / {theirs} - {size}"
                to_tenth = f"{own} * {size} / 10 / {theirs} - {size} / 10"
                full, turn = size, "radians(180)"
            else:
                to = f"{own} * -{size} / {theirs} + {size}"
                to_tenth = f"{own} * -{size} / 10 / {theirs} + {size} / 10"
                full, turn = f"-{size}", "radians(-180)"
            drivers.add(handle, f"to_{limit}_{channel}", type="SCRIPTED", variables=variables, expression=f"0 if {cond} else {to}")
            drivers.add(handle, f"from_{limit}_{channel}", type="SCRIPTED", variables=variables, expression=f"0 if {cond} else {full}")
            drivers.add(eyeball, f"to_{limit}_{channel}", type="SCRIPTED", variables=variables,
                        expression=f"0 if {cond} else {to_tenth}")
            drivers.add(eyeball, f"from_{limit}_{channel}_rot", type="SCRIPTED", variables=variables,
                        expression=f"radians(0) if {cond} else {turn}")


def _eyeball_location_drivers(constraint, v):
    drivers.add(constraint, "influence", type="SCRIPTED", variables=[v.rotSpeed, v.track, v.trackSpeed],
                expression=f"{v.rotSpeed.name} * (1 - {v.track.name}) + {v.trackSpeed.name} * {v.track.name}")
    for prop, expression in (("to_min_x", f"-{v.size.name} / 10"), ("to_max_x", f"{v.size.name} / 10"),
                             ("to_min_z", f"-{v.size.name} / 10"), ("to_max_z", f"{v.size.name} / 10")):
        drivers.add(constraint, prop, type="SCRIPTED", variables=[v.size], expression=expression)


def _track_correction_driver(rig, v, eye, other):
    """The eyeball turns towards a track target that comes nearer the face's middle than it started."""
    e = v.eye[eye]
    org, curr, rot = e["orgDist"].name, e["currDist"].name, e["rotZ"].name
    own, theirs = _term(v, eye, eye.outward, "X", compact=True), _term(v, other, eye.outward, "X", compact=True)
    difference = f"({v.rotZ.name}-{rot})" if eye is LEFT else f"({rot}-{v.rotZ.name})"
    compare = f"<={EPSILON}" if eye.outward == "max" else f">=-{EPSILON}"
    expression = (f"0 if {org}-{curr}<=0 else (radians({eye.turn})+{rot})*({org}-{curr})/{v.factor.name}*{difference}*20"
                  f"*(1 if {own}-{theirs}{compare} else 1+{e['corr'].name}*{own}/{theirs})")
    variables = [e["orgDist"], e["currDist"], v.rotZ, e["rotZ"], e["corr"], e[f"{eye.outward}X"],
                 v.eye[other][f"{eye.outward}X"], e["headX"], v.eye[other]["headX"], v.factor]
    drivers.add(rig.pose.bones[eye.track_correction], "rotation_quaternion", type="SCRIPTED", variables=variables,
                expression=expression, index=3)


def mechanism(build, m):
    """The eye mechanism, in Object Mode."""
    rig = build.metarig
    paths = _properties(build, m)
    cons = _constraints(build, m)
    eyelids = meshes.duplicate_shape_key(build.body, names.EYELIDS_SHAPE_KEY, names.EYELIDS_SHAPE_KEY_COPY)
    v = _Vars(rig, paths)

    # The eyelids follow the Eyes handle up and down, between their min and max.
    value = (f"{v.default.name} + {v.locX.name} * -{v.speed.name} if {v.locX.name} < 0 "
             f"else {v.default.name} - {v.locX.name} * {v.speed.name}")
    drivers.add(eyelids, "value", type="SCRIPTED", variables=[v.locX, v.default, v.min, v.max, v.speed, v.enabled],
                expression=f"{v.enabled.name} * ({v.min.name} if ({value}) < {v.min.name} else {v.max.name} "
                           f"if ({value}) > {v.max.name} else ({value}))")

    # The Eyes handle's limits are the eyes' own, moved by each eye's distance from it.
    eyes = cons["handles"][None]
    drivers.add(eyes["limit"], "influence", type="AVERAGE", variables=[v.limit])
    left, right = v.eye[LEFT], v.eye[RIGHT]
    for axis in ("X", "Y"):
        lmin, rmin, lmax, rmax = left[f"min{axis}"].name, right[f"min{axis}"].name, left[f"max{axis}"].name, right[f"max{axis}"].name
        ld, rd = left[f"dist{axis}"].name, right[f"dist{axis}"].name
        p = axis.lower()
        drivers.add(eyes["limit"], f"min_{p}", type="SCRIPTED",
                    variables=[left[f"min{axis}"], right[f"min{axis}"], left[f"dist{axis}"], right[f"dist{axis}"]],
                    expression=f"{lmin} - {ld} if {lmin} - {ld} <= {rmin} + {rd} else {rmin} + {rd}")
        drivers.add(eyes["limit"], f"max_{p}", type="SCRIPTED",
                    variables=[left[f"max{axis}"], right[f"max{axis}"], left[f"dist{axis}"], right[f"dist{axis}"]],
                    expression=f"{rmax} + {rd} if {rmax} + {rd} > {lmax} - {ld} else {lmax} - {ld}")
    _eyeball_location_drivers(eyes["location"], v)

    for eye, other in ((LEFT, RIGHT), (RIGHT, LEFT)):
        own = cons["handles"][eye]
        for prop in ("min_x", "max_x", "min_y", "max_y"):
            key = prop[:3] + prop[-1].upper()
            drivers.add(own["limit"], prop, type="AVERAGE", variables=[v.eye[eye][key]])
        drivers.add(own["limit"], "influence", type="AVERAGE", variables=[v.eye[eye]["limit"]])
        _correction_drivers(own, v, eye, other)
        _eyeball_location_drivers(own["location"], v)

    for i, variable in enumerate(v.target_parent):
        drivers.add(cons["eyes_target_parent"].targets[i], "weight", type="AVERAGE", variables=[variable])
    drivers.add(cons["eyeballs_track"], "influence", type="AVERAGE", variables=[v.track])
    for eye in EYES:
        drivers.add(cons["eyeball_track", eye], "influence", type="SCRIPTED", variables=[v.track, v.trackCorr],
                    expression=f"{v.track.name} * {v.trackCorr.name}")
    for eye, other in ((LEFT, RIGHT), (RIGHT, LEFT)):
        _track_correction_driver(rig, v, eye, other)

    drivers.add(cons["head_rotation"], "influence", type="AVERAGE", variables=[v.head_track])
    drivers.add(cons["head_limit"], "influence", type="AVERAGE", variables=[v.head_limit])
    for variable, prop in zip(v.head_rotation, ("min_x", "max_x", "min_y", "max_y", "min_z", "max_z")):
        drivers.add(cons["head_limit"], prop, type="SCRIPTED", variables=[variable], expression=f"radians({variable.name})")
    for i, variable in enumerate(v.head_parent):
        drivers.add(cons["head_target_parent"].targets[i], "weight", type="AVERAGE", variables=[variable])

    for name in (names.EYEBALLS_BONE, LEFT.eyeball, RIGHT.eyeball):
        rig.pose.bones[name].lock_location = (True, True, True)
