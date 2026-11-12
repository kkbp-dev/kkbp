"""`.KK hair gloss uv`: where KK's main_hair and main_hair_front read their `_HairGloss` highlight
(models.hair_gloss_shift): the second UV map, moved along u by the light,

    ndl   = Toon shading * 2 - 1                  1 lit from the front, -1 from behind
    shift = Front ? ndl * 0.02 + 0.99 : ndl * 0.005

The image node it feeds applies the texture's own offset and scale. Toon shading passes through: the
template routes its toon value here first, so the bake's fixed value (1 for light, 0 for dark) moves
the highlight as the game's light does, and in the viewport it slides with the shading. The bake's
plane under the mesh has its uv_main corners on every UV map, as the game's quad has. Written by hand."""

NAME = '.KK hair gloss uv'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Vector', 'NodeSocketVector')
    t.socket('OUTPUT', 'Toon shading', 'NodeSocketFloat')
    t.socket('INPUT', 'Toon shading', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Front', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-800, 0))
    t.make('NodeGroupOutput', 'out', (400, 0))

    t.make('ShaderNodeUVMap', 'uv', (-400, 250), {'uv_map': 'uv_nipple_and_shine'})
    ndl = t.math('ndl', 'MULTIPLY_ADD', ('in', 'Toon shading'), 2.0, -1.0, location=(-600, -100))
    back = t.math('shift.back', 'MULTIPLY', ndl, 0.005, location=(-400, -50))
    front = t.math('shift.front', 'MULTIPLY_ADD', ndl, 0.02, 0.99, location=(-400, -200))
    t.make('ShaderNodeMix', 'shift', (-200, -100), {'data_type': 'FLOAT'},
           {'Factor_Float': ('in', 'Front'), 'A_Float': back, 'B_Float': front})
    t.make('ShaderNodeCombineXYZ', 'offset', (0, -100), ins={'X': ('shift', 'Result_Float'), 'Y': 0.0, 'Z': 0.0})
    t.make('ShaderNodeVectorMath', 'moved', (200, 150), {'operation': 'ADD'},
           {'Vector': ('uv', 'UV'), 'Vector_001': ('offset', 'Vector')})
    t.link('moved', 'Vector', 'out', 'Vector')
    t.link('in', 'Toon shading', 'out', 'Toon shading')
    return t
