"""`.SVS eye`: SVS's eye shader (LIF/lif_main_eye) as the exporter bakes it, front-lit (Light) and
back-lit (Dark): `.SVS eye layers` lit by two `.SVS eye light`s (models.lif_main_eye, issue 62).
With Eye white only, the eye white alone, opaque; otherwise the pupil layer over transparency, its
alpha the light pass's coverage (ADR 0034). Written by hand."""

NAME = '.SVS eye'
KIND = 'ShaderNodeTree'

LIGHT = (('Eye white only', 'NodeSocketFloat', 0.0), ('Shadow power', 'NodeSocketFloat', 0.539),
         ('Light color', 'NodeSocketColor', (1.0, 1.0, 1.0, 1.0)), ('N.L light', 'NodeSocketFloat', 0.828421950340271),
         ('N.L dark', 'NodeSocketFloat', -0.9444175958633423), ('Ambient', 'NodeSocketColor', (0.18855378, 0.18145701, 0.1885538, 1.0)))


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('OUTPUT', 'Alpha', 'NodeSocketFloat')
    layers = lib.group('.SVS eye layers')
    forwarded = [s for s in layers.interface.items_tree if getattr(s, 'in_out', None) == 'INPUT']
    for s in forwarded:
        extra = {k: getattr(s, k) for k in ('min_value', 'max_value') if hasattr(s, k)}
        t.socket('INPUT', s.name, s.socket_type, default_value=tuple(s.default_value) if hasattr(s.default_value, '__len__')
                 else s.default_value, **extra)
    for name, kind, default in LIGHT:
        t.socket('INPUT', name, kind, default_value=default)
    t.make('NodeGroupInput', 'in', (-900, 0))
    t.make('NodeGroupOutput', 'out', (900, 0))
    t.make('ShaderNodeGroup', 'layers', (-500, 0), {'node_tree': layers, 'width': 220.0},
           {s.name: ('in', s.name) for s in forwarded})
    for row, kind in enumerate(('light', 'dark')):
        t.make('ShaderNodeGroup', kind, (0, 200 - row * 400), {'node_tree': lib.group('.SVS eye light'), 'width': 220.0},
               {'White': ('layers', 'White'), 'A': ('layers', 'A'), 'B': ('layers', 'B'), 'Cap': ('layers', 'Cap'),
                'Eye white only': ('in', 'Eye white only'), 'Shadow power': ('in', 'Shadow power'),
                'Light color': ('in', 'Light color'), 'N.L': ('in', f'N.L {kind}'), 'Ambient': ('in', 'Ambient')})
        t.link(kind, 'Color', 'out', kind.capitalize())
    t.link('light', 'Coverage', 'out', 'Alpha')
    return t

