"""`SVS lif_main_eyebrow`: the edit template for SVS's eyebrows, which the game draws with
LIF/lif_main_eyebrow straight from its texture. No grade: SVS's bake has none. Written by
hand."""

import edit_templates

NAME = 'SVS lif_main_eyebrow'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["eyebrow"], grade=False)
    t.make('ShaderNodeGroup', 'uv', (-1700, 300), {'node_tree': lib.group('.SVS eyebrow uv')})
    t.link('uv', 'Vector', 'tex.eyebrow', 'Vector')
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.SVS face part'), 'width': 240.0},
           {'Texture': ('encode.eyebrow', 'Color'), 'Texture alpha': ('tex.eyebrow', 'Alpha')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
