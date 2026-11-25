"""`KK main_opaque`: the edit template for KK's clothes, which the game composites with create_topN
and draws with main_opaque. Written by hand."""

import edit_templates

NAME = 'KK main_opaque'


def build(lib):
    return edit_templates.clothes(lib, NAME, '.KK main_opaque', {
        'Detail mask': ('encode.detail_mask', 'Color'), 'Line mask': ('encode.line_mask', 'Color')})
