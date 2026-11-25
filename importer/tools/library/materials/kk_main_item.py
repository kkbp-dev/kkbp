"""`KK main_item`: the edit template for KK's teeth, tongue and items, which the game draws with
main_item straight from their textures. An item's `_AnotherRamp` is read at the toon value
(`.KK ramp uv`), through which the toon value reaches `.Combine colors`; the bake sets it there.
Written by hand."""

import edit_templates

NAME = 'KK main_item'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["main", "color_mask", "detail_mask", "line_mask", "another_ramp"])
    edit_templates.clamp(t, "another_ramp")
    t.make('ShaderNodeGroup', 'ramp', (-1700, -1000), {'node_tree': lib.group('.KK ramp uv')})
    t.link('ramp', 'Vector', 'tex.another_ramp', 'Vector')
    edit_templates.toon_through(t, 'ramp')
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.KK main_item'), 'width': 240.0},
           {'Main': ('encode.main', 'Color'), 'Main alpha': ('tex.main', 'Alpha'),
            'Color mask': ('encode.color_mask', 'Color'), 'Detail mask': ('encode.detail_mask', 'Color'),
            'Line mask': ('encode.line_mask', 'Color'), 'Another ramp': ('encode.another_ramp', 'Color')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
