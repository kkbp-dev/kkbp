"""`.KK main_alpha`: KK's main_alpha (see-through clothes, accessories) as the exporter bakes it, lit from
the front (Light) and from behind (Dark), in linear colour (models.main_alpha). Main is create_topN's
output (or the accessory's own texture).

    tint  = `.KK item tint` of Main and Shadow color;  keep = 1 - Detail mask.g;  lit = ramp * keep
    M     = min(Main + Detail mask.r^2 * Specular color * (0.5 + 0.5 * lit), 1)
    X     = M * mix(tint, 1, lit) * mix(tint, 1, max(1 - Shadow extend, ramp, keep)) * f
    line  = Line color alpha > 0.5 ? 1 - (2 - 2a)(1 - Main * tint) : 2a * Main * tint, clamped
    X     = mix(line, X, ((1 - Line width) * 0.89 + 0.01) ^ ((1 - Detail mask.b) * Detail B line GA))

ramp is 1 for Light and 0 for Dark. The bake's quad faces the camera with the normal map, rim, liquid
and the `_SpecularPower` highlight off; `_LineColorG`'s colour is taken as white. Written by hand."""

NAME = '.KK main_alpha'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Detail mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Specular color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Shadow extend', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Detail B line GA', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line color alpha', 'NodeSocketFloat', default_value=0.065, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line width', 'NodeSocketFloat', default_value=0.32, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-1500, 0))
    t.make('NodeGroupOutput', 'out', (1700, 0))

    t.make('ShaderNodeGroup', 'tint', (-1100, 300), {'node_tree': lib.group('.KK item tint'), 'width': 200.0},
           {'Color': ('in', 'Main'), 'Shadow color': ('in', 'Shadow color'), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength')})
    t.make('ShaderNodeSeparateColor', 'detail', (-1200, -400), ins={'Color': ('in', 'Detail mask')})
    keep = t.math('keep', 'SUBTRACT', 1.0, ('detail', 'Green'), location=(-1000, -400))
    spec = t.math('spec', 'POWER', ('detail', 'Red'), 2.0, location=(-1000, -250))
    unextended = t.math('unextended', 'SUBTRACT', 1.0, ('in', 'Shadow extend'), location=(-1000, -600))
    factor = t.math('light.factor', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(-300, 800)),
                    ('in', 'Ambient strength'), location=(-100, 800))

    # The line colour: twice the line alpha's overlay with the shaded texture.
    t.make('ShaderNodeVectorMath', 'main.tint', (-700, -800), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Main'), 'Vector_001': ('tint', 'Tint')})
    a = ('in', 'Line color alpha')
    t.make('ShaderNodeVectorMath', 'line.rest', (-500, -800), {'operation': 'SUBTRACT'},
           {'Vector': (1.0, 1.0, 1.0), 'Vector_001': ('main.tint', 'Vector')})
    t.make('ShaderNodeVectorMath', 'line.over', (-300, -800), {'operation': 'SCALE'},
           {'Vector': ('line.rest', 'Vector'), 'Scale': t.math('line.span', 'MULTIPLY_ADD', a, -2.0, 2.0, location=(-500, -1000))})
    t.make('ShaderNodeVectorMath', 'line.high', (-100, -800), {'operation': 'SUBTRACT'},
           {'Vector': (1.0, 1.0, 1.0), 'Vector_001': ('line.over', 'Vector')})
    t.make('ShaderNodeVectorMath', 'line.low', (-100, -1000), {'operation': 'SCALE'},
           {'Vector': ('main.tint', 'Vector'), 'Scale': t.math('line.twice', 'MULTIPLY', a, 2.0, location=(-300, -1100))})
    t.make('ShaderNodeMix', 'line.color', (100, -900), {'data_type': 'RGBA', 'clamp_result': True},
           {'Factor_Float': t.math('line.pick', 'GREATER_THAN', a, 0.5, location=(-100, -1200)),
            'A_Color': ('line.low', 'Vector'), 'B_Color': ('line.high', 'Vector')})
    width = t.math('width', 'MULTIPLY_ADD', t.math('width.inv', 'SUBTRACT', 1.0, ('in', 'Line width'), location=(100, -1200)),
                   0.89, 0.01, location=(300, -1200))
    shows = t.math('shows', 'POWER', width, t.math(
        'shows.lines', 'MULTIPLY', t.math('lines', 'SUBTRACT', 1.0, ('detail', 'Blue'), location=(300, -1350)),
        ('in', 'Detail B line GA'), location=(500, -1350)), location=(700, -1250))

    for name, ramp, y in (('Light', 1.0, 500), ('Dark', 0.0, 0)):
        key = name.lower()
        lit = keep if ramp else 0.0
        held = t.math(f'{key}.held', 'MAXIMUM', unextended, keep, location=(-700, y - 250)) if not ramp else 1.0
        t.make('ShaderNodeVectorMath', f'{key}.spec', (-700, y), {'operation': 'SCALE'},
               {'Vector': ('in', 'Specular color'),
                'Scale': t.math(f'{key}.spec.amount', 'MULTIPLY', spec,
                                t.math(f'{key}.spec.half', 'MULTIPLY_ADD', lit, 0.5, 0.5, location=(-900, y - 100)),
                                location=(-800, y - 100))})
        t.make('ShaderNodeVectorMath', f'{key}.m', (-500, y), {'operation': 'ADD'},
               {'Vector': ('in', 'Main'), 'Vector_001': (f'{key}.spec', 'Vector')})
        t.make('ShaderNodeVectorMath', f'{key}.m.clamp', (-300, y), {'operation': 'MINIMUM'},
               {'Vector': (f'{key}.m', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
        t.make('ShaderNodeMix', f'{key}.shade', (-300, y - 200), {'data_type': 'RGBA'},
               {'Factor_Float': lit, 'A_Color': ('tint', 'Tint'), 'B_Color': WHITE})
        t.make('ShaderNodeMix', f'{key}.extend', (-100, y - 200), {'data_type': 'RGBA'},
               {'Factor_Float': held, 'A_Color': ('tint', 'Tint'), 'B_Color': WHITE})
        t.make('ShaderNodeVectorMath', f'{key}.col', (100, y), {'operation': 'MULTIPLY'},
               {'Vector': (f'{key}.m.clamp', 'Vector'), 'Vector_001': (f'{key}.shade', 'Result_Color')})
        t.make('ShaderNodeVectorMath', f'{key}.extended', (300, y), {'operation': 'MULTIPLY'},
               {'Vector': (f'{key}.col', 'Vector'), 'Vector_001': (f'{key}.extend', 'Result_Color')})
        t.make('ShaderNodeVectorMath', f'{key}.lit', (500, y), {'operation': 'SCALE'},
               {'Vector': (f'{key}.extended', 'Vector'), 'Scale': factor})
        t.make('ShaderNodeMix', key, (1300, y), {'data_type': 'RGBA', 'clamp_factor': False},
               {'Factor_Float': shows, 'A_Color': ('line.color', 'Result_Color'), 'B_Color': (f'{key}.lit', 'Vector')})
        t.link(key, 'Result_Color', 'out', name)
    return t
