"""`KK toon_eyew`: the edit template for KK's eyebrows and eyelines, which the game draws with
toon_eyew_lod0 straight from their texture (issue 30). Written by hand."""

import edit_templates

NAME = 'KK toon_eyew'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["main"])
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.KK toon_eyew'), 'width': 220.0},
           {'Main': ('encode.main', 'Color')})
    t.link('tex.main', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
