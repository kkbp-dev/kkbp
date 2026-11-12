"""`KK create_body`: the edit template for KK's body, which the game composites with create_body and
draws with main_skin (issue 30). Written by hand."""

import edit_templates

NAME = 'KK create_body'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["plain", "color_mask", "texture4", "texture3", "texture6", "paint_mask",
                                         *edit_templates.SKIN_SLOTS])
    for k, slot in ((1, "texture3"), (2, "texture6")):
        t.make('ShaderNodeGroup', f'paint{k}', (-1700, 300 - (3 + k - 1) * 320), {'node_tree': lib.group('.KK paint uv')})
        t.link(f'paint{k}', 'Vector', f'tex.{slot}', 'Vector')
    t.make('ShaderNodeGroup', 'create', (-800, 600), {'node_tree': lib.group('.KK create_body'), 'width': 240.0},
           {'Main': ('encode.plain', 'Color'), 'Color mask': ('encode.color_mask', 'Color'),
            'Tan': ('encode.texture4', 'Color'), 'Paint 1': ('encode.texture3', 'Color'), 'Paint 1 alpha': ('tex.texture3', 'Alpha'),
            'Paint 2': ('encode.texture6', 'Color'), 'Paint 2 alpha': ('tex.texture6', 'Alpha'),
            'Paint mask': ('encode.paint_mask', 'Color')})
    edit_templates.skin(t, lib, 'create')
    return t
