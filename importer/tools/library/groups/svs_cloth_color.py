"""`.SVS cloth color`: SVS's clothes shader's colour (models.cloth_color): the composited
texture (Create), times the colour mask's colours (Main color 1 to 3 over 4) when Switch is on, toward
Curvature color by Detail 2's red times its alpha. Linear colours. Written by hand."""

NAME = '.SVS cloth color'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Create', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Detail 2', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for k in (1, 2, 3, 4):
        t.socket('INPUT', f'Main color {k}', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Switch', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Curvature color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Curvature color alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1000, 0))
    t.make('NodeGroupOutput', 'out', (900, 0))
    t.make('ShaderNodeSeparateColor', 'mask', (-800, 300), ins={'Color': ('in', 'Mask')})
    colors = ('in', 'Main color 4')
    for k, ch in ((1, 'Red'), (2, 'Green'), (3, 'Blue')):
        t.make('ShaderNodeMix', f'm{k}', (-600 + k * 150, 300), {'data_type': 'VECTOR'},
               {'Factor_Float': ('mask', ch), 'A_Vector': colors, 'B_Vector': ('in', f'Main color {k}')})
        colors = (f'm{k}', 'Result_Vector')
    t.make('ShaderNodeVectorMath', 'tinted', (100, 300), {'operation': 'MULTIPLY'}, {'Vector': ('in', 'Create'), 'Vector_001': colors})
    t.make('ShaderNodeMix', 'switch', (250, 100), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Switch'), 'A_Vector': ('in', 'Create'), 'B_Vector': ('tinted', 'Vector')})
    t.make('ShaderNodeSeparateColor', 'detail2', (-800, -300), ins={'Color': ('in', 'Detail 2')})
    t.make('ShaderNodeMix', 'curvature', (500, 0), {'data_type': 'VECTOR'},
           {'Factor_Float': t.math('curvature.f', 'MULTIPLY', ('detail2', 'Red'), ('in', 'Curvature color alpha'), location=(250, -200)),
            'A_Vector': ('switch', 'Result_Vector'), 'B_Vector': ('in', 'Curvature color')})
    t.link('curvature', 'Result_Vector', 'out', 'Color')
    return t
