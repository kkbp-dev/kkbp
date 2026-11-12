"""`.KK main_emblem`: KK's main_emblem (clothes emblems) as the exporter bakes it, lit from the front
(Light) and from behind (Dark), in linear colour (models.main_emblem):

    tint  = `.KK item tint` of Main, Scale 0.8, white shadow colour
    Light = Main * f;  Dark = Main * tint * f;  f = max(Light * 0.6 + 0.4, Ambient strength)
    Alpha = 1 where Main alpha ^ 0.3 rounds to 1 (alpha >= 0.0992), else 0

It reads `_ambientshadow`, which the game leaves unset: Ambient and Ambient strength default to 0.
Written by hand."""

NAME = '.KK main_emblem'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Main alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Light', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=2.0)
    t.make('NodeGroupInput', 'in', (-800, 0))
    t.make('NodeGroupOutput', 'out', (700, 0))
    t.make('ShaderNodeGroup', 'tint', (-500, -150), {'node_tree': lib.group('.KK item tint'), 'width': 200.0},
           {'Color': ('in', 'Main'), 'Shadow color': (1.0, 1.0, 1.0, 1.0), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength'), 'Scale': 0.8})
    factor = t.math('light.factor', 'MAXIMUM', t.math('light.term', 'MULTIPLY_ADD', ('in', 'Light'), 0.6, 0.4, location=(-500, 400)),
                    ('in', 'Ambient strength'), location=(-300, 400))
    t.make('ShaderNodeVectorMath', 'shaded', (-200, 0), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Main'), 'Vector_001': ('tint', 'Tint')})
    for name, src, y in (('Light', ('in', 'Main'), 250), ('Dark', ('shaded', 'Vector'), 0)):
        key = name.lower()
        t.make('ShaderNodeVectorMath', key, (300, y), {'operation': 'SCALE'}, {'Vector': src, 'Scale': factor})
        t.link(key, 'Vector', 'out', name)
    alpha = t.math('alpha', 'GREATER_THAN', ('in', 'Main alpha'), 0.5 ** (1 / 0.3) - 1e-6, location=(300, -250))
    t.link(alpha[0], alpha[1], 'out', 'Alpha')
    return t
