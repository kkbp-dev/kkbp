"""`KK main_emblem`: the edit template for KK's clothes emblems, drawn with main_emblem straight from
their texture (issue 30). Written by hand."""

import edit_templates

NAME = 'KK main_emblem'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["main"])
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.KK main_emblem'), 'width': 220.0},
           {'Main': ('encode.main', 'Color'), 'Main alpha': ('tex.main', 'Alpha')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
