"""`SVS lif_main_cloth`: the edit template for SVS's clothes and socks' composited texture, which the
game draws with LIF/lif_main_cloth (issue 62). Phase 1 takes the create shader's output
(`_Create_main_texture`) as it is. It lights once, at the N.L the bake's toon value picks. No grade:
SVS's bake has none. Written by hand."""

import edit_templates

NAME = 'SVS lif_main_cloth'
SLOTS = ["create", "color_mask", "detail_mask", "detail_mask2", "ramp", "ramp2"]


def build(lib):
    t = edit_templates.begin(lib, NAME, SLOTS, grade=False)
    edit_templates.clamp(t, "ramp", "ramp2")
    t.make('ShaderNodeGroup', 'ndl', (-1900, -1700), {'node_tree': lib.group('.SVS toon ndl')})
    edit_templates.toon_through(t, 'ndl')
    t.make('ShaderNodeGroup', 'ramp uv', (-1900, -1400), {'node_tree': lib.group('.SVS ramp uv')},
           {'Detail': ('encode.detail_mask', 'Color'), 'Lift detail': ('encode.detail_mask2', 'Color'), 'N.L': ('ndl', 'N.L')})
    t.link('ramp uv', 'Ramp 1', 'tex.ramp', 'Vector')
    t.link('ramp uv', 'Ramp 2', 'tex.ramp2', 'Vector')
    t.make('ShaderNodeGroup', 'color', (-800, 500), {'node_tree': lib.group('.SVS cloth color'), 'width': 240.0},
           {'Create': ('encode.create', 'Color'), 'Mask': ('encode.color_mask', 'Color'), 'Detail 2': ('encode.detail_mask2', 'Color')})
    t.make('ShaderNodeGroup', 'lit', (-450, 100), {'node_tree': lib.group('.SVS lif_main_cloth'), 'width': 260.0},
           {'Color': ('color', 'Color'), 'Create alpha': ('tex.create', 'Alpha'), 'Detail': ('encode.detail_mask', 'Color'),
            'Ramp 1': ('encode.ramp', 'Color'), 'Ramp 2': ('encode.ramp2', 'Color')})
    edit_templates.light_dark(t, 'lit', light='Color', dark='Color')
    return t
