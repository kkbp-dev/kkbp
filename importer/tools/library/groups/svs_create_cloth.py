"""`.SVS create cloth`: SVS's clothes create shader (LIF/lif_create_main_cloth) in nodes
(models.create_main_cloth, issue 62).

    layer k = mix(mix(Main color k, Sub color k * Pattern k, a * Sub alpha), Pattern k, a * vivid * Sub alpha),
              a = on * Pattern k alpha, vivid = clamp(saturation(Pattern k) * 10 - 0.05), on = Mask alpha >= 0.5
    col     = layer 4, then mix in layers 1 to 3 by the mask's red, green and blue
    col     = each paint k over col by its alpha * its colour's alpha * Paint mask's channel k * (Mask alpha >= 1),
              toward the paint times max(min(its alpha, smoothstep(clamp((saturation - 0.3) * 2.5))), Paint color k)
    Color   = col * Main;  Alpha = sqrt(sqrt(the colours' alpha)) * Main alpha

Each texture's alpha is times its `present` switch; a missing main texture reads white. Linear
colours. Written by hand."""

NAME = '.SVS create cloth'
KIND = 'ShaderNodeTree'

TEXTURES = ('Main', 'Mask', 'Pattern 1', 'Pattern 2', 'Pattern 3', 'Pattern 4', 'Paint 1', 'Paint 2', 'Paint 3', 'Paint mask')


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    for name in TEXTURES:
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'{name} present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2, 3, 4):
        for kind in ('Main color', 'Sub color'):
            t.socket('INPUT', f'{kind} {k}', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
            t.socket('INPUT', f'{kind} {k} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2, 3):
        t.socket('INPUT', f'Paint color {k}', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
        t.socket('INPUT', f'Paint color {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-2400, 0))
    t.make('NodeGroupOutput', 'out', (1800, 0))
    m = t.math
    alpha = {n: m(f'{n}.a', 'MULTIPLY', ('in', f'{n} alpha'), ('in', f'{n} present'), location=(-2200, 1500 - i * 120))
             for i, n in enumerate(TEXTURES)}
    t.make('ShaderNodeSeparateColor', 'mask', (-2200, 300), ins={'Color': ('in', 'Mask')})
    on = m('on', 'GREATER_THAN', alpha['Mask'], 0.4999, location=(-2000, 300))
    full = m('full', 'GREATER_THAN', alpha['Mask'], 0.9999, location=(-2000, 200))
    layers = {}
    for k in (1, 2, 3, 4):
        y = 1200 - k * 450
        a = m(f'l{k}.a', 'MULTIPLY', on, alpha[f'Pattern {k}'], location=(-1800, y))
        t.make('ShaderNodeVectorMath', f'l{k}.sub', (-1800, y - 120), {'operation': 'MULTIPLY'},
               {'Vector': ('in', f'Sub color {k}'), 'Vector_001': ('in', f'Pattern {k}')})
        t.make('ShaderNodeMix', f'l{k}.tint', (-1600, y), {'data_type': 'VECTOR'},
               {'Factor_Float': m(f'l{k}.ta', 'MULTIPLY', a, ('in', f'Sub color {k} alpha'), location=(-1700, y + 100)),
                'A_Vector': ('in', f'Main color {k}'), 'B_Vector': (f'l{k}.sub', 'Vector')})
        t.make('ShaderNodeSeparateColor', f'l{k}.hsv', (-1800, y - 250), {'mode': 'HSV'}, {'Color': ('in', f'Pattern {k}')})
        vivid = m(f'l{k}.vivid', 'MULTIPLY', m(f'l{k}.va', 'MULTIPLY', a, m(f'l{k}.sat', 'MULTIPLY_ADD', (f'l{k}.hsv', 'Green'), 10.0, -0.05,
                  location=(-1650, y - 250), clamp=True), location=(-1500, y - 200)), ('in', f'Sub color {k} alpha'), location=(-1400, y - 200))
        t.make('ShaderNodeMix', f'l{k}', (-1300, y), {'data_type': 'VECTOR'},
               {'Factor_Float': vivid, 'A_Vector': (f'l{k}.tint', 'Result_Vector'), 'B_Vector': ('in', f'Pattern {k}')})
        layers[k] = (f'l{k}', 'Result_Vector')
    rgb, a = layers[4], ('in', 'Main color 4 alpha')
    for k, ch in ((1, 'Red'), (2, 'Green'), (3, 'Blue')):
        t.make('ShaderNodeMix', f'c{k}', (-1000 + k * 150, 600), {'data_type': 'VECTOR'},
               {'Factor_Float': ('mask', ch), 'A_Vector': rgb, 'B_Vector': layers[k]})
        t.make('ShaderNodeMix', f'a{k}', (-1000 + k * 150, 300), {'data_type': 'FLOAT'},
               {'Factor_Float': ('mask', ch), 'A_Float': a, 'B_Float': ('in', f'Main color {k} alpha')})
        rgb, a = (f'c{k}', 'Result_Vector'), (f'a{k}', 'Result_Float')
    t.make('ShaderNodeSeparateColor', 'paint mask', (-600, -600), ins={'Color': ('in', 'Paint mask')})
    for k, ch in ((1, 'Red'), (2, 'Green'), (3, 'Blue')):
        y = -200 - k * 400
        t.make('ShaderNodeSeparateColor', f'p{k}.hsv', (-400, y), {'mode': 'HSV'}, {'Color': ('in', f'Paint {k}')})
        t.make('ShaderNodeMapRange', f'p{k}.smooth', (-250, y), {'interpolation_type': 'SMOOTHSTEP', 'clamp': True},
               {'Value': (f'p{k}.hsv', 'Green'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': 0.0, 'To Max': 1.0})
        f = m(f'p{k}.f', 'MINIMUM', alpha[f'Paint {k}'], (f'p{k}.smooth', 'Result'), location=(-100, y))
        t.make('ShaderNodeCombineXYZ', f'p{k}.fv', (50, y), ins={'X': f, 'Y': f, 'Z': f})
        t.make('ShaderNodeVectorMath', f'p{k}.tint', (200, y), {'operation': 'MAXIMUM'},
               {'Vector': (f'p{k}.fv', 'Vector'), 'Vector_001': ('in', f'Paint color {k}')})
        t.make('ShaderNodeVectorMath', f'p{k}.col', (350, y), {'operation': 'MULTIPLY'},
               {'Vector': ('in', f'Paint {k}'), 'Vector_001': (f'p{k}.tint', 'Vector')})
        amount = m(f'p{k}.amount', 'MULTIPLY', m(f'p{k}.am1', 'MULTIPLY', m(f'p{k}.am0', 'MULTIPLY', alpha[f'Paint {k}'],
                   ('in', f'Paint color {k} alpha'), location=(200, y - 150)), ('paint mask', ch), location=(350, y - 150)), full,
                   location=(500, y - 150))
        t.make('ShaderNodeMix', f'paint{k}', (650, y), {'data_type': 'VECTOR'},
               {'Factor_Float': amount, 'A_Vector': rgb, 'B_Vector': (f'p{k}.col', 'Vector')})
        rgb = (f'paint{k}', 'Result_Vector')
    t.make('ShaderNodeMix', 'main', (900, 200), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Main present'), 'A_Color': (1.0, 1.0, 1.0, 1.0), 'B_Color': ('in', 'Main')})
    t.make('ShaderNodeVectorMath', 'color', (1100, 100), {'operation': 'MULTIPLY'}, {'Vector': rgb, 'Vector_001': ('main', 'Result_Color')})
    t.link('color', 'Vector', 'out', 'Color')
    main_a = m('main.a', 'MULTIPLY_ADD', m('main.a.d', 'SUBTRACT', ('in', 'Main alpha'), 1.0, location=(900, -100)),
               ('in', 'Main present'), 1.0, location=(1050, -100))
    t.link(*m('alpha', 'MULTIPLY', m('alpha.root', 'POWER', a, 0.25, location=(1050, -250)), main_a, location=(1200, -200)), 'out', 'Alpha')
    return t
