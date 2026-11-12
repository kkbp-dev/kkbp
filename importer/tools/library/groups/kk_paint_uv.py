"""`.KK paint uv`: where create_body and create_head read a paint or the mole (models.paint_uv,
mole_uv): `(uv + Paint.xy) * 2s + 0.5 - s` on the first UV map, s = 2 - 2 * Paint w, turned about the
middle by Paint.z turns when Turn is 1 (the paints; the mole doesn't turn). The image node applies the
texture's own offset and scale after. Written by hand."""

NAME = '.KK paint uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Paint', 'NodeSocketVector', default_value=(0.0, 0.0, 0.0))
    t.socket('INPUT', 'Paint w', 'NodeSocketFloat', default_value=0.0)
    t.socket('INPUT', 'Turn', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (600, 0))
    t.make('ShaderNodeUVMap', 'uv', (-700, 250), {'uv_map': 'uv_main'})
    t.make('ShaderNodeSeparateXYZ', 'paint', (-700, 0), ins={'Vector': ('in', 'Paint')})
    s = t.math('s', 'MULTIPLY_ADD', ('in', 'Paint w'), -2.0, 2.0, location=(-700, -250))
    t.make('ShaderNodeCombineXYZ', 'offset', (-500, 50), ins={'X': ('paint', 'X'), 'Y': ('paint', 'Y'), 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'moved', (-300, 200), {'operation': 'ADD'},
           {'Vector': ('uv', 'UV'), 'Vector_001': ('offset', 'Vector')})
    t.make('ShaderNodeVectorMath', 'scaled', (-100, 200), {'operation': 'SCALE'},
           {'Vector': ('moved', 'Vector'), 'Scale': t.math('s.twice', 'MULTIPLY', s, 2.0, location=(-500, -250))})
    shift = t.math('shift', 'SUBTRACT', 0.5, s, location=(-300, -250))
    t.make('ShaderNodeCombineXYZ', 'shift.v', (-100, -150), ins={'X': shift, 'Y': shift, 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'placed', (100, 200), {'operation': 'ADD'},
           {'Vector': ('scaled', 'Vector'), 'Vector_001': ('shift.v', 'Vector')})
    angle = t.math('angle', 'MULTIPLY', t.math('turns', 'MULTIPLY', ('paint', 'Z'), ('in', 'Turn'), location=(-100, -350)),
                   -6.283185307179586, location=(100, -350))
    t.make('ShaderNodeVectorRotate', 'turn', (350, 150), {'rotation_type': 'Z_AXIS'},
           {'Vector': ('placed', 'Vector'), 'Center': (0.5, 0.5, 0.0), 'Angle': angle})
    t.link('turn', 'Vector', 'out', 'Vector')
    return t
