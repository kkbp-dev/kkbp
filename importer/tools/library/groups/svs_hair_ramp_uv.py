"""`.SVS hair ramp uv`: where SVS's hair shader reads its ramp, along the ramp's diagonal, on the bake
quad (models.hair_ramp_uv, issue 62): k = 1 - 0.5 * Detail 1's green, Ramp 1 at clamp(k * clamp(N.L)),
Ramp 2 at clamp(k * clamp(N.L * 0.4 + 0.3)). Written by hand."""

NAME = '.SVS hair ramp uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Ramp 1', 'NodeSocketVector')
    t.socket('OUTPUT', 'Ramp 2', 'NodeSocketVector')
    t.socket('INPUT', 'Detail 1', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'N.L', 'NodeSocketFloat', default_value=0.828421950340271, min_value=-1.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-700, 0))
    t.make('NodeGroupOutput', 'out', (500, 0))
    t.make('ShaderNodeSeparateColor', 'detail', (-500, 200), ins={'Color': ('in', 'Detail 1')})
    k = t.math('k', 'MULTIPLY_ADD', ('detail', 'Green'), -0.5, 1.0, location=(-300, 200))
    a = t.math('ramp1', 'MULTIPLY', k, t.math('ndl', 'ADD', ('in', 'N.L'), 0.0, location=(-500, 0), clamp=True),
               location=(-100, 100), clamp=True)
    b = t.math('ramp2', 'MULTIPLY', k, t.math('ndl2', 'MULTIPLY_ADD', ('in', 'N.L'), 0.4, 0.3, location=(-500, -150), clamp=True),
               location=(-100, -100), clamp=True)
    for name, x in (('Ramp 1', a), ('Ramp 2', b)):
        t.make('ShaderNodeCombineXYZ', name, (150, 100 if name == 'Ramp 1' else -100), ins={'X': x, 'Y': x})
        t.link(name, 'Vector', 'out', name)
    return t
