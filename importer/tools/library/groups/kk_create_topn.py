"""`.KK create_topN`: KK's create_topN (clothes), the composited main texture (models.create_topN):

    pK    = max(mix(1, Pattern K.r, Pattern K present), 1 - Pattern color K alpha)    K = 1, 2, 3
    cK    = mix(Pattern color K, Color K, pK)
    col   = mix(mix(mix(1, c1, mask.r), c2, mask.g), c3, mask.b)
    Color = col * min(Main, 1);  Alpha = Main alpha

The pattern masks are read at `.KK pattern uv`. Linear colours; textures are their stored values.
With Shown colors on, its drawn colours are Shown Colours (shown_colors.py, ADR 0056). Written by hand."""

import shown_colors

NAME = '.KK create_topN'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Main alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Color mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for k in (1, 2, 3):
        t.socket('INPUT', f'Pattern {k}', 'NodeSocketColor', default_value=WHITE)
        t.socket('INPUT', f'Pattern {k} present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2, 3):
        t.socket('INPUT', 'Color' if k == 1 else f'Color {k}', 'NodeSocketColor', default_value=WHITE)
        t.socket('INPUT', f'Pattern color {k}', 'NodeSocketColor', default_value=WHITE)
        t.socket('INPUT', f'Pattern color {k} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (800, 0))

    t.make('ShaderNodeSeparateColor', 'mask', (-900, 700), ins={'Color': ('in', 'Color mask')})
    previous = WHITE
    for k, channel in zip((1, 2, 3), ('Red', 'Green', 'Blue')):
        y = 400 - (k - 1) * 350
        color = 'Color' if k == 1 else f'Color {k}'
        t.make('ShaderNodeSeparateColor', f'pattern{k}', (-900, y), ins={'Color': ('in', f'Pattern {k}')})
        t.make('ShaderNodeMix', f'pattern{k}.present', (-700, y), {'data_type': 'FLOAT'},
               {'Factor_Float': ('in', f'Pattern {k} present'), 'A_Float': 1.0, 'B_Float': (f'pattern{k}', 'Red')})
        p = t.math(f'p{k}', 'MAXIMUM', (f'pattern{k}.present', 'Result_Float'),
                   t.math(f'p{k}.free', 'SUBTRACT', 1.0, ('in', f'Pattern color {k} alpha'), location=(-700, y - 150)),
                   location=(-500, y))
        t.make('ShaderNodeMix', f'c{k}', (-300, y), {'data_type': 'RGBA'},
               {'Factor_Float': p, 'A_Color': ('in', f'Pattern color {k}'), 'B_Color': ('in', color)})
        t.make('ShaderNodeMix', f'col.{k}', (-100 + k * 150, 600), {'data_type': 'RGBA'},
               {'Factor_Float': ('mask', channel), 'A_Color': previous, 'B_Color': (f'c{k}', 'Result_Color')})
        previous = (f'col.{k}', 'Result_Color')
    t.make('ShaderNodeVectorMath', 'main', (300, 200), {'operation': 'MINIMUM'},
           {'Vector': ('in', 'Main'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'color', (550, 300), {'operation': 'MULTIPLY'},
           {'Vector': previous, 'Vector_001': ('main', 'Vector')})
    t.link('color', 'Vector', 'out', 'Color')
    t.link('in', 'Main alpha', 'out', 'Alpha')
    shown_colors.route(t, lib, 'Color', 'Color 2', 'Color 3', 'Pattern color 1', 'Pattern color 2', 'Pattern color 3')
    return t
