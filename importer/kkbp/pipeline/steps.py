"""The Core Import: every built-in Step, in running order, with its Game list.

The reading order is the running order. An empty Game list runs on every Game; a non-empty one
runs only on the Games it names. Steps never check ctx.game: Game differences come from these
lists, the Game Profile (ctx.profile) and the bundle's Roles, Groups and Names.
"""

from .. import joint_corrections
from ..steps import armature, gag, materials, mesh
from .step import Step

STEPS: list[Step] = [
    Step(mesh.load_passes),
    Step(armature.join_armatures),
    Step(mesh.rename_uv_maps),
    Step(mesh.merge_rigged_tongue),
    Step(mesh.build_parts),
    Step(mesh.add_tear_controls),
    Step(gag.combine_gag_keys),
    Step(mesh.order_material_slots),
    Step(mesh.order_shape_keys),
    Step(mesh.link_expression_keys),
    Step(mesh.drive_showing_keys),
    Step(mesh.move_eyelids_forward, games=["SVS"]),
    Step(armature.trim_skeleton),
    Step(armature.set_bone_tails_and_roll),
    Step(armature.bend_limbs_for_ik),
    Step(armature.orient_fingers_and_legs, games=["KK", "KKS"]),
    Step(armature.sort_bone_collections),
    Step(joint_corrections.add_joint_corrections),
    Step(materials.apply_templates),
    Step(materials.apply_outfit_body_textures),
    Step(gag.drive_frames),
    Step(gag.drive_gag_eyes),
    Step(materials.drive_material_changes),
    Step(materials.set_viewport_colors),
    Step(mesh.arrange_collections),
    Step(materials.set_view_transform),
]

# The built-in Hooks (builtin/) by name, in the fixed order they run after the Core Import.
# Fixing seams comes first because it changes the body mesh later Hooks work on; SFW comes before
# Rigify so the rig is built without the bones it deletes. Separate Eyes comes after Rigify so the
# new Parts are made on the finished rig. Delete default scene runs last, once
# every object the other Hooks add is in the file.
BUILTIN_HOOKS: list[str] = [
    "Fix body seams",
    "Convert shaders",
    "Separate meshes",
    "Outlines",
    "Face cards",
    "SFW",
    "Rigify",
    "Separate Eyes",
    "Delete default scene",
]
