"""`.KK skin overlay uv`: where main_skin reads its first two overlays (models.nipple_uv): the nipples
on the second UV map, scaled about the nipple by Nip size where Nip is on, and the underhair on the
third; each times a channel of the vertex colour (red, blue), as the game's. The image nodes apply the
textures' own offset and scale after. The importer's bake copies the vertex colour to its flat mesh;
its plane has none (0), which keeps the overlays off it as the game's quad has. Written by hand."""

NAME = '.KK skin overlay uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Nipple', 'NodeSocketVector')
    t.socket('OUTPUT', 'Underhair', 'NodeSocketVector')
    t.socket('INPUT', 'Nip', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Nip size', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1100, 0))
    t.make('NodeGroupOutput', 'out', (700, 0))
    t.make('ShaderNodeUVMap', 'uv1', (-900, 300), {'uv_map': 'uv_nipple_and_shine'})
    t.make('ShaderNodeUVMap', 'uv2', (-900, -400), {'uv_map': 'uv_underhair'})
    t.make('ShaderNodeVertexColor', 'vertex', (-900, -150), {'layer_name': 'Color'})
    t.make('ShaderNodeSeparateColor', 'vc', (-700, -150), ins={'Color': ('vertex', 'Color')})

    # How far from the middle the nipple scaling reaches: saturate(|uv1 - 0.5| / 0.06 - 1).
    t.make('ShaderNodeVectorMath', 'off', (-700, 450), {'operation': 'SUBTRACT'},
           {'Vector': ('uv1', 'UV'), 'Vector_001': (0.5, 0.5, 0.0)})
    t.make('ShaderNodeVectorMath', 'dist', (-500, 450), {'operation': 'LENGTH'}, {'Vector': ('off', 'Vector')})
    reach = t.math('reach', 'MULTIPLY_ADD', ('dist', 'Value'), 1 / 0.06, -1.0, location=(-300, 450), clamp=True)
    k = t.math('scale', 'MULTIPLY_ADD', ('in', 'Nip size'), -1.4, 2.0, location=(-700, 150))
    c = t.math('shift', 'MULTIPLY_ADD', ('in', 'Nip size'), 0.7, -0.5, location=(-700, 0))
    t.make('ShaderNodeVectorMath', 'scaled', (-500, 250), {'operation': 'SCALE'}, {'Vector': ('uv1', 'UV'), 'Scale': k})
    t.make('ShaderNodeCombineXYZ', 'shift.v', (-500, 100), ins={'X': c, 'Y': c, 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'scaled.at', (-300, 250), {'operation': 'ADD'},
           {'Vector': ('scaled', 'Vector'), 'Vector_001': ('shift.v', 'Vector')})
    t.make('ShaderNodeMix', 'moved', (-100, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': reach, 'A_Vector': ('uv1', 'UV'), 'B_Vector': ('scaled.at', 'Vector')})
    t.make('ShaderNodeMix', 'nip', (100, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Nip'), 'A_Vector': ('uv1', 'UV'), 'B_Vector': ('moved', 'Result_Vector')})
    t.make('ShaderNodeVectorMath', 'nipple', (350, 300), {'operation': 'SCALE'},
           {'Vector': ('nip', 'Result_Vector'), 'Scale': ('vc', 'Red')})
    t.make('ShaderNodeVectorMath', 'underhair', (350, -300), {'operation': 'SCALE'},
           {'Vector': ('uv2', 'UV'), 'Scale': ('vc', 'Blue')})
    t.link('nipple', 'Vector', 'out', 'Nipple')
    t.link('underhair', 'Vector', 'out', 'Underhair')
    return t
