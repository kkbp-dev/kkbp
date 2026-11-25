"""`.SVS acs color`: SVS's item shader's colour (models.acs_color): each colour mask channel
picks Main color k over Main color 4, pattern k (where the mask's alpha is at least 0.5, and pattern
1 only Inside its tile) tinting it toward Sub color k times the pattern, or toward the pattern itself
by clamp(saturation * 10 - 0.05) * Sub color k alpha; then times the main texture. Each texture's
alpha is times its `present` switch (an empty image node reads black, opaque). Linear colours.
Written by hand."""

NAME = '.SVS acs color'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    for name, d in (('Mask', (0.0, 0.0, 0.0, 1.0)), ('Pattern 1', (0.0, 0.0, 0.0, 1.0)), ('Pattern 2', (0.0, 0.0, 0.0, 1.0)),
                    ('Pattern 3', (0.0, 0.0, 0.0, 1.0)), ('Main', (1.0, 1.0, 1.0, 1.0))):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=d)
        t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'{name} present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Inside 1', 'NodeSocketFloat', default_value=1.0)
    for k in (1, 2, 3, 4):
        t.socket('INPUT', f'Main color {k}', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
        t.socket('INPUT', f'Main color {k} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2, 3):
        t.socket('INPUT', f'Sub color {k}', 'NodeSocketColor', default_value=(0.5, 0.5, 0.5, 1.0))
        t.socket('INPUT', f'Sub color {k} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1800, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))
    m = t.math
    t.make('ShaderNodeSeparateColor', 'mask', (-1600, 800), ins={'Color': ('in', 'Mask')})
    # The mask's alpha with a missing mask read as transparent; a missing main texture reads white.
    on = m('on', 'GREATER_THAN', m('mask.a', 'MULTIPLY', ('in', 'Mask alpha'), ('in', 'Mask present'), location=(-1600, 600)),
           0.4999, location=(-1450, 600))
    t.make('ShaderNodeMix', 'main', (-1600, -1000), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Main present'), 'A_Color': (1.0, 1.0, 1.0, 1.0), 'B_Color': ('in', 'Main')})
    main_a = m('main.a', 'MULTIPLY_ADD', m('main.a.d', 'SUBTRACT', ('in', 'Main alpha'), 1.0, location=(-1600, -1200)),
               ('in', 'Main present'), 1.0, location=(-1450, -1200))
    rgb, a = ('in', 'Main color 4'), ('in', 'Main color 4 alpha')
    for k, ch in ((1, 'Red'), (2, 'Green'), (3, 'Blue')):
        y = 900 - k * 500
        w = m(f'p{k}.w', 'MULTIPLY', ('in', f'Pattern {k} alpha'), ('in', f'Pattern {k} present'), location=(-1300, y))
        if k == 1:
            w = m('p1.inside', 'MULTIPLY', w, ('in', 'Inside 1'), location=(-1200, y))
        amount = m(f'p{k}.amount', 'MULTIPLY', on, w, location=(-1100, y))
        t.make('ShaderNodeVectorMath', f'p{k}.sub', (-1100, y - 150), {'operation': 'MULTIPLY'},
               {'Vector': ('in', f'Sub color {k}'), 'Vector_001': ('in', f'Pattern {k}')})
        t.make('ShaderNodeMix', f'p{k}.layer', (-900, y), {'data_type': 'VECTOR'},
               {'Factor_Float': m(f'p{k}.tint', 'MULTIPLY', amount, ('in', f'Sub color {k} alpha'), location=(-1000, y + 100)),
                'A_Vector': ('in', f'Main color {k}'), 'B_Vector': (f'p{k}.sub', 'Vector')})
        t.make('ShaderNodeSeparateColor', f'p{k}.hsv', (-1100, y - 300), {'mode': 'HSV'}, {'Color': ('in', f'Pattern {k}')})
        vivid = m(f'p{k}.vivid', 'MULTIPLY', m(f'p{k}.vivid.a', 'MULTIPLY', amount, m(f'p{k}.sat', 'MULTIPLY_ADD', (f'p{k}.hsv', 'Green'),
                  10.0, -0.05, location=(-950, y - 300), clamp=True), location=(-800, y - 250)), ('in', f'Sub color {k} alpha'),
                  location=(-700, y - 250))
        t.make('ShaderNodeMix', f'p{k}.vivid.mix', (-600, y), {'data_type': 'VECTOR'},
               {'Factor_Float': vivid, 'A_Vector': (f'p{k}.layer', 'Result_Vector'), 'B_Vector': ('in', f'Pattern {k}')})
        t.make('ShaderNodeMix', f'c{k}', (-300, y), {'data_type': 'VECTOR'},
               {'Factor_Float': ('mask', ch), 'A_Vector': rgb, 'B_Vector': (f'p{k}.vivid.mix', 'Result_Vector')})
        t.make('ShaderNodeMix', f'a{k}', (-300, y - 200), {'data_type': 'FLOAT'},
               {'Factor_Float': ('mask', ch), 'A_Float': a, 'B_Float': ('in', f'Main color {k} alpha')})
        rgb, a = (f'c{k}', 'Result_Vector'), (f'a{k}', 'Result_Float')
    t.make('ShaderNodeVectorMath', 'color', (1000, 200), {'operation': 'MULTIPLY'}, {'Vector': rgb, 'Vector_001': ('main', 'Result_Color')})
    t.link('color', 'Vector', 'out', 'Color')
    t.link(*m('alpha', 'MULTIPLY', a, main_a, location=(1000, -200)), 'out', 'Alpha')
    return t
