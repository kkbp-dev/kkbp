"""`.KK main_opaque`: KK's main_opaque (clothes) as the exporter bakes it, lit from the front (Light)
and from behind (Dark), in linear colour (models.main_opaque). Main is create_topN's output.

    tint  = `.KK item tint` of Main, scaled by max(1 - lineR, 1 - Shadow extend another), at most 1
    lineR = mix(Line mask.r, Detail mask.r, Detail R line R)
    lineG = mix(Line mask.g, Detail mask.b, Detail B line G)
    e     = min(1 - Line mask.b, 1 - Detail mask.g) * 1.2 * Shadow extend + 1 - 1.2 * Shadow extend
    lit   = min(Main * mix(tint, 1, e), 1);  shaded = min(Main * tint, 1)
    line  = Line color alpha > 0.5 ? 1 - (2 - 2a)(1 - Main * tint / 2) : a * Main * tint, clamped
    X     = mix(line, X * mix(tint, 1, e), ((1 - Line width) * 0.89 + 0.01) ^ lineG) * f
    f     = max(Light * 0.6 + 0.4, Ambient strength)

The bake's quad faces the camera with the normal map, specular, rim and liquid off; the other ramp
follows the main one. Line color alpha and Line width are the maker's globals (models.LINE_*).
Written by hand."""

NAME = '.KK main_opaque'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Detail mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Line mask', 'NodeSocketColor', default_value=BLACK)
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Shadow extend', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Shadow extend another', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Detail R line R', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Detail B line G', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line color alpha', 'NodeSocketFloat', default_value=0.065, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Line width', 'NodeSocketFloat', default_value=0.32, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-1600, 0))
    t.make('NodeGroupOutput', 'out', (1600, 0))

    t.make('ShaderNodeSeparateColor', 'detail', (-1300, -400), ins={'Color': ('in', 'Detail mask')})
    t.make('ShaderNodeSeparateColor', 'line', (-1300, -650), ins={'Color': ('in', 'Line mask')})
    t.make('ShaderNodeMix', 'line.r', (-1050, -400), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Detail R line R'), 'A_Float': ('line', 'Red'), 'B_Float': ('detail', 'Red')})
    t.make('ShaderNodeMix', 'line.g', (-1050, -650), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Detail B line G'), 'A_Float': ('line', 'Green'), 'B_Float': ('detail', 'Blue')})

    # The shadow tint, kept from where the red line or the other shadow extend says.
    t.make('ShaderNodeGroup', 'tint0', (-1050, 200), {'node_tree': lib.group('.KK item tint'), 'width': 200.0},
           {'Color': ('in', 'Main'), 'Shadow color': ('in', 'Shadow color'), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength')})
    keep = t.math('tint.keep', 'MAXIMUM', t.math('tint.unlined', 'SUBTRACT', 1.0, ('line.r', 'Result_Float'), location=(-850, -150)),
                  t.math('tint.another', 'SUBTRACT', 1.0, ('in', 'Shadow extend another'), location=(-850, -300)),
                  location=(-650, -200))
    t.make('ShaderNodeVectorMath', 'tint.scaled', (-650, 200), {'operation': 'SCALE'},
           {'Vector': ('tint0', 'Tint'), 'Scale': keep})
    t.make('ShaderNodeVectorMath', 'tint', (-450, 200), {'operation': 'MINIMUM'},
           {'Vector': ('tint.scaled', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})

    # e: the shadow extend, held off by the line mask's blue and the detail mask's green.
    extend = t.math('extend', 'MULTIPLY', ('in', 'Shadow extend'), 1.2, location=(-1050, -900))
    held = t.math('extend.held', 'MINIMUM', t.math('extend.line', 'SUBTRACT', 1.0, ('line', 'Blue'), location=(-850, -800)),
                  t.math('extend.detail', 'SUBTRACT', 1.0, ('detail', 'Green'), location=(-850, -950)),
                  location=(-650, -850))
    e = t.math('e', 'ADD', t.math('e.part', 'MULTIPLY', held, extend, location=(-450, -850)),
               t.math('e.rest', 'SUBTRACT', 1.0, extend, location=(-450, -1000)), location=(-250, -900))
    t.make('ShaderNodeMix', 'shade.e', (-250, 0), {'data_type': 'RGBA', 'clamp_factor': False},
           {'Factor_Float': e, 'A_Color': ('tint', 'Vector'), 'B_Color': WHITE})

    # The colour lit from the front (the ramp 1: mix by e) and from behind (the tint alone).
    t.make('ShaderNodeVectorMath', 'main.tint', (-250, 250), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Main'), 'Vector_001': ('tint', 'Vector')})
    t.make('ShaderNodeVectorMath', 'lit.col', (0, 450), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Main'), 'Vector_001': ('shade.e', 'Result_Color')})
    t.make('ShaderNodeVectorMath', 'lit.clamp', (200, 450), {'operation': 'MINIMUM'},
           {'Vector': ('lit.col', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'dark.clamp', (200, 250), {'operation': 'MINIMUM'},
           {'Vector': ('main.tint', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})

    # The line colour: the line alpha's overlay with half the shaded colour.
    alpha = ('in', 'Line color alpha')
    t.make('ShaderNodeVectorMath', 'line.half', (0, -300), {'operation': 'SCALE'},
           {'Vector': ('main.tint', 'Vector'), 'Scale': -0.5})
    t.make('ShaderNodeVectorMath', 'line.rest', (200, -300), {'operation': 'ADD'},
           {'Vector': ('line.half', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    span = t.math('line.span', 'MULTIPLY_ADD', alpha, -2.0, 2.0, location=(200, -500))
    t.make('ShaderNodeVectorMath', 'line.over', (400, -300), {'operation': 'SCALE'},
           {'Vector': ('line.rest', 'Vector'), 'Scale': span})
    t.make('ShaderNodeVectorMath', 'line.high', (600, -300), {'operation': 'SUBTRACT'},
           {'Vector': (1.0, 1.0, 1.0), 'Vector_001': ('line.over', 'Vector')})
    t.make('ShaderNodeVectorMath', 'line.low', (600, -500), {'operation': 'SCALE'},
           {'Vector': ('main.tint', 'Vector'), 'Scale': alpha})
    pick = t.math('line.pick', 'GREATER_THAN', alpha, 0.5, location=(600, -700))
    t.make('ShaderNodeMix', 'line.color', (800, -400), {'data_type': 'RGBA', 'clamp_result': True},
           {'Factor_Float': pick, 'A_Color': ('line.low', 'Vector'), 'B_Color': ('line.high', 'Vector')})

    # How much of the colour shows over the line: the line width to the power of lineG.
    width = t.math('width', 'MULTIPLY_ADD', t.math('width.inv', 'SUBTRACT', 1.0, ('in', 'Line width'), location=(600, -900)),
                   0.89, 0.01, location=(800, -900))
    shows = t.math('shows', 'POWER', width, ('line.g', 'Result_Float'), location=(1000, -900))
    factor = t.math('light.factor', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(1000, 700)),
                    ('in', 'Ambient strength'), location=(1200, 700))
    for name, col, y in (('Light', 'lit.clamp', 450), ('Dark', 'dark.clamp', 150)):
        key = name.lower()
        t.make('ShaderNodeVectorMath', f'{key}.extended', (500, y), {'operation': 'MULTIPLY'},
               {'Vector': (col, 'Vector'), 'Vector_001': ('shade.e', 'Result_Color')})
        t.make('ShaderNodeMix', f'{key}.lined', (1100, y), {'data_type': 'RGBA', 'clamp_factor': False},
               {'Factor_Float': shows, 'A_Color': ('line.color', 'Result_Color'), 'B_Color': (f'{key}.extended', 'Vector')})
        t.make('ShaderNodeVectorMath', key, (1350, y), {'operation': 'SCALE'},
               {'Vector': (f'{key}.lined', 'Result_Color'), 'Scale': factor})
        t.link(key, 'Vector', 'out', name)
    return t
