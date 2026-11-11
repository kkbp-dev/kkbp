"""`KK main_opaque`: the edit template for KK's clothes, which the game composites with create_topN
and draws with main_opaque (issue 30). Written by hand."""

import edit_templates

NAME = 'KK main_opaque'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["plain", "color_mask", "pattern_mask1", "pattern_mask2", "pattern_mask3",
                                         "detail_mask", "line_mask"])
    ins = {'Main': ('encode.plain', 'Color'), 'Main alpha': ('tex.plain', 'Alpha'),
           'Color mask': ('encode.color_mask', 'Color')}
    for k in (1, 2, 3):
        t.make('ShaderNodeGroup', f'pattern{k}', (-1700, 300 - (k + 1) * 320), {'node_tree': lib.group('.KK pattern uv')})
        t.link(f'pattern{k}', 'Vector', f'tex.pattern_mask{k}', 'Vector')
        ins[f'Pattern {k}'] = (f'encode.pattern_mask{k}', 'Color')
    t.make('ShaderNodeGroup', 'create', (-800, 400), {'node_tree': lib.group('.KK create_topN'), 'width': 240.0}, ins)
    t.make('ShaderNodeGroup', 'lit', (-450, 100), {'node_tree': lib.group('.KK main_opaque'), 'width': 240.0},
           {'Main': ('create', 'Color'), 'Detail mask': ('encode.detail_mask', 'Color'),
            'Line mask': ('encode.line_mask', 'Color')})
    t.link('create', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
