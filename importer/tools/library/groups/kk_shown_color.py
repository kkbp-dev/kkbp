"""`.KK shown color`: a colour input of a shader group, as the shader reads it (ADR 0056). With Shown
on, the input is a Shown Colour, the colour the template shows for it (lit, on white): it is
sRGB-encoded, ungraded and decoded back, linear(ungrade(srgb(colour))), the game's own colour, linear.
With Shown off it is the game's colour already and passes as it is. Written by hand."""

NAME = '.KK shown color'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Shown', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-700, 0))
    t.make('NodeGroupOutput', 'out', (800, 0))
    t.make('ShaderNodeGroup', 'encode', (-450, -150), {'node_tree': lib.group('.KK srgb')}, {'Color': ('in', 'Color')})
    t.make('ShaderNodeGroup', 'ungrade', (-150, -150), {'node_tree': lib.group('.KK ungrade')}, {'Color': ('encode', 'Color')})
    t.make('ShaderNodeGroup', 'decode', (150, -150), {'node_tree': lib.group('.KK linear')}, {'Color': ('ungrade', 'Color')})
    t.make('ShaderNodeMix', 'pick', (500, 0), {'data_type': 'RGBA'},
           {'Factor_Float': ('in', 'Shown'), 'A_Color': ('in', 'Color'), 'B_Color': ('decode', 'Color')})
    t.link('pick', 'Result_Color', 'out', 'Color')
    return t
