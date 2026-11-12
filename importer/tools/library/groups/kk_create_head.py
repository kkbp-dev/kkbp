"""`.KK create_head`: KK's create_head, the composited face texture (models.create_head):

    base  = max(mask.b, mix(1, Color, mask.r) * mix(1, Color 2, mask.g)) * Main
    base  = decals Texture 4 (Color 4), Texture 5 (Color 5), Paint 1 (Color 3) and Paint 2 (Color 7)
            by the paint mask's red, then the Mole (Color 6)

Linear colours; textures are their stored values. Written by hand."""

import decals

NAME = '.KK create_head'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Color mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for name in ('Texture 4', 'Texture 5', 'Paint 1', 'Paint 2', 'Mole'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Paint mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for k in range(1, 8):
        name = 'Color' if k == 1 else f'Color {k}'
        t.socket('INPUT', name, 'NodeSocketColor', default_value=WHITE)
        if k >= 3:
            t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (2200, 0))

    t.make('ShaderNodeSeparateColor', 'mask', (-1100, 500), ins={'Color': ('in', 'Color mask')})
    t.make('ShaderNodeSeparateColor', 'paintmask', (-1100, -500), ins={'Color': ('in', 'Paint mask')})
    t.make('ShaderNodeMix', 'skin', (-900, 400), {'data_type': 'RGBA'},
           {'Factor_Float': ('mask', 'Red'), 'A_Color': WHITE, 'B_Color': ('in', 'Color')})
    t.make('ShaderNodeMix', 'detail', (-900, 150), {'data_type': 'RGBA'},
           {'Factor_Float': ('mask', 'Green'), 'A_Color': WHITE, 'B_Color': ('in', 'Color 2')})
    t.make('ShaderNodeVectorMath', 'colors', (-700, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('skin', 'Result_Color'), 'Vector_001': ('detail', 'Result_Color')})
    t.make('ShaderNodeVectorMath', 'kept', (-500, 300), {'operation': 'MAXIMUM'},
           {'Vector': ('colors', 'Vector'), 'Vector_001': ('mask', 'Blue')})
    t.make('ShaderNodeVectorMath', 'base', (-300, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('kept', 'Vector'), 'Vector_001': ('in', 'Main')})
    base = ('base', 'Vector')
    for i, (name, tex, color, mask) in enumerate((('tex4', 'Texture 4', 'Color 4', None), ('tex5', 'Texture 5', 'Color 5', None),
                                                  ('paint1', 'Paint 1', 'Color 3', ('paintmask', 'Red')),
                                                  ('paint2', 'Paint 2', 'Color 7', ('paintmask', 'Red')),
                                                  ('mole', 'Mole', 'Color 6', None))):
        base = decals.decal(t, name, base, ('in', tex), ('in', f'{tex} alpha'), ('in', color), ('in', f'{color} alpha'),
                            mask, location=(-50 + i * 450, 300))
    t.link(base[0], base[1], 'out', 'Color')
    return t
