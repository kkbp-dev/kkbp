"""`.SVS skin head color`: SVS's face colour (models.skin_head_color, issue 62).

    Base  = mix(Main color, Create, Create alpha)
    col   = mix(Base * 0.95, Cheek color, Cheek.r * its alpha), Cheek highlight color screened over it by Cheek.b * its alpha
    col   = mix(col, Lip color, Lip.r * its alpha) + Lip.b * Lip highlight color * its alpha
    col   = col * mix(1, (0.75 + sqrt(v) / 2) * hsv(clamp(h - 0.03), sqrt(s), 1), Nose.r * Nose color alpha)
    Color = clamp(mix(col, Nose line color, Nose.b * its alpha))

h, s, v are Create's. The cheek, lip and nose come in already kept off the bake's plane (their
template scales them by the vertex colour's alpha). Linear colours. Written by hand."""

NAME = '.SVS skin head color'
KIND = 'ShaderNodeTree'

COLORS = (('Main color', (1.0, 0.84, 0.74, 1.0)), ('Cheek color', (1.0, 0.07, 0.0, 1.0)), ('Cheek highlight color', (1.0, 1.0, 1.0, 1.0)),
          ('Lip color', (1.0, 0.0, 0.0, 1.0)), ('Lip highlight color', (1.0, 1.0, 1.0, 1.0)), ('Nose line color', (0.0, 0.0, 0.0, 1.0)))


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Base', 'NodeSocketVector')
    t.socket('OUTPUT', 'Color', 'NodeSocketVector')
    t.socket('INPUT', 'Create', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Create alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for name in ('Cheek', 'Lip', 'Nose'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    for name, d in COLORS:
        t.socket('INPUT', name, 'NodeSocketColor', default_value=d)
        if name != 'Main color':
            t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Nose color alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1600, 0))
    t.make('NodeGroupOutput', 'out', (1400, 0))
    m = t.math
    for row, name in enumerate(('Cheek', 'Lip', 'Nose')):
        t.make('ShaderNodeSeparateColor', name, (-1400, 600 - row * 200), ins={'Color': ('in', name)})
    t.make('ShaderNodeMix', 'base', (-1200, 900), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Create alpha'), 'A_Vector': ('in', 'Main color'), 'B_Vector': ('in', 'Create')})
    t.make('ShaderNodeVectorMath', 'dim', (-1050, 900), {'operation': 'SCALE'}, {'Vector': ('base', 'Result_Vector'), 'Scale': 0.95})
    t.make('ShaderNodeMix', 'cheek', (-900, 900), {'data_type': 'VECTOR'},
           {'Factor_Float': m('cheek.a', 'MULTIPLY', ('Cheek', 'Red'), ('in', 'Cheek color alpha'), location=(-1050, 1000)),
            'A_Vector': ('dim', 'Vector'), 'B_Vector': ('in', 'Cheek color')})
    t.make('ShaderNodeMix', 'cheek.hl', (-700, 900), {'data_type': 'RGBA', 'blend_type': 'SCREEN', 'clamp_result': True},
           {'Factor_Float': m('cheek.hl.a', 'MULTIPLY', ('Cheek', 'Blue'), ('in', 'Cheek highlight color alpha'), location=(-850, 1050)),
            'A_Color': ('cheek', 'Result_Vector'), 'B_Color': ('in', 'Cheek highlight color')})
    t.make('ShaderNodeMix', 'lip', (-500, 900), {'data_type': 'VECTOR'},
           {'Factor_Float': m('lip.a', 'MULTIPLY', ('Lip', 'Red'), ('in', 'Lip color alpha'), location=(-650, 1050)),
            'A_Vector': ('cheek.hl', 'Result_Color'), 'B_Vector': ('in', 'Lip color')})
    lh = m('lip.hl.a', 'MULTIPLY', ('Lip', 'Blue'), ('in', 'Lip highlight color alpha'), location=(-500, 1050))
    t.make('ShaderNodeVectorMath', 'lip.hl.v', (-350, 1050), {'operation': 'SCALE'}, {'Vector': ('in', 'Lip highlight color'), 'Scale': lh})
    t.make('ShaderNodeVectorMath', 'lip.hl', (-200, 900), {'operation': 'ADD'},
           {'Vector': ('lip', 'Result_Vector'), 'Vector_001': ('lip.hl.v', 'Vector')})
    t.make('ShaderNodeSeparateColor', 'hsv', (-1200, 200), {'mode': 'HSV'}, {'Color': ('in', 'Create')})
    t.make('ShaderNodeCombineColor', 'nose.hsv', (-900, 200), {'mode': 'HSV'},
           {'Red': m('nose.h', 'SUBTRACT', ('hsv', 'Red'), 0.03, location=(-1050, 300), clamp=True),
            'Green': m('nose.s', 'SQRT', ('hsv', 'Green'), location=(-1050, 200)), 'Blue': 1.0})
    nv = m('nose.v', 'MULTIPLY_ADD', m('nose.vroot', 'SQRT', ('hsv', 'Blue'), location=(-1050, 50)), 0.5, 0.75, location=(-900, 50))
    t.make('ShaderNodeVectorMath', 'nose.tint', (-750, 200), {'operation': 'SCALE'}, {'Vector': ('nose.hsv', 'Color'), 'Scale': nv})
    t.make('ShaderNodeMix', 'nose.mult', (-550, 200), {'data_type': 'VECTOR'},
           {'Factor_Float': m('nose.a', 'MULTIPLY', ('Nose', 'Red'), ('in', 'Nose color alpha'), location=(-750, 350)),
            'A_Vector': (1.0, 1.0, 1.0), 'B_Vector': ('nose.tint', 'Vector')})
    t.make('ShaderNodeVectorMath', 'nosed', (0, 700), {'operation': 'MULTIPLY'},
           {'Vector': ('lip.hl', 'Vector'), 'Vector_001': ('nose.mult', 'Result_Vector')})
    t.make('ShaderNodeMix', 'nose.line', (200, 700), {'data_type': 'VECTOR'},
           {'Factor_Float': m('nose.l.a', 'MULTIPLY', ('Nose', 'Blue'), ('in', 'Nose line color alpha'), location=(0, 850)),
            'A_Vector': ('nosed', 'Vector'), 'B_Vector': ('in', 'Nose line color')})
    t.make('ShaderNodeVectorMath', 'color', (400, 700), {'operation': 'MINIMUM'}, {'Vector': ('nose.line', 'Result_Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'color.low', (550, 700), {'operation': 'MAXIMUM'}, {'Vector': ('color', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    t.link('base', 'Result_Vector', 'out', 'Base')
    t.link('color.low', 'Vector', 'out', 'Color')
    return t
