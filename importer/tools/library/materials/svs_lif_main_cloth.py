"""`SVS lif_main_cloth`: the edit template for SVS's clothes and socks, which the game draws with
LIF/lif_main_cloth from the texture its create shader (LIF/lif_create_main_cloth) composites (issue
62). With a create material (`use_create`), the template composites it in nodes from the create's
own textures and colours (`.SVS create cloth`); without one, it takes the composited texture as it
is. It lights once, at the N.L the bake's toon value picks. No grade: SVS's bake has none. Written
by hand."""

import edit_templates

NAME = 'SVS lif_main_cloth'
CREATE = ["create_main", "create_mask", "create_pattern1", "create_pattern2", "create_pattern3", "create_pattern4",
          "create_paint1", "create_paint2", "create_paint3", "create_paint_mask"]
SLOTS = ["create", "color_mask", "detail_mask", "detail_mask2", "ramp", "ramp2", *CREATE]
SOCKETS = {"create_main": "Main", "create_mask": "Mask", "create_paint_mask": "Paint mask",
           **{f"create_pattern{k}": f"Pattern {k}" for k in (1, 2, 3, 4)}, **{f"create_paint{k}": f"Paint {k}" for k in (1, 2, 3)}}


def build(lib):
    t = edit_templates.begin(lib, NAME, SLOTS, grade=False)
    edit_templates.clamp(t, "ramp", "ramp2", "create_paint1", "create_paint2", "create_paint3")
    t.make('ShaderNodeGroup', 'ndl', (-1900, -1700), {'node_tree': lib.group('.SVS toon ndl')})
    edit_templates.toon_through(t, 'ndl')
    t.make('ShaderNodeGroup', 'ramp uv', (-1900, -1400), {'node_tree': lib.group('.SVS ramp uv')},
           {'Detail': ('encode.detail_mask', 'Color'), 'Lift detail': ('encode.detail_mask2', 'Color'), 'N.L': ('ndl', 'N.L')})
    t.link('ramp uv', 'Ramp 1', 'tex.ramp', 'Vector')
    t.link('ramp uv', 'Ramp 2', 'tex.ramp2', 'Vector')
    for k in (1, 2, 3, 4):
        t.make('ShaderNodeGroup', f'pattern{k}', (-1900, 300 - (k + 6) * 320), {'node_tree': lib.group('.SVS create pattern uv')})
        t.link(f'pattern{k}', 'Vector', f'tex.create_pattern{k}', 'Vector')
    for k in (1, 2, 3):
        t.make('ShaderNodeGroup', f'paint{k}', (-1900, 300 - (k + 10) * 320), {'node_tree': lib.group('.SVS paint uv')})
        t.link(f'paint{k}', 'Vector', f'tex.create_paint{k}', 'Vector')
    ins = {}
    for slot, socket in SOCKETS.items():
        ins[socket] = (f'encode.{slot}', 'Color')
        ins[f'{socket} alpha'] = (f'tex.{slot}', 'Alpha')
    t.make('ShaderNodeGroup', 'create', (-800, 900), {'node_tree': lib.group('.SVS create cloth'), 'width': 260.0}, ins)
    t.make('ShaderNodeValue', 'use create', (-800, 300))
    t.tree.nodes['use create'].outputs[0].default_value = 0.0
    t.make('ShaderNodeMix', 'create.color', (-600, 600), {'data_type': 'RGBA'},
           {'Factor_Float': ('use create', 'Value'), 'A_Color': ('encode.create', 'Color'), 'B_Color': ('create', 'Color')})
    t.make('ShaderNodeMix', 'create.alpha', (-600, 400), {'data_type': 'FLOAT'},
           {'Factor_Float': ('use create', 'Value'), 'A_Float': ('tex.create', 'Alpha'), 'B_Float': ('create', 'Alpha')})
    t.make('ShaderNodeGroup', 'color', (-800, 500), {'node_tree': lib.group('.SVS cloth color'), 'width': 240.0},
           {'Create': ('create.color', 'Result_Color'), 'Mask': ('encode.color_mask', 'Color'), 'Detail 2': ('encode.detail_mask2', 'Color')})
    t.make('ShaderNodeGroup', 'lit', (-450, 100), {'node_tree': lib.group('.SVS lif_main_cloth'), 'width': 260.0},
           {'Color': ('color', 'Color'), 'Create alpha': ('create.alpha', 'Result_Float'), 'Detail': ('encode.detail_mask', 'Color'),
            'Ramp 1': ('encode.ramp', 'Color'), 'Ramp 2': ('encode.ramp2', 'Color')})
    edit_templates.light_dark(t, 'lit', light='Color', dark='Color')
    return t
