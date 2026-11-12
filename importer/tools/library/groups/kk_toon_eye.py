"""`.KK toon_eye`: KK's toon_eye_lod0 (irises) as the exporter bakes it, lit from the front (Light) and
from behind (Dark), in linear colour (models.toon_eye):

    oK    = Overlay K alpha * (Overlay color K, Overlay color K alpha)     K = 1, 2; the max of both
    hl    = o.alpha * Highlight
    col   = mix(Main, o.rgb, hl);  T = `.KK shadow tint` of Shadow color, Ambient, Ambient strength
    f     = max(Light * 0.6 + 0.4, Ambient strength)
    Light = min(col * f, 1);  Dark = min(col * mix(T, 1, hl) * f, 1);  Alpha = max(Main alpha, hl)

Only the overlays' alpha shows, coloured by their colours. `_exppower` is 0 outside expressions, so
the expression texture is left out. Written by hand."""

NAME = '.KK toon_eye'
KIND = 'ShaderNodeTree'

WHITE = (1.0, 1.0, 1.0, 1.0)


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Main alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    for k in (1, 2):
        t.socket('INPUT', f'Overlay {k} alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
        t.socket('INPUT', f'Overlay color {k}', 'NodeSocketColor', default_value=WHITE)
        t.socket('INPUT', f'Overlay color {k} alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Highlight', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=WHITE)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (1000, 0))

    for k in (1, 2):
        y = 500 - (k - 1) * 300
        t.make('ShaderNodeVectorMath', f'o{k}', (-800, y), {'operation': 'SCALE'},
               {'Vector': ('in', f'Overlay color {k}'), 'Scale': ('in', f'Overlay {k} alpha')})
        t.math(f'o{k}.a', 'MULTIPLY', ('in', f'Overlay color {k} alpha'), ('in', f'Overlay {k} alpha'), location=(-800, y - 150))
    t.make('ShaderNodeVectorMath', 'o', (-600, 400), {'operation': 'MAXIMUM'}, {'Vector': ('o1', 'Vector'), 'Vector_001': ('o2', 'Vector')})
    hl = t.math('hl', 'MULTIPLY', t.math('o.a', 'MAXIMUM', ('o1.a', 'Value'), ('o2.a', 'Value'), location=(-600, 100)),
                ('in', 'Highlight'), location=(-400, 100))
    t.make('ShaderNodeMix', 'col', (-200, 300), {'data_type': 'RGBA'},
           {'Factor_Float': hl, 'A_Color': ('in', 'Main'), 'B_Color': ('o', 'Vector')})
    t.make('ShaderNodeGroup', 'tint', (-400, -200), {'node_tree': lib.group('.KK shadow tint'), 'width': 200.0},
           {'Shadow color': ('in', 'Shadow color'), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength')})
    t.make('ShaderNodeMix', 'shade', (0, -150), {'data_type': 'RGBA'},
           {'Factor_Float': hl, 'A_Color': ('tint', 'Tint'), 'B_Color': WHITE})
    factor = t.math('light.factor', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(0, 600)),
                    ('in', 'Ambient strength'), location=(200, 600))
    t.make('ShaderNodeVectorMath', 'shaded', (250, 0), {'operation': 'MULTIPLY'},
           {'Vector': ('col', 'Result_Color'), 'Vector_001': ('shade', 'Result_Color')})
    for name, src, y in (('Light', ('col', 'Result_Color'), 300), ('Dark', ('shaded', 'Vector'), 0)):
        key = name.lower()
        t.make('ShaderNodeVectorMath', f'{key}.lit', (500, y), {'operation': 'SCALE'}, {'Vector': src, 'Scale': factor})
        t.make('ShaderNodeVectorMath', key, (750, y), {'operation': 'MINIMUM'},
               {'Vector': (f'{key}.lit', 'Vector'), 'Vector_001': (1.0, 1.0, 1.0)})
        t.link(key, 'Vector', 'out', name)
    alpha = t.math('alpha', 'MAXIMUM', ('in', 'Main alpha'), hl, location=(750, -300))
    t.link(alpha[0], alpha[1], 'out', 'Alpha')
    return t
