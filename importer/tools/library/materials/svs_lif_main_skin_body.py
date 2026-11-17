"""`SVS lif_main_skin_body`: the edit template for SVS's body, which the game draws with
LIF/lif_main_skin_body from the texture its create shader (LIF/lif_create_main_skin_body) composites
(issue 62). With a create material (`use_create`), the template composites it in nodes (`.SVS create
skin body`); without one, it takes the composited texture as it is. The nipples and under-hair are
placed on the mesh's second UV map by its vertex colour, whose alpha keeps them off the bake's plane
(the game's quad has them cleared). It lights once, at the N.L the bake's toon value picks. No grade:
SVS's bake has none. Written by hand."""

import edit_templates

NAME = 'SVS lif_main_skin_body'
CREATE = ["create_sunburn", "create_paint1", "create_paint2", "create_paint3", "create_paint_mask"]
SLOTS = ["create", "nip", "underhair", "detail_mask", "detail_mask2", "detail_mask_highlight", "matcap", "ramp", "ramp2",
         "ramp3", *CREATE]


def build(lib):
    t = edit_templates.begin(lib, NAME, SLOTS, grade=False)
    edit_templates.clamp(t, "ramp", "ramp2", "ramp3", "nip", "underhair", "create_paint1", "create_paint2", "create_paint3")
    t.make('ShaderNodeGroup', 'ndl', (-2100, -1700), {'node_tree': lib.group('.SVS toon ndl')})
    edit_templates.toon_through(t, 'ndl')
    t.make('ShaderNodeGroup', 'ramp uv', (-1900, -1400), {'node_tree': lib.group('.SVS ramp uv')},
           {'Detail': ('encode.detail_mask2', 'Color'), 'N.L': ('ndl', 'N.L')})
    t.link('ramp uv', 'Ramp 1', 'tex.ramp', 'Vector')
    t.link('ramp uv', 'Ramp 2', 'tex.ramp2', 'Vector')
    t.make('ShaderNodeGroup', 'highlight uv', (-1900, -1000), {'node_tree': lib.group('.SVS skin highlight uv')},
           {'Toon shading': ('ndl', 'Toon shading'), 'Detail': ('encode.detail_mask', 'Color'), 'N.L': ('ndl', 'N.L')})
    t.link('highlight uv', 'Highlight', 'tex.detail_mask_highlight', 'Vector')
    t.link('highlight uv', 'Ramp', 'tex.ramp3', 'Vector')
    t.make('ShaderNodeGroup', 'nip uv', (-1700, 300 - 320), {'node_tree': lib.group('.SVS skin nipple uv')})
    t.link('nip uv', 'Vector', 'tex.nip', 'Vector')
    t.make('ShaderNodeUVMap', 'uv2', (-1700, 300 - 2 * 320), {'uv_map': 'uv_nipple_and_shine'})
    t.link('uv2', 'UV', 'tex.underhair', 'Vector')
    t.make('ShaderNodeCombineXYZ', 'view normal', (-1700, 300 - 6 * 320), ins={'X': 0.5, 'Y': 0.5, 'Z': 0.0})
    t.link('view normal', 'Vector', 'tex.matcap', 'Vector')
    for k in (1, 2, 3):
        t.make('ShaderNodeGroup', f'paint{k}', (-1900, 300 - (k + 10) * 320), {'node_tree': lib.group('.SVS paint uv')})
        t.link(f'paint{k}', 'Vector', f'tex.create_paint{k}', 'Vector')
    t.make('ShaderNodeVertexColor', 'vertex', (-1100, 1200), {'layer_name': 'Color'})
    t.make('ShaderNodeGroup', 'create', (-800, 1100), {'node_tree': lib.group('.SVS create skin body'), 'width': 260.0},
           {'Sunburn': ('encode.create_sunburn', 'Color'), 'Paint mask': ('encode.create_paint_mask', 'Color'),
            **{f'Paint {k}': (f'encode.create_paint{k}', 'Color') for k in (1, 2, 3)},
            **{f'Paint {k} alpha': (f'tex.create_paint{k}', 'Alpha') for k in (1, 2, 3)}})
    t.make('ShaderNodeValue', 'use create', (-800, 500))
    t.tree.nodes['use create'].outputs[0].default_value = 0.0
    t.make('ShaderNodeMix', 'create.color', (-600, 800), {'data_type': 'RGBA'},
           {'Factor_Float': ('use create', 'Value'), 'A_Color': ('encode.create', 'Color'), 'B_Color': ('create', 'Color')})
    t.make('ShaderNodeMix', 'create.alpha', (-600, 600), {'data_type': 'FLOAT'},
           {'Factor_Float': ('use create', 'Value'), 'A_Float': ('tex.create', 'Alpha'), 'B_Float': 1.0})
    t.make('ShaderNodeGroup', 'color', (-450, 700), {'node_tree': lib.group('.SVS skin body color'), 'width': 240.0},
           {'Create': ('create.color', 'Result_Color'), 'Create alpha': ('create.alpha', 'Result_Float'),
            'Nip': ('encode.nip', 'Color'), 'Nip alpha': ('tex.nip', 'Alpha'),
            'Underhair': ('encode.underhair', 'Color'), 'Underhair alpha': ('tex.underhair', 'Alpha'),
            'Detail 2': ('encode.detail_mask2', 'Color'), 'Vertex': ('vertex', 'Color'), 'On mesh': ('vertex', 'Alpha')})
    t.make('ShaderNodeGroup', 'lit', (-150, 100), {'node_tree': lib.group('.SVS lif_main_skin_body'), 'width': 260.0},
           {'Base': ('color', 'Base'), 'Color': ('color', 'Color'), 'Underhair amount': ('color', 'Underhair amount'),
            'Detail 1': ('encode.detail_mask', 'Color'), 'Detail 1 alpha': ('tex.detail_mask', 'Alpha'),
            'Highlight': ('encode.detail_mask_highlight', 'Color'), 'Detail 2': ('encode.detail_mask2', 'Color'),
            'Matcap': ('encode.matcap', 'Color'), 'Highlight ramp': ('encode.ramp3', 'Color'),
            'Ramp 1': ('encode.ramp', 'Color'), 'Ramp 2': ('encode.ramp2', 'Color')})
    edit_templates.light_dark(t, 'lit', light='Color', dark='Color')
    return t
