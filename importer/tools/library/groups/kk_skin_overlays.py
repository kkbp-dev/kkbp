"""`.KK skin overlays`: main_skin's three overlays over the skin (models.skin_overlays): the nipples
(Overlay 1 times its colour, or with Tex1 mask its red times the colour plus a third of its green times
Nip specular), the underhair (Overlay 2) and the face's eyeshadow (Overlay 3), each by its alpha times
its colour's. Linear colours; textures are their stored values.
With Shown colors on, its drawn colours are Shown Colours (shown_colors.py, ADR 0056). Written by hand."""

import decals
import shown_colors

NAME = '.KK skin overlays'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=WHITE)
    for k in (1, 2, 3):
        t.socket('INPUT', f'Overlay {k}', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'Overlay {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'Overlay color {k}', 'NodeSocketColor', default_value=WHITE)
        t.socket('INPUT', f'Overlay color {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Nip specular', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Tex1 mask', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (1600, 0))

    # The nipples' colour: the overlay times its colour, or (Tex1 mask) red * (colour + green * spec / 3).
    t.make('ShaderNodeSeparateColor', 'o1', (-900, 400), ins={'Color': ('in', 'Overlay 1')})
    t.make('ShaderNodeVectorMath', 'o1.plain', (-700, 600), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Overlay 1'), 'Vector_001': ('in', 'Overlay color 1')})
    gloss = t.math('o1.gloss', 'MULTIPLY', t.math('o1.green', 'MULTIPLY', ('o1', 'Green'), ('in', 'Nip specular'),
                                                  location=(-700, 250)), 0.33, location=(-500, 250))
    t.make('ShaderNodeVectorMath', 'o1.shine', (-300, 400), {'operation': 'ADD'},
           {'Vector': ('in', 'Overlay color 1'), 'Vector_001': gloss})
    t.make('ShaderNodeVectorMath', 'o1.masked', (-100, 400), {'operation': 'SCALE'},
           {'Vector': ('o1.shine', 'Vector'), 'Scale': ('o1', 'Red')})
    t.make('ShaderNodeMix', 'o1.color', (100, 500), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Tex1 mask'), 'A_Color': ('o1.plain', 'Vector'), 'B_Color': ('o1.masked', 'Vector')})
    amount = t.math('o1.amount', 'MULTIPLY', ('in', 'Overlay 1 alpha'), ('in', 'Overlay color 1 alpha'), location=(100, 250))
    t.make('ShaderNodeMix', 'nipples', (350, 300), {'data_type': 'RGBA'},
           {'Factor_Float': amount, 'A_Color': ('in', 'Color'), 'B_Color': ('o1.color', 'Result_Color')})
    base = decals.decal(t, 'underhair', ('nipples', 'Result_Color'), ('in', 'Overlay 2'), ('in', 'Overlay 2 alpha'),
                        ('in', 'Overlay color 2'), ('in', 'Overlay color 2 alpha'), location=(600, 300))
    base = decals.decal(t, 'eyeshadow', base, ('in', 'Overlay 3'), ('in', 'Overlay 3 alpha'),
                        ('in', 'Overlay color 3'), ('in', 'Overlay color 3 alpha'), location=(1100, 300))
    t.link(base[0], base[1], 'out', 'Color')
    shown_colors.route(t, lib, 'Overlay color 1', 'Overlay color 2', 'Overlay color 3')
    return t
