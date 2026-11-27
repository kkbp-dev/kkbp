"""What the Character has that parts of the rig depend on, and the bones whose names the rig needs.
In Object Mode, except `id_bone`."""

from __future__ import annotations

from .. import bones, meshes, names
from ..build import Features

# Accessory bones can be called anything; one named like a bone Rigify makes gives way.
RESERVED = (names.ROOT_BONE, names.TORSO_BONE, names.HEAD_TWEAK_BONE)
# Each spine bone by the child that tells it apart from an accessory bone of the same name.
SPINE = ((names.HEAD_BONE, names.ORIGINAL_EYES_BONE), (names.NECK_BONE, names.HEAD_BONE),
         (names.UPPER_CHEST_BONE, names.NECK_BONE), (names.CHEST_BONE, names.UPPER_CHEST_BONE),
         (names.SPINE_BONE, names.CHEST_BONE), (names.HIPS_BONE, names.SPINE_BONE))
SKIRT_CHAINS, SKIRT_CHAIN_LENGTH = 8, 6
# A Character is male when no vertex of Body weighs this much in the left nipple group. A male KK
# body can keep one stray vertex per side in it, weighted 0.006; the Golden Samples' female bodies
# have 175 to 282 vertices there, the heaviest weighted 0.40 or more.
MALE_NIPPLE_WEIGHT = 0.05


def reserved_names(build):
    """The bones named like the rig's own get " renamed", and so does a bone with a spine bone's name
    that isn't the parent of the next bone up. New bones go into the core collection."""
    metarig = build.metarig
    metarig.data.collections.active_index = metarig.data.collections[names.ORIGINAL_FK_LAYER_INDEX].index
    for name in RESERVED:
        if bone := metarig.pose.bones.get(name):
            bone.name = bone.name + names.RENAMED_NAME_SUFFIX
    for name, child in SPINE:
        parent = metarig.pose.bones.get(child).parent
        if parent.name != name:
            metarig.pose.bones.get(name).name = name + names.RENAMED_NAME_SUFFIX
            metarig.pose.bones.get(parent.name).name = name


def _has_extent(body, group):
    """Whether Body's vertices in `group` span some length on every axis: the breast handles and
    their widgets are sized from it (handles.py), so a body without it gets the male rig."""
    if group not in body.vertex_groups:
        return False
    b = meshes.group_bounds(body, group)
    return b.min_x is not None and all(high > low for low, high in ((b.min_x, b.max_x), (b.min_y, b.max_y),
                                                                     (b.min_z, b.max_z)))


def detect(build):
    """Sets `build.features`."""
    bones_ = build.metarig.pose.bones
    body = build.body
    skirt = names.SKIRT_PARENT_BONE in bones_ and all(
        names.skirt_bone(True, chain) in bones_
        and all(names.skirt_bone(False, chain, i) in bones_ for i in range(SKIRT_CHAIN_LENGTH))
        for chain in range(SKIRT_CHAINS))
    build.features = Features(
        skirt=skirt,
        # The tongue rig reads Body, which holds the tongue (ADR 0039), when it is weighted to the tongue bones.
        rigged_tongue=(bones_.get(names.RIGGED_TONGUE_BONE1) is not None and body is not None
                       and names.RIGGED_TONGUE_BONE1 in body.vertex_groups),
        better_penetration=names.BETTER_PENETRATION_ROOT_CROTCH_BONE in bones_,
        head_mod=meshes.is_group_empty(body, names.ORIGINAL_FACE_UP_DEFORM_BONE),
        male=(meshes.weighs_little(body, names.LEFT_NIPPLE_DEFORM_BONE1, MALE_NIPPLE_WEIGHT)
              or not all(_has_extent(body, g) for g in (names.LEFT_NIPPLE_DEFORM_BONE1,
                                                         names.RIGHT_NIPPLE_DEFORM_BONE1))),
    )


def id_bone(build):
    """The metarig's "Metarig_ID:<random>" bone, made if it has none. In Edit Mode."""
    metarig = build.metarig
    name = None
    for bone in metarig.data.edit_bones:
        if bone.name.startswith(names.METARIG_ID_BONE_PREFIX):
            name = bone.name
    if not name:
        name = names.METARIG_ID_BONE_PREFIX + bones.random_id()
        bones.new_bone(metarig, name)
    build.metarig_id_bone = name
