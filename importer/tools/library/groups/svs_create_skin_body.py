"""`.SVS create skin body`: SVS's body create shader (LIF/lif_create_main_skin_body) in nodes
(models.create_main_skin_body, issue 62).

    col   = mix(Main color, Sunburn color, Sunburn's red * Sunburn color alpha)
    Color = each paint k over col by its alpha * its colour's alpha * Paint mask's red, toward the paint
            times max(min(its alpha, smoothstep(clamp((saturation - 0.3) * 2.5))), Paint color k)

Each paint's alpha is times its `present` switch; a missing sunburn or paint mask reads black, as the
game's default. Linear colours. Written by hand."""

from svs_paints import paint_sockets, paints

NAME = '.SVS create skin body'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Sunburn', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    t.socket('INPUT', 'Paint mask', 'NodeSocketColor', default_value=(0.0, 0.0, 0.0, 1.0))
    paint_sockets(t)
    t.socket('INPUT', 'Main color', 'NodeSocketColor', default_value=(1.0, 0.76, 0.68, 1.0))
    t.socket('INPUT', 'Sunburn color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Sunburn color alpha', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0)
    t.make('NodeGroupInput', 'in', (-1400, 0))
    t.make('NodeGroupOutput', 'out', (1000, 0))
    t.make('ShaderNodeSeparateColor', 'sunburn', (-1200, 400), ins={'Color': ('in', 'Sunburn')})
    t.make('ShaderNodeSeparateColor', 'paint mask', (-1200, 0), ins={'Color': ('in', 'Paint mask')})
    t.make('ShaderNodeMix', 'burnt', (-900, 400), {'data_type': 'VECTOR'},
           {'Factor_Float': t.math('burn', 'MULTIPLY', ('sunburn', 'Red'), ('in', 'Sunburn color alpha'), location=(-1050, 500)),
            'A_Vector': ('in', 'Main color'), 'B_Vector': ('in', 'Sunburn color')})
    rgb = paints(t, ('burnt', 'Result_Vector'), ('Red', 'Red', 'Red'))
    t.link(rgb[0], rgb[1], 'out', 'Color')
    return t
