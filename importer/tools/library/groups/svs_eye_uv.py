"""`.SVS eye uv`: where SVS's eye shader (LIF/lif_main_eye) reads each texture, on the bake quad
(models.eye_uvs).

    p      = the UV turned by (mix(1 - Rotation, Rotation, Mirror) * 0.1 - 0.05) turns about 0.5 - c,
             c = Eye position.zw + Eye position add.zw
    S      = (Eye position.xy + Eye open) * Eye position add.xy
    Grade  = ((c.x + p.x), Grade position * 0.65 + Eye position.w + p.y - 0.25) * G - G / 2 + 0.5,
             G = S + 1 - 2 * Grade size
    q      = (c + p) * S - S / 2 + 0.5;  r = min(|(q.x - 0.5, q.y * 0.6 - 0.3)| * 4 + 0.18, 1)
    Iris   = q + (r * 0.2 - 0.2) * (Parallax - 0.5) * o
    Pupil  = (c + p) * P - P / 2 + (0.05 - 0.1 * Parallax) * o + 0.5,  P = Pupil size + Eye open
    Highlight k = turn((Hk.zw * 0.5 + c + p) * Hs - Hs / 2, (Hk rotation - 0.5) turns)
                  + (0.1 * Parallax - 0.05) * o + 0.5,  Hs = Hk.xy * Eye position add.xy

o is the view offset the bake quad gives (models.bake_view): (0.5 - u, 0.5 - v, 1) normalised, its
x and y over its z + 0.42. A vector's x, y, z come in `<name>` and its w in `<name> w`. Written by
hand."""

import math

NAME = '.SVS eye uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    for name in ('Grade', 'Iris', 'Pupil', 'Highlight 1', 'Highlight 2', 'Highlight 3'):
        t.socket('OUTPUT', name, 'NodeSocketVector')
    vectors = {'Eye position': (1.23, 1.48, 0.0, 0.03), 'Eye position add': (1.0, 1.0, 0.0, 0.06),
               'Pupil size': (1.17, 1.38, 0.0, 0.0),
               'Highlight 1 position': (0.94, 1.26, 0.02, -0.32), 'Highlight 2 position': (2.6, 2.49, 0.36, 0.21),
               'Highlight 3 position': (0.98, 1.26, -0.28, -0.13)}
    for name, d in vectors.items():
        t.socket('INPUT', name, 'NodeSocketVector', default_value=d[:3])
        t.socket('INPUT', f'{name} w', 'NodeSocketFloat', default_value=d[3])
    for name, d in (('Rotation', 0.5), ('Mirror', 0.0), ('Eye open', 0.0), ('Grade position', 0.6), ('Grade size', 0.7),
                    ('Parallax', 1.0), ('Highlight 1 rotation', 0.5), ('Highlight 2 rotation', 0.5),
                    ('Highlight 3 rotation', 0.5)):
        t.socket('INPUT', name, 'NodeSocketFloat', default_value=d)
    t.make('NodeGroupInput', 'in', (-2400, 0))
    t.make('NodeGroupOutput', 'out', (1600, 0))
    m = t.math
    xyz = {}

    def split(name):
        if name not in xyz:
            t.make('ShaderNodeSeparateXYZ', f'{name}.xyz', (-2200, -len(xyz) * 200), ins={'Vector': ('in', name)})
            xyz[name] = f'{name}.xyz'
        return lambda c: (xyz[name], c) if c != 'W' else ('in', f'{name} w')

    ep, epa = split('Eye position'), split('Eye position add')
    t.make('ShaderNodeUVMap', 'uv', (-2400, 600))
    t.make('ShaderNodeSeparateXYZ', 'uv.xy', (-2200, 600), ins={'Vector': ('uv', 'UV')})
    u, v = ('uv.xy', 'X'), ('uv.xy', 'Y')

    # The view offset o.
    vx = m('view.x', 'SUBTRACT', 0.5, u, location=(-2000, 900))
    vy = m('view.y', 'SUBTRACT', 0.5, v, location=(-2000, 800))
    t.make('ShaderNodeCombineXYZ', 'view', (-1850, 850), ins={'X': vx, 'Y': vy, 'Z': 1.0})
    t.make('ShaderNodeVectorMath', 'view.n', (-1700, 850), {'operation': 'NORMALIZE'}, {'Vector': ('view', 'Vector')})
    t.make('ShaderNodeSeparateXYZ', 'view.s', (-1550, 850), ins={'Vector': ('view.n', 'Vector')})
    zden = m('view.z', 'ADD', ('view.s', 'Z'), 0.42, location=(-1400, 750))
    ox = m('o.x', 'DIVIDE', ('view.s', 'X'), zden, location=(-1250, 900))
    oy = m('o.y', 'DIVIDE', ('view.s', 'Y'), zden, location=(-1250, 800))

    # The turned UV p about 0.5 - c.
    cx = m('c.x', 'ADD', epa('Z'), ep('Z'), location=(-2000, 400))
    cy = m('c.y', 'ADD', epa('W'), ep('W'), location=(-2000, 300))
    pivx = m('pivot.x', 'SUBTRACT', 0.5, cx, location=(-1850, 400))
    pivy = m('pivot.y', 'SUBTRACT', 0.5, cy, location=(-1850, 300))
    t.make('ShaderNodeMix', 'turn', (-1850, 550), {'data_type': 'FLOAT', 'clamp_factor': False},
           {'Factor_Float': ('in', 'Mirror'), 'A_Float': m('turn.flip', 'SUBTRACT', 1.0, ('in', 'Rotation'), location=(-2000, 550)),
            'B_Float': ('in', 'Rotation')})
    angle = m('turn.angle', 'MULTIPLY', m('turn.turns', 'MULTIPLY_ADD', ('turn', 'Result_Float'), 0.1, -0.05000001,
              location=(-1700, 550)), 2 * math.pi, location=(-1550, 550))

    def rotate(prefix, x, y, ang, location):
        lx, ly = location
        cos = m(f'{prefix}.cos', 'COSINE', ang, location=(lx, ly + 100))
        sin = m(f'{prefix}.sin', 'SINE', ang, location=(lx, ly))
        rx = m(f'{prefix}.x', 'ADD', m(f'{prefix}.xc', 'MULTIPLY', x, cos, location=(lx + 150, ly + 100)),
               m(f'{prefix}.ys', 'MULTIPLY', y, sin, location=(lx + 150, ly)), location=(lx + 300, ly + 100))
        ry = m(f'{prefix}.y', 'SUBTRACT', m(f'{prefix}.yc', 'MULTIPLY', y, cos, location=(lx + 150, ly - 100)),
               m(f'{prefix}.xs', 'MULTIPLY', x, sin, location=(lx + 150, ly - 200)), location=(lx + 300, ly - 100))
        return rx, ry

    dx = m('d.x', 'SUBTRACT', u, pivx, location=(-1700, 400))
    dy = m('d.y', 'SUBTRACT', v, pivy, location=(-1700, 300))
    rx, ry = rotate('p.turn', dx, dy, angle, (-1550, 350))
    px = m('p.x', 'ADD', rx, pivx, location=(-1100, 450))
    py = m('p.y', 'ADD', ry, pivy, location=(-1100, 300))
    cpx = m('cp.x', 'ADD', cx, px, location=(-950, 450))
    cpy = m('cp.y', 'ADD', cy, py, location=(-950, 300))

    def place(prefix, x, y, sx, sy, location):
        """(x, y) * s - s / 2 + 0.5"""
        lx, ly = location
        ax = m(f'{prefix}.x', 'MULTIPLY_ADD', x, sx, m(f'{prefix}.hx', 'MULTIPLY_ADD', sx, -0.5, 0.5, location=(lx, ly + 50)),
               location=(lx + 150, ly + 50))
        ay = m(f'{prefix}.y', 'MULTIPLY_ADD', y, sy, m(f'{prefix}.hy', 'MULTIPLY_ADD', sy, -0.5, 0.5, location=(lx, ly - 50)),
               location=(lx + 150, ly - 50))
        return ax, ay

    def emit(name, x, y, location):
        t.make('ShaderNodeCombineXYZ', f'{name}.out', location, ins={'X': x, 'Y': y})
        t.link(f'{name}.out', 'Vector', 'out', name)

    sx = m('s.x', 'MULTIPLY', m('s.xo', 'ADD', ep('X'), ('in', 'Eye open'), location=(-1100, 100)), epa('X'), location=(-950, 100))
    sy = m('s.y', 'MULTIPLY', m('s.yo', 'ADD', ep('Y'), ('in', 'Eye open'), location=(-1100, 0)), epa('Y'), location=(-950, 0))
    # Grade
    gs = m('grade.size', 'MULTIPLY_ADD', ('in', 'Grade size'), -2.0, 1.0, location=(-950, -150))
    gy = m('grade.v', 'ADD', m('grade.y0', 'MULTIPLY_ADD', ('in', 'Grade position'), 0.65, ep('W'), location=(-950, -300)),
           m('grade.y1', 'ADD', py, -0.25, location=(-950, -400)), location=(-800, -350))
    gx, gyy = place('grade', cpx, gy, m('grade.sx', 'ADD', sx, gs, location=(-800, -100)),
                    m('grade.sy', 'ADD', sy, gs, location=(-800, -200)), (-650, -250))
    emit('Grade', gx, gyy, (-300, -250))
    # Iris
    qx, qy = place('q', cpx, cpy, sx, sy, (-800, 150))
    r = m('r', 'MINIMUM', m('r.len', 'MULTIPLY_ADD', m('r.hyp', 'SQRT', m('r.sum', 'ADD',
          m('r.xx', 'POWER', m('r.dx', 'SUBTRACT', qx, 0.5, location=(-500, 250)), 2.0, location=(-350, 250)),
          m('r.yy', 'POWER', m('r.dy', 'MULTIPLY_ADD', qy, 0.6, -0.3, location=(-500, 150)), 2.0, location=(-350, 150)),
          location=(-200, 200)), location=(-50, 200)), 4.0, 0.18, location=(100, 200)), 1.0, location=(250, 200))
    depth = m('depth', 'MULTIPLY', m('depth.r', 'MULTIPLY_ADD', r, 0.2, -0.2, location=(400, 200)),
              m('depth.p', 'SUBTRACT', ('in', 'Parallax'), 0.5, location=(400, 100)), location=(550, 150))
    emit('Iris', m('iris.x', 'MULTIPLY_ADD', depth, ox, qx, location=(700, 250)),
         m('iris.y', 'MULTIPLY_ADD', depth, oy, qy, location=(700, 150)), (900, 200))
    # Pupil
    ps = split('Pupil size')
    psx = m('ps.x', 'ADD', ps('X'), ('in', 'Eye open'), location=(-800, -550))
    psy = m('ps.y', 'ADD', ps('Y'), ('in', 'Eye open'), location=(-800, -650))
    pux, puy = place('pupil', cpx, cpy, psx, psy, (-650, -600))
    near = m('near', 'MULTIPLY_ADD', ('in', 'Parallax'), -0.1, 0.05, location=(-500, -750))
    emit('Pupil', m('pupil.ox', 'MULTIPLY_ADD', near, ox, pux, location=(-300, -550)),
         m('pupil.oy', 'MULTIPLY_ADD', near, oy, puy, location=(-300, -650)), (-100, -600))
    # Highlights
    far = m('far', 'MULTIPLY_ADD', ('in', 'Parallax'), 0.1, -0.05, location=(-500, -900))
    for k in (1, 2, 3):
        y0 = -1000 - k * 450
        hp = split(f'Highlight {k} position')
        hx = m(f'h{k}.zx', 'MULTIPLY_ADD', hp('Z'), 0.5, cpx, location=(-950, y0))
        hy = m(f'h{k}.zy', 'MULTIPLY_ADD', hp('W'), 0.5, cpy, location=(-950, y0 - 100))
        hsx = m(f'h{k}.sx', 'MULTIPLY', hp('X'), epa('X'), location=(-950, y0 - 200))
        hsy = m(f'h{k}.sy', 'MULTIPLY', hp('Y'), epa('Y'), location=(-950, y0 - 300))
        ax = m(f'h{k}.ax', 'MULTIPLY_ADD', hx, hsx, m(f'h{k}.bx', 'MULTIPLY', hsx, -0.5, location=(-650, y0 - 200)), location=(-500, y0))
        ay = m(f'h{k}.ay', 'MULTIPLY_ADD', hy, hsy, m(f'h{k}.by', 'MULTIPLY', hsy, -0.5, location=(-650, y0 - 300)), location=(-500, y0 - 100))
        ang = m(f'h{k}.angle', 'MULTIPLY', m(f'h{k}.turns', 'SUBTRACT', ('in', f'Highlight {k} rotation'), 0.5,
                location=(-650, y0 + 100)), 2 * math.pi, location=(-500, y0 + 100))
        tx, ty = rotate(f'h{k}.turn', ax, ay, ang, (-350, y0))
        emit(f'Highlight {k}', m(f'h{k}.u', 'ADD', m(f'h{k}.ou', 'MULTIPLY_ADD', far, ox, tx, location=(100, y0)), 0.5, location=(250, y0)),
             m(f'h{k}.v', 'ADD', m(f'h{k}.ov', 'MULTIPLY_ADD', far, oy, ty, location=(100, y0 - 100)), 0.5, location=(250, y0 - 100)),
             (450, y0))
    return t
