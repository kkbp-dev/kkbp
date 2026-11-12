"""`.KK eye uv`: where toon_eye_lod0 reads the iris (models.eye_rotation): the first UV map turned
about its middle by Rotation turns; the image node it feeds applies the texture's own offset and
scale after. Written by hand."""

NAME = '.KK eye uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Rotation', 'NodeSocketFloat', default_value=0.0, min_value=-1.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-700, 0))
    t.make('NodeGroupOutput', 'out', (500, 0))
    t.make('ShaderNodeUVMap', 'uv', (-500, 200), {'uv_map': 'uv_main'})
    angle = t.math('angle', 'MULTIPLY', ('in', 'Rotation'), -6.283185307179586, location=(-500, -100))
    # x' = x cos + y sin, y' = -x sin + y cos: a turn by -angle about z, around (0.5, 0.5).
    t.make('ShaderNodeVectorRotate', 'turn', (0, 100), {'rotation_type': 'Z_AXIS'},
           {'Vector': ('uv', 'UV'), 'Center': (0.5, 0.5, 0.0), 'Angle': angle})
    t.link('turn', 'Vector', 'out', 'Vector')
    return t
