"""The metarig's bone collections: which collection each bone is in, which bones deform, and how
the Rigify panel lays the collections out. In Object Mode, except `deform_flags`."""

from __future__ import annotations

from .. import bone_collections, names
from ....editing import editing

TWEAK = names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX
TORSO_FK = names.TORSO_LAYER + names.FK_LAYER_SUFFIX
# Each limb's IK bones: (bones, IK collection, FK collection).
LIMBS = (
    (names.LEFT_ARM_IK_LAYER_BONE_NAMES, names.LEFT_ARM_LAYER),
    (names.RIGHT_ARM_IK_LAYER_BONE_NAMES, names.RIGHT_ARM_LAYER),
    (names.LEFT_LEG_IK_LAYER_BONE_NAMES, names.LEFT_LEG_LAYER),
    (names.RIGHT_LEG_IK_LAYER_BONE_NAMES, names.RIGHT_LEG_LAYER),
)
TORSO_HANDLES = (names.BREASTS_HANDLE_BONE, names.LEFT_BREAST_HANDLE_BONE, names.RIGHT_BREAST_HANDLE_BONE,
                 names.BUTTOCKS_HANDLE_BONE, names.LEFT_BUTTOCK_HANDLE_BONE, names.RIGHT_BUTTOCK_HANDLE_BONE)

# The Rigify panel: (collection, row), in the order the collections are made if missing. Row 0
# leaves a collection out of the panel.
ROWS = (
    (names.KOIKATSU_DEFORM_BONES_LAYER, 0),
    (names.JUNK_LAYER, 0),  # issue #25
    (names.TORSO_LAYER, 1), (TORSO_FK, 1),
    (names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX, 2), (names.LEFT_ARM_LAYER + names.FK_LAYER_SUFFIX, 2),
    (names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX, 3), (names.RIGHT_ARM_LAYER + names.FK_LAYER_SUFFIX, 3),
    (names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX, 2), (names.LEFT_LEG_LAYER + names.FK_LAYER_SUFFIX, 2),
    (names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX, 3), (names.RIGHT_LEG_LAYER + names.FK_LAYER_SUFFIX, 3),
    (names.FINGERS_LAYER, 6), (names.HAIR_LAYER, 6),
    (TWEAK, 7), (names.FINGERS_LAYER + names.DETAIL_LAYER_SUFFIX, 7),
    (names.HAIR_LAYER + names.DETAIL_LAYER_SUFFIX, 8), (names.HAIR_LAYER + names.MCH_LAYER_SUFFIX, 8),
    (names.SKIRT_LAYER, 9), (names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX, 9),
    (names.TONGUE_LAYER, 10), (names.FACE_TWEAK_LAYER, 11), (names.FACE_MCH_LAYER, 11),
    (names.NSFW_LAYER, 14),
)
# Drawn first in the bone collection list, last moved first, so the IK collections come before the FK ones.
FIRST = (names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX, names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX,
         names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX, names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX)
# Rigify's colour sets: Tweak blue, Root purple, IK red, FK green, Extra orange, Special yellow.
COLOUR_SETS = (
    (names.TORSO_LAYER, "Special"), (TWEAK, "Tweak"),
    (names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX, "IK"), (names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX, "IK"),
    (names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX, "IK"), (names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX, "IK"),
    (names.RIGHT_ARM_LAYER + names.FK_LAYER_SUFFIX, "FK"), (names.RIGHT_LEG_LAYER + names.FK_LAYER_SUFFIX, "FK"),
    (names.LEFT_ARM_LAYER + names.FK_LAYER_SUFFIX, "FK"), (names.LEFT_LEG_LAYER + names.FK_LAYER_SUFFIX, "FK"),
    (names.FINGERS_LAYER, "Special"), (names.FINGERS_LAYER + names.DETAIL_LAYER_SUFFIX, "Special"),
    (names.NSFW_LAYER, "Tweak"), (names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX, "FK"),
    (names.SKIRT_LAYER, "Special"), (names.FACE_TWEAK_LAYER, "Special"), (names.FACE_MCH_LAYER, "Tweak"),
    (names.TONGUE_LAYER, "Extra"), (names.HAIR_LAYER, "Special"), (names.HAIR_LAYER + names.MCH_LAYER_SUFFIX, "Tweak"),
    (names.HAIR_LAYER + names.DETAIL_LAYER_SUFFIX, "FK"),
)


def sort_bones(build, lists):
    """The collections the Rigify panel shows, by what each bone is for."""
    metarig = build.metarig
    move = lambda bone, collection: bone_collections.move(metarig, bone, collection)  # noqa: E731
    for bone in metarig.data.bones:
        if bone.name.startswith("cf_s_"):  # the game's shape bones, which the character maker moves
            move(bone.name, names.CHARAMAKER_LAYER)
    for bone in metarig.data.bones:
        if bone.name.startswith("cf_d_"):
            move(bone.name, names.DEFORM_LAYER)
    for name in lists.torso:
        move(name, names.TORSO_LAYER)
    for name in lists.torso_tweak:
        move(name, names.NSFW_LAYER)
    for bones, limb in LIMBS:
        for name in bones:
            move(name, limb + names.IK_LAYER_SUFFIX)
            bone_collections.tweak(metarig, name, TWEAK)
            bone_collections.fk(metarig, name, limb + names.FK_LAYER_SUFFIX)
    for name in names.FINGERS_LAYER_BONE_NAMES:
        move(name, names.FINGERS_LAYER)
        bone_collections.tweak(metarig, name, names.FINGERS_LAYER + names.DETAIL_LAYER_SUFFIX)
    for name in lists.tongue_secondary:
        move(name, names.TONGUE_LAYER)
    move(names.HEAD_TRACK_TARGET_BONE, TWEAK)
    bone_collections.tweak(metarig, names.HIPS_BONE, TWEAK)
    bone_collections.fk(metarig, names.HIPS_BONE, TORSO_FK)
    bone_collections.tweak(metarig, names.NECK_BONE, TWEAK)
    for name in TORSO_HANDLES:
        move(name, TORSO_FK)
    move(names.WAIST_BONE, TWEAK)
    for name in names.FACE_BONES:
        if bone := metarig.data.bones.get(name):
            move(bone.name, names.FACE_TWEAK_LAYER)
            bone_collections.lock(metarig, bone.name, False)
            bone.use_deform = True
    for bone in metarig.data.bones:
        if bone.collections.get(names.FACE_MCH_LAYER) or bone.collections.get(names.NSFW_LAYER):
            bone_collections.lock(metarig, bone.name, False)
            bone.use_deform = True
    with editing(metarig, "EDIT"):
        deform_flags(build, lists)


def deform_flags(build, lists):
    """Only the deform bones and the NSFW ones deform. A kept bone's unkept child is let go of, which
    Rigify may otherwise fail on in a finger chain. In Edit Mode."""
    metarig = build.metarig
    for bone in metarig.data.edit_bones:
        if bone.name in lists.deform or bone.collections.get(names.NSFW_LAYER):
            bone.use_deform = True
        else:
            bone.use_deform = False
            if bone.name not in lists.useful and bone.parent and bone.parent.name in lists.useful:
                bone.use_connect = False


def rigify_ui(build):
    """The collections' order and rows in the Rigify panel, their colour sets, and the toe roll."""
    metarig = build.metarig
    data = metarig.data

    def index(name):
        # A collection the Character has no bones for is made empty, as the legacy armature had it.
        return (data.collections_all.get(name) or data.collections.new(name)).index

    for name in FIRST:
        data.collections.move(index(name), 0)
    for name, row in ROWS:
        data.collections_all[index(name)].rigify_ui_row = row
    for name in (names.LEFT_LEG_BONE, names.RIGHT_LEG_BONE):
        metarig.pose.bones[name].rigify_parameters.extra_toe_roll = True
    for name, colour_set in COLOUR_SETS:
        data.collections_all[name].rigify_color_set_name = colour_set
