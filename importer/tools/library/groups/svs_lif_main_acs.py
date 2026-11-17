"""`.SVS lif_main_acs`: SVS's item shader (accessories, teeth, tongue) as the exporter bakes it, at one
N.L (models.lif_main_acs, issue 62).

    c95   = Color * 0.95;  col = clamp(c95, 0, 0.95)
    line  = clamp(the mask's channels times Line color intensity k mixing c95 back over mix(c95, Line color, Line power), 0, 0.95)
    lit   = col * `.SVS item light`(c95)
    w     = Line width S * Line width * Line width SS
    Color = clamp(mix(Alpha line ? mix(line, lit, Alpha) : lit, line,
                      min(clamp(Detail.r * (w * 3.9 + 0.1) + w * 0.35 - 0.35, 0, 0.9), Line texture on)), 0, 0.95)

Alpha is the colour's alpha times `_alpha` (the shader's outline widening of the main texture's
alpha is left out). Linear colours. Written by hand."""

NAME = '.SVS lif_main_acs'
KIND = 'ShaderNodeTree'

LIGHT = ('Detail', 'Ramp 1', 'Ramp 2', 'Shadow setting', 'Shadow setting w', 'Shadow power', 'Shadow extend',
         'Shadow color on', 'Type select', 'Shadow color', 'Light color', 'Ambient')


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.5, 0.5, 0.5, 1.0))
    t.socket('INPUT', 'Color alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    item = lib.group('.SVS item light')
    for s in item.interface.items_tree:
        if getattr(s, 'in_out', None) == 'INPUT' and s.name in LIGHT:
            d = s.default_value
            t.socket('INPUT', s.name, s.socket_type, default_value=tuple(d) if hasattr(d, '__len__') else d)
    t.socket('INPUT', 'Line color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for name, d in (('Line power', 1.0), ('Line color intensity 1', 0.0), ('Line color intensity 2', 0.0),
                    ('Line color intensity 3', 0.0), ('Line width S', 0.0), ('Line width', 0.3), ('Line width SS', 1.0),
                    ('Line texture on', 1.0), ('Alpha line', 0.0), ('Alpha', 1.0)):
        t.socket('INPUT', name, 'NodeSocketFloat', default_value=d)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))
    m = t.math
    t.make('ShaderNodeVectorMath', 'c95', (-1200, 400), {'operation': 'SCALE'}, {'Vector': ('in', 'Color'), 'Scale': 0.95})
    t.make('ShaderNodeVectorMath', 'col', (-1050, 400), {'operation': 'MINIMUM'}, {'Vector': ('c95', 'Vector'), 'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeGroup', 'light', (-1050, 0), {'node_tree': item, 'width': 220.0},
           {'Color': ('c95', 'Vector'), **{n: ('in', n) for n in LIGHT}})
    t.make('ShaderNodeVectorMath', 'lit', (-800, 300), {'operation': 'MULTIPLY'}, {'Vector': ('col', 'Vector'), 'Vector_001': ('light', 'Light')})
    t.make('ShaderNodeSeparateColor', 'mask', (-1200, -600), ins={'Color': ('in', 'Mask')})
    t.make('ShaderNodeMix', 'line.power', (-1000, -400), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': ('in', 'Line power'), 'A_Vector': ('c95', 'Vector'), 'B_Vector': ('in', 'Line color')})
    line = ('line.power', 'Result_Vector')
    for k, ch in ((1, 'Red'), (2, 'Green'), (3, 'Blue')):
        t.make('ShaderNodeMix', f'line.{k}', (-1000 + k * 150, -400), {'data_type': 'VECTOR', 'clamp_factor': False},
               {'Factor_Float': m(f'line.{k}.f', 'MULTIPLY', ('mask', ch), ('in', f'Line color intensity {k}'), location=(-1000 + k * 150, -600)),
                'A_Vector': line, 'B_Vector': ('c95', 'Vector')})
        line = (f'line.{k}', 'Result_Vector')
    t.make('ShaderNodeVectorMath', 'line', (-350, -400), {'operation': 'MINIMUM'}, {'Vector': line, 'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeMix', 'shown', (-500, 100), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Color alpha'), 'A_Vector': ('line', 'Vector'), 'B_Vector': ('lit', 'Vector')})
    t.make('ShaderNodeMix', 'base', (-300, 100), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Alpha line'), 'A_Vector': ('lit', 'Vector'), 'B_Vector': ('shown', 'Result_Vector')})
    w = m('w', 'MULTIPLY', m('w.1', 'MULTIPLY', ('in', 'Line width S'), ('in', 'Line width'), location=(-800, -800)),
          ('in', 'Line width SS'), location=(-650, -800))
    t.make('ShaderNodeSeparateColor', 'detail', (-800, -1000), ins={'Color': ('in', 'Detail')})
    amount = m('amount', 'MULTIPLY_ADD', ('detail', 'Red'), m('amount.w', 'MULTIPLY_ADD', w, 3.9, 0.1, location=(-500, -900)),
               m('amount.c', 'MULTIPLY_ADD', w, 0.35, -0.35, location=(-500, -1000)), location=(-350, -900))
    amount = m('amount.on', 'MINIMUM', m('amount.clamp', 'MINIMUM', m('amount.low', 'MAXIMUM', amount, 0.0, location=(-200, -900)), 0.9,
               location=(-50, -900)), ('in', 'Line texture on'), location=(100, -900))
    t.make('ShaderNodeMix', 'lined', (300, 0), {'data_type': 'VECTOR'},
           {'Factor_Float': amount, 'A_Vector': ('base', 'Result_Vector'), 'B_Vector': ('line', 'Vector')})
    t.make('ShaderNodeVectorMath', 'result', (500, 0), {'operation': 'MINIMUM'},
           {'Vector': ('lined', 'Result_Vector'), 'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeVectorMath', 'result.low', (650, 0), {'operation': 'MAXIMUM'}, {'Vector': ('result', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    t.link('result.low', 'Vector', 'out', 'Color')
    t.link(*m('alpha', 'MULTIPLY', ('in', 'Color alpha'), ('in', 'Alpha'), location=(500, -400)), 'out', 'Alpha')
    return t
