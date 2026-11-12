"""`.KK grade`: the maker camera's AmplifyColor colour grade, `Lut_TimeDay.png`, on an sRGB-encoded
colour (issue 30). Both games' light and dark bakes went through it, so every edit template grades
its light and dark colours last (models.grade).

The LUT is a 1024 x 32 strip of 32 slices, one per blue step, each red (x) by green (y). The colour
is read from the two slices around its blue, each bilinearly, and blended by blue, as the GPU does.
The bilinear filter is done here from four Closest reads per slice: Eevee filters a Linear image
through mipmaps picked by how fast the coordinate changes between pixels, and a LUT's coordinate is
the colour, so along a texture's sharp edges it would read a blurred LUT. The image is Non-Color:
its values are used as they are stored. Written by hand."""

NAME = '.KK grade'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.make('NodeGroupInput', 'in', (-1500, 0))
    t.make('NodeGroupOutput', 'out', (1500, 0))
    t.make('ShaderNodeSeparateColor', 'split', (-1300, 0), ins={'Color': ('in', 'Color')})
    r = t.math('red', 'ADD', ('split', 'Red'), 0.0, location=(-1100, 400), clamp=True)
    g = t.math('green', 'ADD', ('split', 'Green'), 0.0, location=(-1100, 0), clamp=True)
    b = t.math('blue', 'ADD', ('split', 'Blue'), 0.0, location=(-1100, -400), clamp=True)

    # Texel positions: red and green 0..31 within a slice, blue picks the two slices.
    x = t.math('red.x', 'MULTIPLY', r, 31.0, location=(-900, 400))
    x0 = t.math('red.x0', 'FLOOR', x, location=(-700, 450))
    fx = t.math('red.fx', 'SUBTRACT', x, x0, location=(-700, 350))
    y = t.math('green.y', 'MULTIPLY', g, 31.0, location=(-900, 0))
    y0 = t.math('green.y0', 'FLOOR', y, location=(-700, 50))
    fy = t.math('green.fy', 'SUBTRACT', y, y0, location=(-700, -50))
    v0 = t.math('v0', 'MULTIPLY_ADD', y0, 1 / 32, 0.5 / 32, location=(-500, 50))
    v1 = t.math('v1', 'MULTIPLY_ADD', y0, 1 / 32, 1.5 / 32, location=(-500, -50))
    blue = t.math('blue.steps', 'MULTIPLY', b, 31.0, location=(-900, -400))
    low = t.math('slice.low', 'FLOOR', blue, location=(-700, -350))
    high = t.math('slice.high', 'MINIMUM', t.math('slice.next', 'ADD', low, 1.0, location=(-500, -450)), 31.0,
                  location=(-300, -450))
    frac = t.math('slice.blend', 'SUBTRACT', blue, low, location=(-500, -550))

    for s, (name, slice_) in enumerate((('a', low), ('b', high))):
        base_y = 600 - s * 900
        # The slice's first column plus red's, as a texel index.
        column = t.math(f'{name}.x0', 'MULTIPLY_ADD', slice_, 32.0, x0, location=(-300, base_y))
        u0 = t.math(f'{name}.u0', 'MULTIPLY_ADD', column, 1 / 1024, 0.5 / 1024, location=(-100, base_y))
        u1 = t.math(f'{name}.u1', 'MULTIPLY_ADD', column, 1 / 1024, 1.5 / 1024, location=(-100, base_y - 100))
        for i, (corner, u, v) in enumerate((('00', u0, v0), ('10', u1, v0), ('01', u0, v1), ('11', u1, v1))):
            cy = base_y - i * 200
            t.make('ShaderNodeCombineXYZ', f'{name}.uv{corner}', (100, cy), ins={'X': u, 'Y': v})
            t.make('ShaderNodeTexImage', f'{name}.lut{corner}', (300, cy),
                   {'image': lib.image('Lut_TimeDay.png'), 'interpolation': 'Closest', 'extension': 'EXTEND'},
                   {'Vector': (f'{name}.uv{corner}', 'Vector')})
        t.make('ShaderNodeMix', f'{name}.row0', (600, base_y), {'data_type': 'RGBA'},
               {'Factor_Float': fx, 'A_Color': (f'{name}.lut00', 'Color'), 'B_Color': (f'{name}.lut10', 'Color')})
        t.make('ShaderNodeMix', f'{name}.row1', (600, base_y - 400), {'data_type': 'RGBA'},
               {'Factor_Float': fx, 'A_Color': (f'{name}.lut01', 'Color'), 'B_Color': (f'{name}.lut11', 'Color')})
        t.make('ShaderNodeMix', f'{name}.texel', (850, base_y - 200), {'data_type': 'RGBA'},
               {'Factor_Float': fy, 'A_Color': (f'{name}.row0', 'Result_Color'), 'B_Color': (f'{name}.row1', 'Result_Color')})
    t.make('ShaderNodeMix', 'blend', (1200, 0), {'data_type': 'RGBA'},
           {'Factor_Float': frac, 'A_Color': ('a.texel', 'Result_Color'), 'B_Color': ('b.texel', 'Result_Color')})
    t.link('blend', 'Result_Color', 'out', 'Color')
    return t
