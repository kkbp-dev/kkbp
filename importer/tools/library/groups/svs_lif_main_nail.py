"""`.SVS lif_main_nail`: SVS's nail shader as the exporter bakes it, at one N.L (models.lif_main_nail,
issue 62).

    g     = clamp(Gloss power, 0, 10)
    c     = clamp(mix(Color, 1 - (1 - Matcap) * (1 - Color), g), 0, 0.95)
    light = `.SVS item light`(Color, Skin), and its t
    gloss = Matcap.r * Gloss power
    Color = clamp(c * (light + gloss * min(gloss, max(1 - t, 0)) * Light color), 0, 1.01)

Matcap is `_Mat_cap` at the bake quad's view normal, its centre. Linear colours. Written by hand."""

NAME = '.SVS lif_main_nail'
KIND = 'ShaderNodeTree'

LIGHT = ('Ramp 1', 'Ramp 2', 'Shadow setting', 'Shadow setting w', 'Shadow power', 'Shadow color on', 'Shadow color',
         'Light color', 'Ambient')


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Matcap', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Gloss power', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=10.0)
    item = lib.group('.SVS item light')
    for s in item.interface.items_tree:
        if getattr(s, 'in_out', None) == 'INPUT' and s.name in LIGHT:
            d = s.default_value
            t.socket('INPUT', s.name, s.socket_type, default_value=tuple(d) if hasattr(d, '__len__') else d)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (1000, 0))
    m = t.math
    t.make('ShaderNodeGroup', 'light', (-800, -300), {'node_tree': item, 'width': 220.0},
           {'Color': ('in', 'Color'), 'Skin': 1.0, **{n: ('in', n) for n in LIGHT}})
    g = m('g', 'MINIMUM', m('g.low', 'MAXIMUM', ('in', 'Gloss power'), 0.0, location=(-1000, 500)), 10.0, location=(-850, 500))
    t.make('ShaderNodeMix', 'screen', (-800, 300), {'data_type': 'RGBA', 'blend_type': 'SCREEN'},
           {'Factor_Float': 1.0, 'A_Color': ('in', 'Color'), 'B_Color': ('in', 'Matcap')})
    t.make('ShaderNodeMix', 'glossed', (-600, 300), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': g, 'A_Vector': ('in', 'Color'), 'B_Vector': ('screen', 'Result_Color')})
    t.make('ShaderNodeVectorMath', 'c', (-400, 300), {'operation': 'MINIMUM'},
           {'Vector': ('glossed', 'Result_Vector'), 'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeVectorMath', 'c.low', (-250, 300), {'operation': 'MAXIMUM'}, {'Vector': ('c', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    t.make('ShaderNodeSeparateColor', 'matcap', (-1000, 100), ins={'Color': ('in', 'Matcap')})
    gloss = m('gloss', 'MULTIPLY', ('matcap', 'Red'), ('in', 'Gloss power'), location=(-800, 0))
    reach = m('reach', 'MAXIMUM', m('reach.t', 'SUBTRACT', 1.0, ('light', 'T'), location=(-500, -100)), 0.0, location=(-350, -100))
    amount = m('spec', 'MULTIPLY', gloss, m('spec.min', 'MINIMUM', gloss, reach, location=(-200, -100)), location=(-50, -100))
    t.make('ShaderNodeVectorMath', 'spec.v', (100, -150), {'operation': 'SCALE'}, {'Vector': ('in', 'Light color'), 'Scale': amount})
    t.make('ShaderNodeVectorMath', 'lit', (250, -150), {'operation': 'ADD'}, {'Vector': ('light', 'Light'), 'Vector_001': ('spec.v', 'Vector')})
    t.make('ShaderNodeVectorMath', 'out.c', (450, 100), {'operation': 'MULTIPLY'}, {'Vector': ('c.low', 'Vector'), 'Vector_001': ('lit', 'Vector')})
    t.make('ShaderNodeVectorMath', 'out.max', (600, 100), {'operation': 'MINIMUM'}, {'Vector': ('out.c', 'Vector'), 'Vector_001': (1.01, 1.01, 1.01)})
    t.make('ShaderNodeVectorMath', 'out.low', (750, 100), {'operation': 'MAXIMUM'}, {'Vector': ('out.max', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    t.link('out.low', 'Vector', 'out', 'Color')
    return t
