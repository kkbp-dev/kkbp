"""`KK main_hair`: the edit template for KK's hair, which the game draws with main_hair or
main_hair_front (issue 30). The toon value reaches `.Combine colors` through `.KK hair gloss uv`,
which moves the gloss with it; the bake sets it there. Written by hand."""

import edit_templates

NAME = 'KK main_hair'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["main", "color_mask", "detail_mask", "hair_gloss"])
    t.make('ShaderNodeGroup', 'gloss', (-1700, -900), {'node_tree': lib.group('.KK hair gloss uv'), 'width': 200.0})
    t.link('gloss', 'Vector', 'tex.hair_gloss', 'Vector')
    tree = t.tree
    toon = tree.nodes['combine'].inputs['Toon shading']
    for link in [l for l in tree.links if l.to_socket == toon]:
        tree.links.remove(link)
    t.link('shade', 'Toon shading', 'gloss', 'Toon shading')
    t.link('gloss', 'Toon shading', 'combine', 'Toon shading')

    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.KK main_hair'), 'width': 240.0},
           {'Main': ('encode.main', 'Color'), 'Main alpha': ('tex.main', 'Alpha'),
            'Color mask': ('encode.color_mask', 'Color'), 'Detail mask': ('encode.detail_mask', 'Color'),
            'Gloss': ('encode.hair_gloss', 'Color')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
