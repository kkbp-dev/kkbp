"""`.KK srgb`: a linear colour sRGB-encoded, clamped to 0..1 as an 8-bit render target is.

The edit templates use it twice: to give back a bundle texture's stored values (Blender decodes the
PNG as sRGB; the stored values are the linear ones the game's shader sampled, models.py), and before
the colour grade, which works on encoded colours. Written by hand."""

NAME = '.KK srgb'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (700, 0))
    t.make('ShaderNodeSeparateColor', 'split', (-700, 0), ins={'Color': ('in', 'Color')})
    t.make('ShaderNodeCombineColor', 'join', (500, 0))
    for row, channel in enumerate(('Red', 'Green', 'Blue')):
        y = 300 - row * 300
        x = t.math(f'{channel}.clamp', 'ADD', ('split', channel), 0.0, location=(-500, y), clamp=True)
        low = t.math(f'{channel}.low', 'MULTIPLY', x, 12.92, location=(-300, y + 80))
        high = t.math(f'{channel}.high', 'MULTIPLY_ADD', t.math(f'{channel}.pow', 'POWER', x, 1 / 2.4, location=(-300, y - 40)),
                      1.055, -0.055, location=(-100, y - 40))
        pick = t.math(f'{channel}.pick', 'GREATER_THAN', x, 0.0031308, location=(-100, y + 120))
        t.make('ShaderNodeMix', f'{channel}.mix', (150, y), {'data_type': 'FLOAT'},
               {'Factor_Float': pick, 'A_Float': low, 'B_Float': high})
        t.link(f'{channel}.mix', 'Result_Float', 'join', channel)
    t.link('join', 'Color', 'out', 'Color')
    return t
