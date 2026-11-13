"""The torso's bones: the breasts and buttocks bones the handles move, the head's height and the
hips. In Edit Mode."""

from __future__ import annotations

import statistics

from .. import bones, commons, names


def breasts_and_buttocks(build):
    """The breasts bone moves to the breasts' mean depth; a new Buttocks bone on the waist takes the
    two buttock bones, at their length and mean depth."""
    edit = build.metarig.data.edit_bones
    breasts = edit[names.BREASTS_BONE]
    left, right = edit[names.LEFT_BREAST_BONE1], edit[names.RIGHT_BREAST_BONE1]
    breasts.head.y = statistics.mean([left.head.y, right.head.y])
    breasts.tail.y = statistics.mean([left.tail.y, right.tail.y])

    buttocks = bones.copy_bone(build.metarig, names.WAIST_BONE, names.BUTTOCKS_BONE)
    buttocks.parent = edit[names.WAIST_BONE]
    left, right = edit[names.LEFT_BUTTOCK_BONE], edit[names.RIGHT_BUTTOCK_BONE]
    for side in (left, right):
        side.parent = buttocks
        side.length = buttocks.length
    buttocks.head.y = statistics.mean([left.head.y, right.head.y])
    buttocks.tail.y = statistics.mean([left.tail.y, right.tail.y])


def head_and_hips(build):
    """The head's tail at the top of the face: cf_J_FaceUp_ty's vertices, or cf_J_FaceBase's with a
    head mod. The hips start at the waist."""
    edit = build.metarig.data.edit_bones
    top = names.ORIGINAL_FACE_BASE_DEFORM_BONE if build.features.head_mod else names.ORIGINAL_FACE_UP_DEFORM_BONE
    edit[names.HEAD_BONE].tail.z = commons.findVertexGroupExtremities(top, build.body).maxZ
    edit[names.HIPS_BONE].head = edit[names.WAIST_BONE].head
