"""`.SVS ramp uv`: where SVS's hair, item and clothes shaders read their ramp, along the ramp's
diagonal, on the bake quad (models.hair_ramp_uv, item_ramp_uv, cloth_ramp_uv):
k = 1 - Pull * Detail's green, l = Lift detail's red * Lift, Ramp 1 at clamp(k * clamp(clamp(N.L) + l)),
Ramp 2 at clamp(l / 2 + k * clamp(N.L * 0.4 + 0.3)). The hair pulls by 0.5, the items and clothes by
`_ShadowSetting.b`; the clothes lift by `_Detail_mask_02`'s red times `_RimScale`. Written by hand."""

NAME = '.SVS ramp uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Ramp 1', 'NodeSocketVector')
    t.socket('OUTPUT', 'Ramp 2', 'NodeSocketVector')
    t.socket('INPUT', 'Detail', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Pull', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Lift detail', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Lift', 'NodeSocketFloat', default_value=0.0)
    t.socket('INPUT', 'N.L', 'NodeSocketFloat', default_value=0.828421950340271, min_value=-1.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-700, 0))
    t.make('NodeGroupOutput', 'out', (500, 0))
    t.make('ShaderNodeSeparateColor', 'detail', (-500, 200), ins={'Color': ('in', 'Detail')})
    k = t.math('k', 'SUBTRACT', 1.0, t.math('k.pull', 'MULTIPLY', ('detail', 'Green'), ('in', 'Pull'), location=(-400, 300)),
               location=(-300, 200))
    t.make('ShaderNodeSeparateColor', 'lift.detail', (-700, -300), ins={'Color': ('in', 'Lift detail')})
    lift = t.math('lift', 'MULTIPLY', ('lift.detail', 'Red'), ('in', 'Lift'), location=(-500, -300))
    a = t.math('ramp1', 'MULTIPLY', k, t.math('ndl.lift', 'ADD', t.math('ndl', 'ADD', ('in', 'N.L'), 0.0, location=(-500, 0), clamp=True),
               lift, location=(-350, 0), clamp=True), location=(-100, 100), clamp=True)
    b = t.math('ramp2', 'MULTIPLY_ADD', k, t.math('ndl2', 'MULTIPLY_ADD', ('in', 'N.L'), 0.4, 0.3, location=(-500, -150), clamp=True),
               t.math('lift.half', 'MULTIPLY', lift, 0.5, location=(-350, -300)), location=(-100, -100), clamp=True)
    for name, x in (('Ramp 1', a), ('Ramp 2', b)):
        t.make('ShaderNodeCombineXYZ', name, (150, 100 if name == 'Ramp 1' else -100), ins={'X': x, 'Y': x})
        t.link(name, 'Vector', 'out', name)
    return t
