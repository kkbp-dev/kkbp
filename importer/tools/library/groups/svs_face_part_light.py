"""`.SVS face part light`: the light SVS's eyebrow and eyelash shaders multiply their colour by, as the
exporter bakes them (models.svs_face_part_light, issue 62): unshadowed, no additional lights.

    l5     = Light color * 0.75 + 0.25
    lit    = clamp(Ambient' * 0.5 + mix(l5, luma(l5), (1 - mean(Light color)) * 0.1))
    tint   = HSV(hue, sqrt(saturation) of (Color + K) * K, value of Color * K),  K = (0.687, 0.798, 1)
    shadow = min(overlay(Ambient' * 0.6 + 0.3, clamp(l5) * tint) + Ambient' * 0.1, 1)
    t      = min(max(clamp(1 - mean(L)), P * ((1 - N.L) * o - 0.5 * (o - 1))), 1),  o = clamp(mean(L), 1, 99)
    P      = mix(0.75 - 0.65 * a, 0.9 - 0.4 * a, Shadow power),  a = min(mean(max(Ambient, 0)), 1)
    Light  = mix(lit, shadow, t) + clamp(Light color - 1, 0, 99) * (1 - clamp((0.2 - N.L) / 0.15))

Ambient' is Ambient clamped to 0..1: the light probe at the bake quad's normal. Linear colours.
Written by hand."""

NAME = '.SVS face part light'
KIND = 'ShaderNodeTree'

K = (0.686577916, 0.797912478, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketVector')
    t.socket('INPUT', 'Color', 'NodeSocketVector', default_value=(1.0, 1.0, 1.0))
    t.socket('INPUT', 'Shadow power', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light color', 'NodeSocketVector', default_value=(1.0, 1.0, 1.0))
    t.socket('INPUT', 'N.L', 'NodeSocketFloat', default_value=0.828421950340271, min_value=-1.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketVector', default_value=(0.18855378, 0.18145701, 0.1885538))
    t.make('NodeGroupInput', 'in', (-1600, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))

    def vmath(name, op, a, b=None, c=None, location=(0, 0), scale=None):
        ins = {k: v for k, v in (('Vector', a), ('Vector_001', b), ('Vector_002', c)) if v is not None}
        if scale is not None:
            ins['Scale'] = scale
        t.make('ShaderNodeVectorMath', name, location, {'operation': op}, ins)
        return (name, 'Vector' if op not in ('DOT_PRODUCT', 'LENGTH') else 'Value')

    def clamp01(name, v, location):
        return vmath(name, 'MINIMUM', vmath(f'{name}.low', 'MAXIMUM', v, (0.0, 0.0, 0.0), location=location),
                     (1.0, 1.0, 1.0), location=(location[0] + 160, location[1]))

    light = ('in', 'Light color')
    sh = clamp01('ambient', ('in', 'Ambient'), (-1400, -600))
    mean = vmath('light.mean', 'DOT_PRODUCT', light, (1 / 3, 1 / 3, 1 / 3), location=(-1400, 500))
    l5 = vmath('l5', 'MULTIPLY_ADD', light, (0.75, 0.75, 0.75), (0.25, 0.25, 0.25), location=(-1400, 300))
    luma = vmath('luma', 'DOT_PRODUCT', l5, (0.299, 0.587, 0.114), location=(-1200, 300))
    t.make('ShaderNodeCombineXYZ', 'luma.rgb', (-1050, 300), ins={'X': luma, 'Y': luma, 'Z': luma})
    k = t.math('desaturate', 'MULTIPLY', t.math('desaturate.mean', 'SUBTRACT', 1.0, mean, location=(-1200, 500)), 0.1,
               location=(-1050, 500))
    t.make('ShaderNodeMix', 'light.desaturated', (-900, 350), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': k, 'A_Vector': l5, 'B_Vector': ('luma.rgb', 'Vector')})
    lit = clamp01('lit', vmath('lit.sum', 'MULTIPLY_ADD', sh, (0.5, 0.5, 0.5), ('light.desaturated', 'Result_Vector'),
                               location=(-700, 350)), (-550, 350))

    # The shadow colour: hue and saturation of (Color + K) * K, at the value of Color * K.
    shifted = vmath('tint.shifted', 'MULTIPLY', vmath('tint.add', 'ADD', ('in', 'Color'), K, location=(-1400, 0)), K,
                    location=(-1250, 0))
    scaled = vmath('tint.scaled', 'MULTIPLY', ('in', 'Color'), K, location=(-1250, -150))
    t.make('ShaderNodeSeparateColor', 'tint.hs', (-1100, 0), {'mode': 'HSV'}, {'Color': shifted})
    t.make('ShaderNodeSeparateColor', 'tint.v', (-1100, -150), {'mode': 'HSV'}, {'Color': scaled})
    root = t.math('tint.saturation', 'SQRT', ('tint.hs', 'Green'), location=(-950, 0))
    t.make('ShaderNodeCombineColor', 'tint', (-800, -50), {'mode': 'HSV'},
           {'Red': ('tint.hs', 'Red'), 'Green': root, 'Blue': ('tint.v', 'Blue')})
    lifted = vmath('shadow.lit', 'MULTIPLY', clamp01('l5.clamp', l5, (-1100, -350)), ('tint', 'Color'), location=(-650, -100))
    base = vmath('shadow.base', 'MULTIPLY_ADD', sh, (0.6, 0.6, 0.6), (0.3, 0.3, 0.3), location=(-650, -300))
    t.make('ShaderNodeMix', 'shadow.overlay', (-450, -200),
           {'data_type': 'RGBA', 'blend_type': 'OVERLAY', 'clamp_result': True},
           {'Factor_Float': 1.0, 'A_Color': base, 'B_Color': lifted})
    shadow = vmath('shadow', 'MINIMUM', vmath('shadow.sum', 'MULTIPLY_ADD', sh, (0.1, 0.1, 0.1), ('shadow.overlay', 'Result_Color'),
                                              location=(-250, -200)), (1.0, 1.0, 1.0), location=(-100, -200))

    # How far into the shadow colour: P * (1 - N.L), past what light over 1 lifts.
    over = t.math('over', 'MINIMUM', t.math('over.low', 'MAXIMUM', mean, 1.0, location=(-1050, 700)), 99.0, location=(-900, 700))
    turned = t.math('turned', 'MULTIPLY_ADD', t.math('turned.base', 'SUBTRACT', 1.0, ('in', 'N.L'), location=(-900, 850)), over,
                    t.math('turned.lift', 'MULTIPLY_ADD', over, -0.5, 0.5, location=(-750, 700)), location=(-600, 800))
    amb = t.math('ambient.mean', 'MINIMUM', vmath('ambient.dot', 'DOT_PRODUCT', vmath('ambient.pos', 'MAXIMUM', ('in', 'Ambient'),
                 (0.0, 0.0, 0.0), location=(-1250, -800)), (1 / 3, 1 / 3, 1 / 3), location=(-1100, -800)), 1.0, location=(-950, -800))
    p = t.make('ShaderNodeMix', 'power', (-750, -800), {'data_type': 'FLOAT', 'clamp_factor': False},
               {'Factor_Float': ('in', 'Shadow power'),
                'A_Float': t.math('power.low', 'MULTIPLY_ADD', amb, -0.65, 0.75, location=(-900, -700)),
                'B_Float': t.math('power.high', 'MULTIPLY_ADD', amb, -0.4, 0.9, location=(-900, -900))})
    floor = t.math('dim', 'SUBTRACT', 1.0, mean, location=(-600, 600), clamp=True)
    amount = t.math('amount', 'MINIMUM', t.math('amount.max', 'MAXIMUM', floor,
                    t.math('amount.p', 'MULTIPLY', (p, 'Result_Float'), turned, location=(-450, 750)), location=(-300, 700)),
                    1.0, location=(-150, 700))
    t.make('ShaderNodeMix', 'mixed', (100, 200), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': amount, 'A_Vector': lit, 'B_Vector': shadow})

    back = t.math('back', 'MULTIPLY', t.math('back.span', 'SUBTRACT', 0.2, ('in', 'N.L'), location=(-150, 1000)), 1 / 0.15,
                  location=(0, 1000), clamp=True)
    front = t.math('front', 'SUBTRACT', 1.0, back, location=(150, 1000))
    excess = vmath('excess', 'MINIMUM', vmath('excess.low', 'MAXIMUM', vmath('excess.over', 'SUBTRACT', light, (1.0, 1.0, 1.0),
                   location=(150, 800)), (0.0, 0.0, 0.0), location=(300, 800)), (99.0, 99.0, 99.0), location=(450, 800))
    total = vmath('total', 'MULTIPLY_ADD', excess, (0.0, 0.0, 0.0), ('mixed', 'Result_Vector'), location=(800, 300))
    t.make('ShaderNodeCombineXYZ', 'front.rgb', (450, 1000), ins={'X': front, 'Y': front, 'Z': front})
    t.link('front.rgb', 'Vector', 'total', 'Vector_001')
    t.link(*total, 'out', 'Light')
    return t
