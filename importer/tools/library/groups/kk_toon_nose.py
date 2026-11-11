"""`.KK toon_nose`: KK's toon_nose_lod0, unlit: the colour where the texture's red is dark, plus its
green; alpha the texture's times the colour's (models.toon_nose). Colours are linear; Main is the
texture's stored value. Written by hand."""

NAME = '.KK toon_nose'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Main alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Color alpha', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-800, 0))
    t.make('NodeGroupOutput', 'out', (600, 0))
    t.make('ShaderNodeSeparateColor', 'main', (-550, 200), ins={'Color': ('in', 'Main')})
    dark = t.math('dark', 'SUBTRACT', 1.0, ('main', 'Red'), location=(-300, 250))
    t.make('ShaderNodeVectorMath', 'colour', (-100, 150), {'operation': 'SCALE'}, {'Vector': ('in', 'Color'), 'Scale': dark})
    t.make('ShaderNodeCombineXYZ', 'green', (-100, -50), ins={'X': ('main', 'Green'), 'Y': ('main', 'Green'), 'Z': ('main', 'Green')})
    t.make('ShaderNodeVectorMath', 'sum', (150, 100), {'operation': 'ADD'},
           {'Vector': ('colour', 'Vector'), 'Vector_001': ('green', 'Vector')})
    t.math('alpha', 'MULTIPLY', ('in', 'Main alpha'), ('in', 'Color alpha'), location=(150, -150))
    t.link('sum', 'Vector', 'out', 'Color')
    t.link('alpha', 'Value', 'out', 'Alpha')
    return t
