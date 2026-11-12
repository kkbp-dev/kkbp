"""`.KK pattern uv`: where create_topN reads a pattern mask, `uv * (20 - 19 * Scale)` per axis on the
first UV map; the image node it feeds applies the mask's own offset and scale. Written by hand."""

NAME = '.KK pattern uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Scale u', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Scale v', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-700, 0))
    t.make('NodeGroupOutput', 'out', (300, 0))
    t.make('ShaderNodeUVMap', 'uv', (-300, 200), {'uv_map': 'uv_main'})
    u = t.math('repeat.u', 'MULTIPLY_ADD', ('in', 'Scale u'), -19.0, 20.0, location=(-450, -50))
    v = t.math('repeat.v', 'MULTIPLY_ADD', ('in', 'Scale v'), -19.0, 20.0, location=(-450, -200))
    t.make('ShaderNodeCombineXYZ', 'repeat', (-250, -100), ins={'X': u, 'Y': v, 'Z': 1.0})
    t.make('ShaderNodeVectorMath', 'scaled', (0, 100), {'operation': 'MULTIPLY'},
           {'Vector': ('uv', 'UV'), 'Vector_001': ('repeat', 'Vector')})
    t.link('scaled', 'Vector', 'out', 'Vector')
    return t
