"""`SVS lif_main_nail`: the edit template for SVS's nails, which the game draws with LIF/lif_main_nail:
`.SVS nail color` from the colour mask, main texture and paints, lit by `.SVS lif_main_nail`
once, at the N.L the bake's toon value picks. The matcap is read at the bake quad's view normal, its
centre. No grade: SVS's bake has none. Written by hand."""

import edit_templates

NAME = 'SVS lif_main_nail'
SLOTS = ["color_mask", "main", "paint1", "paint2", "paint3", "matcap", "ramp", "ramp2"]


def build(lib):
    t = edit_templates.begin(lib, NAME, SLOTS, grade=False)
    edit_templates.clamp(t, "ramp", "ramp2", "paint1", "paint2", "paint3")
    t.make('ShaderNodeGroup', 'ndl', (-1900, -1700), {'node_tree': lib.group('.SVS toon ndl')})
    edit_templates.toon_through(t, 'ndl')
    t.make('ShaderNodeGroup', 'ramp uv', (-1900, -1400), {'node_tree': lib.group('.SVS ramp uv')}, {'N.L': ('ndl', 'N.L')})
    t.link('ramp uv', 'Ramp 1', 'tex.ramp', 'Vector')
    t.link('ramp uv', 'Ramp 2', 'tex.ramp2', 'Vector')
    for k in (1, 2, 3):
        t.make('ShaderNodeGroup', f'paint{k}', (-1900, 300 - (k + 1) * 320), {'node_tree': lib.group('.SVS paint uv')})
        t.link(f'paint{k}', 'Vector', f'tex.paint{k}', 'Vector')
    t.make('ShaderNodeCombineXYZ', 'view normal', (-1700, 300 - 5 * 320), ins={'X': 0.5, 'Y': 0.5, 'Z': 0.0})
    t.link('view normal', 'Vector', 'tex.matcap', 'Vector')
    t.make('ShaderNodeGroup', 'color', (-800, 500), {'node_tree': lib.group('.SVS nail color'), 'width': 240.0},
           {'Mask': ('encode.color_mask', 'Color'), 'Main': ('encode.main', 'Color'),
            **{f'Paint {k}': (f'encode.paint{k}', 'Color') for k in (1, 2, 3)},
            **{f'Paint {k} alpha': (f'tex.paint{k}', 'Alpha') for k in (1, 2, 3)}})
    t.make('ShaderNodeGroup', 'lit', (-450, 100), {'node_tree': lib.group('.SVS lif_main_nail'), 'width': 260.0},
           {'Color': ('color', 'Color'), 'Matcap': ('encode.matcap', 'Color'),
            'Ramp 1': ('encode.ramp', 'Color'), 'Ramp 2': ('encode.ramp2', 'Color')})
    edit_templates.light_dark(t, 'lit', light='Color', dark='Color')
    return t
