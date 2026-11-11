"""`.KK toon_eyew`: KK's toon_eyew_lod0 (eye whites, eyebrows, eyelines) as the exporter bakes it,
lit from the front (Light) and from behind (Dark), in linear colour (models.toon_eyew):

    base  = Main * Color
    S     = 1 - (1 - Ambient)^2                      the ambient shadow, _ambientshadowG = Ambient
    shade = Shadow color > 0.5 ? 1 - (2 - 2 * Shadow color) * (1 - S) : 2 * S * Shadow color
    Light = base * max(Light * 0.6 + 0.4, Ambient);  Dark = Light's factor * base * shade

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
    t.socket('INPUT', 'Ambient', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-1200, 0))
    t.make('NodeGroupOutput', 'out', (900, 0))

    t.make('ShaderNodeVectorMath', 'base', (-600, 300), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Main'), 'Vector_001': ('in', 'Color')})
    keep = t.math('ambient.keep', 'SUBTRACT', 1.0, ('in', 'Ambient'), location=(-1000, -300))
    s = t.math('ambient.shadow', 'SUBTRACT', 1.0, t.math('ambient.keep2', 'MULTIPLY', keep, keep, location=(-850, -300)),
               location=(-700, -300), clamp=True)
    not_s = t.math('ambient.lit', 'SUBTRACT', 1.0, s, location=(-550, -300))
    t.make('ShaderNodeSeparateColor', 'shadow', (-1000, -50), ins={'Color': ('in', 'Shadow color')})
    t.make('ShaderNodeCombineXYZ', 'shade', (100, -100))
    for row, (channel, axis) in enumerate((('Red', 'X'), ('Green', 'Y'), ('Blue', 'Z'))):
        y = 0 - row * 250
        sc = ('shadow', channel)
        high = t.math(f'{channel}.high', 'SUBTRACT', 1.0, t.math(
            f'{channel}.over', 'MULTIPLY', t.math(f'{channel}.span', 'MULTIPLY_ADD', sc, -2.0, 2.0, location=(-400, y)),
            not_s, location=(-250, y)), location=(-100, y), clamp=True)
        low = t.math(f'{channel}.low', 'MULTIPLY', t.math(f'{channel}.tint', 'MULTIPLY', sc, s, location=(-400, y - 80)),
                     2.0, location=(-250, y - 80), clamp=True)
        pick = t.math(f'{channel}.pick', 'GREATER_THAN', sc, 0.5, location=(-250, y + 80))
        t.make('ShaderNodeMix', f'{channel}.mix', (-50, y - 40), {'data_type': 'FLOAT'},
               {'Factor_Float': pick, 'A_Float': low, 'B_Float': high})
        t.link(f'{channel}.mix', 'Result_Float', 'shade', axis)

    factor = t.math('light', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(-600, 500)),
                    ('in', 'Ambient'), location=(-400, 500))
    t.make('ShaderNodeVectorMath', 'lit', (400, 300), {'operation': 'SCALE'}, {'Vector': ('base', 'Vector'), 'Scale': factor})
    t.make('ShaderNodeVectorMath', 'shaded', (300, 0), {'operation': 'MULTIPLY'},
           {'Vector': ('base', 'Vector'), 'Vector_001': ('shade', 'Vector')})
    t.make('ShaderNodeVectorMath', 'dark', (550, 0), {'operation': 'SCALE'}, {'Vector': ('shaded', 'Vector'), 'Scale': factor})
    t.link('lit', 'Vector', 'out', 'Light')
    t.link('dark', 'Vector', 'out', 'Dark')
    return t
