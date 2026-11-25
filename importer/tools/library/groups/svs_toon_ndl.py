"""`.SVS toon ndl`: N.L on the bake quad picked by the toon value the bake sets (1 lit, 0 dark), for
SVS templates that light once at it. The toon value passes through to `.Combine
colors`. Written by hand."""

NAME = '.SVS toon ndl'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Toon shading', 'NodeSocketFloat')
    t.socket('OUTPUT', 'N.L', 'NodeSocketFloat')
    t.socket('INPUT', 'Toon shading', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'N.L light', 'NodeSocketFloat', default_value=0.828421950340271, min_value=-1.0, max_value=1.0)
    t.socket('INPUT', 'N.L dark', 'NodeSocketFloat', default_value=-0.9444175958633423, min_value=-1.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-400, 0))
    t.make('NodeGroupOutput', 'out', (300, 0))
    t.make('ShaderNodeMix', 'ndl', (0, -100), {'data_type': 'FLOAT', 'clamp_factor': False},
           {'Factor_Float': ('in', 'Toon shading'), 'A_Float': ('in', 'N.L dark'), 'B_Float': ('in', 'N.L light')})
    t.link('in', 'Toon shading', 'out', 'Toon shading')
    t.link('ndl', 'Result_Float', 'out', 'N.L')
    return t
