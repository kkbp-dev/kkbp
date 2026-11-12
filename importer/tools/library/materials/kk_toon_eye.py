"""`KK toon_eye`: the edit template for KK's irises, which the game draws with toon_eye_lod0 from the
composited iris (issue 30). The highlights read the second and third UV maps. Written by hand."""

import edit_templates

NAME = 'KK toon_eye'


def build(lib):
    t = edit_templates.begin(lib, NAME, ["main", "overlay1", "overlay2"])
    t.make('ShaderNodeGroup', 'iris', (-1700, 300), {'node_tree': lib.group('.KK eye uv')})
    t.link('iris', 'Vector', 'tex.main', 'Vector')
    for k, uv_map in ((1, 'uv_nipple_and_shine'), (2, 'uv_underhair')):
        t.make('ShaderNodeUVMap', f'uv{k}', (-1700, 300 - k * 320), {'uv_map': uv_map})
        t.link(f'uv{k}', 'UV', f'tex.overlay{k}', 'Vector')
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.KK toon_eye'), 'width': 240.0},
           {'Main': ('encode.main', 'Color'), 'Main alpha': ('tex.main', 'Alpha'),
            'Overlay 1 alpha': ('tex.overlay1', 'Alpha'), 'Overlay 2 alpha': ('tex.overlay2', 'Alpha')})
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
