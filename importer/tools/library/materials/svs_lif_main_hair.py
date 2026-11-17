"""`SVS lif_main_hair`: the edit template for SVS's hair, which the game draws with LIF/lif_main_hair
from its colour mask and colours (issue 62). It lights once, at the N.L the bake's toon value picks
(`.SVS toon ndl`), reading the ramp at two places (the `ramp` and `ramp2` slots hold the same
texture). No grade: SVS's bake has none. Written by hand."""

import edit_templates

NAME = 'SVS lif_main_hair'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["color_mask", "detail1", "detail2", "ramp", "ramp2"], grade=False)
    edit_templates.clamp(t, "ramp", "ramp2")
    t.make('ShaderNodeGroup', 'ndl', (-1700, -1000), {'node_tree': lib.group('.SVS toon ndl')})
    edit_templates.toon_through(t, 'ndl')
    t.make('ShaderNodeGroup', 'ramp uv', (-1700, -700), {'node_tree': lib.group('.SVS ramp uv')},
           {'Detail': ('encode.detail1', 'Color'), 'Pull': 0.5, 'N.L': ('ndl', 'N.L')})
    t.link('ramp uv', 'Ramp 1', 'tex.ramp', 'Vector')
    t.link('ramp uv', 'Ramp 2', 'tex.ramp2', 'Vector')
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.SVS lif_main_hair'), 'width': 260.0},
           {'Color mask': ('encode.color_mask', 'Color'), 'Color mask alpha': ('tex.color_mask', 'Alpha'),
            'Detail 1': ('encode.detail1', 'Color'), 'Detail 2': ('encode.detail2', 'Color'),
            'Ramp 1': ('encode.ramp', 'Color'), 'Ramp 2': ('encode.ramp2', 'Color')})
    edit_templates.light_dark(t, 'lit', light='Color', dark='Color')
    return t
