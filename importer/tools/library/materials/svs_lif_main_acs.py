"""`SVS lif_main_acs`: the edit template for SVS's accessories, teeth and tongue, which the game draws
with LIF/lif_main_acs from a main texture, colour mask and three patterns (issue 62). It lights once,
at the N.L the bake's toon value picks, reading the ramp at two places. No grade: SVS's bake has
none. Written by hand."""

import edit_templates

NAME = 'SVS lif_main_acs'
SLOTS = ["main", "color_mask", "pattern_mask1", "pattern_mask2", "pattern_mask3", "detail_mask", "ramp", "ramp2"]


def build(lib):
    t = edit_templates.begin(lib, NAME, SLOTS, grade=False)
    edit_templates.clamp(t, "ramp", "ramp2")
    t.make('ShaderNodeGroup', 'ndl', (-1900, -2300), {'node_tree': lib.group('.SVS toon ndl')})
    edit_templates.toon_through(t, 'ndl')
    for k in (1, 2, 3):
        t.make('ShaderNodeGroup', f'pattern{k}', (-1900, 300 - (k + 1) * 320), {'node_tree': lib.group('.SVS pattern uv')})
        t.link(f'pattern{k}', 'Vector', f'tex.pattern_mask{k}', 'Vector')
    t.make('ShaderNodeGroup', 'ramp uv', (-1900, -2000), {'node_tree': lib.group('.SVS ramp uv')},
           {'Detail': ('encode.detail_mask', 'Color'), 'N.L': ('ndl', 'N.L')})
    t.link('ramp uv', 'Ramp 1', 'tex.ramp', 'Vector')
    t.link('ramp uv', 'Ramp 2', 'tex.ramp2', 'Vector')
    ins = {'Inside 1': ('pattern1', 'Inside')}
    for slot, socket in (('main', 'Main'), ('color_mask', 'Mask'), ('pattern_mask1', 'Pattern 1'), ('pattern_mask2', 'Pattern 2'),
                         ('pattern_mask3', 'Pattern 3')):
        ins[socket] = (f'encode.{slot}', 'Color')
        ins[f'{socket} alpha'] = (f'tex.{slot}', 'Alpha')
    t.make('ShaderNodeGroup', 'color', (-800, 500), {'node_tree': lib.group('.SVS acs color'), 'width': 240.0}, ins)
    t.make('ShaderNodeGroup', 'lit', (-450, 100), {'node_tree': lib.group('.SVS lif_main_acs'), 'width': 260.0},
           {'Color': ('color', 'Color'), 'Color alpha': ('color', 'Alpha'), 'Mask': ('encode.color_mask', 'Color'),
            'Detail': ('encode.detail_mask', 'Color'), 'Ramp 1': ('encode.ramp', 'Color'), 'Ramp 2': ('encode.ramp2', 'Color')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit', light='Color', dark='Color')
    return t
