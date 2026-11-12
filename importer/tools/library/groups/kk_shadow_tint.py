"""`.KK shadow tint`: the colour the games' lit shaders multiply the unlit side by, per channel
(models.shade of models.ambient_shadow): the shadow colour's overlay with the ambient shadow, which
is the ambient colour's overlay with its strength (the `finalAmbientShadow` block).

    S    = 1 - (1 - Ambient strength) * (1 - Ambient)
    Tint = Shadow color > 0.5 ? 1 - (2 - 2 * Shadow color) * (1 - S) : 2 * S * Shadow color

Linear colours. Written by hand."""

NAME = '.KK shadow tint'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Tint', 'NodeSocketColor')
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1100, 0))
    t.make('NodeGroupOutput', 'out', (400, 0))

    keep = t.math('ambient.keep', 'SUBTRACT', 1.0, ('in', 'Ambient strength'), location=(-850, -500))
    t.make('ShaderNodeSeparateColor', 'shadow', (-850, 100), ins={'Color': ('in', 'Shadow color')})
    t.make('ShaderNodeSeparateColor', 'ambient', (-850, -250), ins={'Color': ('in', 'Ambient')})
    t.make('ShaderNodeCombineColor', 'tint', (200, 0))
    for row, channel in enumerate(('Red', 'Green', 'Blue')):
        y = 200 - row * 250
        sc = ('shadow', channel)
        # 1 - S, and S: the ambient colour's overlay with the strength.
        not_s = t.math(f'{channel}.lit', 'MULTIPLY', keep,
                       t.math(f'{channel}.ambient', 'SUBTRACT', 1.0, ('ambient', channel), location=(-650, y - 160)),
                       location=(-500, y - 160))
        s = t.math(f'{channel}.shadow', 'SUBTRACT', 1.0, not_s, location=(-350, y - 160))
        high = t.math(f'{channel}.high', 'SUBTRACT', 1.0, t.math(
            f'{channel}.over', 'MULTIPLY', t.math(f'{channel}.span', 'MULTIPLY_ADD', sc, -2.0, 2.0, location=(-350, y)),
            not_s, location=(-200, y)), location=(-50, y), clamp=True)
        low = t.math(f'{channel}.low', 'MULTIPLY', t.math(f'{channel}.tint', 'MULTIPLY', sc, s, location=(-200, y - 80)),
                     2.0, location=(-50, y - 80), clamp=True)
        pick = t.math(f'{channel}.pick', 'GREATER_THAN', sc, 0.5, location=(-200, y + 80))
        t.make('ShaderNodeMix', f'{channel}.mix', (0, y - 40), {'data_type': 'FLOAT'},
               {'Factor_Float': pick, 'A_Float': low, 'B_Float': high})
        t.link(f'{channel}.mix', 'Result_Float', 'tint', channel)
    t.link('tint', 'Color', 'out', 'Tint')
    return t
