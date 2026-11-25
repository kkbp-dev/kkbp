"""`.SVS face paint uv`: where SVS's face create shader reads a paint (Size 2) or the mole (Size 2.4)
(models.face_paint_uv): as `.SVS paint uv`, its v moved by 0.8 (Position.y + 0.0966849998)
and s = 2 - Size * Position w. Written by hand."""

import math

NAME = '.SVS face paint uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Position', 'NodeSocketVector', default_value=(0.0, 0.0, 0.0))
    t.socket('INPUT', 'Position w', 'NodeSocketFloat', default_value=0.5)
    t.socket('INPUT', 'Size', 'NodeSocketFloat', default_value=2.0)
    t.make('NodeGroupInput', 'in', (-1000, 0))
    t.make('NodeGroupOutput', 'out', (800, 0))
    m = t.math
    t.make('ShaderNodeUVMap', 'uv', (-1000, 400))
    t.make('ShaderNodeSeparateXYZ', 'uv.xy', (-800, 400), ins={'Vector': ('uv', 'UV')})
    t.make('ShaderNodeSeparateXYZ', 'pos', (-800, 0), ins={'Vector': ('in', 'Position')})
    s = m('s', 'SUBTRACT', 2.0, m('s.w', 'MULTIPLY', ('in', 'Size'), ('in', 'Position w'), location=(-800, -200)), location=(-650, -200))
    two_s = m('2s', 'MULTIPLY', s, 2.0, location=(-500, -200))
    shift = m('shift', 'SUBTRACT', 0.0, s, location=(-500, -300))
    pu = m('p.u', 'MULTIPLY_ADD', m('p.u.off', 'ADD', ('uv.xy', 'X'), ('pos', 'X'), location=(-650, 200)), two_s, shift, location=(-350, 200))
    vy = m('p.v.y', 'MULTIPLY_ADD', m('p.v.shift', 'ADD', ('pos', 'Y'), 0.0966849998, location=(-800, -50)), 0.8, ('uv.xy', 'Y'),
           location=(-650, -50))
    pv = m('p.v', 'MULTIPLY_ADD', vy, two_s, shift, location=(-350, -50))
    angle = m('angle', 'MULTIPLY', ('pos', 'Z'), 2 * math.pi, location=(-500, -450))
    cos, sin = m('cos', 'COSINE', angle, location=(-350, -400)), m('sin', 'SINE', angle, location=(-350, -500))
    x = m('x', 'ADD', m('x.t', 'ADD', m('x.c', 'MULTIPLY', pu, cos, location=(-200, 250)), m('x.s', 'MULTIPLY', pv, sin,
          location=(-200, 150)), location=(-50, 200)), 0.5, location=(100, 200))
    y = m('y', 'ADD', m('y.t', 'SUBTRACT', m('y.c', 'MULTIPLY', pv, cos, location=(-200, -50)), m('y.s', 'MULTIPLY', pu, sin,
          location=(-200, -150)), location=(-50, -100)), 0.5, location=(100, -100))
    t.make('ShaderNodeCombineXYZ', 'vector', (300, 50), ins={'X': x, 'Y': y})
    t.link('vector', 'Vector', 'out', 'Vector')
    return t
