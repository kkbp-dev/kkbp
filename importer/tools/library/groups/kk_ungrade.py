"""`.KK ungrade`: the inverse of `.KK grade`, on an sRGB-encoded colour (ADR 0056): a colour the grade
turns into the one given. It reads `Lut_TimeDay inverse.exr` (importer/tools/make_ungrade_lut.py) as
`lut_nodes.lookup` says. Written by hand."""

import lut_nodes

NAME = '.KK ungrade'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.make('NodeGroupInput', 'in', (-1500, 0))
    t.make('NodeGroupOutput', 'out', (1500, 0))
    t.link(*lut_nodes.lookup(t, lib.image('Lut_TimeDay inverse.exr'), ('in', 'Color')), 'out', 'Color')
    return t
