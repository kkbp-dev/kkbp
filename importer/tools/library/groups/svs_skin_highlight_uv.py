"""`.SVS skin highlight uv`: where SVS's body shader reads its highlight and the ramp that dims it
(models.highlight_uv): the UV moved by 0.4 (Height - 1) times the light's x and y (Light xy
or Dark xy, picked by the toon value), and the ramp at clamp(N.L - 0.4 * Detail's green). Written by
hand."""

NAME = '.SVS skin highlight uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Highlight', 'NodeSocketVector')
    t.socket('OUTPUT', 'Ramp', 'NodeSocketVector')
    t.socket('INPUT', 'Toon shading', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Height', 'NodeSocketFloat', default_value=0.95)
    t.socket('INPUT', 'Light xy', 'NodeSocketVector', default_value=(0.3629303574562073, 0.4266132414340973, 0.0))
    t.socket('INPUT', 'Dark xy', 'NodeSocketVector', default_value=(0.05610156059265137, 0.32392600178718567, 0.0))
    t.socket('INPUT', 'Detail', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'N.L', 'NodeSocketFloat', default_value=0.828421950340271, min_value=-1.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (600, 0))
    m = t.math
    t.make('ShaderNodeUVMap', 'uv', (-700, 400))
    t.make('ShaderNodeMix', 'xy', (-600, 200), {'data_type': 'VECTOR', 'clamp_factor': False},
           {'Factor_Float': ('in', 'Toon shading'), 'A_Vector': ('in', 'Dark xy'), 'B_Vector': ('in', 'Light xy')})
    k = m('k', 'MULTIPLY_ADD', ('in', 'Height'), 0.4, -0.4, location=(-600, 0))
    t.make('ShaderNodeCombineXYZ', 'k.v', (-450, 0), ins={'X': k, 'Y': k, 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'moved', (-300, 300), {'operation': 'MULTIPLY_ADD'},
           {'Vector': ('xy', 'Result_Vector'), 'Vector_001': ('k.v', 'Vector'), 'Vector_002': ('uv', 'UV')})
    t.link('moved', 'Vector', 'out', 'Highlight')
    t.make('ShaderNodeSeparateColor', 'detail', (-700, -300), ins={'Color': ('in', 'Detail')})
    r = m('ramp', 'MULTIPLY_ADD', ('detail', 'Green'), -0.4, ('in', 'N.L'), location=(-400, -300), clamp=True)
    t.make('ShaderNodeCombineXYZ', 'ramp.v', (-200, -300), ins={'X': r, 'Y': r})
    t.link('ramp.v', 'Vector', 'out', 'Ramp')
    return t
