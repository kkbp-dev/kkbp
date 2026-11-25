"""`KK Light Dark Face`: `KK Light Dark` with the face's bakes without eyeshadow and the group that
fades between the two (ADR 0046). Written by hand from kk_light_dark.py."""

NAME = 'KK Light Dark Face'


def build(lib):
    t = lib.new_material(NAME, props={
            'use_backface_culling_lightprobe_volume': False,
        })

    t.node('ShaderNodeOutputMaterial', 'Material Output', props={
        'location': (-15.574121, 153.89597),
    })
    t.node('ShaderNodeTexImage', 'tex.permalight_mask', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1034.7039, 132.73479),
        'width': 495.81143,
        'label': 'tex.permalight_mask',
        'hide': True,
    })
    t.node('ShaderNodeUVMap', 'UV Map.001', props={
        'location': (-1591.76, 305.6142),
        'width': 150.0,
    })
    t.node('ShaderNodeTexImage', 'tex.normal', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1033.5652, 291.54193),
        'width': 489.18396,
        'label': 'tex.normal',
        'hide': True,
    })
    t.node('ShaderNodeTexImage', 'tex.detail_normal', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1035.4178, 232.44507),
        'width': 492.27393,
        'label': 'tex.detail_normal',
        'hide': True,
        'image': lib.image('Template: Normal detail placeholder'),
    })
    t.node('ShaderNodeTexImage', 'tex.main.dark', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1047.5474, -87.97512),
        'width': 495.81143,
        'label': 'tex.main.dark',
        'hide': True,
        'image': lib.image('Template: Placeholder'),
    })
    t.node('ShaderNodeTexImage', 'tex.main.light', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1044.554, 19.94051),
        'width': 495.81143,
        'label': 'tex.main.light',
        'hide': True,
        'show_texture': True,
        'image': lib.image('Template: Placeholder'),
    })
    t.node('ShaderNodeTexImage', 'tex.alpha_mask', outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
        'location': (-1053.2344, -168.05202),
        'width': 495.81143,
        'label': 'tex.alpha_mask',
        'hide': True,
        'image': lib.image('Template: Placeholder'),
    })
    t.node('ShaderNodeGroup', 'shader', props={
        'node_tree': lib.group('.KK'),
        'location': (-293.7166, 140.9407),
        'width': 274.96265,
        'label': 'KK Light Dark Texture',
    })
    t.node('ShaderNodeMapping', 'UV Scale', props={
        'location': (-1423.9677, 112.13985),
        'label': 'UV Scale',
        'vector_type': 'VECTOR',
    })
    for variant, y in (('light', -260.0), ('dark', -340.0)):
        name = f'tex.main.{variant}_no_eyeshadow'
        t.node('ShaderNodeTexImage', name, outputs={'Color': (0.0, 0.0, 0.0, 0.0)}, props={
            'location': (-1047.5474, y),
            'width': 495.81143,
            'label': name,
            'hide': True,
            'image': lib.image('Template: Placeholder'),
        })
    t.node('ShaderNodeGroup', 'eyeshadow', props={
        'node_tree': lib.group('.Eyeshadow'),
        'location': (-480.0, -80.0),
        'hide': True,
        'label': 'eyeshadow',
    })
    t.node('NodeReroute', 'Reroute', props={
        'location': (-1101.1786, -30.387344),
        'socket_idname': 'NodeSocketVector',
    })

    t.link('shader', 'Shader', 'Material Output', 'Surface')
    t.link('tex.alpha_mask', 'Alpha', 'shader', 'Alpha mask alpha')
    t.link('tex.detail_normal', 'Color', 'shader', 'Normal detail')
    t.link('tex.normal', 'Color', 'shader', 'Normal')
    t.link('tex.main.dark', 'Color', 'eyeshadow', 'Dark')
    t.link('tex.main.dark_no_eyeshadow', 'Color', 'eyeshadow', 'Dark without')
    t.link('eyeshadow', 'Dark', 'shader', 'Dark')
    t.link('tex.detail_normal', 'Alpha', 'shader', 'Normal detail alpha')
    t.link('tex.normal', 'Alpha', 'shader', 'Normal alpha')
    t.link('tex.main.light', 'Alpha', 'shader', 'Light alpha')
    t.link('tex.permalight_mask', 'Color', 'shader', 'Permalight mask')
    t.link('tex.alpha_mask', 'Color', 'shader', 'Alpha mask')
    t.link('tex.main.light', 'Color', 'eyeshadow', 'Light')
    t.link('tex.main.light_no_eyeshadow', 'Color', 'eyeshadow', 'Light without')
    t.link('eyeshadow', 'Light', 'shader', 'Light')
    t.link('Reroute', 'Output', 'tex.main.light', 'Vector')
    t.link('Reroute', 'Output', 'tex.main.dark', 'Vector')
    t.link('Reroute', 'Output', 'tex.main.light_no_eyeshadow', 'Vector')
    t.link('Reroute', 'Output', 'tex.main.dark_no_eyeshadow', 'Vector')
    t.link('UV Map.001', 'UV', 'UV Scale', 'Vector')
    t.link('UV Scale', 'Vector', 'tex.normal', 'Vector')
    t.link('UV Scale', 'Vector', 'tex.detail_normal', 'Vector')
    t.link('UV Scale', 'Vector', 'tex.alpha_mask', 'Vector')
    t.link('UV Map.001', 'UV', 'Reroute', 'Input')
    return t
