"""`.SVS paint uv`: where SVS's create shaders read a paint (models.create_paint_uv):
s = 2 - 2 * Position w; p = (uv + Position.xy) * 2s + 0.5 - s - 0.5, turned by Position.z turns, + 0.5.
Written by hand."""

import math

NAME = '.SVS paint uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Position', 'NodeSocketVector', default_value=(0.0, 0.0, 0.0))
    t.socket('INPUT', 'Position w', 'NodeSocketFloat', default_value=0.5)
    t.make('NodeGroupInput', 'in', (-1000, 0))
    t.make('NodeGroupOutput', 'out', (800, 0))
    m = t.math
    t.make('ShaderNodeUVMap', 'uv', (-1000, 400))
    t.make('ShaderNodeSeparateXYZ', 'uv.xy', (-800, 400), ins={'Vector': ('uv', 'UV')})
    t.make('ShaderNodeSeparateXYZ', 'pos', (-800, 0), ins={'Vector': ('in', 'Position')})
    s = m('s', 'MULTIPLY_ADD', ('in', 'Position w'), -2.0, 2.0, location=(-650, -200))
    two_s = m('2s', 'MULTIPLY', s, 2.0, location=(-500, -200))
    shift = m('shift', 'SUBTRACT', 0.0, s, location=(-500, -300))
    p = {}
    for row, (a, c) in enumerate((('u', 'X'), ('v', 'Y'))):
        y = 200 - row * 250
        p[a] = m(f'p.{a}', 'MULTIPLY_ADD', m(f'p.{a}.off', 'ADD', ('uv.xy', 'XY'[row]), ('pos', c), location=(-650, y)), two_s, shift,
                 location=(-350, y))
    angle = m('angle', 'MULTIPLY', ('pos', 'Z'), 2 * math.pi, location=(-500, -450))
    cos, sin = m('cos', 'COSINE', angle, location=(-350, -400)), m('sin', 'SINE', angle, location=(-350, -500))
    x = m('x', 'ADD', m('x.t', 'ADD', m('x.c', 'MULTIPLY', p['u'], cos, location=(-200, 250)), m('x.s', 'MULTIPLY', p['v'], sin,
          location=(-200, 150)), location=(-50, 200)), 0.5, location=(100, 200))
    y = m('y', 'ADD', m('y.t', 'SUBTRACT', m('y.c', 'MULTIPLY', p['v'], cos, location=(-200, -50)), m('y.s', 'MULTIPLY', p['u'], sin,
          location=(-200, -150)), location=(-50, -100)), 0.5, location=(100, -100))
    t.make('ShaderNodeCombineXYZ', 'vector', (300, 50), ins={'X': x, 'Y': y})
    t.link('vector', 'Vector', 'out', 'Vector')
    return t
