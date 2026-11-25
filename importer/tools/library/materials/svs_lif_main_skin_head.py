"""`SVS lif_main_skin_head`: the edit template for SVS's face, which the game draws with
LIF/lif_main_skin_head from the texture its create shader (LIF/lif_create_main_skin_head) composites.
With a create material (`use_create`), the template composites it in nodes (`.SVS create
skin head`), whose Eyeshadow param Save turns to 0 for the face's bakes without eyeshadow (ADR 0046);
without one, it takes the composited texture as it is. The cheek, lips and nose sit on the mesh's
second to fourth UV maps, scaled by the vertex colour's alpha, which keeps them off the bake's plane
(the game's quad has them cleared). It lights once, at the N.L the bake's toon value picks. No grade:
SVS's bake has none. Written by hand."""

import edit_templates

NAME = 'SVS lif_main_skin_head'
CREATE = ["create_skin_mask", "create_facetype", "create_paint1", "create_paint2", "create_paint3", "create_mole",
          "create_paint_mask", "create_eyeshadow"]
SLOTS = ["create", "cheek", "lip", "nose", "detail_mask", "detail_mask2", "matcap", "ramp", "ramp2", *CREATE]


def build(lib):
    t = edit_templates.begin(lib, NAME, SLOTS, grade=False)
    edit_templates.clamp(t, "ramp", "ramp2", "cheek", "lip", "nose", "create_paint1", "create_paint2", "create_paint3", "create_mole")
    t.make('ShaderNodeGroup', 'ndl', (-2100, -1700), {'node_tree': lib.group('.SVS toon ndl')})
    edit_templates.toon_through(t, 'ndl')
    t.make('ShaderNodeGroup', 'cheek uv', (-1700, 300 - 320), {'node_tree': lib.group('.SVS cheek uv')})
    t.link('cheek uv', 'Vector', 'tex.cheek', 'Vector')
    for slot, uv, row in (('lip', 'uv_underhair', 2), ('nose', 'uv_eyeshadow', 3)):
        t.make('ShaderNodeUVMap', f'uv.{slot}', (-1700, 300 - row * 320), {'uv_map': uv})
        t.link(f'uv.{slot}', 'UV', f'tex.{slot}', 'Vector')
    t.make('ShaderNodeCombineXYZ', 'view normal', (-1700, 300 - 6 * 320), ins={'X': 0.5, 'Y': 0.5, 'Z': 0.0})
    t.link('view normal', 'Vector', 'tex.matcap', 'Vector')
    for k in (1, 2, 3):
        t.make('ShaderNodeGroup', f'paint{k}', (-1900, 300 - (k + 11) * 320), {'node_tree': lib.group('.SVS face paint uv')})
        t.link(f'paint{k}', 'Vector', f'tex.create_paint{k}', 'Vector')
    t.make('ShaderNodeGroup', 'mole', (-1900, 300 - 15 * 320), {'node_tree': lib.group('.SVS face paint uv')}, {'Size': 2.4})
    t.link('mole', 'Vector', 'tex.create_mole', 'Vector')
    # The mesh-placed layers, off the bake's plane.
    t.make('ShaderNodeVertexColor', 'vertex', (-1100, 1300), {'layer_name': 'Color'})
    for slot in ('cheek', 'lip', 'nose'):
        t.make('ShaderNodeVectorMath', f'on.{slot}', (-900, 1200 - ('cheek', 'lip', 'nose').index(slot) * 150), {'operation': 'SCALE'},
               {'Vector': (f'encode.{slot}', 'Color'), 'Scale': ('vertex', 'Alpha')})
    t.make('ShaderNodeGroup', 'create', (-800, 1700), {'node_tree': lib.group('.SVS create skin head'), 'width': 260.0},
           {'Skin mask': ('encode.create_skin_mask', 'Color'), 'Facetype': ('encode.create_facetype', 'Color'),
            'Mole': ('encode.create_mole', 'Color'), 'Paint mask': ('encode.create_paint_mask', 'Color'),
            'Eyeshadow texture': ('encode.create_eyeshadow', 'Color'),
            **{f'Paint {k}': (f'encode.create_paint{k}', 'Color') for k in (1, 2, 3)},
            **{f'Paint {k} alpha': (f'tex.create_paint{k}', 'Alpha') for k in (1, 2, 3)}})
    t.make('ShaderNodeValue', 'use create', (-800, 900))
    t.tree.nodes['use create'].outputs[0].default_value = 0.0
    t.make('ShaderNodeMix', 'create.color', (-600, 1100), {'data_type': 'RGBA'},
           {'Factor_Float': ('use create', 'Value'), 'A_Color': ('encode.create', 'Color'), 'B_Color': ('create', 'Color')})
    t.make('ShaderNodeMix', 'create.alpha', (-600, 950), {'data_type': 'FLOAT'},
           {'Factor_Float': ('use create', 'Value'), 'A_Float': ('tex.create', 'Alpha'), 'B_Float': 1.0})
    t.make('ShaderNodeGroup', 'color', (-400, 900), {'node_tree': lib.group('.SVS skin head color'), 'width': 240.0},
           {'Create': ('create.color', 'Result_Color'), 'Create alpha': ('create.alpha', 'Result_Float'),
            'Cheek': ('on.cheek', 'Vector'), 'Lip': ('on.lip', 'Vector'), 'Nose': ('on.nose', 'Vector')})
    t.make('ShaderNodeGroup', 'ramp uv', (-1900, -1400), {'node_tree': lib.group('.SVS face ramp uv')},
           {'Detail 1': ('encode.detail_mask', 'Color'), 'Detail 2': ('encode.detail_mask2', 'Color'), 'Nose': ('on.nose', 'Vector'),
            'N.L': ('ndl', 'N.L')})
    t.link('ramp uv', 'Ramp 1', 'tex.ramp', 'Vector')
    t.link('ramp uv', 'Ramp 2', 'tex.ramp2', 'Vector')
    t.make('ShaderNodeGroup', 'lit', (-150, 100), {'node_tree': lib.group('.SVS lif_main_skin_head'), 'width': 260.0},
           {'Base': ('color', 'Base'), 'Color': ('color', 'Color'), 'Detail': ('ramp uv', 'Detail'),
            'Detail 2': ('encode.detail_mask2', 'Color'), 'Matcap': ('encode.matcap', 'Color'),
            'Ramp 1': ('encode.ramp', 'Color'), 'Ramp 2': ('encode.ramp2', 'Color')})
    edit_templates.light_dark(t, 'lit', light='Color', dark='Color')
    return t
