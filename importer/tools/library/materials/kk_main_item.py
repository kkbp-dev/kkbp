"""`KK main_item`: the edit template for KK's teeth, tongue and items, which the game draws with
main_item straight from their textures (issue 30). Written by hand."""

import edit_templates

NAME = 'KK main_item'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["main", "color_mask", "detail_mask", "line_mask"])
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.KK main_item'), 'width': 240.0},
           {'Main': ('encode.main', 'Color'), 'Main alpha': ('tex.main', 'Alpha'),
            'Color mask': ('encode.color_mask', 'Color'), 'Detail mask': ('encode.detail_mask', 'Color'),
            'Line mask': ('encode.line_mask', 'Color')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
