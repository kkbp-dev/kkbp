"""`.SVS lif_main_hair`: SVS's hair shader as the exporter bakes it, at one N.L (models.lif_main_hair,
issue 62).

    col    = mix(Main color, Sub color 2, mask.g * its alpha);  col = mix(col, Sub color 1, mask.b * its alpha)
    col    = mix(col, Add skin color, Detail 2.b * its alpha)
    col    = Ex hair color 2 on ? mix(col, Ex hair color 2, clamp(2 - 2 * smoothstep((mask.a - 0.05) / 0.9)) * its alpha) : col
    col    = clamp(Ex hair color on ? mix(col, Ex hair color, mask.r * its alpha) : col, 0, 0.95)
    t      = clamp(P * max(clamp(max(Ramp 2.b * Shadow power * 0.5, Ramp 1.g) + Detail 1.g), clamp(1 - mean(L))) * lum - 0.75 * (lum - 1))
    P      = mix(0.5 - 0.1 * sum(Ambient') + 0.4 * Shadow power, Shadow power, Shadow color on);  lum = clamp(luminance(L), 1, 99)
    lit    = l5 + (mean(L) - 1) * -0.25 * (luma(l5) - l5) + Ambient' * 0.5,  l5 = L * 0.75 + 0.25
    shadow = mix(overlay(Ambient' * 0.7 + 0.1, clamp(l5) * Shadow color), Shadow color 2, Shadow color on)
    Color  = min(col * mix(lit, shadow, t), 1)

L is Light color, Ambient' the ambient clamped to 0..1; Shadow color is `_Shadow_color`, Shadow
color 2 `_ShadowColor`. Colours are linear. Written by hand."""

NAME = '.SVS lif_main_hair'
KIND = 'ShaderNodeTree'

COLORS = ('Main color', 'Sub color 1', 'Sub color 2', 'Add skin color', 'Ex hair color', 'Ex hair color 2',
          'Shadow color', 'Shadow color 2')


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    for name in ('Color mask', 'Detail 1', 'Detail 2', 'Ramp 1', 'Ramp 2'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Color mask alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for name in COLORS:
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
        if name not in ('Main color', 'Shadow color', 'Shadow color 2'):
            t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for name, d in (('Ex hair color on', 0.0), ('Ex hair color 2 on', 0.0), ('Shadow power', 0.539), ('Shadow color on', 0.0)):
        t.socket('INPUT', name, 'NodeSocketFloat', default_value=d, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.18855378, 0.18145701, 0.1885538, 1.0))
    t.make('NodeGroupInput', 'in', (-2200, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))
    m = t.math

    def vec(name, op, a, b=None, c=None, location=(0, 0)):
        ins = {k: x for k, x in (('Vector', a), ('Vector_001', b), ('Vector_002', c)) if x is not None}
        t.make('ShaderNodeVectorMath', name, location, {'operation': op}, ins)
        return (name, 'Value' if op == 'DOT_PRODUCT' else 'Vector')

    def mix(name, a, b, f, location, clamp=False):
        kind, key = ('RGBA', 'Color') if clamp else ('VECTOR', 'Vector')
        t.make('ShaderNodeMix', name, location, {'data_type': kind, 'clamp_result': clamp},
               {'Factor_Float': f, f'A_{key}': a, f'B_{key}': b})
        return (name, f'Result_{key}')

    for row, name in enumerate(('Color mask', 'Detail 1', 'Detail 2', 'Ramp 1', 'Ramp 2')):
        t.make('ShaderNodeSeparateColor', name, (-2000, 800 - 400 * row), ins={'Color': ('in', name)})
    a = lambda n: ('in', f'{n} alpha')  # noqa: E731
    col = mix('sub2', ('in', 'Main color'), ('in', 'Sub color 2'), m('sub2.f', 'MULTIPLY', ('Color mask', 'Green'), a('Sub color 2'),
              location=(-1800, 800)), (-1600, 800))
    col = mix('sub1', col, ('in', 'Sub color 1'), m('sub1.f', 'MULTIPLY', ('Color mask', 'Blue'), a('Sub color 1'),
              location=(-1800, 650)), (-1450, 700))
    col = mix('skin', col, ('in', 'Add skin color'), m('skin.f', 'MULTIPLY', ('Detail 2', 'Blue'), a('Add skin color'),
              location=(-1800, 500)), (-1300, 600))
    s = m('ex2.x', 'MULTIPLY_ADD', ('in', 'Color mask alpha'), 1 / 0.9, -0.05 / 0.9, location=(-1800, 350), clamp=True)
    t.make('ShaderNodeMapRange', 'ex2.smooth', (-1500, 350), {'interpolation_type': 'SMOOTHSTEP', 'clamp': True},
           {'Value': s, 'From Min': 0.0, 'From Max': 1.0, 'To Min': 0.0, 'To Max': 1.0})
    ex2 = m('ex2.f', 'MULTIPLY', m('ex2.far', 'MULTIPLY_ADD', ('ex2.smooth', 'Result'), -2.0, 2.0, location=(-1350, 350), clamp=True),
            a('Ex hair color 2'), location=(-1200, 350))
    col = mix('ex2', col, ('in', 'Ex hair color 2'), m('ex2.on', 'MULTIPLY', ex2, ('in', 'Ex hair color 2 on'), location=(-1050, 350)),
              (-1000, 550))
    ex = m('ex.f', 'MULTIPLY', m('ex.mask', 'MULTIPLY', ('Color mask', 'Red'), a('Ex hair color'), location=(-1050, 200)),
           ('in', 'Ex hair color on'), location=(-900, 200))
    col = mix('ex', col, ('in', 'Ex hair color'), ex, (-850, 500))
    col = vec('col', 'MINIMUM', vec('col.low', 'MAXIMUM', col, (0.0, 0.0, 0.0), location=(-700, 500)), (0.95, 0.95, 0.95), location=(-550, 500))

    light = ('in', 'Light color')
    sh = vec('sh', 'MINIMUM', vec('sh.low', 'MAXIMUM', ('in', 'Ambient'), (0.0, 0.0, 0.0), location=(-1800, -600)), (1.0, 1.0, 1.0),
             location=(-1650, -600))
    mean = vec('mean', 'DOT_PRODUCT', light, (1 / 3, 1 / 3, 1 / 3), location=(-1800, -300))
    lum = m('lum', 'MINIMUM', m('lum.low', 'MAXIMUM', vec('lum.dot', 'DOT_PRODUCT', light, (0.212672904, 0.715152204, 0.0721750036),
            location=(-1800, -400)), 1.0, location=(-1650, -400)), 99.0, location=(-1500, -400))
    power = ('in', 'Shadow power')
    t.make('ShaderNodeMix', 'P', (-1300, -800), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Shadow color on'), 'B_Float': power,
            'A_Float': m('P.base', 'MULTIPLY_ADD', power, 0.4, m('P.sh', 'MULTIPLY_ADD', vec('sh.sum', 'DOT_PRODUCT', sh, (1.0, 1.0, 1.0),
                         location=(-1500, -800)), -0.1, 0.5, location=(-1400, -900)), location=(-1300, -950))})
    ramp = m('ramp', 'ADD', m('ramp.max', 'MAXIMUM', m('ramp.b', 'MULTIPLY', ('Ramp 2', 'Blue'), m('ramp.p', 'MULTIPLY', power, 0.5,
             location=(-1800, -1100)), location=(-1650, -1100)), ('Ramp 1', 'Green'), location=(-1500, -1100)), ('Detail 1', 'Green'),
             location=(-1350, -1100), clamp=True)
    tt = m('t', 'MULTIPLY', ('P', 'Result_Float'), m('t.x', 'MULTIPLY_ADD', m('t.max', 'MAXIMUM', ramp,
           m('t.dim', 'SUBTRACT', 1.0, mean, location=(-1350, -1250), clamp=True), location=(-1200, -1150)), lum,
           m('t.lift', 'MULTIPLY_ADD', lum, -0.75, 0.75, location=(-1200, -1300)), location=(-1050, -1150)), location=(-900, -1000), clamp=True)

    l5 = vec('l5', 'MULTIPLY_ADD', light, (0.75, 0.75, 0.75), (0.25, 0.25, 0.25), location=(-1500, -100))
    luma = vec('luma', 'DOT_PRODUCT', l5, (0.299, 0.587, 0.114), location=(-1350, -100))
    t.make('ShaderNodeCombineXYZ', 'luma.v', (-1200, -100), ins={'X': luma, 'Y': luma, 'Z': luma})
    desat = mix('desat', l5, ('luma.v', 'Vector'), m('desat.f', 'MULTIPLY_ADD', mean, -0.25, 0.25, location=(-1200, 0)), (-1050, -50))
    lit = vec('lit', 'MULTIPLY_ADD', sh, (0.5, 0.5, 0.5), desat, location=(-900, -50))
    l5c = vec('l5c', 'MINIMUM', vec('l5c.low', 'MAXIMUM', l5, (0.0, 0.0, 0.0), location=(-1350, -250)), (1.0, 1.0, 1.0), location=(-1200, -250))
    t.make('ShaderNodeMix', 'shadow.overlay', (-900, -300), {'data_type': 'RGBA', 'blend_type': 'OVERLAY', 'clamp_result': True},
           {'Factor_Float': 1.0, 'A_Color': vec('shadow.base', 'MULTIPLY_ADD', sh, (0.7, 0.7, 0.7), (0.1, 0.1, 0.1), location=(-1050, -400)),
            'B_Color': vec('shadow.top', 'MULTIPLY', l5c, ('in', 'Shadow color'), location=(-1050, -250))})
    shadow = mix('shadow', ('shadow.overlay', 'Result_Color'), ('in', 'Shadow color 2'), ('in', 'Shadow color on'), (-700, -300))
    mixed = mix('mixed', lit, shadow, tt, (-500, -100))
    result = vec('result', 'MINIMUM', vec('result.col', 'MULTIPLY', col, mixed, location=(-300, 200)), (1.0, 1.0, 1.0), location=(-150, 200))
    t.link(*result, 'out', 'Color')
    return t
