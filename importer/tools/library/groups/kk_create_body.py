"""`.KK create_body`: KK's create_body, the composited body texture (models.create_body):

    t     = max(mix(1, Tan.r, Tan present), 1 - Color 4 alpha)
    base  = mix(Color 4, Color, t) * Main * mix(1, Color 2, mask.g * Color 2 alpha)
    base  = decals Paint 1 (Color 3) and Paint 2 (Color 6), each by the paint mask's red
    Color = mix(base, Color 5 * base, mask.b)                       the nails

Linear colours; textures are their stored values.
With Shown colors on, its drawn colours are Shown Colours (shown_colors.py, ADR 0056). Written by hand."""

import decals
import shown_colors

NAME = '.KK create_body'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Color mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Tan', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Tan present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2):
        t.socket('INPUT', f'Paint {k}', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'Paint {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Paint mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for k in range(1, 7):
        name = 'Color' if k == 1 else f'Color {k}'
        t.socket('INPUT', name, 'NodeSocketColor', default_value=WHITE)
        if k in (2, 3, 4, 6):
            t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))

    t.make('ShaderNodeSeparateColor', 'mask', (-1100, 500), ins={'Color': ('in', 'Color mask')})
    t.make('ShaderNodeSeparateColor', 'tan', (-1100, 250), ins={'Color': ('in', 'Tan')})
    t.make('ShaderNodeSeparateColor', 'paintmask', (-1100, -500), ins={'Color': ('in', 'Paint mask')})
    t.make('ShaderNodeMix', 'tan.present', (-900, 250), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Tan present'), 'A_Float': 1.0, 'B_Float': ('tan', 'Red')})
    tan = t.math('tan.amount', 'MAXIMUM', ('tan.present', 'Result_Float'),
                 t.math('tan.free', 'SUBTRACT', 1.0, ('in', 'Color 4 alpha'), location=(-900, 100)), location=(-700, 200))
    t.make('ShaderNodeMix', 'skin', (-500, 300), {'data_type': 'RGBA'},
           {'Factor_Float': tan, 'A_Color': ('in', 'Color 4'), 'B_Color': ('in', 'Color')})
    t.make('ShaderNodeMix', 'detail', (-500, 0), {'data_type': 'RGBA'},
           {'Factor_Float': t.math('detail.amount', 'MULTIPLY', ('mask', 'Green'), ('in', 'Color 2 alpha'), location=(-700, -50)),
            'A_Color': WHITE, 'B_Color': ('in', 'Color 2')})
    t.make('ShaderNodeVectorMath', 'skin.main', (-300, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('skin', 'Result_Color'), 'Vector_001': ('in', 'Main')})
    t.make('ShaderNodeVectorMath', 'base', (-100, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('skin.main', 'Vector'), 'Vector_001': ('detail', 'Result_Color')})
    base = decals.decal(t, 'paint1', ('base', 'Vector'), ('in', 'Paint 1'), ('in', 'Paint 1 alpha'), ('in', 'Color 3'),
                        ('in', 'Color 3 alpha'), ('paintmask', 'Red'), location=(150, 300))
    base = decals.decal(t, 'paint2', base, ('in', 'Paint 2'), ('in', 'Paint 2 alpha'), ('in', 'Color 6'),
                        ('in', 'Color 6 alpha'), ('paintmask', 'Red'), location=(650, 300))
    t.make('ShaderNodeVectorMath', 'nails.color', (950, 0), {'operation': 'MULTIPLY'},
           {'Vector': base, 'Vector_001': ('in', 'Color 5')})
    t.make('ShaderNodeMix', 'nails', (1150, 200), {'data_type': 'RGBA'},
           {'Factor_Float': ('mask', 'Blue'), 'A_Color': base, 'B_Color': ('nails.color', 'Vector')})
    t.link('nails', 'Result_Color', 'out', 'Color')
    shown_colors.route(t, lib, 'Color', *(f'Color {k}' for k in range(2, 7)))
    return t
