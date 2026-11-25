"""`.SVS lif_main_skin_head`: SVS's face shader as the exporter bakes it, at one N.L
(models.lif_main_skin_head).

    albedo = clamp(Color * mix(1, Shadow color 2, Matcap.b * Shadow color 2 alpha * (1 - Detail 2.b) * (Shadow power * 0.35 + 0.35)), 0, 0.95)
    Color  = clamp(albedo * `.SVS item light`(Base, Detail, Skin), 0, 1.01)

Matcap is `_shadematcap` at the bake's view normal, its centre; Detail comes from `.SVS face ramp uv`.
Linear colours. Written by hand."""

NAME = '.SVS lif_main_skin_head'
KIND = 'ShaderNodeTree'

LIGHT = ('Detail', 'Ramp 1', 'Ramp 2', 'Shadow setting', 'Shadow setting w', 'Shadow power', 'Shadow extend', 'Shadow color on',
         'Shadow color', 'Light color', 'Ambient')


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Base', 'NodeSocketVector', default_value=(1.0, 0.8, 0.7))
    t.socket('INPUT', 'Color', 'NodeSocketVector', default_value=(1.0, 0.8, 0.7))
    t.socket('INPUT', 'Detail 2', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Matcap', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    item = lib.group('.SVS item light')
    for s in item.interface.items_tree:
        if getattr(s, 'in_out', None) == 'INPUT' and s.name in LIGHT:
            d = s.default_value
            t.socket('INPUT', s.name, s.socket_type, default_value=tuple(d) if hasattr(d, '__len__') else d)
    t.socket('INPUT', 'Shadow color 2', 'NodeSocketColor', default_value=(0.9, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Shadow color 2 alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (800, 0))
    m = t.math
    t.make('ShaderNodeSeparateColor', 'matcap', (-1000, 500), ins={'Color': ('in', 'Matcap')})
    t.make('ShaderNodeSeparateColor', 'detail2', (-1000, 300), ins={'Color': ('in', 'Detail 2')})
    amount = m('amount', 'MULTIPLY', m('amount.3', 'MULTIPLY', m('amount.2', 'MULTIPLY', ('matcap', 'Blue'), ('in', 'Shadow color 2 alpha'),
               location=(-850, 500)), m('amount.d', 'SUBTRACT', 1.0, ('detail2', 'Blue'), location=(-850, 350)), location=(-700, 450)),
               m('amount.s', 'MULTIPLY_ADD', ('in', 'Shadow power'), 0.35, 0.35, location=(-850, 250)), location=(-550, 400))
    t.make('ShaderNodeMix', 'tint', (-400, 400), {'data_type': 'VECTOR'},
           {'Factor_Float': amount, 'A_Vector': (1.0, 1.0, 1.0), 'B_Vector': ('in', 'Shadow color 2')})
    t.make('ShaderNodeVectorMath', 'shaded', (-200, 400), {'operation': 'MULTIPLY'}, {'Vector': ('in', 'Color'), 'Vector_001': ('tint', 'Result_Vector')})
    t.make('ShaderNodeVectorMath', 'albedo', (-50, 400), {'operation': 'MINIMUM'}, {'Vector': ('shaded', 'Vector'), 'Vector_001': (0.95, 0.95, 0.95)})
    t.make('ShaderNodeGroup', 'light', (-400, -200), {'node_tree': item, 'width': 220.0},
           {'Color': ('in', 'Base'), 'Skin': 1.0, **{n: ('in', n) for n in LIGHT}})
    t.make('ShaderNodeVectorMath', 'lit', (200, 200), {'operation': 'MULTIPLY'}, {'Vector': ('albedo', 'Vector'), 'Vector_001': ('light', 'Light')})
    t.make('ShaderNodeVectorMath', 'lit.max', (350, 200), {'operation': 'MINIMUM'}, {'Vector': ('lit', 'Vector'), 'Vector_001': (1.01, 1.01, 1.01)})
    t.make('ShaderNodeVectorMath', 'lit.low', (500, 200), {'operation': 'MAXIMUM'}, {'Vector': ('lit.max', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    t.link('lit.low', 'Vector', 'out', 'Color')
    return t
