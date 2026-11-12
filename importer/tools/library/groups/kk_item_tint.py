"""`.KK item tint`: ShadeAdjustItem, the shadow tint of KK's clothes and items (models.item_tint), and
main_skin's (models.skin_tint, Saturation 0.66 and a white Shadow color): the hue of Color * Shadow
color at Saturation of its saturation and value 1, at 0.9, overlaid with the ambient shadow by
`.KK shadow tint`. Blender's HSV separate and combine are the shader's own
rgb-to-hsv and hsv-to-rgb. Linear colours. Written by hand."""

NAME = '.KK item tint'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Tint', 'NodeSocketColor')
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Shadow color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Ambient', 'NodeSocketColor', default_value=(0.15, 0.15, 0.15, 1.0))
    t.socket('INPUT', 'Ambient strength', 'NodeSocketFloat', default_value=0.15, min_value=0.0, max_value=1.0)
    t.socket('INPUT', 'Saturation', 'NodeSocketFloat', default_value=0.5, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1000, 0))
    t.make('NodeGroupOutput', 'out', (600, 0))

    t.make('ShaderNodeVectorMath', 'shadowed', (-750, 100), {'operation': 'MULTIPLY'},
           {'Vector': ('in', 'Color'), 'Vector_001': ('in', 'Shadow color')})
    t.make('ShaderNodeSeparateColor', 'hsv', (-550, 100), {'mode': 'HSV'}, {'Color': ('shadowed', 'Vector')})
    half = t.math('half', 'MULTIPLY', ('hsv', 'Green'), ('in', 'Saturation'), location=(-350, 50))
    t.make('ShaderNodeCombineColor', 'pastel', (-150, 100), {'mode': 'HSV'},
           {'Red': ('hsv', 'Red'), 'Green': half, 'Blue': 1.0})
    t.make('ShaderNodeVectorMath', 'scaled', (50, 100), {'operation': 'SCALE'},
           {'Vector': ('pastel', 'Color'), 'Scale': 0.9})
    t.make('ShaderNodeGroup', 'tint', (300, 0), {'node_tree': lib.group('.KK shadow tint'), 'width': 200.0},
           {'Shadow color': ('scaled', 'Vector'), 'Ambient': ('in', 'Ambient'),
            'Ambient strength': ('in', 'Ambient strength')})
    t.link('tint', 'Tint', 'out', 'Tint')
    return t
