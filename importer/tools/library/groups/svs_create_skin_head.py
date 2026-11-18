"""`.SVS create skin head`: SVS's face create shader (LIF/lif_create_main_skin_head) in nodes
(models.create_main_skin_head, issue 62).

    base  = mix(Main color, Mouth color, Skin mask.r) * (Facetype present ? Facetype : white)
    col   = each paint k over base, as `.SVS create skin body`'s (no mask), then mix(col, Mole color, Mole.r * its alpha)
    col   = base + Paint mask.rgb * (col - base)
    Color = mix(col, Eyeshadow color, Eyeshadow.r * Eyeshadow color alpha * Eyeshadow)

Eyeshadow (1) is 0 for the face's bakes without eyeshadow (ADR 0046). Linear colours. Written by hand."""

from svs_paints import paint_sockets, paints

NAME = '.SVS create skin head'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    for name in ('Skin mask', 'Facetype', 'Mole', 'Paint mask', 'Eyeshadow texture'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Facetype present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    paint_sockets(t)
    t.socket('INPUT', 'Main color', 'NodeSocketColor', default_value=(1.0, 0.76, 0.68, 1.0))
    t.socket('INPUT', 'Mouth color', 'NodeSocketColor', default_value=(0.56, 0.15, 0.15, 1.0))
    for name in ('Mole color', 'Eyeshadow color'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Eyeshadow', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1600, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))
    m = t.math
    for row, name in enumerate(('Skin mask', 'Mole', 'Eyeshadow texture')):
        t.make('ShaderNodeSeparateColor', name, (-1400, 600 - row * 200), ins={'Color': ('in', name)})
    t.make('ShaderNodeMix', 'mouth', (-1200, 500), {'data_type': 'VECTOR'},
           {'Factor_Float': ('Skin mask', 'Red'), 'A_Vector': ('in', 'Main color'), 'B_Vector': ('in', 'Mouth color')})
    t.make('ShaderNodeMix', 'facetype', (-1200, 300), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Facetype present'), 'A_Color': (1.0, 1.0, 1.0, 1.0), 'B_Color': ('in', 'Facetype')})
    t.make('ShaderNodeVectorMath', 'base', (-1000, 400), {'operation': 'MULTIPLY'},
           {'Vector': ('mouth', 'Result_Vector'), 'Vector_001': ('facetype', 'Result_Color')})
    rgb = paints(t, ('base', 'Vector'), (None, None, None), x=-900)
    t.make('ShaderNodeMix', 'mole', (400, 200), {'data_type': 'VECTOR'},
           {'Factor_Float': m('mole.a', 'MULTIPLY', ('Mole', 'Red'), ('in', 'Mole color alpha'), location=(250, 300)),
            'A_Vector': rgb, 'B_Vector': ('in', 'Mole color')})
    t.make('ShaderNodeVectorMath', 'diff', (550, 200), {'operation': 'SUBTRACT'}, {'Vector': ('mole', 'Result_Vector'), 'Vector_001': ('base', 'Vector')})
    t.make('ShaderNodeVectorMath', 'masked', (700, 200), {'operation': 'MULTIPLY_ADD'},
           {'Vector': ('diff', 'Vector'), 'Vector_001': ('in', 'Paint mask'), 'Vector_002': ('base', 'Vector')})
    es = m('es', 'MULTIPLY', m('es.a', 'MULTIPLY', ('Eyeshadow texture', 'Red'), ('in', 'Eyeshadow color alpha'), location=(700, 0)),
           ('in', 'Eyeshadow'), location=(850, 0))
    t.make('ShaderNodeMix', 'eyeshadow', (1000, 200), {'data_type': 'VECTOR'},
           {'Factor_Float': es, 'A_Vector': ('masked', 'Vector'), 'B_Vector': ('in', 'Eyeshadow color')})
    t.link('eyeshadow', 'Result_Vector', 'out', 'Color')
    return t
