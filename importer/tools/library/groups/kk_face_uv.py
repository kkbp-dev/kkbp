"""`.KK face uv`: where create_head reads `_Texture4` and `_Texture5` (models.face_uv): `(uv + Place.xy)
* s - s + 0.5` on the first UV map, s = 1 - (Place.z, Place w). The image node applies the texture's
own offset and scale after. Written by hand."""

NAME = '.KK face uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('INPUT', 'Place', 'NodeSocketVector', default_value=(0.0, 0.0, 0.0))
    t.socket('INPUT', 'Place w', 'NodeSocketFloat', default_value=0.0)
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (500, 0))
    t.make('ShaderNodeUVMap', 'uv', (-700, 250), {'uv_map': 'uv_main'})
    t.make('ShaderNodeSeparateXYZ', 'place', (-700, 0), ins={'Vector': ('in', 'Place')})
    su = t.math('s.u', 'SUBTRACT', 1.0, ('place', 'Z'), location=(-500, -100))
    sv = t.math('s.v', 'SUBTRACT', 1.0, ('in', 'Place w'), location=(-500, -250))
    t.make('ShaderNodeCombineXYZ', 'offset', (-500, 100), ins={'X': ('place', 'X'), 'Y': ('place', 'Y'), 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'moved', (-300, 200), {'operation': 'ADD'},
           {'Vector': ('uv', 'UV'), 'Vector_001': ('offset', 'Vector')})
    t.make('ShaderNodeCombineXYZ', 's', (-300, -150), ins={'X': su, 'Y': sv, 'Z': 1.0})
    t.make('ShaderNodeVectorMath', 'scaled', (-100, 200), {'operation': 'MULTIPLY'},
           {'Vector': ('moved', 'Vector'), 'Vector_001': ('s', 'Vector')})
    t.make('ShaderNodeCombineXYZ', 'shift', (-100, -150), ins={
        'X': t.math('shift.u', 'SUBTRACT', 0.5, su, location=(-300, -350)),
        'Y': t.math('shift.v', 'SUBTRACT', 0.5, sv, location=(-300, -500)), 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'placed', (150, 200), {'operation': 'ADD'},
           {'Vector': ('scaled', 'Vector'), 'Vector_001': ('shift', 'Vector')})
    t.link('placed', 'Vector', 'out', 'Vector')
    return t
