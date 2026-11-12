"""`KK create_head`: the edit template for KK's face, which the game composites with create_head and
draws with main_skin (issue 30). Written by hand."""

import edit_templates

NAME = 'KK create_head'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["plain", "color_mask", "texture4", "texture5", "texture3", "texture7", "texture6",
                                         "paint_mask", *edit_templates.SKIN_SLOTS])
    for k, slot in ((4, "texture4"), (5, "texture5")):
        t.make('ShaderNodeGroup', f'place{k}', (-1700, 300 - (k - 2) * 320), {'node_tree': lib.group('.KK face uv')})
        t.link(f'place{k}', 'Vector', f'tex.{slot}', 'Vector')
    for name, slot, row, turn in (('paint1', 'texture3', 4, 1.0), ('paint2', 'texture7', 5, 1.0), ('mole', 'texture6', 6, 0.0)):
        t.make('ShaderNodeGroup', name, (-1700, 300 - row * 320), {'node_tree': lib.group('.KK paint uv')}, {'Turn': turn})
        t.link(name, 'Vector', f'tex.{slot}', 'Vector')
    ins = {'Main': ('encode.plain', 'Color'), 'Color mask': ('encode.color_mask', 'Color'),
           'Paint mask': ('encode.paint_mask', 'Color')}
    for name, slot in (('Texture 4', 'texture4'), ('Texture 5', 'texture5'), ('Paint 1', 'texture3'),
                       ('Paint 2', 'texture7'), ('Mole', 'texture6')):
        ins[name] = (f'encode.{slot}', 'Color')
        ins[f'{name} alpha'] = (f'tex.{slot}', 'Alpha')
    t.make('ShaderNodeGroup', 'create', (-800, 600), {'node_tree': lib.group('.KK create_head'), 'width': 240.0}, ins)
    edit_templates.skin(t, lib, 'create')
    return t
