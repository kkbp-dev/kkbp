"""What drives each shape key: terms, which the controls add, summed in one driver per key as
`clamp(raw + term + ..., 0, 1)`, where `raw` is the key's Face Properties slider if it has one.

A term is an expression fragment with `{placeholders}` and the driver variables they stand for.
Every expression is a simple one, so the face moves with auto-run Python off (ADR 0058).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ... import names
from ...drivers import Variable

MAX_EXPRESSION = 255  # Blender keeps no more (importer/README.md, "Blender quirks")


@dataclass
class Term:
    expr: str
    variables: dict = field(default_factory=dict)  # placeholder -> Variable (its name is replaced)


def channel(rig, bone, transform, space="LOCAL_SPACE", rotation_mode=None):
    """A variable reading a bone's transform channel; LOCAL_SPACE includes its limit constraints."""
    return Variable("", "TRANSFORMS", rig, bone=bone, space=space, transform=transform, rotation_mode=rotation_mode)


def prop(rig, data_path):
    return Variable("", "SINGLE_PROP", rig, data_path=data_path)


def axis(rig, bone, transform, travel, sign=1.0, weight=1.0, start=0.0):
    """Moving `bone` by `travel` along `transform` in the `sign` direction, past `start`, gives
    `weight`; the other direction gives nothing."""
    k = round(sign * weight / travel, 5)
    base = "({c}-1)" if transform.startswith("SCALE") else "{c}"
    if start:
        off = round(sign * start, 6)
        expr = f"max(0,({base}-{off})*{k})".replace("--", "+")
    else:
        expr = f"max(0,{base}*{k})"
    return Term(expr, {"c": channel(rig, bone, transform)})


class Terms:
    def __init__(self):
        self.by_key = {}

    def add(self, key, term, weight=1.0):
        if weight != 1.0:
            term = Term(f"{round(weight, 5)}*({term.expr})", term.variables)
        self.by_key.setdefault(key, []).append(term)

    def keys(self):
        return list(self.by_key)


def build_drivers(rig, body, terms, raw_keys, log):
    """One driver per key that has a Face Properties slider or a term."""
    keys = body.data.shape_keys
    raw = set(raw_keys)
    for name in list(raw_keys) + [k for k in terms.keys() if k not in raw]:
        block = keys.key_blocks.get(name)
        if block is None:
            log.warning(f"The face rig has no shape key {name!r} to drive")
            continue
        variables, parts = [], []
        if name in raw:
            path = f'pose.bones["{names.FACE_PROPERTIES_BONE}"]["{name}"]'
            variables.append(Variable("r", "SINGLE_PROP", rig, data_path=path))
            parts.append("r")
        for i, term in enumerate(terms.by_key.get(name, ())):
            mapping = {}
            for placeholder, variable in term.variables.items():
                mapping[placeholder] = f"{placeholder}{i}"
                variables.append(Variable(f"{placeholder}{i}", variable.type, variable.target, bone=variable.bone,
                                          space=variable.space, transform=variable.transform,
                                          data_path=variable.data_path, rotation_mode=variable.rotation_mode))
            parts.append(term.expr.format(**mapping))
        expression = "r" if parts == ["r"] else f"clamp({'+'.join(parts)},0,1)"
        if len(expression) > MAX_EXPRESSION:
            raise ValueError(f"The face rig's driver for {name!r} is {len(expression)} characters long")
        driver(keys, f'key_blocks["{_quote(name)}"].value', expression, [(v.name, v) for v in variables])
        block.slider_max = 1.0


def _quote(name):
    return name.replace("\\", "\\\\").replace('"', '\\"')


def driver(owner, path, expression, variables, index=-1):
    """A scripted driver on item `index` of `owner`'s `path` (-1: the property as a whole), whose
    expression must be simple. `variables` are (name, Variable) pairs."""
    fcurve = owner.driver_add(path, index)
    for modifier in list(fcurve.modifiers):
        fcurve.modifiers.remove(modifier)
    d = fcurve.driver
    d.type = "SCRIPTED"
    for name, v in variables:
        variable = d.variables.new()
        variable.name, variable.type = name, v.type
        target = variable.targets[0]
        target.id = v.target
        if v.data_path:
            target.data_path = v.data_path
        if v.bone:
            target.bone_target = v.bone
        if v.space:
            target.transform_space = v.space
        if v.transform:
            target.transform_type = v.transform
        if v.rotation_mode:
            target.rotation_mode = v.rotation_mode
    d.expression = expression
    if not d.is_simple_expression:
        raise ValueError(f"Not a simple expression: {expression}")
    return fcurve
