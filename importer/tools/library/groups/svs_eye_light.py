"""`.SVS eye light`: one pass of SVS's eye shader lit, and the layer the exporter bakes from it
(models.lif_main_eye and pupil_layer, issue 62, ADR 0034), from `.SVS eye layers`.

    lit(x, cap) = min(x * `.SVS face part light`(x, cap), 1)
    eye     = lit(White * A + B, Cap);  white = lit(White, 1)
    cover   = 1 - clamp(mean((lit(A + B, Cap) - lit(B, Cap)) / lit(1, 1)))
    Color   = Eye white only ? white : (cover > 0 ? clamp((eye - (1 - cover) * white) / cover) : white)
    Coverage = Eye white only ? 1 : cover

The eye's light, as the exporter measures it: lit over its eye white set black and white. Linear
colours. Written by hand."""

NAME = '.SVS eye light'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('OUTPUT', 'Coverage', 'NodeSocketFloat')
    t.socket('INPUT', 'White', 'NodeSocketVector', default_value=(1.0, 1.0, 1.0))
    t.socket('INPUT', 'A', 'NodeSocketFloat', default_value=1.0)
    t.socket('INPUT', 'B', 'NodeSocketVector', default_value=(0.0, 0.0, 0.0))
    t.socket('INPUT', 'Cap', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Eye white only', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Shadow power', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light color', 'NodeSocketVector', default_value=(1.0, 1.0, 1.0))
    t.socket('INPUT', 'N.L', 'NodeSocketFloat', default_value=0.828421950340271, min_value=-1.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketVector', default_value=(0.18855378, 0.18145701, 0.1885538))
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))

    t.make('ShaderNodeCombineXYZ', 'A.v', (-1200, 300), ins={'X': ('in', 'A'), 'Y': ('in', 'A'), 'Z': ('in', 'A')})
    t.make('ShaderNodeVectorMath', 'over.white', (-1000, 400), {'operation': 'MULTIPLY_ADD'},
           {'Vector': ('in', 'White'), 'Vector_001': ('A.v', 'Vector'), 'Vector_002': ('in', 'B')})
    t.make('ShaderNodeVectorMath', 'over.one', (-1000, 200), {'operation': 'ADD'},
           {'Vector': ('A.v', 'Vector'), 'Vector_001': ('in', 'B')})
    cases = (('eye', ('over.white', 'Vector'), ('in', 'Cap')), ('white', ('in', 'White'), 1.0),
             ('one', ('over.one', 'Vector'), ('in', 'Cap')), ('zero', ('in', 'B'), ('in', 'Cap')), ('lit', (1.0, 1.0, 1.0), 1.0))
    for row, (name, x, cap) in enumerate(cases):
        y = 600 - row * 300
        ins = {'Color': x, 'Cap': cap, 'Shadow power': ('in', 'Shadow power'), 'Light color': ('in', 'Light color'),
               'N.L': ('in', 'N.L'), 'Ambient': ('in', 'Ambient')}
        t.make('ShaderNodeGroup', f'{name}.light', (-700, y), {'node_tree': lib.group('.SVS face part light'), 'width': 200.0}, ins)
        t.make('ShaderNodeVectorMath', f'{name}.times', (-450, y), {'operation': 'MULTIPLY'},
               {'Vector': x, 'Vector_001': (f'{name}.light', 'Light')})
        t.make('ShaderNodeVectorMath', name, (-300, y), {'operation': 'MINIMUM'},
               {'Vector': (f'{name}.times', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'uncovered.d', (-100, 0), {'operation': 'SUBTRACT'},
           {'Vector': ('one', 'Vector'), 'Vector_001': ('zero', 'Vector')})
    t.make('ShaderNodeVectorMath', 'uncovered', (50, 0), {'operation': 'DIVIDE'},
           {'Vector': ('uncovered.d', 'Vector'), 'Vector_001': ('lit', 'Vector')})
    t.make('ShaderNodeVectorMath', 'uncovered.mean', (200, 0), {'operation': 'DOT_PRODUCT'},
           {'Vector': ('uncovered', 'Vector'), 'Vector_001': (1 / 3, 1 / 3, 1 / 3)})
    cover = t.math('cover', 'SUBTRACT', 1.0, t.math('cover.clamp', 'ADD', ('uncovered.mean', 'Value'), 0.0, location=(350, 0),
                   clamp=True), location=(500, 0))
    t.make('ShaderNodeVectorMath', 'under', (500, 300), {'operation': 'SCALE'},
           {'Vector': ('white', 'Vector'), 'Scale': t.math('cover.not', 'SUBTRACT', 1.0, cover, location=(350, 200))})
    t.make('ShaderNodeVectorMath', 'layer.d', (650, 400), {'operation': 'SUBTRACT'},
           {'Vector': ('eye', 'Vector'), 'Vector_001': ('under', 'Vector')})
    t.make('ShaderNodeVectorMath', 'layer', (800, 400), {'operation': 'SCALE'},
           {'Vector': ('layer.d', 'Vector'),
            'Scale': t.math('cover.inv', 'DIVIDE', 1.0, t.math('cover.floor', 'MAXIMUM', cover, 1e-6, location=(650, 150)),
                            location=(800, 150))})
    t.make('ShaderNodeMix', 'layer.clamp', (950, 400), {'data_type': 'RGBA', 'clamp_result': True},
           {'Factor_Float': 0.0, 'A_Color': ('layer', 'Vector')})
    shown = t.math('shown', 'GREATER_THAN', cover, 0.0, location=(950, 150))
    t.make('ShaderNodeMix', 'pupil', (1100, 300), {'data_type': 'RGBA'},
           {'Factor_Float': shown, 'A_Color': ('white', 'Vector'), 'B_Color': ('layer.clamp', 'Result_Color')})
    t.make('ShaderNodeMix', 'color', (1250, 300), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Eye white only'), 'A_Color': ('pupil', 'Result_Color'), 'B_Color': ('white', 'Vector')})
    t.make('ShaderNodeMix', 'coverage', (1250, 0), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Eye white only'), 'A_Float': cover, 'B_Float': 1.0})
    t.link('color', 'Result_Color', 'out', 'Color')
    t.link('coverage', 'Result_Float', 'out', 'Coverage')
    return t
