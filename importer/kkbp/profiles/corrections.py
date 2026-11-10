"""The games' joint corrections as data, and a plain evaluation of them (docs/design/joint-corrections.md).

A Game Profile's `CORRECTIONS` lists what the game reads from the pose (`inputs`), values worked out
from those (`values`), and what it then writes to the correction bones (`outputs`), in the game's own
order and units: Unity's left-handed space, degrees, and each bone's position in its parent's unscaled
units. Every formula is an expression of input and value names that Python and a Blender driver both
understand: arithmetic, comparisons, `a if c else b`, and the functions in `FUNCTIONS`.

`evaluate` runs the rules on a `Pose`, as the game does each frame. The host tests compare it with
what the games themselves did (importer/tests/data/corrections), and the corrections Step uses it for
the rest pose's values and to check its drivers.

Inputs:
- ("euler", bone, order, axis): a component of the bone's local rotation as Euler angles in the
  game's `ConvertRotation` order.
- ("point", bone, offset, frame, axis): where the bone is, or a point `offset` from it along its own
  axes, as seen from a frame:
    ("under", bone, (x, y, z)): a child of that bone at that local position;
    ("bone", bone): the bone itself;
    ("at", bone, rotation_bone): at the first bone, turned as the second, with no scale.
- ("rest_position", bone, axis), ("rest_scale", bone, axis): the bone's own local position or scale.
  The corrections never move these bones, so the rest pose's value stands for the game's live one.

Outputs, applied in order:
- ("position", bone, {axis: formula}): sets those components of the local position.
- ("rotation", bone, order, {axis: formula}): reads the local rotation as Euler angles in `order`,
  replaces those components and writes it back. Unity's own Euler angles are order "yxz".
- ("scale", bone, {axis: formula}): sets those components of the local scale.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from . import gamemath as gm

FUNCTIONS = MappingProxyType({
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "atan2": math.atan2, "radians": math.radians,
    "degrees": math.degrees, "abs": abs, "min": min, "max": max,
})
_AXES = "xyz"
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_KEYWORDS = frozenset(("if", "else", "and", "or", "not"))


class CorrectionError(Exception):
    """A profile's CORRECTIONS is wrong."""


@dataclass(frozen=True)
class Input:
    kind: str  # euler, point, rest_position or rest_scale
    bone: str
    axis: int
    order: str | None = None  # euler
    offset: gm.Vec | None = None  # point
    frame: tuple | None = None  # point


@dataclass(frozen=True)
class Output:
    kind: str  # position, rotation or scale
    bone: str
    formulas: Mapping[int, str]  # axis -> formula
    order: str | None = None  # rotation


@dataclass(frozen=True)
class Corrections:
    inputs: Mapping[str, Input]
    values: Mapping[str, str]
    outputs: tuple[Output, ...]

    def names(self, formula: str) -> tuple[str, ...]:
        """The inputs and values a formula uses, in the order they first appear."""
        found = []
        for name in _NAME.findall(formula):
            if name not in FUNCTIONS and name not in _KEYWORDS and name not in found:
                found.append(name)
        return tuple(found)

    def bones(self) -> set[str]:
        """Every bone the rules name."""
        found = {o.bone for o in self.outputs}
        for i in self.inputs.values():
            found.add(i.bone)
            if i.frame is not None:
                found.update(b for b in i.frame[1:] if isinstance(b, str))
        return found

    def without(self, missing) -> "Corrections":
        """The rules that can still run on a skeleton that lacks the `missing` bones: an output goes
        if its bone or anything a formula of it reads is missing."""
        missing = set(missing)
        bad = {name for name, i in self.inputs.items()
               if i.bone in missing or (i.frame and any(b in missing for b in i.frame[1:] if isinstance(b, str)))}
        changed = True
        while changed:
            changed = False
            for name, formula in self.values.items():
                if name not in bad and any(n in bad for n in self.names(formula)):
                    bad.add(name)
                    changed = True
        outputs = tuple(o for o in self.outputs if o.bone not in missing
                        and not any(n in bad for f in o.formulas.values() for n in self.names(f)))
        used = set()
        todo = [n for o in outputs for f in o.formulas.values() for n in self.names(f)]
        while todo:
            n = todo.pop()
            if n not in used:
                used.add(n)
                todo.extend(self.names(self.values[n]) if n in self.values else ())
        return Corrections(inputs=MappingProxyType({k: v for k, v in self.inputs.items() if k in used}),
                           values=MappingProxyType({k: v for k, v in self.values.items() if k in used}),
                           outputs=outputs)


def _axis(game, where, axis):
    if axis not in _AXES or len(axis) != 1:
        raise CorrectionError(f"profile {game}: CORRECTIONS {where} has no axis {axis!r}")
    return _AXES.index(axis)


def parse(game: str, data) -> Corrections:
    """A profile module's CORRECTIONS as checked, read-only rules."""
    try:
        inputs = {}
        for name, spec in data["inputs"].items():
            kind = spec[0]
            if kind == "euler":
                _, bone, order, axis = spec
                if order not in gm.ORDERS:
                    raise CorrectionError(f"profile {game}: CORRECTIONS input {name} has unknown order {order!r}")
                inputs[name] = Input(kind, bone, _axis(game, name, axis), order=order)
            elif kind == "point":
                _, bone, offset, frame, axis = spec
                if frame[0] not in ("under", "bone", "at"):
                    raise CorrectionError(f"profile {game}: CORRECTIONS input {name} has unknown frame {frame[0]!r}")
                inputs[name] = Input(kind, bone, _axis(game, name, axis),
                                     offset=tuple(float(c) for c in offset) if offset else None,
                                     frame=tuple(tuple(float(c) for c in p) if isinstance(p, (tuple, list)) else p
                                                 for p in frame))
            elif kind in ("rest_position", "rest_scale"):
                _, bone, axis = spec
                inputs[name] = Input(kind, bone, _axis(game, name, axis))
            else:
                raise CorrectionError(f"profile {game}: CORRECTIONS input {name} has unknown kind {kind!r}")
        values = dict(data["values"])
        outputs = []
        for spec in data["outputs"]:
            kind, bone = spec[0], spec[1]
            if kind == "rotation":
                order, formulas = spec[2], spec[3]
                if order not in gm.ORDERS:
                    raise CorrectionError(f"profile {game}: CORRECTIONS output {bone} has unknown order {order!r}")
            elif kind in ("position", "scale"):
                order, formulas = None, spec[2]
            else:
                raise CorrectionError(f"profile {game}: CORRECTIONS output {bone} has unknown kind {kind!r}")
            outputs.append(Output(kind, bone, MappingProxyType({_axis(game, bone, a): f for a, f in formulas.items()}),
                                  order=order))
        rules = Corrections(MappingProxyType(inputs), MappingProxyType(values), tuple(outputs))
    except (KeyError, TypeError, ValueError, IndexError) as ex:
        raise CorrectionError(f"profile {game}: CORRECTIONS is malformed ({ex})") from None
    overlap = set(inputs) & set(values)
    if overlap:
        raise CorrectionError(f"profile {game}: CORRECTIONS names {sorted(overlap)} are both inputs and values")
    for where, formula in [*values.items(), *((o.bone, f) for o in outputs for f in o.formulas.values())]:
        try:
            compile(formula, "<formula>", "eval")
        except SyntaxError as ex:
            raise CorrectionError(f"profile {game}: CORRECTIONS formula for {where} doesn't parse ({ex.msg})") from None
        unknown = [n for n in rules.names(formula) if n not in inputs and n not in values]
        if unknown:
            raise CorrectionError(f"profile {game}: CORRECTIONS formula for {where} uses unknown {', '.join(unknown)}")
    return rules


# --- evaluation -------------------------------------------------------------------------

@dataclass
class Bone:
    parent: str | None
    position: gm.Vec
    rotation: gm.Quat
    scale: gm.Vec = (1.0, 1.0, 1.0)


@dataclass
class Pose:
    """Bones by name with their local transforms, in the game's space and units."""

    bones: dict[str, Bone] = field(default_factory=dict)

    def copy(self) -> "Pose":
        return Pose({n: Bone(b.parent, b.position, b.rotation, b.scale) for n, b in self.bones.items()})

    def _chain(self, name):
        chain = []
        while name is not None and name in self.bones:
            chain.append(self.bones[name])
            name = self.bones[name].parent
        return chain

    def to_world(self, name: str, point: gm.Vec) -> gm.Vec:
        """Transform.TransformPoint: a point in the bone's own space, in the root's."""
        for b in self._chain(name):
            point = gm.add(gm.rotate(b.rotation, gm.mul(point, b.scale)), b.position)
        return point

    def to_local(self, name: str, point: gm.Vec) -> gm.Vec:
        """Transform.InverseTransformPoint."""
        for b in reversed(self._chain(name)):
            point = gm.div(gm.rotate(gm.qinv(b.rotation), gm.sub(point, b.position)), b.scale)
        return point

    def world_rotation(self, name: str) -> gm.Quat:
        q = gm.IDENTITY
        for b in self._chain(name):
            q = gm.qmul(b.rotation, q)
        return q


def read(rules: Corrections, pose: Pose, i: Input, rest: Pose | None = None) -> float:
    """One input, as the game reads it from the pose."""
    if i.kind == "euler":
        return gm.to_euler(i.order, pose.bones[i.bone].rotation)[i.axis]
    if i.kind == "rest_position":
        return (rest or pose).bones[i.bone].position[i.axis]
    if i.kind == "rest_scale":
        return (rest or pose).bones[i.bone].scale[i.axis]
    point = pose.to_world(i.bone, (0.0, 0.0, 0.0))
    if i.offset:
        point = gm.add(point, gm.rotate(pose.world_rotation(i.bone), i.offset))
    kind = i.frame[0]
    if kind == "bone":
        return pose.to_local(i.frame[1], point)[i.axis]
    if kind == "under":
        return gm.sub(pose.to_local(i.frame[1], point), i.frame[2])[i.axis]
    origin = pose.to_world(i.frame[1], (0.0, 0.0, 0.0))
    return gm.rotate(gm.qinv(pose.world_rotation(i.frame[2])), gm.sub(point, origin))[i.axis]


class _Names(dict):
    """Formula names, worked out when a formula first asks for them."""

    def __init__(self, rules, pose, rest):
        super().__init__(FUNCTIONS)
        self.rules, self.pose, self.rest = rules, pose, rest

    def __missing__(self, name):
        if name in self.rules.inputs:
            value = read(self.rules, self.pose, self.rules.inputs[name], self.rest)
        else:
            value = eval(self.rules.values[name], {"__builtins__": {}}, self)  # noqa: S307 (profile data)
        self[name] = value
        return value


def formula_values(rules: Corrections, pose: Pose, names, rest: Pose | None = None) -> dict[str, float]:
    """The values of inputs or values by name, read from `pose` as it stands."""
    env = _Names(rules, pose, rest)
    return {n: env[n] for n in names}


def evaluate(rules: Corrections, pose: Pose, rest: Pose | None = None) -> Pose:
    """`pose` after one run of the game's corrections. `rest` is where the rest_ inputs are read."""
    pose = pose.copy()
    for o in rules.outputs:
        env = _Names(rules, pose, rest)  # afresh: an earlier output may be a later one's input
        new = {axis: float(eval(f, {"__builtins__": {}}, env)) for axis, f in o.formulas.items()}  # noqa: S307
        bone = pose.bones[o.bone]
        if o.kind == "rotation":
            e = list(gm.to_euler(o.order, bone.rotation))
            for axis, v in new.items():
                e[axis] = v
            bone.rotation = gm.from_euler(o.order, tuple(e))
        else:
            v = list(bone.position if o.kind == "position" else bone.scale)
            for axis, value in new.items():
                v[axis] = value
            if o.kind == "position":
                bone.position = tuple(v)
            else:
                bone.scale = tuple(v)
    return pose
