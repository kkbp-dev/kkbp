"""`.SVS pattern uv`: where SVS's item shader (LIF/lif_main_acs) reads a pattern mask
(models.acs_pattern_uv).

    s      = clamp(Scale * Aspect * (Remap max - Remap min) + Remap min, 0, 999), per axis
    p      = turn(uv * s + 2 * Offset - 1 - 0.5 * s, (Rotator - 0.5) turns) + 0.5
    Vector = mix(p, frac(clamp(p)), Clamp);  Inside = mix(1, min(ceil(p.x), ceil(p.y)), Clamp)

Written by hand."""

import math

NAME = '.SVS pattern uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('OUTPUT', 'Inside', 'NodeSocketFloat')
    for name, d in (('Scale u', 1.0), ('Scale v', 1.0), ('Aspect u', 1.0), ('Aspect v', 1.0), ('Remap min', 20.0),
                    ('Remap max', 1.0), ('Offset u', 0.5), ('Offset v', 0.5), ('Rotator', 0.5), ('Clamp', 0.0)):
        t.socket('INPUT', name, 'NodeSocketFloat', default_value=d)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1000, 0))
    m = t.math
    t.make('ShaderNodeUVMap', 'uv', (-1400, 400))
    t.make('ShaderNodeSeparateXYZ', 'uv.xy', (-1200, 400), ins={'Vector': ('uv', 'UV')})
    span = m('span', 'SUBTRACT', ('in', 'Remap max'), ('in', 'Remap min'), location=(-1200, 100))
    axes = {}
    for row, a in enumerate(('u', 'v')):
        y = 200 - row * 300
        s = m(f's.{a}', 'MINIMUM', m(f's.{a}.low', 'MAXIMUM', m(f's.{a}.remap', 'MULTIPLY_ADD', m(f's.{a}.raw', 'MULTIPLY',
              ('in', f'Scale {a}'), ('in', f'Aspect {a}'), location=(-1050, y)), span, ('in', 'Remap min'), location=(-900, y)),
              0.0, location=(-750, y)), 999.0, location=(-600, y))
        p = m(f'p.{a}', 'ADD', m(f'p.{a}.uv', 'MULTIPLY_ADD', ('uv.xy', 'XY'[row]), s,
              m(f'p.{a}.off', 'MULTIPLY_ADD', ('in', f'Offset {a}'), 2.0, -1.0, location=(-600, y - 120)), location=(-450, y)),
              m(f'p.{a}.half', 'MULTIPLY', s, -0.5, location=(-450, y - 120)), location=(-300, y))
        axes[a] = p
    angle = m('angle', 'MULTIPLY', m('angle.turns', 'SUBTRACT', ('in', 'Rotator'), 0.5, location=(-450, -400)), 2 * math.pi,
              location=(-300, -400))
    cos, sin = m('cos', 'COSINE', angle, location=(-150, -350)), m('sin', 'SINE', angle, location=(-150, -450))
    x = m('x', 'ADD', m('x.t', 'ADD', m('x.c', 'MULTIPLY', axes['u'], cos, location=(0, 250)), m('x.s', 'MULTIPLY', axes['v'], sin,
          location=(0, 150)), location=(150, 200)), 0.5, location=(300, 200))
    y = m('y', 'ADD', m('y.t', 'SUBTRACT', m('y.c', 'MULTIPLY', axes['v'], cos, location=(0, -50)), m('y.s', 'MULTIPLY', axes['u'], sin,
          location=(0, -150)), location=(150, -100)), 0.5, location=(300, -100))
    wrapped = []
    for name, p in (('x', x), ('y', y)):
        w = m(f'{name}.wrap', 'FRACT', m(f'{name}.clamp', 'ADD', p, 0.0, location=(450, 300 if name == 'x' else 0), clamp=True),
              location=(600, 300 if name == 'x' else 0))
        t.make('ShaderNodeMix', f'{name}.pick', (750, 250 if name == 'x' else -50), {'data_type': 'FLOAT', 'clamp_factor': False},
               {'Factor_Float': ('in', 'Clamp'), 'A_Float': p, 'B_Float': w})
        wrapped.append((f'{name}.pick', 'Result_Float'))
    t.make('ShaderNodeCombineXYZ', 'vector', (900, 100), ins={'X': wrapped[0], 'Y': wrapped[1]})
    t.link('vector', 'Vector', 'out', 'Vector')
    inside = m('inside.min', 'MINIMUM', m('inside.x', 'CEIL', x, location=(450, -300)), m('inside.y', 'CEIL', y, location=(450, -400)),
               location=(600, -350))
    t.make('ShaderNodeMix', 'inside', (750, -350), {'data_type': 'FLOAT', 'clamp_factor': False},
           {'Factor_Float': ('in', 'Clamp'), 'A_Float': 1.0, 'B_Float': inside})
    t.link('inside', 'Result_Float', 'out', 'Inside')
    return t
