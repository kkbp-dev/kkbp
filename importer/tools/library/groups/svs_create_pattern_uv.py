"""`.SVS create pattern uv`: where SVS's clothes create shader (LIF/lif_create_main_cloth) reads a
pattern mask (models.create_pattern_uv, issue 62): p = (uv + 2 * Offset - 1) * (20 - 19 * Scale) - 0.5,
turned by (Rotator - 0.5) turns, + 0.5. Written by hand."""

import math

NAME = '.SVS create pattern uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    for name, d in (('Offset u', 0.5), ('Offset v', 0.5), ('Scale u', 1.0), ('Scale v', 1.0), ('Rotator', 0.5)):
        t.socket('INPUT', name, 'NodeSocketFloat', default_value=d)
    t.make('NodeGroupInput', 'in', (-1000, 0))
    t.make('NodeGroupOutput', 'out', (800, 0))
    m = t.math
    t.make('ShaderNodeUVMap', 'uv', (-1000, 400))
    t.make('ShaderNodeSeparateXYZ', 'uv.xy', (-800, 400), ins={'Vector': ('uv', 'UV')})
    p = {}
    for row, a in enumerate(('u', 'v')):
        y = 200 - row * 250
        p[a] = m(f'p.{a}', 'MULTIPLY_ADD', m(f'p.{a}.off', 'ADD', ('uv.xy', 'XY'[row]), m(f'p.{a}.o', 'MULTIPLY_ADD', ('in', f'Offset {a}'),
                 2.0, -1.0, location=(-800, y)), location=(-650, y)),
                 m(f'p.{a}.s', 'MULTIPLY_ADD', ('in', f'Scale {a}'), -19.0, 20.0, location=(-650, y - 100)), -0.5, location=(-500, y))
    angle = m('angle', 'MULTIPLY', m('angle.t', 'SUBTRACT', ('in', 'Rotator'), 0.5, location=(-650, -400)), 2 * math.pi, location=(-500, -400))
    cos, sin = m('cos', 'COSINE', angle, location=(-350, -350)), m('sin', 'SINE', angle, location=(-350, -450))
    x = m('x', 'ADD', m('x.t', 'ADD', m('x.c', 'MULTIPLY', p['u'], cos, location=(-200, 250)), m('x.s', 'MULTIPLY', p['v'], sin,
          location=(-200, 150)), location=(-50, 200)), 0.5, location=(100, 200))
    y = m('y', 'ADD', m('y.t', 'SUBTRACT', m('y.c', 'MULTIPLY', p['v'], cos, location=(-200, -50)), m('y.s', 'MULTIPLY', p['u'], sin,
          location=(-200, -150)), location=(-50, -100)), 0.5, location=(100, -100))
    t.make('ShaderNodeCombineXYZ', 'vector', (300, 50), ins={'X': x, 'Y': y})
    t.link('vector', 'Vector', 'out', 'Vector')
    return t
