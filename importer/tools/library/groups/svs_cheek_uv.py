"""`.SVS cheek uv`: where SVS's face shader reads its cheek blush (models.cheek_position with
create_paint_uv), on the mesh's second UV map: a paint position of (Position x * 0.24 +
Cheek position.x - 0.12, Position y * -0.2 + Cheek position.y + 0.1, Cheek position.z - Rotation + 0.5),
w = Size * 0.2 + Cheek position w - 0.1. Written by hand."""

import math

NAME = '.SVS cheek uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Cheek position', 'NodeSocketVector', default_value=(-0.12, 0.0, 0.0))
    t.socket('INPUT', 'Cheek position w', 'NodeSocketFloat', default_value=0.75)
    for name, d in (('Position x', 0.5), ('Position y', 0.5), ('Rotation', 0.5), ('Size', 0.5)):
        t.socket('INPUT', name, 'NodeSocketFloat', default_value=d)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (800, 0))
    m = t.math
    t.make('ShaderNodeUVMap', 'uv', (-1000, 400), {'uv_map': 'uv_nipple_and_shine'})
    t.make('ShaderNodeSeparateXYZ', 'uv.xy', (-800, 400), ins={'Vector': ('uv', 'UV')})
    t.make('ShaderNodeSeparateXYZ', 'cp', (-1000, 0), ins={'Vector': ('in', 'Cheek position')})
    px = m('px', 'ADD', m('px.a', 'MULTIPLY_ADD', ('in', 'Position x'), 0.24, ('cp', 'X'), location=(-850, 100)), -0.12, location=(-700, 100))
    py = m('py', 'ADD', m('py.a', 'MULTIPLY_ADD', ('in', 'Position y'), -0.2, ('cp', 'Y'), location=(-850, 0)), 0.1, location=(-700, 0))
    pz = m('pz', 'ADD', m('pz.a', 'SUBTRACT', ('cp', 'Z'), ('in', 'Rotation'), location=(-850, -100)), 0.5, location=(-700, -100))
    pw = m('pw', 'ADD', m('pw.a', 'MULTIPLY_ADD', ('in', 'Size'), 0.2, ('in', 'Cheek position w'), location=(-850, -200)), -0.1,
           location=(-700, -200))
    s = m('s', 'MULTIPLY_ADD', pw, -2.0, 2.0, location=(-550, -200))
    two_s = m('2s', 'MULTIPLY', s, 2.0, location=(-400, -200))
    shift = m('shift', 'SUBTRACT', 0.0, s, location=(-400, -300))
    pu = m('p.u', 'MULTIPLY_ADD', m('p.u.off', 'ADD', ('uv.xy', 'X'), px, location=(-550, 200)), two_s, shift, location=(-250, 200))
    pv = m('p.v', 'MULTIPLY_ADD', m('p.v.off', 'ADD', ('uv.xy', 'Y'), py, location=(-550, 0)), two_s, shift, location=(-250, 0))
    angle = m('angle', 'MULTIPLY', pz, 2 * math.pi, location=(-400, -450))
    cos, sin = m('cos', 'COSINE', angle, location=(-250, -400)), m('sin', 'SINE', angle, location=(-250, -500))
    x = m('x', 'ADD', m('x.t', 'ADD', m('x.c', 'MULTIPLY', pu, cos, location=(-100, 250)), m('x.s', 'MULTIPLY', pv, sin,
          location=(-100, 150)), location=(50, 200)), 0.5, location=(200, 200))
    y = m('y', 'ADD', m('y.t', 'SUBTRACT', m('y.c', 'MULTIPLY', pv, cos, location=(-100, -50)), m('y.s', 'MULTIPLY', pu, sin,
          location=(-100, -150)), location=(50, -100)), 0.5, location=(200, -100))
    t.make('ShaderNodeCombineXYZ', 'vector', (400, 50), ins={'X': x, 'Y': y})
    t.link('vector', 'Vector', 'out', 'Vector')
    return t
