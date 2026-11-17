"""`.SVS lif_main_skin_body`: SVS's body shader as the exporter bakes it, at one N.L
(models.lif_main_skin_body, issue 62).

    s       = Shadow power * 0.35 + 0.35
    shaded  = Color * mix(1, Shadow color 2, Matcap.b * Shadow color 2 alpha * s)
    h       = clamp(Highlight.b * 5/3) * Highlight power * (1 - max(Detail 2.g, Highlight ramp.g, Matcap.g * Shadow color 2 alpha * s))
    q       = Detail 1 alpha * Matcap.r
    shine   = clamp((h * High light power * (1 - q) + q * (1 - q) * (1 - Underhair amount)) * clamp(mean(L)) * Highlight color)
    albedo  = clamp(shaded + Highlight color alpha * shine, 0, 0.95)
    light   = `.SVS item light`(Base, Detail 2, Skin), and its t
    gloss   = max(h * sum(Highlight color) * its alpha * High light power / 3, (1 - Underhair amount) * q * its alpha)
    Color   = clamp(albedo * (light + gloss * min(gloss, max(1 - t, 0)) * L), 0, 1.01)

Matcap is `_shadematcap` at the bake's view normal, its centre; Highlight is `_Detail_mask_01` at
`.SVS skin highlight uv`. Linear colours. Written by hand."""

NAME = '.SVS lif_main_skin_body'
KIND = 'ShaderNodeTree'

LIGHT = ('Ramp 1', 'Ramp 2', 'Shadow setting', 'Shadow setting w', 'Shadow power', 'Shadow extend', 'Shadow color on',
         'Shadow color', 'Light color', 'Ambient')


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Base', 'NodeSocketVector', default_value=(1.0, 0.8, 0.7))
    t.socket('INPUT', 'Color', 'NodeSocketVector', default_value=(1.0, 0.8, 0.7))
    t.socket('INPUT', 'Underhair amount', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    for name in ('Detail 1', 'Highlight', 'Detail 2', 'Matcap', 'Highlight ramp'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Detail 1 alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    item = lib.group('.SVS item light')
    for s in item.interface.items_tree:
        if getattr(s, 'in_out', None) == 'INPUT' and s.name in LIGHT:
            d = s.default_value
            t.socket('INPUT', s.name, s.socket_type, default_value=tuple(d) if hasattr(d, '__len__') else d)
    for name, d in (('Shadow color 2', (0.9, 0.0, 0.0, 1.0)), ('Highlight color', (1.0, 0.8, 0.7, 1.0))):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=d)
        t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Highlight power', 'NodeSocketFloat', default_value=0.5)
    t.socket('INPUT', 'High light power', 'NodeSocketFloat', default_value=1.0)
    t.make('NodeGroupInput', 'in', (-1600, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))
    m = t.math

    def vec(name, op, a, b=None, c=None, location=(0, 0), **extra):
        ins = {k: x for k, x in (('Vector', a), ('Vector_001', b), ('Vector_002', c)) if x is not None}
        ins.update(extra)
        t.make('ShaderNodeVectorMath', name, location, {'operation': op}, ins)
        return (name, 'Value' if op in ('DOT_PRODUCT', 'LENGTH') else 'Vector')

    for row, name in enumerate(('Matcap', 'Highlight', 'Detail 2', 'Highlight ramp')):
        t.make('ShaderNodeSeparateColor', name, (-1400, 700 - row * 200), ins={'Color': ('in', name)})
    s = m('s', 'MULTIPLY_ADD', ('in', 'Shadow power'), 0.35, 0.35, location=(-1400, -200))
    sca = m('sca', 'MULTIPLY', ('in', 'Shadow color 2 alpha'), s, location=(-1250, -200))
    t.make('ShaderNodeMix', 'tint', (-1000, 900), {'data_type': 'VECTOR'},
           {'Factor_Float': m('tint.f', 'MULTIPLY', ('Matcap', 'Blue'), sca, location=(-1150, 950)),
            'A_Vector': (1.0, 1.0, 1.0), 'B_Vector': ('in', 'Shadow color 2')})
    shaded = vec('shaded', 'MULTIPLY', ('in', 'Color'), ('tint', 'Result_Vector'), location=(-800, 900))
    hl_ramp = m('hlr', 'MAXIMUM', m('hlr.1', 'MAXIMUM', ('Detail 2', 'Green'), ('Highlight ramp', 'Green'), location=(-1150, 500)),
                m('hlr.m', 'MULTIPLY', ('Matcap', 'Green'), sca, location=(-1150, 400)), location=(-1000, 450))
    h = m('h', 'MULTIPLY', m('h.p', 'MULTIPLY', m('h.b', 'MULTIPLY', ('Highlight', 'Blue'), 5 / 3, location=(-1000, 650), clamp=True),
          ('in', 'Highlight power'), location=(-850, 650)), m('h.r', 'SUBTRACT', 1.0, hl_ramp, location=(-850, 500)), location=(-700, 600))
    q = m('q', 'MULTIPLY', ('in', 'Detail 1 alpha'), ('Matcap', 'Red'), location=(-1000, 200))
    off_hair = m('off.hair', 'SUBTRACT', 1.0, ('in', 'Underhair amount'), location=(-1000, 100))
    one_q = m('1-q', 'SUBTRACT', 1.0, q, location=(-850, 200))
    mean = vec('mean', 'DOT_PRODUCT', ('in', 'Light color'), (1 / 3, 1 / 3, 1 / 3), location=(-1000, 0))
    mean = m('mean.c', 'ADD', mean, 0.0, location=(-850, 0), clamp=True)
    amount = m('shine.a', 'ADD', m('shine.h', 'MULTIPLY', m('shine.hp', 'MULTIPLY', h, ('in', 'High light power'), location=(-550, 400)),
               one_q, location=(-400, 400)), m('shine.q', 'MULTIPLY', m('shine.q1', 'MULTIPLY', q, one_q, location=(-700, 250)), off_hair,
               location=(-550, 250)), location=(-250, 350))
    amount = m('shine.m', 'MULTIPLY', amount, mean, location=(-100, 350))
    shine = vec('shine', 'SCALE', ('in', 'Highlight color'), location=(50, 400), Scale=amount)
    shine = vec('shine.c', 'MINIMUM', vec('shine.low', 'MAXIMUM', shine, (0.0, 0.0, 0.0), location=(200, 400)), (1.0, 1.0, 1.0),
                location=(350, 400))
    t.make('ShaderNodeCombineXYZ', 'hca.v', (350, 600),
           ins={'X': ('in', 'Highlight color alpha'), 'Y': ('in', 'Highlight color alpha'), 'Z': ('in', 'Highlight color alpha')})
    albedo = vec('albedo', 'MULTIPLY_ADD', shine, ('hca.v', 'Vector'), shaded, location=(550, 700))
    albedo = vec('albedo.c', 'MINIMUM', vec('albedo.low', 'MAXIMUM', albedo, (0.0, 0.0, 0.0), location=(700, 700)), (0.95, 0.95, 0.95),
                 location=(850, 700))
    t.make('ShaderNodeGroup', 'light', (-400, -400), {'node_tree': item, 'width': 220.0},
           {'Color': ('in', 'Base'), 'Detail': ('in', 'Detail 2'), 'Skin': 1.0, **{n: ('in', n) for n in LIGHT}})
    hc_sum = vec('hc.sum', 'DOT_PRODUCT', ('in', 'Highlight color'), (1.0, 1.0, 1.0), location=(-700, -100))
    g1 = m('g1', 'MULTIPLY', m('g1.b', 'MULTIPLY', m('g1.a', 'MULTIPLY', h, hc_sum, location=(-550, -100)), ('in', 'Highlight color alpha'),
           location=(-400, -100)), m('g1.c', 'MULTIPLY', ('in', 'High light power'), 1 / 3, location=(-550, -200)), location=(-250, -100))
    g2 = m('g2', 'MULTIPLY', m('g2.a', 'MULTIPLY', off_hair, q, location=(-550, -300)), ('in', 'Highlight color alpha'), location=(-400, -300))
    gloss = m('gloss', 'MAXIMUM', g1, g2, location=(-100, -150))
    reach = m('reach', 'MAXIMUM', m('reach.t', 'SUBTRACT', 1.0, ('light', 'T'), location=(-100, -400)), 0.0, location=(50, -400))
    spec = m('spec', 'MULTIPLY', gloss, m('spec.min', 'MINIMUM', gloss, reach, location=(200, -300)), location=(350, -300))
    lit = vec('lit', 'ADD', ('light', 'Light'), vec('spec.v', 'SCALE', ('in', 'Light color'), location=(500, -300), Scale=spec),
              location=(650, -200))
    result = vec('result', 'MULTIPLY', albedo, lit, location=(1000, 200))
    result = vec('result.c', 'MINIMUM', vec('result.low', 'MAXIMUM', result, (0.0, 0.0, 0.0), location=(1100, 200)), (1.01, 1.01, 1.01),
                 location=(1200, 200))
    t.link(result[0], result[1], 'out', 'Color')
    return t
