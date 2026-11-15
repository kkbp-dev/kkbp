"""Joint corrections: the game's own corrections (the Game Profile's CORRECTIONS,
profiles/corrections.py) rebuilt as hidden helper bones, constraints and drivers, so the correction
bones follow the limbs in Blender as they do in the game (docs/design/joint-corrections.md).

The rules work in the game's terms: each bone's local transform in its parent's frame, Unity's axes,
degrees and the parent's unscaled units. The helper bones give the drivers exactly those:

- `JC-F <bone>`, a child of the bone, rests on the game's own axes for it. Whatever way the Blender
  bone points (ADR 0017), this one turns as the game bone does.
- `JC-I <bone>` sits on the parent's `JC-F` and copies the bone's `JC-F` rotation, so its local
  rotation is the game's local rotation, rest included. A driver reads it as a quaternion and works
  out the game's Euler angles with the game's own formula.
- `JC-P …` and `JC-Q …` measure where a bone is from a frame, for the rules that read positions.
- `JC-R <name>` holds one input or value of the rules in its X location, so the drivers that use it
  stay under Blender's 256-character limit and simple enough to run without Python.
- `JC-H <bone>` sits on the parent's `JC-F` with the game's local transform of the correction bone
  as its channels; `JC-T <bone>` under it is where the correction bone must be, and the correction
  bone copies it.

Every driver is a simple expression, so the rig works with Python scripts off.

The Step keeps the rules and the bones' game rest poses on the armature (`kkbp_joint_corrections`)
and tags the bones they name (`kkbp_game_bone`). A Hook that changes the skeleton takes the
corrections off first (`remove`) and puts them back on the finished armature (`refresh`), which finds
each bone by its tag, so Hooks need neither the Game Profile nor the bundle's bone Ids.
"""

from __future__ import annotations

import json
import math
import re

import bpy
from mathutils import Matrix, Quaternion, Vector

from .bundle import model
from .editing import editing
from .profiles import corrections as rules_mod
from .profiles import gamemath as gm

COLLECTION = "Joint corrections (MCH)"
CONSTRAINT = "Joint correction"
STASH = "kkbp_joint_corrections"  # on the armature object: the rules and the game's rest poses
TAG = "kkbp_game_bone"  # on each bone they name: its game name
PREFIX = "JC-"
HELPER_LENGTH = 0.02
# glTF space (+Y up) into Blender's (+Z up), as the glTF importer turns it.
_TO_BLENDER = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
# The rules' Euler orders ("zyx" is Rz * Ry * Rx) as Blender's rotation modes, which name the axes in
# the order they apply.
BLENDER_ORDER = {order: order[::-1].upper() for order in gm.ORDERS}
_EXPRESSION_LIMIT = 255
_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class GameSkeleton:
    """The bundle's skeleton in the game's terms: each bone's frame in Blender's armature space and
    its local transform in Unity's space and the parent's unscaled units."""

    def __init__(self, skeleton):
        self.by_name = {}
        for b in skeleton.bones:
            self.by_name.setdefault(b.name, b)
        for b in skeleton.bones:  # an Id that is also a name wins
            if b.id == b.name:
                self.by_name[b.name] = b
        self._by_id = {b.id: b for b in skeleton.bones}
        self._world = {}

    def id(self, name):
        bone = self.by_name.get(name)
        return bone.id if bone else None

    def bone(self, name):
        return self.by_name[name]

    def parent(self, name):
        if name not in self.by_name:
            return None
        p = self.by_name[name].parent
        return self._by_id[p].name if p in self._by_id else None

    def _gltf_world(self, bone_id):
        if bone_id not in self._world:
            b = self._by_id[bone_id]
            x, y, z, w = b.rotation
            rot = Quaternion((w, x, y, z)).to_matrix()
            pos = Vector(b.translation)
            if b.parent in self._by_id:
                prot, ppos = self._gltf_world(b.parent)
                rot, pos = prot @ rot, ppos + prot @ pos
            self._world[bone_id] = (rot, pos)
        return self._world[bone_id]

    def frame(self, name, offset=(0.0, 0.0, 0.0)):
        """The game's frame of a bone, or of a point `offset` from it along its axes in world units
        (Unity's axes), as a Blender armature-space matrix with no scale."""
        rot, pos = self._gltf_world(self.by_name[name].id)
        pos = pos + rot @ Vector((-offset[0], offset[1], offset[2]))
        m = (_TO_BLENDER @ rot).to_4x4()
        m.translation = _TO_BLENDER @ pos
        return m

    def game_scale(self, name):
        return tuple(self.by_name[name].game_scale) if name else (1.0, 1.0, 1.0)

    def local(self, name):
        """The bone's local transform in the game at capture: position, rotation and scale."""
        b = self.by_name[name]
        ps = self.game_scale(self.parent(name))
        s = b.game_scale
        t = b.translation
        return ((-t[0] / ps[0], t[1] / ps[1], t[2] / ps[2]), (b.rotation[0], -b.rotation[1], -b.rotation[2], b.rotation[3]),
                (s[0] / ps[0], s[1] / ps[1], s[2] / ps[2]))

    def rest_pose(self, names):
        pose = rules_mod.Pose()
        todo = list(names)
        while todo:
            n = todo.pop()
            if n in pose.bones or n not in self.by_name:
                continue
            p, q, s = self.local(n)
            pose.bones[n] = rules_mod.Bone(self.parent(n), p, q, s)
            if pose.bones[n].parent:
                todo.append(pose.bones[n].parent)
        return pose


# --- the Step -------------------------------------------------------------------------------

def add_joint_corrections(ctx):
    """The game's joint corrections, from the Game Profile, on the armature (see the module's notes)."""
    armature, skeleton = ctx.character.armature, ctx.bundle.skeleton
    game = GameSkeleton(skeleton)
    rules = ctx.profile.corrections
    keep = []
    for name in sorted(rules.bones()):
        while name is not None and name in game.by_name and name not in keep:
            keep.append(name)
            name = game.parent(name)
    # Each named bone's children with a Bone Role can stand in for it on a rig that drops it (the
    # Rigify Hook drops KK's ankle, cf_j_leg03, and hangs the foot on the knee).
    stand_ins = {}
    for b in skeleton.bones:
        parent = game.parent(b.name)
        if b.role and parent in rules.bones() and b.name not in keep:
            stand_ins.setdefault(parent, b.name)
    keep += [n for n in stand_ins.values() if n not in keep]
    bones = [game.bone(n) for n in keep]
    armature[STASH] = json.dumps({
        "rules": rules_mod.to_data(rules),
        "bones": [{"name": b.name, "parent": game.parent(b.name), "translation": list(b.translation),
                   "rotation": list(b.rotation), "game_scale": list(b.game_scale)} for b in bones],
        "stand_ins": stand_ins})
    for b in bones:
        bone = armature.data.bones.get(b.id)
        if bone is not None:
            bone[TAG] = b.name
    count, missing = refresh(armature)
    if missing:
        ctx.log.info(f"No joint corrections need {', '.join(missing[:12])}{' …' if len(missing) > 12 else ''}, "
                     f"which the skeleton lacks")
    if count:
        ctx.log.info(f"Added the game's joint corrections to {count} bones")
    else:
        ctx.log.info("The skeleton has none of the bones the joint corrections move")


def has_corrections(armature) -> bool:
    return STASH in armature


def remove(armature):
    """Takes the corrections off: their helper bones, drivers and constraints. The stash and the tags
    stay, for `refresh`."""
    if armature.animation_data:
        for fcurve in list(armature.animation_data.drivers):
            if fcurve.data_path.startswith(f'pose.bones["{PREFIX}'):
                armature.animation_data.drivers.remove(fcurve)
    for pb in armature.pose.bones:
        c = pb.constraints.get(CONSTRAINT)
        if c is not None:
            pb.constraints.remove(c)
    helpers = [b.name for b in armature.data.bones if b.name.startswith(PREFIX)]
    if helpers:
        with editing(armature, "EDIT"):
            bones = armature.data.edit_bones
            for name in helpers:
                bones.remove(bones[name])
    collection = armature.data.collections_all.get(COLLECTION)
    if collection is not None:
        armature.data.collections.remove(collection)


def refresh(armature, source=None) -> tuple[int, list[str]]:
    """Builds the corrections afresh on `armature` from the stash on `source` (the armature itself
    by default), finding each bone by its tag. Returns how many bones they move, and the bones the
    rules name that it lacks."""
    source = source or armature
    remove(armature)
    if STASH not in source:
        return 0, []
    data = json.loads(source[STASH])
    if source is not armature:
        armature[STASH] = source[STASH]
    rules = rules_mod.parse("stash", data["rules"])
    skeleton = model.Skeleton(bones=tuple(
        model.Bone(id=b["name"], name=b["name"], parent=b["parent"], role=None, group="deform",
                   translation=tuple(b["translation"]), rotation=tuple(b["rotation"]), scale=(1.0, 1.0, 1.0),
                   game_scale=tuple(b["game_scale"])) for b in data["bones"]))
    game = GameSkeleton(skeleton)
    bone_of = tagged_bones(armature)
    # A dropped bone whose child stands in: the child's turns count as the bone's. Only what a bone
    # turns is read through its stand-in, so only bones the rules read rotations of may use one.
    turned = {i.bone for i in rules.inputs.values() if i.kind == "euler"}
    for name, child in data.get("stand_ins", {}).items():
        if name not in bone_of and child in bone_of and name in turned and \
                not any(i.bone == name or name in (i.frame or ()) for i in rules.inputs.values() if i.kind == "point") and \
                not any(o.bone == name or game.parent(o.bone) == name for o in rules.outputs):
            bone_of[name] = bone_of[child]
    missing = sorted(n for n in rules.bones() if n not in bone_of)
    # a bone whose rest frame comes from its parent needs the parent too
    framed = {i.bone for i in rules.inputs.values() if i.kind == "euler"} | {o.bone for o in rules.outputs}
    orphans = sorted(n for n in framed if n not in missing and game.parent(n) not in bone_of)
    rules = rules.without(missing + orphans)
    if not rules.outputs:
        return 0, missing
    return build(armature, game, rules, bone_of), missing


def tagged_bones(armature) -> dict[str, str]:
    """Each tagged game bone's bone in this armature: the bone of that name, else Rigify's ORG- copy,
    else the only other bone with the tag."""
    found = {}
    for bone in armature.data.bones:
        tag = bone.get(TAG)
        if tag:
            found.setdefault(tag, []).append(bone.name)
    out = {}
    for tag, names in found.items():
        best = [n for n in names if n == tag] or [n for n in names if n.startswith("ORG-")] or \
            [n for n in names if not n.startswith(("DEF-", "MCH-"))]
        if len(best) >= 1:
            out[tag] = best[0]
    return out


def build(armature, game: GameSkeleton, rules: rules_mod.Corrections, bone_of=None) -> int:
    """Builds the corrections on `armature`. `bone_of` maps a game bone name to its bone in the
    armature (by default its bundle Id). Returns how many bones they move."""
    plan = _Plan(armature, game, rules, bone_of or {n: b.id for n, b in game.by_name.items()})
    with editing(armature, "EDIT"):
        plan.make_bones(armature.data.edit_bones)
    plan.wire(armature)
    collection = armature.data.collections_all.get(COLLECTION) or armature.data.collections.new(COLLECTION)
    for name in plan.helpers:
        bone = armature.data.bones[name]
        for c in list(bone.collections):
            c.unassign(bone)
        collection.assign(bone)
        bone.hide = True
    collection.is_visible = False
    return len(plan.outputs)


class _Plan:
    def __init__(self, armature, game, rules, bone_of):
        self.armature, self.game, self.rules, self.bone_of = armature, game, rules, bone_of
        self.helpers: list[str] = []
        self._specs: dict[str, dict] = {}  # helper name -> how to make it
        self.outputs = _merge(rules.outputs)
        self.registers: dict[str, str] = {}
        self.constants: dict[str, float] = {}
        rest = game.rest_pose(rules.bones())
        unturned = {o.bone for o in self.outputs if not o.order}
        for name, i in rules.inputs.items():
            # A correction bone's own rotation, where no correction turns it, is its rest one: its
            # constraint holds it there, as nothing but an animation would turn it in the game.
            if i.kind in ("rest_position", "rest_scale") or (i.kind == "euler" and i.bone in unturned):
                self.constants[name] = rules_mod.read(rules, rest, i)
        self.rest = rest
        _check_cycles(rules, game, self.outputs, self.constants)

    # helpers ---------------------------------------------------------------------------------
    def _helper(self, name, **spec):
        if name not in self._specs:
            self._specs[name] = spec
            self.helpers.append(name)
        return name

    def frame(self, bone):
        """`JC-F <bone>`: on the game's axes of the bone, following it."""
        return self._helper(f"JC-F {bone}", parent=self.bone_of[bone], matrix=self.game.frame(bone))

    def euler_reader(self, bone):
        parent = self.game.parent(bone)
        return self._helper(f"JC-I {bone}", parent=self.frame(parent), matrix=self.game.frame(parent),
                            copy=("COPY_ROTATION", self.frame(bone)), mode="QUATERNION")

    def point(self, bone, offset):
        if not offset:
            return self.frame(bone)
        key = ",".join(f"{c:g}" for c in offset)
        return self._helper(f"JC-P {bone} {key}", parent=self.frame(bone), matrix=self.game.frame(bone, offset))

    def measuring_frame(self, frame):
        kind = frame[0]
        if kind == "bone":
            return self.frame(frame[1]), self.game.game_scale(frame[1])
        if kind == "under":
            bone, o = frame[1], frame[2]
            s = self.game.game_scale(bone)
            offset = (o[0] * s[0], o[1] * s[1], o[2] * s[2])
            key = ",".join(f"{c:g}" for c in o)
            return self._helper(f"JC-P {bone} {key}", parent=self.frame(bone), matrix=self.game.frame(bone, offset)), s
        at, turned = frame[1], frame[2]
        m = self.game.frame(turned)
        m.translation = self.game.frame(at).translation
        return self._helper(f"JC-A {at} {turned}", parent=self.frame(turned), matrix=m,
                            copy=("COPY_LOCATION", self.frame(at))), (1.0, 1.0, 1.0)

    def point_reader(self, i):
        frame, scale = self.measuring_frame(i.frame)
        target = self.point(i.bone, i.offset)
        name = self._helper(f"JC-Q {target[5:]} in {frame[5:]}", parent=frame, matrix=self._specs[frame]["matrix"],
                            copy=("COPY_LOCATION", target))
        return name, scale

    def register(self, name):
        if name not in self.registers:
            self.registers[name] = self._helper(f"JC-R {name}", parent=None, matrix=Matrix.Identity(4))
        return self.registers[name]

    # building ----------------------------------------------------------------------------------
    def make_bones(self, edit_bones):
        # Plan every helper first: reading the rules makes them.
        self._readers = {}
        for name, i in self.rules.inputs.items():
            if name in self.constants:
                continue
            if i.kind == "euler":
                self._readers[name] = ("euler", self.euler_reader(i.bone))
            else:
                self._readers[name] = ("point", *self.point_reader(i))
            self.register(name)
        for name in self.rules.values:
            self.register(name)
        self._holders = {}
        for out in self.outputs:
            for k in range(len(out.steps) - 1):
                self.register(f"{out.safe}_u{k}")
                for a in range(3):
                    self.register(f"{out.safe}_v{k}{a}")
            parent = self.game.parent(out.bone)
            pf = self.frame(parent)
            parent_frame = self.game.frame(parent)
            h = self._helper(f"JC-H {out.bone}", parent=pf, matrix=parent_frame, mode=out.mode)
            offset = parent_frame @ self.game.frame(out.bone).inverted() @ edit_bones[self.bone_of[out.bone]].matrix
            t = self._helper(f"JC-T {out.bone}", parent=h, matrix=offset)
            self._holders[out.bone] = (h, t)
        for name in self.helpers:
            spec = self._specs[name]
            eb = edit_bones.get(name) or edit_bones.new(name)
            eb.head, eb.tail, eb.roll = (0.0, 0.0, 0.0), (0.0, HELPER_LENGTH, 0.0), 0.0
            eb.matrix = spec["matrix"]
            eb.use_deform = False
            eb.use_connect = False
        for name in self.helpers:
            parent = self._specs[name]["parent"]
            if parent is not None:
                edit_bones[name].parent = edit_bones[parent]

    def wire(self, armature):
        pose = armature.pose.bones
        for name in self.helpers:
            spec = self._specs[name]
            pb = pose[name]
            pb.rotation_mode = spec.get("mode") or "QUATERNION"
            if "copy" in spec:
                kind, target = spec["copy"]
                c = pb.constraints.new(kind)
                c.name = CONSTRAINT
                c.target, c.subtarget = armature, target
                c.target_space = c.owner_space = "WORLD"
        # registers: one driver each, in the X location of its own bone
        for name, reg in self.registers.items():
            if name in self.rules.inputs:
                kind = self._readers[name][0]
                if kind == "euler":
                    i = self.rules.inputs[name]
                    variables = [(c, ("bone", self._readers[name][1], f"ROT_{c.upper()}", "LOCAL_SPACE", "QUATERNION"))
                                 for c in "wxyz"]
                    expression = gm.euler_expression(i.order, i.axis)
                else:
                    _, reader, scale = self._readers[name]
                    i = self.rules.inputs[name]
                    axis = "XYZ"[i.axis]
                    variables = [("v", ("bone", reader, f"LOC_{axis}", "LOCAL_SPACE", None))]
                    sign = "-" if i.axis == 0 else ""
                    expression = f"{sign}v/{_num(scale[i.axis])}"
            elif name in self.rules.values:
                expression, variables = self._formula(self.rules.values[name])
            else:
                continue  # a rotation step's, driven with its output
            _driver(armature, pose[reg], "location", 0, expression, variables)
        # outputs: the holder's channels are the game's local transform of the correction bone
        for out in self.outputs:
            h, t = self._holders[out.bone]
            ph = pose[h]
            parent_scale = self.game.game_scale(self.game.parent(out.bone))
            p, q, s = self.rest.bones[out.bone].position, self.rest.bones[out.bone].rotation, self.rest.bones[out.bone].scale
            for axis in range(3):
                mirror = -1.0 if axis == 0 else 1.0
                factor = mirror * parent_scale[axis]
                if axis in out.position:
                    expression, variables = self._formula(out.position[axis], f"({{}})*{_num(factor)}")
                    _driver(armature, ph, "location", axis, expression, variables)
                else:
                    ph.location[axis] = p[axis] * factor
            if out.order:
                self._rotation(armature, ph, out, gm.to_euler(out.order, q))
            if not out.order:
                x, y, z, w = q
                ph.rotation_quaternion = (w, x, -y, -z)
            for axis in range(3):
                if axis in out.scale:
                    expression, variables = self._formula(out.scale[axis], f"({{}})/{_num(s[axis])}")
                    _driver(armature, ph, "scale", axis, expression, variables)
            c = pose[self.bone_of[out.bone]].constraints.new("COPY_TRANSFORMS")
            c.name = CONSTRAINT
            c.target, c.subtarget = armature, t
            c.target_space = c.owner_space = "WORLD"

    def _term(self, term):
        kind, value = term
        if kind == "const":
            return f"({_num(value)})", []
        if kind == "formula":
            text, variables = self._formula(value)
            return f"({text})", variables
        return value, [(value, ("register", self.registers[value]))]

    def _rotation(self, armature, holder, out, rest_euler):
        """The holder's Euler channels after the bone's rotation steps. Before each later step the
        game reads the angles back in their usual form, so a middle angle past ±90° comes back as
        180° less it, with the other two turned by 180°."""
        pose = armature.pose.bones
        mid = "xyz".index(out.order[1])
        state = [("const", rest_euler[a]) for a in range(3)]
        for k, step in enumerate(out.steps):
            u = [("formula", step[a]) if a in step else state[a] for a in range(3)]
            if k == len(out.steps) - 1:
                break
            middle = f"{out.safe}_u{k}"
            text, variables = self._term(u[mid])
            _driver(armature, pose[self.registers[middle]], "location", 0, text, variables)
            m_vars = [(middle, ("register", self.registers[middle]))]
            state = []
            for a in range(3):
                name = f"{out.safe}_v{k}{a}"
                if a == mid:
                    expression = f"((180 if {middle}>0 else -180)-{middle} if abs({middle})>90 else {middle})"
                    variables = m_vars
                else:
                    text, variables = self._term(u[a])
                    expression = f"({text}+180 if abs({middle})>90 else {text})"
                    variables = variables + m_vars
                _driver(armature, pose[self.registers[name]], "location", 0, expression, variables)
                state.append(("reg", name))
        for a in range(3):
            mirror = -1.0 if a else 1.0
            if u[a][0] == "const":
                holder.rotation_euler[a] = math.radians(mirror * u[a][1])
            else:
                text, variables = self._term(u[a])
                _driver(armature, holder, "rotation_euler", a, f"radians({_num(mirror)}*{text})", variables)

    def _formula(self, formula, wrap="{}"):
        """A rule's formula as a driver expression with its variables, constants written in."""
        names = self.rules.names(formula)
        text = _WORD.sub(lambda m: f"({_num(self.constants[m.group(0)])})" if m.group(0) in self.constants
                         else m.group(0), formula)
        variables = [(n, ("register", self.registers[n])) for n in names if n not in self.constants]
        return wrap.format(text), variables


class _Output:
    """One correction bone's outputs merged: the last formula for each position and scale channel,
    and its rotations in one Euler order as steps. Each step sets some angles and keeps the others as
    the game reads them back, which matters when a step leaves the middle angle past ±90° (SVS)."""

    def __init__(self, bone):
        self.bone = bone
        self.position, self.scale = {}, {}
        self.steps: list[dict] = []
        self.order = None

    @property
    def rotation(self):
        merged = {}
        for step in self.steps:
            merged.update(step)
        return merged

    @property
    def safe(self):
        return re.sub(r"\W", "_", self.bone)

    @property
    def mode(self):
        return BLENDER_ORDER[self.order] if self.order else "QUATERNION"


def _merge(outputs):
    merged = {}
    for o in outputs:
        m = merged.setdefault(o.bone, _Output(o.bone))
        if o.kind == "rotation":
            if m.order not in (None, o.order):
                raise rules_mod.CorrectionError(f"CORRECTIONS turn {o.bone} in two Euler orders")
            m.order = o.order
            m.steps.append(dict(o.formulas))
        else:
            (m.position if o.kind == "position" else m.scale).update(o.formulas)
    return list(merged.values())


def _check_cycles(rules, game, outputs, constants):
    """A correction that reads a bone it moves, or one below it, would make a dependency cycle."""
    def ancestors(name):
        while name is not None:
            yield name
            name = game.parent(name)

    def inputs_of(formula, seen):
        for n in rules.names(formula):
            if n in rules.inputs:
                seen.add(n)
            elif n in rules.values and n not in seen:
                seen.add(n)
                inputs_of(rules.values[n], seen)
        return seen

    for out in outputs:
        used = set()
        for f in [*out.position.values(), *out.rotation.values(), *out.scale.values()]:
            inputs_of(f, used)
        for n in used:
            i = rules.inputs.get(n)
            if i is None or n in constants:
                continue
            bones = [i.bone] + [b for b in (i.frame or ())[1:] if isinstance(b, str)]
            if any(out.bone in ancestors(b) for b in bones):
                raise rules_mod.CorrectionError(f"the correction of {out.bone} reads {n}, which it moves")


def _num(v):
    return f"{v:.9g}"


def _driver(armature, owner, prop, index, expression, variables):
    if len(expression) > _EXPRESSION_LIMIT:
        raise rules_mod.CorrectionError(f"a joint-correction driver on {owner.name} is longer than Blender allows")
    owner.driver_remove(prop, index)
    fcurve = owner.driver_add(prop, index)
    driver = fcurve.driver
    driver.type = "SCRIPTED"
    seen = set()
    for name, (kind, *what) in variables:
        if name in seen:
            continue
        seen.add(name)
        var = driver.variables.new()
        var.name = name
        var.type = "TRANSFORMS"
        t = var.targets[0]
        t.id = armature
        if kind == "register":
            t.bone_target, t.transform_type, t.transform_space = what[0], "LOC_X", "TRANSFORM_SPACE"
        else:
            bone, ttype, space, mode = what
            t.bone_target, t.transform_type, t.transform_space = bone, ttype, space
            if mode:
                t.rotation_mode = mode
    driver.expression = expression
    # A new driver curve maps the value through keyframes (0, 0) and (1, 1) with an ease between, or
    # through a Generator; with neither, the driver's value is used as it is.
    for m in list(fcurve.modifiers):
        fcurve.modifiers.remove(m)
    while fcurve.keyframe_points:
        fcurve.keyframe_points.remove(fcurve.keyframe_points[0], fast=True)
    return fcurve
