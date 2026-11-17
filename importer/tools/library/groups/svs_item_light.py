"""`.SVS item light`: the light SVS's item shaders (accessories, teeth, tongue) give a colour, at one N.L
(models.svs_item_light, issue 62).

    ramp   = clamp(max(Ramp 1.g * SS.x, Ramp 2.b * Shadow power * SS.y) + Detail.g * SS.w)
    t      = clamp(P * (max(ramp, clamp(1 - mean(L))) * lum - 0.75 * (lum - 1))) + clamp(Detail.g * Shadow extend)
    tint   = Type select 3 (skin face) ? (0.357, 0.057, 0.039) : the colour's hue at saturation clamp(2 - 2v + sqrt(s), 0, 0.9)
             and value 0.99 v sqrt(1 - s), toward (0.095, 0.413, 1) by clamp(clamp(blue * 10 - 7.5) + 1 - sqrt(s))
    shadow = mix(overlay(Ambient' * 0.7 + 0.1, clamp(l5) * tint), Shadow color, Shadow color on)
    Light  = mix(l5 + (mean(L) - 1) * -0.25 * (luma(l5) - l5) + Ambient' * 0.5, shadow, t)

SS is Shadow setting (`_ShadowSetting`, its w apart), P and lum as `.SVS lif_main_hair`'s, blue the
colour's dot with (0.064, 0.257, 0.964). Color is the colour times 0.95. Linear colours. Written by
hand."""

NAME = '.SVS item light'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketVector')
    t.socket('INPUT', 'Color', 'NodeSocketVector', default_value=(0.5, 0.5, 0.5))
    for name in ('Detail', 'Ramp 1', 'Ramp 2'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Shadow setting', 'NodeSocketVector', default_value=(1.0, 0.0, 0.0))
    t.socket('INPUT', 'Shadow setting w', 'NodeSocketFloat', default_value=0.0)
    for name, d in (('Shadow power', 1.0), ('Shadow extend', 0.0), ('Shadow color on', 0.0)):
        t.socket('INPUT', name, 'NodeSocketFloat', default_value=d, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Type select', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=3.0)
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=(0.18, 0.29, 0.51, 1.0))
    t.socket('INPUT', 'Light color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.18855378, 0.18145701, 0.1885538, 1.0))
    t.make('NodeGroupInput', 'in', (-2000, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))
    m = t.math

    def vec(name, op, a, b=None, c=None, location=(0, 0)):
        ins = {k: x for k, x in (('Vector', a), ('Vector_001', b), ('Vector_002', c)) if x is not None}
        t.make('ShaderNodeVectorMath', name, location, {'operation': op}, ins)
        return (name, 'Value' if op == 'DOT_PRODUCT' else 'Vector')

    for row, name in enumerate(('Detail', 'Ramp 1', 'Ramp 2')):
        t.make('ShaderNodeSeparateColor', name, (-1800, 800 - row * 200), ins={'Color': ('in', name)})
    t.make('ShaderNodeSeparateXYZ', 'ss', (-1800, 200), ins={'Vector': ('in', 'Shadow setting')})
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
    d = ('Detail', 'Green')
    ramp = m('ramp', 'MULTIPLY_ADD', d, ('in', 'Shadow setting w'), m('ramp.max', 'MAXIMUM',
             m('ramp.1', 'MULTIPLY', ('Ramp 1', 'Green'), ('ss', 'X'), location=(-1650, 900)),
             m('ramp.2', 'MULTIPLY', m('ramp.2p', 'MULTIPLY', ('Ramp 2', 'Blue'), power, location=(-1650, 750)), ('ss', 'Y'),
               location=(-1500, 750)), location=(-1350, 850)), location=(-1200, 850), clamp=True)
    tt = m('t', 'MULTIPLY', ('P', 'Result_Float'), m('t.x', 'MULTIPLY_ADD', m('t.max', 'MAXIMUM', ramp,
           m('t.dim', 'SUBTRACT', 1.0, mean, location=(-1200, 700), clamp=True), location=(-1050, 750)), lum,
           m('t.lift', 'MULTIPLY_ADD', lum, -0.75, 0.75, location=(-1050, 600)), location=(-900, 700)), location=(-750, 700), clamp=True)
    tt = m('t.extend', 'ADD', tt, m('extend', 'MULTIPLY', d, ('in', 'Shadow extend'), location=(-750, 550), clamp=True),
           location=(-600, 650))

    # The shadow tint.
    t.make('ShaderNodeSeparateColor', 'hsv', (-1500, 300), {'mode': 'HSV'}, {'Color': ('in', 'Color')})
    root = m('root', 'SQRT', ('hsv', 'Green'), location=(-1350, 250))
    sat = m('sat', 'ADD', m('sat.v', 'MULTIPLY_ADD', ('hsv', 'Blue'), -2.0, 2.0, location=(-1200, 350)), root, location=(-1050, 350))
    sat = m('sat.clamp', 'MINIMUM', m('sat.low', 'MAXIMUM', sat, 0.0, location=(-900, 350)), 0.9, location=(-750, 350))
    value = m('value', 'MULTIPLY', m('value.s', 'MULTIPLY', m('value.root', 'SQRT', m('value.1-s', 'SUBTRACT', 1.0, ('hsv', 'Green'),
              location=(-1200, 200)), location=(-1050, 200)), ('hsv', 'Blue'), location=(-900, 200)), 0.99, location=(-750, 200))
    t.make('ShaderNodeCombineColor', 'tint.hsv', (-600, 300), {'mode': 'HSV'}, {'Red': ('hsv', 'Red'), 'Green': sat, 'Blue': value})
    blue = m('blue', 'ADD', m('blue.c', 'MULTIPLY_ADD', vec('blue.dot', 'DOT_PRODUCT', ('in', 'Color'), (0.0642824322, 0.257129729, 0.964236498),
             location=(-1350, 0)), 10.0, -7.5, location=(-1200, 0), clamp=True), m('blue.dull', 'SUBTRACT', 1.0, root, location=(-1200, -100)),
             location=(-1050, -50), clamp=True)
    t.make('ShaderNodeMix', 'tint.blue', (-450, 200), {'data_type': 'RGBA'},
           {'Factor_Float': blue, 'A_Color': ('tint.hsv', 'Color'), 'B_Color': (0.0953074992, 0.413035095, 1.0, 1.0)})
    t.make('ShaderNodeMix', 'tint', (-300, 200), {'data_type': 'RGBA'},
           {'Factor_Float': m('skin.face', 'COMPARE', ('in', 'Type select'), 3.0, 0.5, location=(-450, 50)), 'A_Color': ('tint.blue', 'Result_Color'),
            'B_Color': (0.357276797, 0.0573572218, 0.0388724506, 1.0)})
    l5 = vec('l5', 'MULTIPLY_ADD', light, (0.75, 0.75, 0.75), (0.25, 0.25, 0.25), location=(-1500, -100))
    l5c = vec('l5c', 'MINIMUM', vec('l5c.low', 'MAXIMUM', l5, (0.0, 0.0, 0.0), location=(-1350, -250)), (1.0, 1.0, 1.0), location=(-1200, -250))
    t.make('ShaderNodeMix', 'shadow.overlay', (-100, -200), {'data_type': 'RGBA', 'blend_type': 'OVERLAY', 'clamp_result': True},
           {'Factor_Float': 1.0, 'A_Color': vec('shadow.base', 'MULTIPLY_ADD', sh, (0.7, 0.7, 0.7), (0.1, 0.1, 0.1), location=(-300, -400)),
            'B_Color': vec('shadow.top', 'MULTIPLY', l5c, ('tint', 'Result_Color'), location=(-250, -200))})
    t.make('ShaderNodeMix', 'shadow', (100, -200), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Shadow color on'), 'A_Vector': ('shadow.overlay', 'Result_Color'), 'B_Vector': ('in', 'Shadow color')})
    luma = vec('luma', 'DOT_PRODUCT', l5, (0.299, 0.587, 0.114), location=(-1350, -100))
    t.make('ShaderNodeCombineXYZ', 'luma.v', (-1200, -100), ins={'X': luma, 'Y': luma, 'Z': luma})
    t.make('ShaderNodeMix', 'desat', (-1050, -50), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': m('desat.f', 'MULTIPLY_ADD', mean, -0.25, 0.25, location=(-1200, 50)), 'A_Vector': l5, 'B_Vector': ('luma.v', 'Vector')})
    lit = vec('lit', 'MULTIPLY_ADD', sh, (0.5, 0.5, 0.5), ('desat', 'Result_Vector'), location=(-900, -50))
    t.make('ShaderNodeMix', 'light', (400, 0), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': tt, 'A_Vector': lit, 'B_Vector': ('shadow', 'Result_Vector')})
    t.link('light', 'Result_Vector', 'out', 'Light')
    return t
