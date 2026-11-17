"""The three paints SVS's skin create shaders lay over their colour, for the group modules in `groups/`
to call (models.svs_paints). Not a module of its own datablock: build.py's registry skips it."""


def paints(t, rgb, mask_channels, x=-600):
    """The LIF create shaders' three paints over `rgb` (a source), each by the paint mask's channel in
    `mask_channels` (None: no mask). Returns the result's source."""
    m = t.math
    for k, ch in zip((1, 2, 3), mask_channels):
        y = -200 - k * 400
        a = m(f'p{k}.a.p', 'MULTIPLY', ('in', f'Paint {k} alpha'), ('in', f'Paint {k} present'), location=(x, y - 150))
        t.make('ShaderNodeSeparateColor', f'p{k}.hsv', (x, y), {'mode': 'HSV'}, {'Color': ('in', f'Paint {k}')})
        t.make('ShaderNodeMapRange', f'p{k}.smooth', (x + 150, y), {'interpolation_type': 'SMOOTHSTEP', 'clamp': True},
               {'Value': (f'p{k}.hsv', 'Green'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 1.0})
        f = m(f'p{k}.f', 'MINIMUM', a, (f'p{k}.smooth', 'Result'), location=(x + 300, y))
        t.make('ShaderNodeCombineXYZ', f'p{k}.fv', (x + 450, y), ins={'X': f, 'Y': f, 'Z': f})
        t.make('ShaderNodeVectorMath', f'p{k}.tint', (x + 600, y), {'operation': 'MAXIMUM'},
               {'Vector': (f'p{k}.fv', 'Vector'), 'Vector_001': ('in', f'Paint color {k}')})
        t.make('ShaderNodeVectorMath', f'p{k}.col', (x + 750, y), {'operation': 'MULTIPLY'},
               {'Vector': ('in', f'Paint {k}'), 'Vector_001': (f'p{k}.tint', 'Vector')})
        amount = m(f'p{k}.amount', 'MULTIPLY', a, ('in', f'Paint color {k} alpha'), location=(x + 600, y - 150))
        if ch is not None:
            amount = m(f'p{k}.masked', 'MULTIPLY', amount, ('paint mask', ch), location=(x + 750, y - 150))
        t.make('ShaderNodeMix', f'paint{k}', (x + 900, y), {'data_type': 'VECTOR'},
               {'Factor_Float': amount, 'A_Vector': rgb, 'B_Vector': (f'p{k}.col', 'Vector')})
        rgb = (f'paint{k}', 'Result_Vector')
    return rgb


def paint_sockets(t):
    for k in (1, 2, 3):
        t.socket('INPUT', f'Paint {k}', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'Paint {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'Paint {k} present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2, 3):
        t.socket('INPUT', f'Paint color {k}', 'NodeSocketColor', default_value=(1.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'Paint color {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
