"""`KK create_eyewhite`: the edit template for KK's eye whites: create_eyewhite composites their
texture, toon_eyew_lod0 shades it. Opaque, as the game's composited texture is. Written
by hand."""

import edit_templates

NAME = 'KK create_eyewhite'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["create_main"], force_visibility=1.0)
    t.make('ShaderNodeGroup', 'create', (-800, 300), {'node_tree': lib.group('.KK create_eyewhite'), 'width': 220.0},
           {'Main': ('encode.create_main', 'Color')})
    t.make('ShaderNodeGroup', 'lit', (-450, 100), {'node_tree': lib.group('.KK toon_eyew'), 'width': 220.0},
           {'Main': ('create', 'Color')})
    edit_templates.light_dark(t, 'lit')
    return t
