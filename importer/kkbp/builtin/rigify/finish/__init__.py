"""What the Rigify Hook does to the rig Rigify generated from the metarig.

`finish_rig` runs the phases in order. Each works in Object Mode; `fixups.edit_bones` runs in the
editing() block here, and the face rig and grounding open their own.
"""

from __future__ import annotations

from ....editing import editing
from . import face, fixups, ground, outfits, shapes


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
    outfits.outfit_collections(build)
    fixups.ik_stretch_off(build)
    ground.ground(build)
    face.face_rig(build)  # after grounding, which moves the rig's bones and would leave its Child Of stale
