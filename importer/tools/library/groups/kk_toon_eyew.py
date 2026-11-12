"""`.KK toon_eyew`: KK's toon_eyew_lod0 and KKS's Koikano/main_eyew (eye whites, eyebrows, eyelines)
as the exporter bakes them, lit from the front (Light) and from behind (Dark), in linear colour
(models.toon_eyew). The ambient inputs are the Game's Maker Light (models.KK, models.KKS); their
defaults are KK's, and KKS's profile sets its own.

    base  = Main * Color
    shade = `.KK shadow tint` of Shadow color, Ambient, Ambient strength
    f     = max(Light * 0.6 + 0.4, Ambient strength)
    Light = base * f;  Dark = mix(base * shade, base, Shadow floor) * f

Colours are linear; Main is the texture's stored value. Written by hand."""

NAME = '.KK toon_eyew'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Shadow floor', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-800, 0))
    t.make('NodeGroupOutput', 'out', (900, 0))

    t.make('ShaderNodeVectorMath', 'base', (-400, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Main'), 'Vector_001': ('in', 'Color')})
    t.make('ShaderNodeGroup', 'shade', (-400, -100), {'node_tree': lib.group('.KK shadow tint'), 'width': 200.0},
           {'Shadow color': ('in', 'Shadow color'), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength')})
    factor = t.math('light', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(-400, 500)),
                    ('in', 'Ambient strength'), location=(-200, 500))
    t.make('ShaderNodeVectorMath', 'lit', (400, 300), {'operation': 'SCALE'}, {'Vector': ('base', 'Vector'), 'Scale': factor})
    t.make('ShaderNodeVectorMath', 'shaded', (0, 0), {'operation': 'MULTIPLY'},
           {'Vector': ('base', 'Vector'), 'Vector_001': ('shade', 'Tint')})
    t.make('ShaderNodeMix', 'floor', (250, 0), {'data_type': 'VECTOR'},
           {'Factor_Float': ('in', 'Shadow floor'), 'A_Vector': ('shaded', 'Vector'), 'B_Vector': ('base', 'Vector')})
    t.make('ShaderNodeVectorMath', 'dark', (500, 0), {'operation': 'SCALE'}, {'Vector': ('floor', 'Result_Vector'), 'Scale': factor})
    t.link('lit', 'Vector', 'out', 'Light')
    t.link('dark', 'Vector', 'out', 'Dark')
    return t
