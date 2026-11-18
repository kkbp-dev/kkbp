"""`SVS lif_main_eyelash_up`: the edit template for SVS's eyelashes, which the game draws with
LIF/lif_main_eyelash_up from its upper and lower eyelash textures, the lower over the upper by its
alpha (issue 62). No grade: SVS's bake has none. Written by hand."""

import edit_templates

NAME = 'SVS lif_main_eyelash_up'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["eyelash_up", "eyelash_down"], grade=False)
    t.make('ShaderNodeMix', 'texture', (-850, 300), {'data_type': 'RGBA'},
           {'Factor_Float': ('tex.eyelash_down', 'Alpha'), 'A_Color': ('encode.eyelash_up', 'Color'),
            'B_Color': ('encode.eyelash_down', 'Color')})
    alpha = t.math('texture.alpha', 'MAXIMUM', ('tex.eyelash_up', 'Alpha'), ('tex.eyelash_down', 'Alpha'), location=(-850, 0))
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.SVS face part'), 'width': 240.0},
           {'Texture': ('texture', 'Result_Color'), 'Texture alpha': alpha, 'By alpha': 0.0, 'Alpha cut': 0.9})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
