"""What the Rigify Hook does to the Character's armature before Rigify generates the rig from it:
the metarig.

`build_metarig` runs the phases in order. Each phase works in Object Mode unless its docstring says
Edit Mode; the Edit Mode ones run inside the editing() blocks here, which group them as the legacy
scripts' mode switches did, so bones are made in the same order.
"""

from __future__ import annotations

from .... import compat
from ....editing import editing
from . import accessories, deform, eyes, features, handles, layout, limbs, teeth, torso, types
from . import lists as bone_lists


def build_metarig(build):
    metarig = build.metarig
    features.reserved_names(build)
    features.detect(build)
    with editing(metarig, "EDIT"):
        features.id_bone(build)
        eyes.eye_bones(build)
        torso.breasts_and_buttocks(build)
    handles.widgets_and_handles(build)
    with editing(metarig, "EDIT"):
        measures = eyes.tracking_bones(build)
    eyes.mechanism(build, measures)
    compat.add_rigify_color_sets(metarig)  # Rigify's standard colour sets, which the UI phase names
    with editing(metarig, "EDIT"):
        deform.deform_vertex_groups(build)
        found = accessories.chains(build)
        accessories.tongue_side_bones(build)
        torso.head_and_hips(build)
        limbs.limbs(build)
        accessories.skirt(build)
        teeth_plan = teeth.add_bones(build) if build.teeth_bones else None
    types.rigify_types(build)
    teeth.rig(build, teeth_plan)
    lists = bone_lists.bone_lists(build, found)
    layout.sort_bones(build, lists)
    layout.rigify_ui(build)
