"""`.SVS skin body color`: SVS's body colour (models.skin_body_color).

    Base   = mix(Main color, Create, Create alpha)
    nipped = clamp(mix(mix(Base, Nip color 1, Nip.r), that * Nip color 1 * Nip color 2, Nip.g))
    col    = mix(Base, nipped, Nip alpha * Nip color 1 alpha * (1 - Vertex.r) * On mesh)
    col    = mix(col, Underhair * Under hair color, Underhair amount),  amount = its alpha * its colour's * Vertex.r * On mesh
    Color  = clamp(mix(col * 0.95, Detail color 2, Detail 2.r * Skin red power * Detail color 2 alpha * (0.67 v + 0.33)))

v is Base's value. The layers' alphas are times their `present` switches. On mesh is the vertex colour's
alpha: the importer's bake plane has none, as the game's quad has its mesh-placed layers cleared. Linear
colours. Written by hand."""

NAME = '.SVS skin body color'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Base', 'NodeSocketVector')
    t.socket('OUTPUT', 'Color', 'NodeSocketVector')
    t.socket('OUTPUT', 'Underhair amount', 'NodeSocketFloat')
    t.socket('INPUT', 'Create', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Create alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for name in ('Nip', 'Underhair'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
        t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'{name} present', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Detail 2', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Vertex', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'On mesh', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for name, d in (('Main color', (1.0, 0.82, 0.71, 1.0)), ('Nip color 1', (1.0, 0.23, 0.17, 1.0)),
                    ('Nip color 2', (1.0, 0.4, 0.36, 1.0)), ('Under hair color', (0.09, 0.06, 0.06, 1.0)),
                    ('Detail color 2', (1.0, 0.0, 0.0, 1.0))):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=d)
        if name != 'Main color' and name != 'Nip color 2':
            t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Skin red power', 'NodeSocketFloat', default_value=0.5)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1200, 0))
    m = t.math
    t.make('ShaderNodeMix', 'base', (-1100, 500), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Create alpha'), 'A_Vector': ('in', 'Main color'), 'B_Vector': ('in', 'Create')})
    base = ('base', 'Result_Vector')
    t.make('ShaderNodeSeparateColor', 'nip', (-1200, 200), ins={'Color': ('in', 'Nip')})
    t.make('ShaderNodeSeparateColor', 'vertex', (-1200, -200), ins={'Color': ('in', 'Vertex')})
    t.make('ShaderNodeSeparateColor', 'detail2', (-1200, -500), ins={'Color': ('in', 'Detail 2')})
    t.make('ShaderNodeMix', 'n1', (-900, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': ('nip', 'Red'), 'A_Vector': base, 'B_Vector': ('in', 'Nip color 1')})
    t.make('ShaderNodeVectorMath', 'n12', (-1050, 150), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Nip color 1'), 'Vector_001': ('in', 'Nip color 2')})
    t.make('ShaderNodeVectorMath', 'n2.col', (-750, 150), {'operation': 'MULTIPLY'},
           {'Vector': ('n1', 'Result_Vector'), 'Vector_001': ('n12', 'Vector')})
    t.make('ShaderNodeMix', 'n2', (-600, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': ('nip', 'Green'), 'A_Vector': ('n1', 'Result_Vector'), 'B_Vector': ('n2.col', 'Vector')})
    t.make('ShaderNodeVectorMath', 'nipped', (-450, 300), {'operation': 'MINIMUM'}, {'Vector': ('n2', 'Result_Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'nipped.low', (-300, 300), {'operation': 'MAXIMUM'}, {'Vector': ('nipped', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    off_red = m('1-vr', 'SUBTRACT', 1.0, ('vertex', 'Red'), location=(-1000, -200))
    nip_w = m('nip.w', 'MULTIPLY', m('nip.w2', 'MULTIPLY', m('nip.w1', 'MULTIPLY', m('nip.a', 'MULTIPLY', ('in', 'Nip alpha'), ('in', 'Nip present'),
              location=(-1000, 100)), ('in', 'Nip color 1 alpha'), location=(-850, 100)), off_red, location=(-700, 100)),
              ('in', 'On mesh'), location=(-550, 100))
    t.make('ShaderNodeMix', 'nipples', (-150, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': nip_w, 'A_Vector': base, 'B_Vector': ('nipped.low', 'Vector')})
    uh = m('uh', 'MULTIPLY', m('uh.3', 'MULTIPLY', m('uh.2', 'MULTIPLY', m('uh.1', 'MULTIPLY', ('in', 'Underhair alpha'), ('in', 'Underhair present'),
           location=(-1000, -350)), ('in', 'Under hair color alpha'), location=(-850, -350)), ('vertex', 'Red'), location=(-700, -350)),
           ('in', 'On mesh'), location=(-550, -350))
    t.make('ShaderNodeVectorMath', 'uh.col', (-400, 0), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Underhair'), 'Vector_001': ('in', 'Under hair color')})
    t.make('ShaderNodeMix', 'hair', (0, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': uh, 'A_Vector': ('nipples', 'Result_Vector'), 'B_Vector': ('uh.col', 'Vector')})
    t.make('ShaderNodeSeparateColor', 'base.hsv', (-900, -600), {'mode': 'HSV'}, {'Color': base})
    red = m('red', 'MULTIPLY', m('red.3', 'MULTIPLY', m('red.2', 'MULTIPLY', ('detail2', 'Red'), ('in', 'Skin red power'), location=(-750, -700)),
            ('in', 'Detail color 2 alpha'), location=(-600, -700)), m('red.v', 'MULTIPLY_ADD', ('base.hsv', 'Blue'), 0.67, 0.33, location=(-750, -800)),
            location=(-450, -700))
    t.make('ShaderNodeVectorMath', 'dim', (200, 300), {'operation': 'SCALE'}, {'Vector': ('hair', 'Result_Vector'), 'Scale': 0.95})
    t.make('ShaderNodeMix', 'reddened', (400, 300), {'data_type': 'VECTOR'},
           {'Factor_Float': red, 'A_Vector': ('dim', 'Vector'), 'B_Vector': ('in', 'Detail color 2')})
    t.make('ShaderNodeVectorMath', 'color', (600, 300), {'operation': 'MINIMUM'}, {'Vector': ('reddened', 'Result_Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'color.low', (750, 300), {'operation': 'MAXIMUM'}, {'Vector': ('color', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    t.link('base', 'Result_Vector', 'out', 'Base')
    t.link('color.low', 'Vector', 'out', 'Color')
    t.link(uh[0], uh[1], 'out', 'Underhair amount')
    return t
