"""`KK toon_nose`: the edit template for KK's nose line, which toon_nose_lod0 draws unlit, so light
and dark are the same. Written by hand."""

import edit_templates

NAME = 'KK toon_nose'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["main"], props={"use_backface_culling": True})
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.KK toon_nose'), 'width': 220.0},
           {'Main': ('encode.main', 'Color'), 'Main alpha': ('tex.main', 'Alpha')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit', 'Color', 'Color')
    return t
