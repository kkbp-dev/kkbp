"""`.KK main_skin`: KK's main_skin (body, face) as the exporter bakes it, lit from the front (Light)
and from behind (Dark), in linear colour (models.main_skin). Color is the composited skin with its
overlays.

    tint  = `.KK item tint` of Color, Saturation 0.66, white shadow colour
    e     = min(1 - Line mask.b * s, 1 - Detail mask.g) * 1.2 * Shadow extend + 1 - 1.2 * Shadow extend
            s = Detail normal map scale, which weights the line mask
    X     = Color * (lit: mix(tint, 1, e), dark: tint) * f * mix(tint, 1, e)
    line  = overlay of Line color alpha with Color * tint * (1 - Detail mask.g / 2), clamped
    shows = min(1 - Line mask.r * s / 2, ((1 - Line width) * 0.8 + 0.2) ^ Line mask.g), 1 without Line tex on
    X     = mix(line, X, shows)

The bake's quad faces the camera with the normal maps, specular, rim and liquid off; `_LineColorG`'s
colour is taken as white and the face shadow as at most 1. Written by hand."""

NAME = '.KK main_skin'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Detail mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Line mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Detail normal map scale', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Shadow extend', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line tex on', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line color alpha', 'NodeSocketFloat', default_value=0.065, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line width', 'NodeSocketFloat', default_value=0.32, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-1600, 0))
    t.make('NodeGroupOutput', 'out', (1700, 0))

    t.make('ShaderNodeGroup', 'tint', (-1100, 300), {'node_tree': lib.group('.KK item tint'), 'width': 200.0},
           {'Color': ('in', 'Color'), 'Shadow color': WHITE, 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength'), 'Saturation': 0.66})
    t.make('ShaderNodeSeparateColor', 'detail', (-1300, -400), ins={'Color': ('in', 'Detail mask')})
    t.make('ShaderNodeSeparateColor', 'line', (-1300, -700), ins={'Color': ('in', 'Line mask')})
    scale = ('in', 'Detail normal map scale')
    extend = t.math('extend', 'MULTIPLY', ('in', 'Shadow extend'), 1.2, location=(-1100, -1000))
    held = t.math('held', 'MINIMUM', t.math('held.line', 'MULTIPLY_ADD', ('line', 'Blue'),
                                            t.math('neg.scale', 'MULTIPLY', scale, -1.0, location=(-1300, -900)), 1.0,
                                            location=(-1100, -750)),
                  t.math('held.detail', 'SUBTRACT', 1.0, ('detail', 'Green'), location=(-1100, -500)), location=(-900, -650))
    e = t.math('e', 'ADD', t.math('e.part', 'MULTIPLY', held, extend, location=(-700, -700)),
               t.math('e.rest', 'SUBTRACT', 1.0, extend, location=(-700, -900)), location=(-500, -800))
    t.make('ShaderNodeMix', 'shade.e', (-300, 0), {'data_type': 'RGBA', 'clamp_factor': False},
           {'Factor_Float': e, 'A_Color': ('tint', 'Tint'), 'B_Color': WHITE})
    factor = t.math('light.factor', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(-300, 700)),
                    ('in', 'Ambient strength'), location=(-100, 700))

    # The line colour: the line alpha's overlay with the shaded colour, softened by the detail's green.
    t.make('ShaderNodeVectorMath', 'col.tint', (-300, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Color'), 'Vector_001': ('tint', 'Tint')})
    t.make('ShaderNodeVectorMath', 'lined', (-100, -300), {'operation': 'SCALE'},
           {'Vector': ('col.tint', 'Vector'),
            'Scale': t.math('soft', 'MULTIPLY_ADD', ('detail', 'Green'), -0.5, 1.0, location=(-300, -400))})
    a = ('in', 'Line color alpha')
    t.make('ShaderNodeVectorMath', 'line.rest', (100, -300), {'operation': 'SUBTRACT'},
           {'Vector': (1.0, 1.0, 1.0), 'Vector_001': ('lined', 'Vector')})
    t.make('ShaderNodeVectorMath', 'line.over', (300, -300), {'operation': 'SCALE'},
           {'Vector': ('line.rest', 'Vector'), 'Scale': t.math('line.span', 'MULTIPLY_ADD', a, -2.0, 2.0, location=(100, -500))})
    t.make('ShaderNodeVectorMath', 'line.high', (500, -300), {'operation': 'SUBTRACT'},
           {'Vector': (1.0, 1.0, 1.0), 'Vector_001': ('line.over', 'Vector')})
    t.make('ShaderNodeVectorMath', 'line.low', (500, -500), {'operation': 'SCALE'},
           {'Vector': ('lined', 'Vector'), 'Scale': t.math('line.twice', 'MULTIPLY', a, 2.0, location=(300, -600))})
    t.make('ShaderNodeMix', 'line.color', (700, -400), {'data_type': 'RGBA', 'clamp_result': True},
           {'Factor_Float': t.math('line.pick', 'GREATER_THAN', a, 0.5, location=(500, -700)),
            'A_Color': ('line.low', 'Vector'), 'B_Color': ('line.high', 'Vector')})

    # How much of the colour shows over the line.
    red = t.math('shows.red', 'MULTIPLY_ADD', t.math('shows.r', 'MULTIPLY', ('line', 'Red'), scale, location=(300, -900)),
                 -0.5, 1.0, location=(500, -900))
    width = t.math('width', 'MULTIPLY_ADD', t.math('width.inv', 'SUBTRACT', 1.0, ('in', 'Line width'), location=(300, -1100)),
                   0.8, 0.2, location=(500, -1100))
    shows = t.math('shows.min', 'MINIMUM', red, t.math('shows.g', 'POWER', width, ('line', 'Green'), location=(700, -1100)),
                   location=(900, -1000))
    shows = t.math('shows', 'MULTIPLY_ADD', t.math('shows.off', 'SUBTRACT', shows, 1.0, location=(1100, -1000)),
                   ('in', 'Line tex on'), 1.0, location=(1300, -1000))

    for name, shade, y in (('Light', ('shade.e', 'Result_Color'), 400), ('Dark', ('tint', 'Tint'), 100)):
        key = name.lower()
        t.make('ShaderNodeVectorMath', f'{key}.col', (100, y), {'operation': 'MULTIPLY'},
               {'Vector': ('in', 'Color'), 'Vector_001': shade})
        t.make('ShaderNodeVectorMath', f'{key}.lit', (300, y), {'operation': 'SCALE'},
               {'Vector': (f'{key}.col', 'Vector'), 'Scale': factor})
        t.make('ShaderNodeVectorMath', f'{key}.extended', (500, y), {'operation': 'MULTIPLY'},
               {'Vector': (f'{key}.lit', 'Vector'), 'Vector_001': ('shade.e', 'Result_Color')})
        t.make('ShaderNodeMix', key, (1300, y), {'data_type': 'RGBA', 'clamp_factor': False},
               {'Factor_Float': shows, 'A_Color': ('line.color', 'Result_Color'), 'B_Color': (f'{key}.extended', 'Vector')})
        t.link(key, 'Result_Color', 'out', name)
    return t
