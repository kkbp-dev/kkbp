"""`.KK create_eyewhite`: KK's create_eyewhite and KKS's Koikano/create_eyew, which composite the eye
white's texture: its two colours by the base texture's red, `lerp(Color 2, Color, main.r)`
(models.create_eyewhite). Colours are linear; Main is the texture's stored value. Written by hand."""

NAME = '.KK create_eyewhite'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Color', 'NodeSocketColor')
    t.socket('INPUT', 'Main', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Color', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.socket('INPUT', 'Color 2', 'NodeSocketColor', default_value=(1.0, 1.0, 1.0, 1.0))
    t.make('NodeGroupInput', 'in', (-600, 0))
    t.make('NodeGroupOutput', 'out', (400, 0))
    t.make('ShaderNodeSeparateColor', 'main', (-350, 150), ins={'Color': ('in', 'Main')})
    t.make('ShaderNodeMix', 'mix', (100, 0), {'data_type': 'RGBA'},
           {'Factor_Float': ('main', 'Red'), 'A_Color': ('in', 'Color 2'), 'B_Color': ('in', 'Color')})
    t.link('mix', 'Result_Color', 'out', 'Color')
    return t
