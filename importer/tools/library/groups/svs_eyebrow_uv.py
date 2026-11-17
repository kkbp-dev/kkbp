"""`.SVS eyebrow uv`: where SVS's eyebrow shader reads its texture (models.eyebrow_uv, issue 62):
stretched along u by Length and along v by Width; both 0.5 is the texture as it is.

    su = mix(2 - 2 * Length, 1.2 - 0.4 * Length, round(Length))
    sv = 1.3 - 0.6 * Width
    u' = u * su - 0.2 * (su - 1);  v' = v * sv - 0.5 * (0.3 - 0.6 * Width)

The game rounds half to even (round(0.5) = 0); this rounds 0.5 up, so Length 0.5 takes the second
formula, which gives the same 1 there. Written by hand."""

NAME = '.SVS eyebrow uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Length', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Width', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (700, 0))
    t.make('ShaderNodeUVMap', 'uv', (-900, 300))
    t.make('ShaderNodeSeparateXYZ', 'split', (-700, 300), ins={'Vector': ('uv', 'UV')})
    length = ('in', 'Length')
    a = t.math('su.a', 'MULTIPLY_ADD', length, -2.0, 2.0, location=(-700, 0))
    b = t.math('su.b', 'MULTIPLY_ADD', length, -0.4, 1.2, location=(-700, -150))
    t.make('ShaderNodeMix', 'su', (-450, -50), {'data_type': 'FLOAT', 'clamp_factor': False},
           {'Factor_Float': t.math('su.pick', 'ROUND', length, location=(-700, 150)), 'A_Float': a, 'B_Float': b})
    su = ('su', 'Result_Float')
    u = t.math('u', 'MULTIPLY_ADD', ('split', 'X'), su, t.math('u.shift', 'MULTIPLY_ADD', su, -0.2, 0.2, location=(-250, 0)),
               location=(0, 200))
    sv = t.math('sv', 'MULTIPLY_ADD', ('in', 'Width'), -0.6, 1.3, location=(-450, -350))
    v = t.math('v', 'MULTIPLY_ADD', ('split', 'Y'), sv,
               t.math('v.shift', 'MULTIPLY_ADD', ('in', 'Width'), 0.3, -0.15, location=(-250, -350)), location=(0, -100))
    t.make('ShaderNodeCombineXYZ', 'join', (300, 0), ins={'X': u, 'Y': v})
    t.link('join', 'Vector', 'out', 'Vector')
    return t
