"""`.SVS face part`: SVS's eyebrow and eyelash shaders (LIF/lif_main_eyebrow, lif_main_eyelash_up) as
the exporter bakes them, front-lit (Light) and back-lit (Dark), in linear colour
(models.svs_face_part, issue 62).

    w     = By alpha ? a : 1
    col   = mix(Color 1, Color 2, r * Color 2 alpha * w)
    col   = mix(col, Color 3, g * Color 3 alpha * w);  col = mix(col, Line color, b * Line color alpha * w)
    col   = clamp(mix(col, Light color * col, 0.7 * Light influence))
    Light = clamp(col * `.SVS face part light`(col, N.L light));  Dark the same at N.L dark
    Alpha = a where a >= Alpha cut, else 0

r, g, b, a are the texture's. The eyebrow weighs its layers by its alpha and cuts at 0.5; the
eyelash doesn't, and cuts at 0.9. Colours are linear. Written by hand."""

NAME = '.SVS face part'
KIND = 'ShaderNodeTree'

LIGHT_NDL = 0.828421950340271  # models.SVS_LIGHT
DARK_NDL = -0.9444175958633423  # models.SVS_DARK
AMBIENT = (0.18855378, 0.18145701, 0.1885538)  # models.SVS_QUAD_AMBIENT


def color_layers(t, colors, location):
    """The texture's r, g and b pick colours over the first, each by its alpha (and the texture's,
    by `By alpha`); returns the source of the result."""
    x, y = location
    t.make('ShaderNodeSeparateColor', 'tex', (x, y + 300), ins={'Color': ('in', 'Texture')})
    t.make('ShaderNodeMix', 'weight', (x, y + 500), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'By alpha'), 'A_Float': 1.0, 'B_Float': ('in', 'Texture alpha')})
    previous = ('in', colors[0])
    for k, (channel, name) in enumerate(zip(('Red', 'Green', 'Blue'), colors[1:])):
        f = t.math(f'{name}.amount', 'MULTIPLY', t.math(f'{name}.alpha', 'MULTIPLY', ('tex', channel), ('in', f'{name} alpha'),
                   location=(x + 200, y - k * 250)), ('weight', 'Result_Float'), location=(x + 350, y - k * 250))
        t.make('ShaderNodeMix', f'{name}.mix', (x + 550, y - k * 250), {'data_type': 'VECTOR'},
               {'Factor_Float': f, 'A_Vector': previous, 'B_Vector': ('in', name)})
        previous = (f'{name}.mix', 'Result_Vector')
    return previous


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Texture', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Texture alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for name, default in (('Color 1', (0.12, 0.065, 0.05)), ('Color 2', (1.0, 0.43, 0.43)), ('Color 3', (0.47, 0.26, 0.16)),
                          ('Line color', (0.0, 0.0, 0.0))):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(*default, 1.0))
        if name != 'Color 1':
            t.socket('INPUT', f'{name} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'By alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Alpha cut', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light influence', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Shadow power', 'NodeSocketFloat', default_value=0.7, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'N.L light', 'NodeSocketFloat', default_value=LIGHT_NDL, min_value=-1.0, max_value=1.0)
    t.socket('INPUT', 'N.L dark', 'NodeSocketFloat', default_value=DARK_NDL, min_value=-1.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(*AMBIENT, 1.0))
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (900, 0))

    col = color_layers(t, ('Color 1', 'Color 2', 'Color 3', 'Line color'), (-1200, 0))
    t.make('ShaderNodeVectorMath', 'lit.col', (-450, 300), {'operation': 'MULTIPLY'},
           {'Vector': col, 'Vector_001': ('in', 'Light color')})
    t.make('ShaderNodeMix', 'influence', (-250, 200), {'data_type': 'VECTOR', 'clamp_result': False},
           {'Factor_Float': t.math('influence.amount', 'MULTIPLY', ('in', 'Light influence'), 0.7, location=(-450, 450)),
            'A_Vector': col, 'B_Vector': ('lit.col', 'Vector')})
    t.make('ShaderNodeVectorMath', 'col.min', (-50, 200), {'operation': 'MINIMUM'},
           {'Vector': ('influence', 'Result_Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
    t.make('ShaderNodeVectorMath', 'col', (100, 200), {'operation': 'MAXIMUM'},
           {'Vector': ('col.min', 'Vector'), 'Vector_001': (0.0, 0.0, 0.0)})
    for row, kind in enumerate(('light', 'dark')):
        y = 100 - row * 300
        t.make('ShaderNodeGroup', f'{kind}.term', (300, y), {'node_tree': lib.group('.SVS face part light'), 'width': 200.0},
               {'Color': ('col', 'Vector'), 'Shadow power': ('in', 'Shadow power'), 'Light color': ('in', 'Light color'),
                'N.L': ('in', f'N.L {kind}'), 'Ambient': ('in', 'Ambient')})
        t.make('ShaderNodeVectorMath', f'{kind}.out', (550, y), {'operation': 'MULTIPLY'},
               {'Vector': ('col', 'Vector'), 'Vector_001': (f'{kind}.term', 'Light')})
        t.make('ShaderNodeVectorMath', f'{kind}.clamp', (700, y), {'operation': 'MINIMUM'},
               {'Vector': (f'{kind}.out', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
        t.link(f'{kind}.clamp', 'Vector', 'out', kind.capitalize())
    cut = t.math('alpha.cut', 'GREATER_THAN', ('in', 'Texture alpha'),
                 t.math('alpha.edge', 'SUBTRACT', ('in', 'Alpha cut'), 0.0001, location=(300, -600)), location=(500, -500))
    t.link(*t.math('alpha', 'MULTIPLY', cut, ('in', 'Texture alpha'), location=(700, -500)), 'out', 'Alpha')
    return t
