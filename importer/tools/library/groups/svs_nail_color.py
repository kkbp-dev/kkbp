"""`.SVS nail color`: SVS's nail colour (models.nail_color, issue 62).

    col   = mix(mix(mix(white, Nail color 1, Mask.r), Nail color 2, Mask.g), Nail color 3, Mask.b)
    col   = col + Main * Nail color 1 alpha
    Color = each paint k over col, toward Paint k * Paint color k, by its alpha * its colour's alpha

Each paint's alpha is times its `present` switch (a missing texture reads black and transparent, as the
game's default). Linear colours. Written by hand."""

NAME = '.SVS nail color'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketVector')
    t.socket('INPUT', 'Mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for k in (1, 2, 3):
        t.socket('INPUT', f'Nail color {k}', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Nail color 1 alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2, 3):
        t.socket('INPUT', f'Paint {k}', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'Paint {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'Paint {k} present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'Paint color {k}', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'Paint color {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1000, 0))
    m = t.math
    t.make('ShaderNodeSeparateColor', 'mask', (-1200, 400), ins={'Color': ('in', 'Mask')})
    col = (1.0, 1.0, 1.0)
    for k, ch in ((1, 'Red'), (2, 'Green'), (3, 'Blue')):
        t.make('ShaderNodeMix', f'c{k}', (-1000 + k * 180, 400), {'data_type': 'VECTOR'},
               {'Factor_Float': ('mask', ch), 'A_Vector': col, 'B_Vector': ('in', f'Nail color {k}')})
        col = (f'c{k}', 'Result_Vector')
    t.make('ShaderNodeCombineXYZ', 'nail1.a', (-500, 200),
           ins={'X': ('in', 'Nail color 1 alpha'), 'Y': ('in', 'Nail color 1 alpha'), 'Z': ('in', 'Nail color 1 alpha')})
    t.make('ShaderNodeVectorMath', 'main', (-300, 300), {'operation': 'MULTIPLY_ADD'},
           {'Vector': ('in', 'Main'), 'Vector_001': ('nail1.a', 'Vector'), 'Vector_002': col})
    col = ('main', 'Vector')
    for k in (1, 2, 3):
        y = 200 - k * 250
        t.make('ShaderNodeVectorMath', f'p{k}.col', (-100 + k * 250, y), {'operation': 'MULTIPLY'},
               {'Vector': ('in', f'Paint {k}'), 'Vector_001': ('in', f'Paint color {k}')})
        amount = m(f'p{k}.amount', 'MULTIPLY', m(f'p{k}.a', 'MULTIPLY', ('in', f'Paint {k} alpha'), ('in', f'Paint {k} present'),
                   location=(-250 + k * 250, y - 150)), ('in', f'Paint color {k} alpha'), location=(-100 + k * 250, y - 150))
        t.make('ShaderNodeMix', f'paint{k}', (50 + k * 250, y), {'data_type': 'VECTOR'},
               {'Factor_Float': amount, 'A_Vector': col, 'B_Vector': (f'p{k}.col', 'Vector')})
        col = (f'paint{k}', 'Result_Vector')
    t.link(col[0], col[1], 'out', 'Color')
    return t
