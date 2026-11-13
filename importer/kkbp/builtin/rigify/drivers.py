"""Drivers the Rigify Hook adds, and the bone properties they read."""

from __future__ import annotations

from dataclasses import dataclass

from rna_prop_ui import rna_idprop_ui_create


@dataclass(frozen=True)
class Variable:
    """One driver variable. `target` is the object read; `bone`, `space` and `transform` describe a
    TRANSFORMS variable, `target2`, `bone2` and `space2` the second end of a distance or rotation
    difference, and `data_path` a SINGLE_PROP one."""
    name: str
    type: str
    target: object
    bone: str = None
    space: str = None
    target2: object = None
    bone2: str = None
    space2: str = None
    data_path: str = None
    transform: str = None
    rotation_mode: str = None


def add(owner, path, *, type, variables, expression=None, index=None):
    """A driver on `owner`'s `path` (item `index` of an array property). Returns its F-curve."""
    # A falsy index adds the driver to the property as a whole, as the legacy helper did; the
    # callers that drive an array's first item rely on that for a property that has one value.
    fcurve = owner.driver_add(path, index) if index else owner.driver_add(path)
    fcurve.driver.type = type
    for v in variables:
        variable = fcurve.driver.variables.new()
        variable.name = v.name
        variable.type = v.type
        first = variable.targets[0]
        first.id = v.target
        if v.data_path:
            first.data_path = v.data_path
        if v.bone:
            first.bone_target = v.bone
        if v.space:
            first.transform_space = v.space
        if v.transform:
            first.transform_type = v.transform
        if v.rotation_mode:
            first.rotation_mode = v.rotation_mode
        if v.target2:
            variable.targets[1].id = v.target2
        if v.bone2:
            variable.targets[1].bone_target = v.bone2
        if v.space2:
            variable.targets[1].transform_space = v.space2
        if expression:
            fcurve.driver.expression = expression
    return fcurve


def bone_property(rig, bone, name, *, description, default, min, max):
    """A custom property on the pose bone, with its UI range; returns its data path, for drivers."""
    rna_idprop_ui_create(rig.pose.bones[bone], name, default=default, min=min, max=max, soft_min=None,
                         soft_max=None, description=description)
    return f'pose.bones["{bone}"]["{name}"]'
