"""`.KK main_hair`: KK's main_hair and main_hair_front as the exporter bakes them, lit from the front
(Light) and from behind (Dark), in linear colour (models.main_hair):

    col   = mix(mix(mix(1, Color, mask.r), Color 2, mask.g), Color 3, mask.b)
    base  = mix(1, Main, Use main texture) * col
    T     = `.KK shadow tint` of Shadow color, Ambient, Ambient strength
    keep  = 1 - Detail mask.g;  f = max(Light * 0.6 + 0.4, Ambient strength)
    Light = min(base * mix(T, 1, keep) + Gloss.r, 1) * f
    Dark  = min(base * T + Gloss.r / 2, 1) * mix(T, 1, max(keep, 1 - Shadow extend)) * f

The bake's flat mesh faces the camera, so the rim light, the back-face darkening and the normal map
are gone; the gloss's second read (0.008 higher, a faint edge darkening) changes no bake measurably
and is left out. Colours are linear; textures are their stored values. Written by hand."""

NAME = '.KK main_hair'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Main alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Use main texture', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Color mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Detail mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Gloss', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Color 2', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Color 3', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Shadow extend', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1300, 0))

    # The colour mask's three colours over white, and the main texture (white when there is none).
    t.make('ShaderNodeSeparateColor', 'mask', (-1100, 500), ins={'Color': ('in', 'Color mask')})
    previous = WHITE
    for i, (channel, color) in enumerate((('Red', 'Color'), ('Green', 'Color 2'), ('Blue', 'Color 3'))):
        t.make('ShaderNodeMix', f'col.{i}', (-900 + i * 200, 500), {'data_type': 'RGBA'},
               {'Factor_Float': ('mask', channel), 'A_Color': previous, 'B_Color': ('in', color)})
        previous = (f'col.{i}', 'Result_Color')
    t.make('ShaderNodeMix', 'main', (-900, 250), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Use main texture'), 'A_Color': WHITE, 'B_Color': ('in', 'Main')})
    t.make('ShaderNodeVectorMath', 'base', (-300, 350), {'operation': 'MULTIPLY'},
           {'Vector': ('main', 'Result_Color'), 'Vector_001': previous})
    t.make('ShaderNodeMix', 'alpha', (-900, 0), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Use main texture'), 'A_Float': 1.0, 'B_Float': ('in', 'Main alpha')})
    t.link('alpha', 'Result_Float', 'out', 'Alpha')

    t.make('ShaderNodeGroup', 'tint', (-900, -300), {'node_tree': lib.group('.KK shadow tint'), 'width': 200.0},
           {'Shadow color': ('in', 'Shadow color'), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength')})
    t.make('ShaderNodeSeparateColor', 'detail', (-1100, -600), ins={'Color': ('in', 'Detail mask')})
    keep = t.math('keep', 'SUBTRACT', 1.0, ('detail', 'Green'), location=(-900, -600))
    t.make('ShaderNodeSeparateColor', 'gloss', (-1100, -800), ins={'Color': ('in', 'Gloss')})
    factor = t.math('light', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(-300, 700)),
                    ('in', 'Ambient strength'), location=(-100, 700))

    # Lit from the front: the detail mask's green keeps the shadow tint.
    t.make('ShaderNodeMix', 'lit.shade', (-300, 100), {'data_type': 'RGBA'},
           {'Factor_Float': keep, 'A_Color': ('tint', 'Tint'), 'B_Color': WHITE})
    t.make('ShaderNodeVectorMath', 'lit.base', (0, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('base', 'Vector'), 'Vector_001': ('lit.shade', 'Result_Color')})
    t.make('ShaderNodeVectorMath', 'lit.gloss', (200, 300), {'operation': 'ADD'},
           {'Vector': ('lit.base', 'Vector'), 'Vector_001': ('gloss', 'Red')})
    t.make('ShaderNodeVectorMath', 'lit.clamp', (400, 300), {'operation': 'MINIMUM'},
           {'Vector': ('lit.gloss', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'lit', (700, 300), {'operation': 'SCALE'}, {'Vector': ('lit.clamp', 'Vector'), 'Scale': factor})

    # Lit from behind: the tint everywhere, half the gloss, then the shadow extend's second tint.
    half = t.math('dark.half', 'MULTIPLY', ('gloss', 'Red'), 0.5, location=(-100, -500))
    t.make('ShaderNodeVectorMath', 'dark.base', (0, -200), {'operation': 'MULTIPLY'},
           {'Vector': ('base', 'Vector'), 'Vector_001': ('tint', 'Tint')})
    t.make('ShaderNodeVectorMath', 'dark.gloss', (200, -200), {'operation': 'ADD'},
           {'Vector': ('dark.base', 'Vector'), 'Vector_001': half})
    t.make('ShaderNodeVectorMath', 'dark.clamp', (400, -200), {'operation': 'MINIMUM'},
           {'Vector': ('dark.gloss', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    extend = t.math('dark.extend', 'MAXIMUM', keep,
                    t.math('dark.unextended', 'SUBTRACT', 1.0, ('in', 'Shadow extend'), location=(-300, -700)),
                    location=(-100, -700))
    t.make('ShaderNodeMix', 'dark.shade', (200, -500), {'data_type': 'RGBA'},
           {'Factor_Float': extend, 'A_Color': ('tint', 'Tint'), 'B_Color': WHITE})
    t.make('ShaderNodeVectorMath', 'dark.shaded', (600, -200), {'operation': 'MULTIPLY'},
           {'Vector': ('dark.clamp', 'Vector'), 'Vector_001': ('dark.shade', 'Result_Color')})
    t.make('ShaderNodeVectorMath', 'dark', (900, -200), {'operation': 'SCALE'}, {'Vector': ('dark.shaded', 'Vector'), 'Scale': factor})
    t.link('lit', 'Vector', 'out', 'Light')
    t.link('dark', 'Vector', 'out', 'Dark')
    return t
