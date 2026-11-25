"""`.KK grade`: the maker camera's AmplifyColor colour grade, `Lut_TimeDay.png`, on an sRGB-encoded
colour. Both games' light and dark bakes went through it, so every edit template grades
its light and dark colours last (models.grade). The table is read as `lut_nodes.lookup` says.
Written by hand."""

import lut_nodes

NAME = '.KK grade'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.make('NodeGroupInput', 'in', (-1500, 0))
    t.make('NodeGroupOutput', 'out', (1500, 0))
    t.link(*lut_nodes.lookup(t, lib.image('Lut_TimeDay.png'), ('in', 'Color')), 'out', 'Color')
    return t
