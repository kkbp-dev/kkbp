"""`.SVS lif_main_cloth`: SVS's clothes shader as the exporter bakes it, at one N.L
(models.lif_main_cloth).

    line  = clamp(mix(Color, Line color, Line power * 0.8 + 0.2), 0, 0.95)
    lit   = clamp(Color, 0, 0.95) * `.SVS item light`(Color)
    lit   = Alpha line ? mix(line, lit, round(Create alpha)) : lit
    Color = clamp(lit + d * (d * line - lit), 0, 0.95),  d = Detail's red

Linear colours. Written by hand."""

NAME = '.SVS lif_main_cloth'
KIND = 'ShaderNodeTree'

LIGHT = ('Detail', 'Ramp 1', 'Ramp 2', 'Shadow setting', 'Shadow setting w', 'Shadow power', 'Shadow extend',
         'Shadow color on', 'Type select', 'Shadow color', 'Light color', 'Ambient')


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.5, 0.5, 0.5, 1.0))
    t.socket('INPUT', 'Create alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    item = lib.group('.SVS item light')
    for s in item.interface.items_tree:
        if getattr(s, 'in_out', None) == 'INPUT' and s.name in LIGHT:
            d = s.default_value
            t.socket('INPUT', s.name, s.socket_type, default_value=tuple(d) if hasattr(d, '__len__') else d)
    t.socket('INPUT', 'Line color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Line power', 'NodeSocketFloat', default_value=1.0)
    t.socket('INPUT', 'Alpha line', 'NodeSocketFloat', default_value=1.0)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (1000, 0))
    m = t.math
    t.make('ShaderNodeGroup', 'light', (-900, -100), {'node_tree': item, 'width': 220.0},
           {'Color': ('in', 'Color'), **{n: ('in', n) for n in LIGHT}})
    t.make('ShaderNodeVectorMath', 'shown', (-900, 300), {'operation': 'MINIMUM'}, {'Vector': ('in', 'Color'), 'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeVectorMath', 'lit', (-650, 200), {'operation': 'MULTIPLY'}, {'Vector': ('shown', 'Vector'), 'Vector_001': ('light', 'Light')})
    t.make('ShaderNodeMix', 'line.mix', (-900, 600), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': m('line.f', 'MULTIPLY_ADD', ('in', 'Line power'), 0.8, 0.2, location=(-1100, 700)),
            'A_Vector': ('in', 'Color'), 'B_Vector': ('in', 'Line color')})
    t.make('ShaderNodeVectorMath', 'line', (-700, 600), {'operation': 'MINIMUM'}, {'Vector': ('line.mix', 'Result_Vector'),
                                                                                 'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeMix', 'alpha.line', (-450, 400), {'data_type': 'VECTOR'},
           {'Factor_Float': m('round', 'ROUND', ('in', 'Create alpha'), location=(-650, 450)), 'A_Vector': ('line', 'Vector'),
            'B_Vector': ('lit', 'Vector')})
    t.make('ShaderNodeMix', 'base', (-250, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Alpha line'), 'A_Vector': ('lit', 'Vector'), 'B_Vector': ('alpha.line', 'Result_Vector')})
    t.make('ShaderNodeSeparateColor', 'detail', (-700, -600), ins={'Color': ('in', 'Detail')})
    d = ('detail', 'Red')
    t.make('ShaderNodeVectorMath', 'dline', (-250, 600), {'operation': 'SCALE'}, {'Vector': ('line', 'Vector'), 'Scale': d})
    t.make('ShaderNodeMix', 'lined', (0, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': d, 'A_Vector': ('base', 'Result_Vector'), 'B_Vector': ('dline', 'Vector')})
    t.make('ShaderNodeVectorMath', 'result', (200, 300), {'operation': 'MINIMUM'}, {'Vector': ('lined', 'Result_Vector'),
                                                                                  'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeVectorMath', 'result.low', (350, 300), {'operation': 'MAXIMUM'}, {'Vector': ('result', 'Vector'),
                                                                                      'Vector_001': (0.0, 0.0, 0.0)})
    t.link('result.low', 'Vector', 'out', 'Color')
    return t
