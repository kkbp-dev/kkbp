"""`.SVS eye layers`: SVS's eye shader (LIF/lif_main_eye) up to its light, as an affine function of
the eye white under it (models.lif_main_eye, issue 62): the eye over an eye white `under` is
`under * A + B`, so the light group can light it over the real eye white and over black and white,
as the exporter's pupil layer needs.

    White = mix(Eye white 1, Shadow mask * Eye white 2, Shadow mask alpha * Eye white 2 alpha)
    iris  = mix(Eye 1, Eye 2, Iris.r * Eye 2 alpha * e);  iris = clamp(mix(iris, iris + 2 * Eye 3 - 1, Iris.g * Eye 3 alpha * e))
    c     = the pupil's three colours over iris (Pupil.a, .r, .g, each by its alpha), the line by
            Pupil.b * Pupil.a and Iris.b, then the gradient's soft light, `2cg + c^2 (1 - 2g)`, by Grade.r * its alpha
    top   = the three highlight colours over the eye by hk = Highlight k alpha * colour alpha, then the
            line by their blue: top = eye * P + Q
    eye   = mix(under, c, e);  out = mix(eye, top, amount),  amount = clamp(sum hk) * Highlight power
    A     = (1 - e) * K,  B = c * e * K + amount * Q,  K = 1 - amount + amount * P
    Cap   = 1 - 0.2 * clamp(sum of the highlights' alpha)

e is the iris mask's alpha. Each texture's alpha is multiplied by its `present` switch, which a
missing texture turns off (an empty image node reads black, opaque). Colours are linear. Written by
hand."""

NAME = '.SVS eye layers'
KIND = 'ShaderNodeTree'

TEXTURES = ('Shadow mask', 'Iris', 'Pupil', 'Grade', 'Highlight 1', 'Highlight 2', 'Highlight 3')
COLORS = (('Eye white 1', False), ('Eye white 2', True), ('Eye 1', False), ('Eye 2', True), ('Eye 3', True),
          ('Pupil 1', True), ('Pupil 2', True), ('Pupil 3', True), ('Line color', True), ('Grade color', True),
          ('Highlight color 1', True), ('Highlight color 2', True), ('Highlight color 3', True))


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'White', 'NodeSocketVector')
    t.socket('OUTPUT', 'A', 'NodeSocketFloat')
    t.socket('OUTPUT', 'B', 'NodeSocketVector')
    t.socket('OUTPUT', 'Cap', 'NodeSocketFloat')
    for name in TEXTURES:
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'{name} present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for name, alpha in COLORS:
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
        if alpha:
            t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Highlight power', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-2600, 0))
    t.make('NodeGroupOutput', 'out', (2000, 0))
    m = t.math
    rgb, alpha = {}, {}
    for row, name in enumerate(TEXTURES):
        y = 1500 - row * 250
        t.make('ShaderNodeSeparateColor', f'{name}.rgb', (-2400, y), ins={'Color': ('in', name)})
        rgb[name] = lambda c, n=name: (f'{n}.rgb', c)
        alpha[name] = m(f'{name}.a', 'MULTIPLY', ('in', f'{name} alpha'), ('in', f'{name} present'), location=(-2400, y - 120))
    col = lambda n: ('in', n)  # noqa: E731
    amt = lambda n: ('in', f'{n} alpha')  # noqa: E731
    y = [1500]

    def mix(name, a, b, f, location=None, clamp=False):
        """A vector mix; clamped, a colour mix, whose result Blender can clamp."""
        y[0] -= 180
        kind, key = ('RGBA', 'Color') if clamp else ('VECTOR', 'Vector')
        t.make('ShaderNodeMix', name, location or (-1800, y[0]), {'data_type': kind, 'clamp_result': clamp},
               {'Factor_Float': f, f'A_{key}': a, f'B_{key}': b})
        return (name, f'Result_{key}')

    def mul(name, *xs):
        out = xs[0]
        for k, x in enumerate(xs[1:]):
            out = m(f'{name}.{k}', 'MULTIPLY', out, x, location=(-2100, y[0] - k * 60))
        return out

    # The eye white.
    t.make('ShaderNodeVectorMath', 'white.mask', (-2100, 1700), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Shadow mask'), 'Vector_001': col('Eye white 2')})
    white = mix('white', col('Eye white 1'), ('white.mask', 'Vector'),
                m('white.amount', 'MULTIPLY', ('in', 'Shadow mask alpha'), amt('Eye white 2'), location=(-2100, 1600)))
    t.link(*white, 'out', 'White')

    e = alpha['Iris']
    iris = mix('iris', col('Eye 1'), col('Eye 2'), mul('iris.amount', rgb['Iris']('Red'), amt('Eye 2'), e))
    t.make('ShaderNodeVectorMath', 'iris.3', (-2100, y[0] - 200), {'operation': 'MULTIPLY_ADD'},
           {'Vector': col('Eye 3'), 'Vector_001': (2.0, 2.0, 2.0), 'Vector_002': iris})
    t.make('ShaderNodeVectorMath', 'iris.3b', (-1950, y[0] - 200), {'operation': 'SUBTRACT'},
           {'Vector': ('iris.3', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    iris = mix('iris.light', iris, ('iris.3b', 'Vector'), mul('iris.3amount', rgb['Iris']('Green'), amt('Eye 3'), e), clamp=True)

    pa = alpha['Pupil']
    c = mix('pupil.1', iris, col('Pupil 1'), m('pupil.1amount', 'MULTIPLY', pa, amt('Pupil 1'), location=(-2100, y[0])))
    c = mix('pupil.2', c, col('Pupil 2'), mul('pupil.2amount', rgb['Pupil']('Red'), amt('Pupil 2'), pa))
    c = mix('pupil.3', c, col('Pupil 3'), mul('pupil.3amount', rgb['Pupil']('Green'), amt('Pupil 3'), pa))
    line = m('line.amount', 'MULTIPLY_ADD', mul('line.pupil', rgb['Pupil']('Blue'), pa), amt('Line color'),
             m('line.iris', 'MULTIPLY', amt('Line color'), rgb['Iris']('Blue'), location=(-2100, y[0] - 300)), location=(-1950, y[0] - 300))
    c = mix('line', c, col('Line color'), line)

    # The gradient's soft light.
    t.make('ShaderNodeVectorMath', 'g', (-1600, 600), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Grade'), 'Vector_001': col('Grade color')})
    t.make('ShaderNodeVectorMath', 'soft.2cg', (-1450, 700), {'operation': 'MULTIPLY'}, {'Vector': c, 'Vector_001': ('g', 'Vector')})
    t.make('ShaderNodeVectorMath', 'soft.cc', (-1450, 550), {'operation': 'MULTIPLY'}, {'Vector': c, 'Vector_001': c})
    t.make('ShaderNodeVectorMath', 'soft.1-2g', (-1450, 400), {'operation': 'MULTIPLY_ADD'},
           {'Vector': ('g', 'Vector'), 'Vector_001': (-2.0, -2.0, -2.0), 'Vector_002': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'soft.b', (-1300, 500), {'operation': 'MULTIPLY'},
           {'Vector': ('soft.cc', 'Vector'), 'Vector_001': ('soft.1-2g', 'Vector')})
    t.make('ShaderNodeVectorMath', 'soft', (-1150, 600), {'operation': 'MULTIPLY_ADD'},
           {'Vector': ('soft.2cg', 'Vector'), 'Vector_001': (2.0, 2.0, 2.0), 'Vector_002': ('soft.b', 'Vector')})
    c = mix('grade', c, ('soft', 'Vector'), mul('grade.amount', rgb['Grade']('Red'), amt('Grade color')),
            location=(-1000, 600), clamp=True)

    # The highlights: top = eye * P + Q.
    hk = [m(f'h{k}', 'MULTIPLY', alpha[f'Highlight {k}'], amt(f'Highlight color {k}'), location=(-1300, -200 - k * 150))
          for k in (1, 2, 3)]
    q = (0.0, 0.0, 0.0)
    keep = 1.0
    for k in (1, 2, 3):
        q = mix(f'q{k}', q, col(f'Highlight color {k}'), hk[k - 1], location=(-1000, -200 - k * 150))
        keep = m(f'keep{k}', 'MULTIPLY', keep, m(f'keep{k}.1', 'SUBTRACT', 1.0, hk[k - 1], location=(-1150, -250 - k * 150)),
                 location=(-850, -250 - k * 150))
    lines = 0.0
    for k in (1, 2, 3):
        lines = m(f'lines{k}', 'MULTIPLY_ADD', mul(f'lines{k}.f', rgb[f'Highlight {k}']('Blue'), alpha[f'Highlight {k}'],
                  amt(f'Highlight color {k}')), amt('Line color'), lines, location=(-1000, -800 - k * 150))
    q = mix('q.line', q, col('Line color'), lines, location=(-700, -600))
    p = m('P', 'MULTIPLY', keep, m('P.lines', 'SUBTRACT', 1.0, lines, location=(-700, -800)), location=(-550, -700))
    amount = m('amount', 'MULTIPLY', m('amount.sum', 'ADD', m('amount.12', 'ADD', hk[0], hk[1], location=(-700, -1000)), hk[2],
               location=(-550, -1000), clamp=True), ('in', 'Highlight power'), location=(-400, -1000))
    k_ = m('K', 'ADD', m('K.1', 'SUBTRACT', 1.0, amount, location=(-250, -900)), m('K.2', 'MULTIPLY', amount, p, location=(-250, -1000)),
           location=(-100, -950))
    t.link(*m('A', 'MULTIPLY', m('A.1', 'SUBTRACT', 1.0, e, location=(50, -800)), k_, location=(200, -850)), 'out', 'A')
    t.make('ShaderNodeVectorMath', 'B.c', (50, 300), {'operation': 'SCALE'},
           {'Vector': c, 'Scale': m('B.ek', 'MULTIPLY', e, k_, location=(50, 100))})
    t.make('ShaderNodeVectorMath', 'B', (300, 200), {'operation': 'MULTIPLY_ADD'},
           {'Vector': q, 'Vector_002': ('B.c', 'Vector')})
    t.make('ShaderNodeCombineXYZ', 'B.amount', (150, 0), ins={'X': amount, 'Y': amount, 'Z': amount})
    t.link('B.amount', 'Vector', 'B', 'Vector_001')
    t.link('B', 'Vector', 'out', 'B')
    hsum = m('cap.sum', 'ADD', m('cap.12', 'ADD', alpha['Highlight 1'], alpha['Highlight 2'], location=(200, -1200)),
             alpha['Highlight 3'], location=(350, -1200), clamp=True)
    t.link(*m('Cap', 'MULTIPLY_ADD', hsum, -0.2, 1.0, location=(500, -1200)), 'out', 'Cap')
    return t
