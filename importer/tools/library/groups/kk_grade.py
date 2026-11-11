"""`.KK grade`: the maker camera's AmplifyColor colour grade, `Lut_TimeDay.png`, on an sRGB-encoded
colour (issue 30). Both games' light and dark bakes went through it, so every edit template grades
its light and dark colours last (models.grade).

The LUT is a 1024 x 32 strip of 32 slices, one per blue step, each red (x) by green (y). The colour
is read from the two slices around its blue with linear filtering and blended by blue, as the GPU
does. The image is Non-Color: its values are used as they are stored. Written by hand."""

NAME = '.KK grade'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.make('NodeGroupInput', 'in', (-1300, 0))
    t.make('NodeGroupOutput', 'out', (900, 0))
    t.make('ShaderNodeSeparateColor', 'split', (-1100, 0), ins={'Color': ('in', 'Color')})
    r = t.math('red', 'ADD', ('split', 'Red'), 0.0, location=(-900, 250), clamp=True)
    g = t.math('green', 'ADD', ('split', 'Green'), 0.0, location=(-900, 0), clamp=True)
    b = t.math('blue', 'ADD', ('split', 'Blue'), 0.0, location=(-900, -250), clamp=True)
    blue = t.math('blue.steps', 'MULTIPLY', b, 31.0, location=(-700, -250))
    low = t.math('slice.low', 'FLOOR', blue, location=(-500, -200))
    high = t.math('slice.high', 'MINIMUM', t.math('slice.next', 'ADD', low, 1.0, location=(-300, -300)), 31.0,
                  location=(-100, -300))
    frac = t.math('slice.blend', 'SUBTRACT', blue, low, location=(-300, -450))
    red_u = t.math('red.u', 'MULTIPLY_ADD', r, 31 / 1024, 0.5 / 1024, location=(-700, 250))
    v = t.math('green.v', 'MULTIPLY_ADD', g, 31 / 32, 0.5 / 32, location=(-700, 0))
    for name, slice_, y in (('a', low, 250), ('b', high, -50)):
        u = t.math(f'u.{name}', 'MULTIPLY_ADD', slice_, 1 / 32, red_u, location=(100, y))
        t.make('ShaderNodeCombineXYZ', f'uv.{name}', (300, y), ins={'X': u, 'Y': v})
        t.make('ShaderNodeTexImage', f'lut.{name}', (500, y),
               {'image': lib.image('Lut_TimeDay.png'), 'interpolation': 'Linear', 'extension': 'EXTEND'},
               {'Vector': (f'uv.{name}', 'Vector')})
    t.make('ShaderNodeMix', 'blend', (750, 0), {'data_type': 'RGBA'},
           {'Factor_Float': frac, 'A_Color': ('lut.a', 'Color'), 'B_Color': ('lut.b', 'Color')})
    t.link('blend', 'Result_Color', 'out', 'Color')
    return t
