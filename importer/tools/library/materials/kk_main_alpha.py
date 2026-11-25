"""`KK main_alpha`: the edit template for KK's see-through clothes and accessories, which the game
composites with create_topN (or not: an accessory's own texture) and draws with main_alpha.
Written by hand."""

import edit_templates

NAME = 'KK main_alpha'


def build(lib):
    return edit_templates.clothes(lib, NAME, '.KK main_alpha', {'Detail mask': ('encode.detail_mask', 'Color')})
