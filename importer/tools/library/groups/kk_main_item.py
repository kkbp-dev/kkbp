"""`.KK main_item`: KK's main_item (the teeth, the tongue, items) as the exporter bakes it, lit from
the front (Light) and from behind (Dark), in linear colour (models.main_item):

    base  = mix(1, Main, Use main texture) * colour mask colours over white * (1 - Line mask.b)
    lineR = mix(Line mask.r, Detail mask.r, Detail R line R);  full = mix(lineR, 1, Another ramp full)
    tint  = (saturate(2 - Shadow extend another - full) * 0.67 + 0.33) * `.KK item tint` of base
    spec  = Detail mask.r ^ 2 * (1 - Not use tex specular)
    e     = (1 - Detail mask.g) * 1.2 * Shadow extend + 1 - 1.2 * Shadow extend
    X     = (base * (lit: 1, dark: tint) + spec) * f * mix(tint, 1, e)
    line  = Line color alpha > 0.5 ? 1 - (2 - 2a)(1 - base * tint) : 2a * base * tint, clamped
    X     = mix(X, line, mix(Line mask.g, Detail mask.b, Detail B line G))
    Alpha = saturate(2 * mix(1, Main alpha, Use main texture)) * 2 - 1

The bake's quad faces the camera with the normal map, rim and the `_SpecularPower` highlight off.
`_LineColorG`'s colour is taken as white. Written by hand."""

NAME = '.KK main_item'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Main alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Use main texture', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Color mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Detail mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Line mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Color 2', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Color 3', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Shadow extend', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Shadow extend another', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Another ramp full', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Detail R line R', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Detail B line G', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Not use tex specular', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line color alpha', 'NodeSocketFloat', default_value=0.065, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-1800, 0))
    t.make('NodeGroupOutput', 'out', (1700, 0))

    # The base colour: the colour mask's colours over the main texture, less the line mask's blue.
    t.make('ShaderNodeSeparateColor', 'mask', (-1500, 600), ins={'Color': ('in', 'Color mask')})
    t.make('ShaderNodeSeparateColor', 'detail', (-1500, -500), ins={'Color': ('in', 'Detail mask')})
    t.make('ShaderNodeSeparateColor', 'line', (-1500, -750), ins={'Color': ('in', 'Line mask')})
    previous = WHITE
    for i, (channel, color) in enumerate((('Red', 'Color'), ('Green', 'Color 2'), ('Blue', 'Color 3'))):
        t.make('ShaderNodeMix', f'col.{i}', (-1300 + i * 200, 600), {'data_type': 'RGBA'},
               {'Factor_Float': ('mask', channel), 'A_Color': previous, 'B_Color': ('in', color)})
        previous = (f'col.{i}', 'Result_Color')
    t.make('ShaderNodeMix', 'main', (-1300, 350), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Use main texture'), 'A_Color': WHITE, 'B_Color': ('in', 'Main')})
    t.make('ShaderNodeVectorMath', 'main.col', (-700, 450), {'operation': 'MULTIPLY'},
           {'Vector': ('main', 'Result_Color'), 'Vector_001': previous})
    unlined = t.math('unlined', 'SUBTRACT', 1.0, ('line', 'Blue'), location=(-1300, -850))
    t.make('ShaderNodeVectorMath', 'base', (-500, 450), {'operation': 'SCALE'},
           {'Vector': ('main.col', 'Vector'), 'Scale': unlined})
    t.make('ShaderNodeMix', 'alpha.main', (-1300, 100), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Use main texture'), 'A_Float': 1.0, 'B_Float': ('in', 'Main alpha')})
    alpha = t.math('alpha', 'MULTIPLY_ADD', t.math('alpha.double', 'MULTIPLY', ('alpha.main', 'Result_Float'), 2.0,
                                                   location=(-1100, 100), clamp=True), 2.0, -1.0, location=(-900, 100))
    t.link(alpha[0], alpha[1], 'out', 'Alpha')

    # The tint, scaled down where the red line (or the full other ramp) says.
    line_r = ('line.r', 'Result_Float')
    t.make('ShaderNodeMix', 'line.r', (-1100, -500), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Detail R line R'), 'A_Float': ('line', 'Red'), 'B_Float': ('detail', 'Red')})
    t.make('ShaderNodeMix', 'full', (-900, -500), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Another ramp full'), 'A_Float': line_r, 'B_Float': 1.0})
    scale = t.math('tint.scale', 'MULTIPLY_ADD', t.math(
        'tint.room', 'SUBTRACT', t.math('tint.another', 'SUBTRACT', 2.0, ('in', 'Shadow extend another'), location=(-900, -300)),
        ('full', 'Result_Float'), location=(-700, -300), clamp=True), 0.67, 0.33, location=(-500, -300))
    t.make('ShaderNodeGroup', 'tint0', (-300, 100), {'node_tree': lib.group('.KK item tint'), 'width': 200.0},
           {'Color': ('base', 'Vector'), 'Shadow color': ('in', 'Shadow color'), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength')})
    t.make('ShaderNodeVectorMath', 'tint', (-50, 100), {'operation': 'SCALE'}, {'Vector': ('tint0', 'Tint'), 'Scale': scale})

    # The highlight the detail mask's red draws, and e, the shadow extend held off by its green.
    spec = t.math('spec', 'MULTIPLY', t.math('spec.red', 'POWER', ('detail', 'Red'), 2.0, location=(-900, -700)),
                  t.math('spec.on', 'SUBTRACT', 1.0, ('in', 'Not use tex specular'), location=(-900, -850)),
                  location=(-700, -750))
    extend = t.math('extend', 'MULTIPLY', ('in', 'Shadow extend'), 1.2, location=(-900, -1050))
    e = t.math('e', 'ADD', t.math('e.part', 'MULTIPLY', t.math('e.held', 'SUBTRACT', 1.0, ('detail', 'Green'), location=(-700, -950)),
                                  extend, location=(-500, -1000)),
               t.math('e.rest', 'SUBTRACT', 1.0, extend, location=(-500, -1150)), location=(-300, -1050))
    t.make('ShaderNodeMix', 'shade.e', (200, -200), {'data_type': 'RGBA', 'clamp_factor': False},
           {'Factor_Float': e, 'A_Color': ('tint', 'Vector'), 'B_Color': WHITE})
    factor = t.math('light.factor', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(200, 800)),
                    ('in', 'Ambient strength'), location=(400, 800))

    # The line colour: twice the line alpha's overlay with the shaded base.
    t.make('ShaderNodeVectorMath', 'base.tint', (200, 100), {'operation': 'MULTIPLY'},
           {'Vector': ('base', 'Vector'), 'Vector_001': ('tint', 'Vector')})
    a = ('in', 'Line color alpha')
    t.make('ShaderNodeVectorMath', 'line.rest', (400, -500), {'operation': 'SUBTRACT'},
           {'Vector': (1.0, 1.0, 1.0), 'Vector_001': ('base.tint', 'Vector')})
    t.make('ShaderNodeVectorMath', 'line.over', (600, -500), {'operation': 'SCALE'},
           {'Vector': ('line.rest', 'Vector'),
            'Scale': t.math('line.span', 'MULTIPLY_ADD', a, -2.0, 2.0, location=(400, -700))})
    t.make('ShaderNodeVectorMath', 'line.high', (800, -500), {'operation': 'SUBTRACT'},
           {'Vector': (1.0, 1.0, 1.0), 'Vector_001': ('line.over', 'Vector')})
    t.make('ShaderNodeVectorMath', 'line.low', (800, -700), {'operation': 'SCALE'},
           {'Vector': ('base.tint', 'Vector'), 'Scale': t.math('line.twice', 'MULTIPLY', a, 2.0, location=(600, -800))})
    t.make('ShaderNodeMix', 'line.color', (1000, -600), {'data_type': 'RGBA', 'clamp_result': True},
           {'Factor_Float': t.math('line.pick', 'GREATER_THAN', a, 0.5, location=(800, -900)),
            'A_Color': ('line.low', 'Vector'), 'B_Color': ('line.high', 'Vector')})
    t.make('ShaderNodeMix', 'line.g', (1000, -900), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Detail B line G'), 'A_Float': ('line', 'Green'), 'B_Float': ('detail', 'Blue')})

    for name, col, y in (('Light', ('base', 'Vector'), 500), ('Dark', ('base.tint', 'Vector'), 250)):
        key = name.lower()
        t.make('ShaderNodeVectorMath', f'{key}.spec', (500, y), {'operation': 'ADD'}, {'Vector': col, 'Vector_001': spec})
        t.make('ShaderNodeVectorMath', f'{key}.lit', (700, y), {'operation': 'SCALE'},
               {'Vector': (f'{key}.spec', 'Vector'), 'Scale': factor})
        t.make('ShaderNodeVectorMath', f'{key}.extended', (900, y), {'operation': 'MULTIPLY'},
               {'Vector': (f'{key}.lit', 'Vector'), 'Vector_001': ('shade.e', 'Result_Color')})
        t.make('ShaderNodeMix', key, (1300, y), {'data_type': 'RGBA', 'clamp_factor': False},
               {'Factor_Float': ('line.g', 'Result_Float'), 'A_Color': (f'{key}.extended', 'Vector'),
                'B_Color': ('line.color', 'Result_Color')})
        t.link(key, 'Result_Color', 'out', name)
    return t
