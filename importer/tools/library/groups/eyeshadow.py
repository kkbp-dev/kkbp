"""`.Eyeshadow`: fades the face's eyeshadow, between the bakes with it and the bakes without it
(issue 38, ADR 0046). At 1 the face is the game's own bake. `Hide with gag eyes` takes the eyeshadow
away as it rises, whatever `Eyeshadow` is: the importer drives it from the Gag eyes shape key, and it
can be raised by hand too. Written by hand."""

NAME = '.Eyeshadow'
KIND = 'ShaderNodeTree'


def build(lib):
    t = lib.new_group(NAME, KIND, props={})
    t.socket('OUTPUT', 'Light', 'NodeSocketColor')
    t.socket('OUTPUT', 'Dark', 'NodeSocketColor')
    t.socket('INPUT', 'Eyeshadow', 'NodeSocketFloat', default_value=1.0, min_value=0.0, max_value=1.0,
             subtype='FACTOR')
    t.socket('INPUT', 'Hide with gag eyes', 'NodeSocketFloat', default_value=0.0, min_value=0.0, max_value=1.0,
             subtype='FACTOR')
    t.socket('INPUT', 'Light', 'NodeSocketColor')
    t.socket('INPUT', 'Dark', 'NodeSocketColor')
    t.socket('INPUT', 'Light without', 'NodeSocketColor')
    t.socket('INPUT', 'Dark without', 'NodeSocketColor')
    t.make('NodeGroupInput', 'in', (-400, 0))
    t.make('NodeGroupOutput', 'out', (400, 0))
    keep = t.math('keep', 'SUBTRACT', 1.0, ('in', 'Hide with gag eyes'), location=(-150, 250), clamp=True)
    shown = t.math('shown', 'MULTIPLY', ('in', 'Eyeshadow'), keep, location=(0, 250), clamp=True)
    for name, y in (('Light', 100), ('Dark', -100)):
        t.make('ShaderNodeMix', name.lower(), (150, y), {'data_type': 'RGBA'},
               {'Factor_Float': shown, 'A_Color': ('in', f'{name} without'), 'B_Color': ('in', name)})
        t.link(name.lower(), 'Result_Color', 'out', name)
    return t
