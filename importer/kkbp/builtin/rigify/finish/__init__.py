"""What the Rigify Hook does to the rig Rigify generated from the metarig.

`finish_rig` runs the phases in order. Each works in Object Mode; `fixups.edit_bones` runs in the
editing() block here, and the emotion grid and grounding open their own.
"""

from __future__ import annotations

from ....editing import editing
from . import emotions, fixups, ground, outfits, shapes


def finish_rig(build):
    fixups.display(build)
    shapes.scale_and_turn(build)
    fixups.head_constraints(build)
    fixups.retarget(build)
    with editing(build.rig, "EDIT"):
        fixups.edit_bones(build)
    fixups.root_colour(build)
    fixups.visible_collections(build)
    fixups.tags(build)
    if not build.kk_extras:
        shapes.hand_ik(build)
    outfits.outfit_collections(build)
    fixups.ik_stretch_off(build)
    emotions.emotion_grid(build)
    ground.ground(build)
