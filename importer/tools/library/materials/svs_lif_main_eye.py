"""`SVS lif_main_eye`: the edit template for SVS's eyes and their eye white copies, which the game
draws together with LIF/lif_main_eye. The eye white copy bakes the eye white alone; the
eye bakes the pupil layer over it (ADR 0034), set by the `eye_white_only` param. The eye's textures
are placed by `.SVS eye uv` and clamped, as the game's samplers are. No grade: SVS's bake has none.
Written by hand."""

import edit_templates

NAME = 'SVS lif_main_eye'

# Edit slot -> the `.SVS eye` / `.SVS eye uv` socket names it feeds.
SLOTS = {"shadow_mask": ("Shadow mask", None), "iris_mask": ("Iris", "Iris"), "pupil": ("Pupil", "Pupil"),
         "grade": ("Grade", "Grade"), "highlight1": ("Highlight 1", "Highlight 1"),
         "highlight2": ("Highlight 2", "Highlight 2"), "highlight3": ("Highlight 3", "Highlight 3")}


def build(lib):
    t = edit_templates.begin(lib, NAME, list(SLOTS), grade=False, force_visibility=0.0)
    edit_templates.clamp(t, *SLOTS)
    t.make('ShaderNodeGroup', 'uv', (-1900, 300), {'node_tree': lib.group('.SVS eye uv'), 'width': 220.0})
    ins = {}
    for slot, (socket, place) in SLOTS.items():
        if place:
            t.link('uv', place, f'tex.{slot}', 'Vector')
        ins[socket] = (f'encode.{slot}', 'Color')
        ins[f'{socket} alpha'] = (f'tex.{slot}', 'Alpha')
    t.make('ShaderNodeGroup', 'lit', (-600, 100), {'node_tree': lib.group('.SVS eye'), 'width': 260.0}, ins)
    t.link('lit', 'Alpha', 'combine', 'Main texture (alpha)')
    edit_templates.light_dark(t, 'lit')
    return t
