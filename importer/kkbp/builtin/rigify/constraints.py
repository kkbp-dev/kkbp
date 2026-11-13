"""Bone constraints the Rigify Hook adds. Each targets a bone of the same armature and replaces a
constraint of the same name on that bone, so running a step again doesn't stack them."""

from __future__ import annotations

AXES = "xyz"


def remove(rig, bone, name):
    constraint = rig.pose.bones[bone].constraints.get(name)
    if constraint:
        rig.pose.bones[bone].constraints.remove(constraint)


def move(rig, bone, name, index):
    """Moves the constraint `name` to `index` in the bone's stack."""
    constraints = rig.pose.bones[bone].constraints
    for i, constraint in enumerate(constraints):
        if constraint.name == name:
            constraints.move(i, index)
            break


def _new(rig, bone, kind, name):
    remove(rig, bone, name)
    constraint = rig.pose.bones[bone].constraints.new(kind)
    constraint.name = name
    return constraint


def copy_transforms(rig, bone, target, *, name, mix, space):
    c = _new(rig, bone, "COPY_TRANSFORMS", name)
    c.target, c.subtarget = rig, target
    c.mix_mode = mix
    c.owner_space = c.target_space = space
    return c


def copy_rotation(rig, bone, target, *, name, mix, space, use=(True, True, True), invert=(False, False, False)):
    c = _new(rig, bone, "COPY_ROTATION", name)
    c.target, c.subtarget = rig, target
    c.mix_mode = mix
    c.owner_space = c.target_space = space
    for axis, on, inverted in zip(AXES, use, invert):
        setattr(c, f"use_{axis}", on)
        setattr(c, f"invert_{axis}", inverted)
    return c


# The Transformation constraint's range and mix properties for each kind of channel.
_RANGE = {"LOCATION": "", "ROTATION": "_rot", "SCALE": "_scale"}
_MIX = {"LOCATION": "mix_mode", "ROTATION": "mix_mode_rot", "SCALE": "mix_mode_scale"}


def transformation(rig, bone, target, *, name, mix, space, map_from, from_range, map_to, to_range,
                   from_rotation_mode=None, to_euler_order=None, map_to_from=("X", "Y", "Z")):
    """`from_range` and `to_range` are ((min, max) for x, for y, for z), in the units of `map_from` and
    `map_to`. `mix` is the mix mode of the `map_to` channel."""
    c = _new(rig, bone, "TRANSFORM", name)
    c.target, c.subtarget = rig, target
    c.owner_space = c.target_space = space
    c.map_from = map_from
    if map_from == "ROTATION":
        c.from_rotation_mode = from_rotation_mode
    for axis, (low, high) in zip(AXES, from_range):
        setattr(c, f"from_min_{axis}{_RANGE[map_from]}", low)
        setattr(c, f"from_max_{axis}{_RANGE[map_from]}", high)
    c.map_to = map_to
    if map_to == "ROTATION":
        c.to_euler_order = to_euler_order
    for axis, (low, high) in zip(AXES, to_range):
        setattr(c, f"to_min_{axis}{_RANGE[map_to]}", low)
        setattr(c, f"to_max_{axis}{_RANGE[map_to]}", high)
    setattr(c, _MIX[map_to], mix)
    c.map_to_x_from, c.map_to_y_from, c.map_to_z_from = map_to_from
    return c


def limit_location(rig, bone, *, name, space, space_bone=None, min=(None, None, None), max=(None, None, None)):
    """A limit for each axis in `min` and `max`; None leaves that side of the axis free."""
    c = _new(rig, bone, "LIMIT_LOCATION", name)
    c.owner_space = space
    if space == "CUSTOM":
        c.space_object, c.space_subtarget = rig, space_bone
    for axis, low, high in zip(AXES, min, max):
        setattr(c, f"use_min_{axis}", low is not None)
        setattr(c, f"min_{axis}", low or 0.0)
        setattr(c, f"use_max_{axis}", high is not None)
        setattr(c, f"max_{axis}", high or 0.0)
    return c


def limit_rotation(rig, bone, *, name, space, space_bone=None, limits=(None, None, None)):
    """`limits` is a (min, max) in radians for each axis, or None to leave it free."""
    c = _new(rig, bone, "LIMIT_ROTATION", name)
    c.owner_space = space
    if space == "CUSTOM":
        c.space_object, c.space_subtarget = rig, space_bone
    for axis, limit in zip(AXES, limits):
        setattr(c, f"use_limit_{axis}", limit is not None)
        low, high = limit if limit is not None else (0.0, 0.0)
        setattr(c, f"min_{axis}", low)
        setattr(c, f"max_{axis}", high)
    return c


def armature(rig, bone, targets, *, name):
    c = _new(rig, bone, "ARMATURE", name)
    for i, target in enumerate(targets):
        c.targets.new()
        c.targets[i].target, c.targets[i].subtarget = rig, target
    return c


def damped_track(rig, bone, target, *, name):
    c = _new(rig, bone, "DAMPED_TRACK", name)
    c.target, c.subtarget = rig, target
    return c
