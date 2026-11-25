"""`.SVS face ramp uv`: where SVS's face shader reads its ramp (models.face_ramp_uv), and the
detail it weights the shadow by: d = max(Detail 1.g, Nose.g); Ramp 1 at clamp(clamp(N.L + Detail 2.b / 2)
* (1 - d * Pull)), Ramp 2 at min(4 clamp(N.L * 0.4 + 0.3), 1); Detail is (0, d, 0). Written by hand."""

NAME = '.SVS face ramp uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Ramp 1', 'NodeSocketVector')
    t.socket('OUTPUT', 'Ramp 2', 'NodeSocketVector')
    t.socket('OUTPUT', 'Detail', 'NodeSocketColor')
    for name in ('Detail 1', 'Detail 2', 'Nose'):
        t.socket('INPUT', name, 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Pull', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'N.L', 'NodeSocketFloat', default_value=0.828421950340271, min_value=-1.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (600, 0))
    m = t.math
    for row, name in enumerate(('Detail 1', 'Detail 2', 'Nose')):
        t.make('ShaderNodeSeparateColor', name, (-700, 300 - row * 200), ins={'Color': ('in', name)})
    d = m('d', 'MAXIMUM', ('Detail 1', 'Green'), ('Nose', 'Green'), location=(-500, 300))
    k = m('k', 'MULTIPLY_ADD', d, m('k.pull', 'SUBTRACT', 0.0, ('in', 'Pull'), location=(-500, 200)), 1.0, location=(-350, 250))
    a = m('ramp1', 'MULTIPLY', m('ramp1.n', 'MULTIPLY_ADD', ('Detail 2', 'Blue'), 0.5, ('in', 'N.L'), location=(-350, 50), clamp=True), k,
          location=(-200, 100), clamp=True)
    b = m('ramp2', 'MINIMUM', m('ramp2.4', 'MULTIPLY', m('ramp2.n', 'MULTIPLY_ADD', ('in', 'N.L'), 0.4, 0.3, location=(-350, -150), clamp=True),
          4.0, location=(-200, -150)), 1.0, location=(-50, -150))
    for name, x, y in (('Ramp 1', a, 100), ('Ramp 2', b, -150)):
        t.make('ShaderNodeCombineXYZ', name, (150, y), ins={'X': x, 'Y': x})
        t.link(name, 'Vector', 'out', name)
    t.make('ShaderNodeCombineColor', 'detail', (150, 300), ins={'Red': 0.0, 'Green': d, 'Blue': 0.0})
    t.link('detail', 'Color', 'out', 'Detail')
    return t
