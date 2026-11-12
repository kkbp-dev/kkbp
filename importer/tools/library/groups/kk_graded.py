"""`.KK graded`: a lit shader's linear colour as the game's bake stores it, graded, and decoded back
to linear for the emission that shows it (issue 30): linear(grade(srgb(colour))). Written by hand."""

NAME = '.KK graded'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.make('NodeGroupInput', 'in', (-700, 0))
    t.make('NodeGroupOutput', 'out', (500, 0))
    t.make('ShaderNodeGroup', 'encode', (-450, 0), {'node_tree': lib.group('.KK srgb')}, {'Color': ('in', 'Color')})
    t.make('ShaderNodeGroup', 'grade', (-150, 0), {'node_tree': lib.group('.KK grade')}, {'Color': ('encode', 'Color')})
    t.make('ShaderNodeGroup', 'decode', (150, 0), {'node_tree': lib.group('.KK linear')}, {'Color': ('grade', 'Color')})
    t.link('decode', 'Color', 'out', 'Color')
    return t
