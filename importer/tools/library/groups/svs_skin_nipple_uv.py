"""`.SVS skin nipple uv`: where SVS's body shader reads `_Nip` (models.skin_nipple_uv, issue 62): the
second UV map scaled about its centre by 2 - 2k and moved by Nip size * 0.27 + 0.04 (k = Nip size *
0.27 + 0.54), fading back to the UV map by clamp((|uv - 0.5| + 0.15) * 6.06 - 1). Written by hand."""

NAME = '.SVS skin nipple uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Nip size', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (700, 0))
    m = t.math
    t.make('ShaderNodeUVMap', 'uv2', (-900, 300), {'uv_map': 'uv_nipple_and_shine'})
    t.make('ShaderNodeVectorMath', 'off', (-700, 400), {'operation': 'SUBTRACT'}, {'Vector': ('uv2', 'UV'), 'Vector_001': (0.5, 0.5, 0.0)})
    t.make('ShaderNodeSeparateXYZ', 'off.xy', (-550, 400), ins={'Vector': ('off', 'Vector')})
    t.make('ShaderNodeCombineXYZ', 'off.2d', (-400, 400), ins={'X': ('off.xy', 'X'), 'Y': ('off.xy', 'Y'), 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'dist', (-250, 400), {'operation': 'LENGTH'}, {'Vector': ('off.2d', 'Vector')})
    reach = m('reach', 'MULTIPLY_ADD', m('reach.d', 'ADD', ('dist', 'Value'), 0.15, location=(-100, 450)), 6.060606, -1.0,
              location=(50, 450), clamp=True)
    scale = m('scale', 'MULTIPLY_ADD', ('in', 'Nip size'), -0.54, 0.92, location=(-700, 100))
    shift = m('shift', 'MULTIPLY_ADD', ('in', 'Nip size'), 0.27, 0.04, location=(-700, -50))
    t.make('ShaderNodeCombineXYZ', 'scale.v', (-500, 100), ins={'X': scale, 'Y': scale, 'Z': 1.0})
    t.make('ShaderNodeCombineXYZ', 'shift.v', (-500, -50), ins={'X': shift, 'Y': shift, 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'scaled', (-300, 100), {'operation': 'MULTIPLY_ADD'},
           {'Vector': ('uv2', 'UV'), 'Vector_001': ('scale.v', 'Vector'), 'Vector_002': ('shift.v', 'Vector')})
    t.make('ShaderNodeMix', 'nip', (300, 100), {'data_type': 'VECTOR'},
           {'Factor_Float': reach, 'A_Vector': ('scaled', 'Vector'), 'B_Vector': ('uv2', 'UV')})
    t.link('nip', 'Result_Vector', 'out', 'Vector')
    return t
