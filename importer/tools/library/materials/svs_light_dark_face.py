"""`SVS Light Dark Face`: `SVS Light Dark` with the face's bakes without eyeshadow and the group that
fades between the two (issue 38, ADR 0046). Written by hand from svs_light_dark.py."""

NAME = 'SVS Light Dark Face'


def build(lib):
    t = lib.new_material(NAME, props={
            'use_backface_culling_lightprobe_volume': False,
        })

    t.node('ShaderNodeOutputMaterial', 'Material Output', props={
        'location': (-320.16373, 288.63107),
    })
    t.node('ShaderNodeTexImage', 'tex.permalight_mask', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1284.0472, 301.05417),
        'width': 495.81143,
        'label': 'tex.permalight_mask',
        'hide': True,
    })
    t.node('ShaderNodeUVMap', 'UV Map.001', props={
        'location': (-1838.1248, 420.2532),
        'width': 150.0,
    })
    t.node('ShaderNodeTexImage', 'tex.normal', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1282.9086, 459.86133),
        'width': 489.18396,
        'label': 'tex.normal',
        'hide': True,
    })
    t.node('ShaderNodeTexImage', 'tex.detail_normal', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1284.7612, 400.76447),
        'width': 492.27393,
        'label': 'tex.detail_normal',
        'hide': True,
        'image': lib.image('Template: Normal detail placeholder'),
    })
    t.node('ShaderNodeTexImage', 'tex.main.dark', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1296.8907, 80.34426),
        'width': 495.81143,
        'label': 'tex.main.dark',
        'hide': True,
        'image': lib.image('Template: Placeholder'),
    })
    t.node('ShaderNodeTexImage', 'tex.main.light', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1293.8973, 188.25989),
        'width': 495.81143,
        'label': 'tex.main.light',
        'hide': True,
        'show_texture': True,
        'image': lib.image('Template: Placeholder'),
    })
    t.node('ShaderNodeTexImage', 'tex.alpha_mask', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1310.1515, -99.58501),
        'width': 495.81143,
        'label': 'tex.alpha_mask',
        'hide': True,
        'image': lib.image('Template: BlackWithAlpha'),
    })
    t.node('ShaderNodeMapping', 'UV Scale', props={
        'location': (-1673.311, 280.45923),
        'label': 'UV Scale',
        'vector_type': 'VECTOR',
    })
    t.node('ShaderNodeTexImage', 'tex.alpha_mask_bottom', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1303.5708, -18.501923),
        'width': 495.81143,
        'label': 'tex.alpha_mask_bottom',
        'hide': True,
        'image': lib.image('Template: BlackWithAlpha'),
    })
    t.node('ShaderNodeGroup', 'shader', props={
        'node_tree': lib.group('.SVS'),
        'location': (-647.576, 308.9397),
        'width': 284.3376,
    })
    for variant, y in (('light', -180.0), ('dark', -260.0)):
        name = f'tex.main.{variant}_no_eyeshadow'
        t.node('ShaderNodeTexImage', name, outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
            'location': (-1296.8907, y),
            'width': 495.81143,
            'label': name,
            'hide': True,
            'image': lib.image('Template: Placeholder'),
        })
    t.node('ShaderNodeGroup', 'eyeshadow', props={
        'node_tree': lib.group('.Eyeshadow'),
        'location': (-760.0, 60.0),
        'hide': True,
        'label': 'eyeshadow',
    })
    t.node('NodeReroute', 'Reroute', props={
        'location': (-1345.9197, 143.05667),
        'socket_idname': 'NodeSocketVector',
    })

    t.link('Reroute', 'Output', 'tex.main.light', 'Vector')
    t.link('Reroute', 'Output', 'tex.main.dark', 'Vector')
    t.link('Reroute', 'Output', 'tex.main.light_no_eyeshadow', 'Vector')
    t.link('Reroute', 'Output', 'tex.main.dark_no_eyeshadow', 'Vector')
    t.link('UV Map.001', 'UV', 'UV Scale', 'Vector')
    t.link('UV Scale', 'Vector', 'tex.normal', 'Vector')
    t.link('UV Scale', 'Vector', 'tex.detail_normal', 'Vector')
    t.link('UV Scale', 'Vector', 'tex.alpha_mask_bottom', 'Vector')
    t.link('UV Scale', 'Vector', 'tex.alpha_mask', 'Vector')
    t.link('shader', 'Shader', 'Material Output', 'Surface')
    t.link('tex.main.dark', 'Color', 'eyeshadow', 'Dark')
    t.link('tex.main.dark_no_eyeshadow', 'Color', 'eyeshadow', 'Dark without')
    t.link('eyeshadow', 'Dark', 'shader', 'Dark')
    t.link('tex.detail_normal', 'Color', 'shader', 'Normal detail')
    t.link('tex.normal', 'Alpha', 'shader', 'Normal alpha')
    t.link('tex.alpha_mask_bottom', 'Color', 'shader', 'Alpha mask bottom')
    t.link('tex.alpha_mask', 'Color', 'shader', 'Alpha mask')
    t.link('tex.alpha_mask', 'Alpha', 'shader', 'Alpha mask alpha')
    t.link('tex.main.light', 'Color', 'eyeshadow', 'Light')
    t.link('tex.main.light_no_eyeshadow', 'Color', 'eyeshadow', 'Light without')
    t.link('eyeshadow', 'Light', 'shader', 'Light')
    t.link('tex.normal', 'Color', 'shader', 'Normal')
    t.link('tex.detail_normal', 'Alpha', 'shader', 'Normal detail alpha')
    t.link('tex.permalight_mask', 'Color', 'shader', 'Permalight mask')
    t.link('tex.alpha_mask_bottom', 'Alpha', 'shader', 'Alpha mask bottom alpha')
    t.link('tex.main.light', 'Alpha', 'shader', 'Light alpha')
    t.link('UV Map.001', 'UV', 'Reroute', 'Input')
    return t
