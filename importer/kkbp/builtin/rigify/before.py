
#Switch to Object Mode and select Metarig

import bpy
import math
from math import radians
import statistics
from mathutils import Matrix, Vector, Euler
from . import commons as koikatsuCommons
from . import names
from . import bones, constraints, drivers, meshes
from ... import compat
from ...editing import editing, switch
from . import widgets
from .metarig import accessories, deform, features, layout, limbs, torso, types
from .metarig import lists as bone_lists
    
def main(build):
    """Turns the Character's armature into the Rigify metarig, phase by phase. Each phase
    leaves Blender in the mode the next expects, as the one long function did."""
    metarig = build.metarig
    features.reserved_names(build)
    features.detect(build)
    with editing(metarig, "EDIT"):
        features.id_bone(build)
        _eye_bones(build)
        torso.breasts_and_buttocks(build)
    _widgets_and_handles(build)
    _eyes(build)
    compat.add_rigify_color_sets(metarig)  # Rigify's standard colour sets, which the UI phase names
    with editing(metarig, "EDIT"):
        deform.deform_vertex_groups(build)
        found = accessories.chains(build)
        accessories.tongue_side_bones(build)
        torso.head_and_hips(build)
        limbs.limbs(build)
        accessories.skirt(build)
    types.rigify_types(build)
    lists = bone_lists.bone_lists(build, found)
    layout.sort_bones(build, lists)
    layout.rigify_ui(build)


def _eye_bones(build):
    """The Eyes target bone, and the left and right eye targets under it, where the Eye Controller is.
    In Edit Mode."""
    metarig = build.metarig
    eyesBone = bones.copy_bone(metarig, names.ORIGINAL_EYES_BONE, names.EYES_BONE)
    leftEyeBone = bones.copy_bone(metarig, names.ORIGINAL_EYES_BONE, names.LEFT_EYE_BONE)
    rightEyeBone = bones.copy_bone(metarig, names.ORIGINAL_EYES_BONE, names.RIGHT_EYE_BONE)
    leftEyeBone.parent = eyesBone
    rightEyeBone.parent = eyesBone


def _widgets_and_handles(build):
    """The eye, breast and buttock widgets and the handle bones they draw."""
    metarig = build.metarig
    isMale = build.features.male
    
    #Import custom bone shapes
    widgets.append_library(build)
    widgetEyes = createEyesWidget(build, names.WIDGET_EYES, names.WIDGET_COLLECTION, metarig, names.EYES_BONE)
    widgetEyeLeft = createEyeWidget(build, names.WIDGET_EYE_LEFT, names.WIDGET_COLLECTION, metarig, names.LEFT_EYE_BONE)
    widgetEyeRight = createEyeWidget(build, names.WIDGET_EYE_RIGHT, names.WIDGET_COLLECTION, metarig, names.RIGHT_EYE_BONE)

    arrangeTripleWidgetSet(names.WIDGET_COLLECTION, widgetEyes, widgetEyeLeft, widgetEyeRight, False, 
    build.body, names.LEFT_EYE_DEFORM_BONE, names.RIGHT_EYE_DEFORM_BONE, 
    True, 90, 0, 90, 
    True, 0.93, 1.66427, 1, 
    True, 1.16, 1, 1.65, 
    True, metarig, names.EYES_BONE, names.EYES_HANDLE_BONE, names.LEFT_EYE_BONE, names.LEFT_EYE_HANDLE_BONE, names.RIGHT_EYE_BONE, names.RIGHT_EYE_HANDLE_BONE)
    
    widgetBreasts = koikatsuCommons.copyObject(build, names.ORIGINAL_WIDGET_BREASTS, names.WIDGET_BREASTS)
    objToBone(widgetBreasts, metarig, names.BREASTS_BONE)
    widgetBreastLeft = koikatsuCommons.copyObject(build, names.ORIGINAL_WIDGET_BREAST_LEFT, names.WIDGET_BREAST_LEFT)
    objToBone(widgetBreastLeft, metarig, names.BREASTS_BONE)
    widgetBreastRight = koikatsuCommons.copyObject(build, names.ORIGINAL_WIDGET_BREAST_RIGHT, names.WIDGET_BREAST_RIGHT)
    objToBone(widgetBreastRight, metarig, names.BREASTS_BONE)
        
    if not isMale:
        arrangeTripleWidgetSet(names.WIDGET_COLLECTION, widgetBreasts, widgetBreastLeft, widgetBreastRight, True, 
        build.body, names.LEFT_NIPPLE_DEFORM_BONE1, names.RIGHT_NIPPLE_DEFORM_BONE1, 
        False, None, None, None,
        True, 0.3, 1.66427, 0.9955, 
        True, 21, 1, 19, 
        True, metarig, names.BREASTS_BONE, names.BREASTS_HANDLE_BONE, names.LEFT_BREAST_BONE1, names.LEFT_BREAST_HANDLE_BONE, names.RIGHT_BREAST_BONE1, names.RIGHT_BREAST_HANDLE_BONE)
        
    widgetButtocks = koikatsuCommons.copyObject(build, names.ORIGINAL_WIDGET_BREASTS, names.WIDGET_BUTTOCKS)
    objToBone(widgetButtocks, metarig, names.BUTTOCKS_BONE)
    widgetButtockLeft = koikatsuCommons.copyObject(build, names.ORIGINAL_WIDGET_BREAST_LEFT, names.WIDGET_BUTTOCK_LEFT)
    objToBone(widgetButtockLeft, metarig, names.BUTTOCKS_BONE)
    widgetButtockRight = koikatsuCommons.copyObject(build, names.ORIGINAL_WIDGET_BREAST_RIGHT, names.WIDGET_BUTTOCK_RIGHT)
    objToBone(widgetButtockRight, metarig, names.BUTTOCKS_BONE)
        
    arrangeTripleWidgetSet(names.WIDGET_COLLECTION, widgetButtocks, widgetButtockLeft, widgetButtockRight, True, 
    build.body, names.LEFT_BUTTOCK_DEFORM_BONE, names.RIGHT_BUTTOCK_DEFORM_BONE, 
    False, None, None, None,
    True, 0, -3.6, 1, 
    True, 30, 1, 25, 
    True, metarig, names.BUTTOCKS_BONE, names.BUTTOCKS_HANDLE_BONE, names.LEFT_BUTTOCK_BONE, names.LEFT_BUTTOCK_HANDLE_BONE, names.RIGHT_BUTTOCK_BONE, names.RIGHT_BUTTOCK_HANDLE_BONE)
    

    finalizeHandleBone(True, metarig, names.EYES_BONE, names.EYES_HANDLE_BONE, widgetEyes)
    finalizeHandleBone(True, metarig, names.LEFT_EYE_BONE, names.LEFT_EYE_HANDLE_BONE, widgetEyeLeft)
    finalizeHandleBone(True, metarig, names.RIGHT_EYE_BONE, names.RIGHT_EYE_HANDLE_BONE, widgetEyeRight)
    if not isMale:
        finalizeHandleBone(False, metarig, names.BREASTS_BONE, names.BREASTS_HANDLE_BONE, widgetBreasts)
        finalizeHandleBone(False, metarig, names.LEFT_BREAST_BONE1, names.LEFT_BREAST_HANDLE_BONE, widgetBreastLeft)   
        finalizeHandleBone(False, metarig, names.RIGHT_BREAST_BONE1, names.RIGHT_BREAST_HANDLE_BONE, widgetBreastRight)   
    finalizeHandleBone(False, metarig, names.BUTTOCKS_BONE, names.BUTTOCKS_HANDLE_BONE, widgetButtocks)   
    finalizeHandleBone(False, metarig, names.LEFT_BUTTOCK_BONE, names.LEFT_BUTTOCK_HANDLE_BONE, widgetButtockLeft)   
    finalizeHandleBone(False, metarig, names.RIGHT_BUTTOCK_BONE, names.RIGHT_BUTTOCK_HANDLE_BONE, widgetButtockRight)
    copyTransformsConstraintName = names.COPY_TRANSFORMS_CONSTRAINT_BASE + names.JOINT_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX
    constraints.copy_transforms(
        metarig,
        names.LEFT_BUTTOCK_HANDLE_BONE,
        names.LEFT_BUTTOCK_JOINT_CORRECTION_BONE,
        name=copyTransformsConstraintName,
        mix='AFTER',
        space='LOCAL',
    )
    constraints.copy_transforms(
        metarig,
        names.RIGHT_BUTTOCK_HANDLE_BONE,
        names.RIGHT_BUTTOCK_JOINT_CORRECTION_BONE,
        name=copyTransformsConstraintName,
        mix='AFTER',
        space='LOCAL',
    )


def _eyes(build):
    """The eye and head tracking bones, and the eye mechanism's properties, constraints and drivers."""
    metarig = build.metarig
    switch(metarig, 'EDIT')
    
    #create tracking bones
    eyesTrackTargetBone = bones.copy_bone(metarig, names.EYES_HANDLE_BONE, names.EYES_TRACK_TARGET_BONE)
    eyesTrackTargetParentBone = bones.copy_bone(metarig, names.EYES_HANDLE_BONE, names.EYES_TRACK_TARGET_PARENT_BONE)
    eyesHandleMarkerBone = bones.copy_bone(metarig, names.EYES_HANDLE_BONE, names.EYES_HANDLE_MARKER_BONE)
    leftEyeHandleMarkerBone = bones.copy_bone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYE_HANDLE_MARKER_BONE)
    rightEyeHandleMarkerBone = bones.copy_bone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_MARKER_BONE)
    leftEyeHandleMarkerXBone = bones.copy_bone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYE_HANDLE_MARKER_X_BONE)
    rightEyeHandleMarkerXBone = bones.copy_bone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_MARKER_X_BONE)
    leftEyeHandleMarkerXBone.head.z = eyesHandleMarkerBone.head.z
    rightEyeHandleMarkerXBone.head.z = eyesHandleMarkerBone.head.z
    leftEyeHandleMarkerXBone.tail.z = eyesHandleMarkerBone.head.z
    rightEyeHandleMarkerXBone.tail.z = eyesHandleMarkerBone.head.z
    leftEyeHandleMarkerZBone = bones.copy_bone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYE_HANDLE_MARKER_Z_BONE)
    rightEyeHandleMarkerZBone = bones.copy_bone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_MARKER_Z_BONE)
    leftEyeHandleMarkerZBone.head.x = eyesHandleMarkerBone.head.x
    rightEyeHandleMarkerZBone.head.x = eyesHandleMarkerBone.head.x
    leftEyeHandleMarkerZBone.tail.x = eyesHandleMarkerBone.head.x
    rightEyeHandleMarkerZBone.tail.x = eyesHandleMarkerBone.head.x
    eyesTrackTargetBone.parent = eyesTrackTargetParentBone
    eyesTrackTargetParentBone.parent = None
    headBone = metarig.data.edit_bones[names.HEAD_BONE]
    leftEyeHandleMarkerBone.parent = headBone
    rightEyeHandleMarkerBone.parent = headBone
    leftEyeHandleMarkerXBone.parent = headBone
    rightEyeHandleMarkerXBone.parent = headBone
    leftEyeHandleMarkerZBone.parent = headBone
    rightEyeHandleMarkerZBone.parent = headBone
    eyeballsBone = bones.copy_bone(metarig, names.EYES_HANDLE_BONE, names.EYEBALLS_BONE)
    eyeballsBone.roll = radians(0)
    leftEyeballBone = bones.copy_bone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYEBALL_BONE)
    rightEyeballBone = bones.copy_bone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYEBALL_BONE)
    leftEyeballBone.parent = headBone
    rightEyeballBone.parent = headBone
    leftEyeballBone.roll = radians(0)
    rightEyeballBone.roll = radians(0)
    leftEyeballBone.head.y = metarig.data.edit_bones[names.LEFT_EYE_DEFORM_BONE].head.y
    rightEyeballBone.head.y = metarig.data.edit_bones[names.RIGHT_EYE_DEFORM_BONE].head.y
    eyeballsBone.head.y = statistics.mean([leftEyeballBone.head.y, rightEyeballBone.head.y])    
    eyeballsBone.length = metarig.data.edit_bones[names.EYES_HANDLE_BONE].length
    leftEyeballBone.length = metarig.data.edit_bones[names.LEFT_EYE_HANDLE_BONE].length
    rightEyeballBone.length = metarig.data.edit_bones[names.RIGHT_EYE_HANDLE_BONE].length    
    eyeballsTrackBone = bones.copy_bone(metarig, names.EYEBALLS_BONE, names.EYEBALLS_TRACK_BONE)
    leftEyeballTrackBone = bones.copy_bone(metarig, names.LEFT_EYEBALL_BONE, names.LEFT_EYEBALL_TRACK_BONE)
    rightEyeballTrackBone = bones.copy_bone(metarig, names.RIGHT_EYEBALL_BONE, names.RIGHT_EYEBALL_TRACK_BONE)
    leftEyeballTrackCorrectionBone = bones.copy_bone(metarig, names.LEFT_EYEBALL_TRACK_BONE, names.LEFT_EYEBALL_TRACK_CORRECTION_BONE)
    rightEyeballTrackCorrectionBone = bones.copy_bone(metarig, names.RIGHT_EYEBALL_TRACK_BONE, names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE)
    leftHeadMarkerXBone = bones.copy_bone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_HEAD_MARKER_X_BONE)
    rightHeadMarkerXBone = bones.copy_bone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_HEAD_MARKER_X_BONE)
    leftHeadMarkerXBone.parent = headBone
    rightHeadMarkerXBone.parent = headBone
    leftHeadMarkerXBone.head.y = headBone.head.y
    rightHeadMarkerXBone.head.y = headBone.head.y
    leftHeadMarkerXBone.length = metarig.data.edit_bones[names.LEFT_EYE_HANDLE_BONE].length
    rightHeadMarkerXBone.length = metarig.data.edit_bones[names.RIGHT_EYE_HANDLE_BONE].length
    leftHeadMarkerXBone.head.z = headBone.head.z
    rightHeadMarkerXBone.head.z = headBone.head.z
    leftHeadMarkerXBone.tail.z = headBone.head.z
    rightHeadMarkerXBone.tail.z = headBone.head.z
    leftHeadMarkerZBone = bones.copy_bone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_HEAD_MARKER_Z_BONE)
    rightHeadMarkerZBone = bones.copy_bone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_HEAD_MARKER_Z_BONE)
    leftHeadMarkerZBone.parent = headBone
    rightHeadMarkerZBone.parent = headBone
    leftHeadMarkerZBone.head.y = headBone.head.y
    rightHeadMarkerZBone.head.y = headBone.head.y
    leftHeadMarkerZBone.length = metarig.data.edit_bones[names.LEFT_EYE_HANDLE_BONE].length
    rightHeadMarkerZBone.length = metarig.data.edit_bones[names.RIGHT_EYE_HANDLE_BONE].length
    leftHeadMarkerZBone.head.x = headBone.head.x
    rightHeadMarkerZBone.head.x = headBone.head.x
    leftHeadMarkerZBone.tail.x = headBone.head.x
    rightHeadMarkerZBone.tail.x = headBone.head.x
    headTrackTargetBone = bones.copy_bone(metarig, names.EYES_HANDLE_BONE, names.HEAD_TRACK_TARGET_BONE)
    headTrackTargetBone.length = headBone.length
    headTrackTargetParentBone = bones.copy_bone(metarig, names.HEAD_TRACK_TARGET_BONE, names.HEAD_TRACK_TARGET_PARENT_BONE)
    headTrackTargetBone.parent = headTrackTargetParentBone
    headTrackTargetParentBone.parent = None
    headTrackBone = bones.copy_bone(metarig, names.EYEBALLS_BONE, names.HEAD_TRACK_BONE)
    headTrackBone.parent = None
    headTrackBone.head.y = headBone.head.y
    placeholderHeadTweakBone = bones.new_bone(metarig, names.HEAD_TWEAK_BONE + names.PLACEHOLDER_BONE_SUFFIX)
    placeholderTorsoBone = bones.new_bone(metarig, names.TORSO_BONE + names.PLACEHOLDER_BONE_SUFFIX)
    placeholderRootBone = bones.new_bone(metarig, names.ROOT_BONE + names.PLACEHOLDER_BONE_SUFFIX)
        
    placeholderHeadTweakBoneName = placeholderHeadTweakBone.name
    placeholderTorsoBoneName = placeholderTorsoBone.name
    placeholderRootBoneName = placeholderRootBone.name
        
    leftHeadDistX = leftHeadMarkerXBone.head.x - headBone.head.x
    rightHeadDistX = rightHeadMarkerXBone.head.x - headBone.head.x
    leftHeadDistZ = leftHeadMarkerZBone.head.z - headBone.head.z
    rightHeadDistZ = rightHeadMarkerZBone.head.z - headBone.head.z
    leftHeadDistXReference = 0.031159714929090754
    rightHeadDistXReference = -0.031183381431473478
    leftHeadDistZReference = 0.053977131843566895
    rightHeadDistZReference = 0.05397462844848633
    
    leftEyeballTrackCorrectionLeftEyeHandleDistY = leftEyeballTrackCorrectionBone.head.y - leftEyeHandleMarkerBone.head.y
    rightEyeballTrackCorrectionRightEyeHandleDistY = rightEyeballTrackCorrectionBone.head.y - rightEyeHandleMarkerBone.head.y
    leftEyeballTrackCorrectionLeftEyeHandleDistYReference = 0.09179527312517166
    rightEyeballTrackCorrectionRightEyeHandleDistYReference = 0.0917946808040142
    
    switch(metarig, 'OBJECT')
    
    eyesSizeFactor = 100.0
        
    eyesHandleLimitLocationDataPath = drivers.bone_property(
        metarig,
        names.EYES_HANDLE_BONE,
        '01A) Limit location',
        description='Limits the maximum reachable X and Y locations based on the left and right eye handles settings',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    eyesHandleEyelidsAutomationDataPath = drivers.bone_property(
        metarig,
        names.EYES_HANDLE_BONE,
        '02A) Eyelids automation',
        description='Enables eyelids shape key automation when both eyes move up and down',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    eyesHandleDefaultEyelidsValueDataPath = drivers.bone_property(
        metarig,
        names.EYES_HANDLE_BONE,
        '02B) Default eyelids value',
        description='Eyelids shape key automation value when both eyes are at their default position',
        default=0.05,
        min=0.0,
        max=1.0,
    )
    eyesHandleMinEyelidsValueDataPath = drivers.bone_property(
        metarig,
        names.EYES_HANDLE_BONE,
        '02C) Min eyelids value',
        description='Minimum reachable eyelids shape key automation value when both eyes move down',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    eyesHandleMaxEyelidsValueDataPath = drivers.bone_property(
        metarig,
        names.EYES_HANDLE_BONE,
        '02D) Max eyelids value',
        description='Maximum reachable eyelids shape key automation value when both eyes move up',
        default=0.25,
        min=0.0,
        max=1.0,
    )
    eyesHandleEyelidsSpeedFactorDataPath = drivers.bone_property(
        metarig,
        names.EYES_HANDLE_BONE,
        '02E) Eyelids speed factor',
        description='Determines how fast the eyelids shape key automation value will change when both eyes move up and down',
        default=2.0,
        min=0.0,
        max=eyesSizeFactor * 10,
    )
    eyesHandleEyesSizeFactorDataPath = drivers.bone_property(
        metarig,
        names.EYES_HANDLE_BONE,
        '03A) Eyes size factor',
        description="Factors into many constraints and drivers for the eyes mechanics; it's better not to change this value",
        default=eyesSizeFactor,
        min=0,
        max=eyesSizeFactor * 10,
    )
    leftEyeHandleLimitLocationDataPath = drivers.bone_property(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        '01A) Limit location',
        description='Limits the maximum reachable X and Y locations based on the settings below',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    leftEyeHandleMinXLocationDataPath = drivers.bone_property(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        '01B) Min X location',
        description='Minimum reachable X location limit',
        default=-0.075 - leftHeadDistXReference + leftHeadDistX,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    leftEyeHandleMaxXLocationDataPath = drivers.bone_property(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        '01C) Max X location',
        description='Maximum reachable X location limit',
        default=0.25 - leftHeadDistXReference + leftHeadDistX,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    leftEyeHandleMinYLocationDataPath = drivers.bone_property(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        '01D) Min Y location',
        description='Minimum reachable Y location limit',
        default=-0.1 - leftHeadDistZReference + leftHeadDistZ,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    leftEyeHandleMaxYLocationDataPath = drivers.bone_property(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        '01E) Max Y location',
        description='Maximum reachable Y location limit',
        default=0.13 - leftHeadDistZReference + leftHeadDistZ,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    leftEyeHandleSpeedCorrectionDataPath = drivers.bone_property(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        '02A) Speed correction',
        description='Increases the speed at which the eye moves when not controlled directly in order to reach its maximum location limits at the same time as the other eye',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    rightEyeHandleLimitLocationDataPath = drivers.bone_property(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        '01A) Limit location',
        description='Limits the maximum reachable X and Y locations based on the settings below',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    rightEyeHandleMinXLocationDataPath = drivers.bone_property(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        '01B) Min X location',
        description='Minimum reachable X location limit',
        default=-0.25 - rightHeadDistXReference + rightHeadDistX,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    rightEyeHandleMaxXLocationDataPath = drivers.bone_property(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        '01C) Max X location',
        description='Maximum reachable X location limit',
        default=0.075 - rightHeadDistXReference + rightHeadDistX,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    rightEyeHandleMinYLocationDataPath = drivers.bone_property(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        '01D) Min Y location',
        description='Minimum reachable Y location limit',
        default=-0.1 - rightHeadDistZReference + rightHeadDistZ,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    rightEyeHandleMaxYLocationDataPath = drivers.bone_property(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        '01E) Max Y location',
        description='Maximum reachable Y location limit',
        default=0.13 - rightHeadDistZReference + rightHeadDistZ,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    rightEyeHandleSpeedCorrectionDataPath = drivers.bone_property(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        '02A) Speed correction',
        description='Increases the speed at which the eye moves when not controlled directly in order to reach its maximum location limits at the same time as the other eye',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    eyesTrackTargetParentToHeadDataPath = drivers.bone_property(
        metarig,
        names.EYES_TRACK_TARGET_BONE,
        '01A) Parent to head',
        description='The bone will act as if it was parented to the head bone',
        default=1,
        min=0,
        max=1,
    )
    eyesTrackTargetParentToTorsoDataPath = drivers.bone_property(
        metarig,
        names.EYES_TRACK_TARGET_BONE,
        '01B) Parent to torso',
        description='The bone will act as if it was parented to the torso bone',
        default=0,
        min=0,
        max=1,
    )
    eyesTrackTargetParentToRootDataPath = drivers.bone_property(
        metarig,
        names.EYES_TRACK_TARGET_BONE,
        '01C) Parent to root',
        description='The bone will act as if it was parented to the root bone',
        default=0,
        min=0,
        max=1,
    )
    eyeballsSpeedFactorDataPath = drivers.bone_property(
        metarig,
        names.EYEBALLS_BONE,
        '01A) Eyeballs speed factor',
        description='Determines how fast the eyes will move when rotating the eyeball bones manually',
        default=0.26,
        min=0.0,
        max=1.0,
    )
    eyeballsTrackTargetDataPath = drivers.bone_property(
        metarig,
        names.EYEBALLS_BONE,
        '02A) Track target',
        description='Enables tracking of the eyeballs track target bone',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    eyeballsTrackSpeedFactorDataPath = drivers.bone_property(
        metarig,
        names.EYEBALLS_BONE,
        '02B) Eyeballs track speed factor',
        description='Determines how fast the eyes will move when the eyeballs are tracking their target',
        default=0.04,
        min=0.0,
        max=1.0,
    )
    eyeballsNearbyTargetTrackCorrectionDataPath = drivers.bone_property(
        metarig,
        names.EYEBALLS_BONE,
        '02C) Nearby target track correction',
        description='When tracking a target that moves closer to the middle of the face than its original location, the individual eyes will gradually point towards it instead of keeping the original distance between them',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    eyeballsNearbyTargetSizeFactorDataPath = drivers.bone_property(
        metarig,
        names.EYEBALLS_BONE,
        '02D) Nearby target track size factor',
        description='Factors into the nearby target track correction, if the character is scaled up or down after running the first Rigify script this value should be changed proportionally',
        default=rightEyeballTrackCorrectionRightEyeHandleDistY / rightEyeballTrackCorrectionRightEyeHandleDistYReference,
        min=eyesSizeFactor * -10,
        max=eyesSizeFactor * 10,
    )
    headTrackTargetLimitRotationDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '01A) Limit rotation',
        description='Limits the maximum reachable rotation of the head based on the settings below',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    headTrackTargetMinXRotationDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '01B) Min X rotation',
        description='Minimum reachable X angle limit',
        default=-40.0,
        min=-180.0,
        max=0.0,
    )
    headTrackTargetMaxXRotationDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '01C) Max X rotation',
        description='Maximum reachable X angle limit',
        default=50.0,
        min=0.0,
        max=180.0,
    )
    headTrackTargetMinYRotationDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '01D) Min Y rotation',
        description='Minimum reachable Y angle limit',
        default=-80.0,
        min=-180.0,
        max=0.0,
    )
    headTrackTargetMaxYRotationDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '01E) Max Y rotation',
        description='Maximum reachable Y angle limit',
        default=80.0,
        min=0.0,
        max=180.0,
    )
    headTrackTargetMinZRotationDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '01F) Min Z rotation',
        description='Minimum reachable Z angle limit',
        default=-50.0,
        min=-180.0,
        max=0.0,
    )
    headTrackTargetMaxZRotationDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '01G) Max Z rotation',
        description='Maximum reachable Z angle limit',
        default=50.0,
        min=0.0,
        max=180.0,
    )
    headTrackTargetTrackTargetDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '02A) Track target',
        description='Enables tracking of the head track target bone',
        default=0.0,
        min=0.0,
        max=1.0,
    )
    headTrackTargetParentToHeadDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '03A) Parent to head',
        description='The bone will act as if it was parented to the head bone',
        default=1,
        min=0,
        max=1,
    )
    headTrackTargetParentToTorsoDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '03B) Parent to torso',
        description='The bone will act as if it was parented to the torso bone',
        default=0,
        min=0,
        max=1,
    )
    headTrackTargetParentToRootDataPath = drivers.bone_property(
        metarig,
        names.HEAD_TRACK_TARGET_BONE,
        '03C) Parent to root',
        description='The bone will act as if it was parented to the root bone',
        default=0,
        min=0,
        max=1,
    )
        
    eyesHandleTransformationConstraintEyeballLocation = constraints.transformation(
        metarig,
        names.EYES_HANDLE_BONE,
        names.EYEBALLS_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='ROTATION',
        from_range=((math.radians(-180), math.radians(180)), (math.radians(0), math.radians(0)), (math.radians(-180), math.radians(180))),
        map_to='LOCATION',
        to_range=((eyesSizeFactor / -10, eyesSizeFactor / 10), (0, 0), (eyesSizeFactor / -10, eyesSizeFactor / 10)),
        from_rotation_mode='AUTO',
    )    
    eyesHandleCopyRotationConstraintEyeball = constraints.copy_rotation(
        metarig,
        names.EYES_HANDLE_BONE,
        names.EYEBALLS_BONE,
        name=names.COPY_ROTATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX,
        mix='AFTER',
        space='LOCAL',
        use=(False, True, False),
        invert=(False, False, False),
    )
    eyesHandleTransformationContraintEyeballScale = constraints.transformation(
        metarig,
        names.EYES_HANDLE_BONE,
        names.EYEBALLS_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.SCALE_CONSTRAINT_SUFFIX,
        mix='MULTIPLY',
        space='LOCAL',
        map_from='SCALE',
        from_range=((0.0, 100.0), (1.0, 1.0), (0.0, 100.0)),
        map_to='SCALE',
        to_range=((0.0, 100.0), (1.0, 1.0), (0.0, 100.0)),
    )
    eyesHandleLimitLocationConstraint = constraints.limit_location(
        metarig,
        names.EYES_HANDLE_BONE,
        name=names.LIMIT_LOCATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX,
        space='CUSTOM',
        space_bone=names.HEAD_BONE,
        min=(-eyesSizeFactor, -eyesSizeFactor, None),
        max=(eyesSizeFactor, eyesSizeFactor, None),
    )
    leftEyeHandleTransformationConstraintEyeballLocation = constraints.transformation(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        names.LEFT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='ROTATION',
        from_range=((math.radians(-180), math.radians(180)), (math.radians(0), math.radians(0)), (math.radians(-180), math.radians(180))),
        map_to='LOCATION',
        to_range=((eyesSizeFactor / -10, eyesSizeFactor / 10), (0, 0), (eyesSizeFactor / -10, eyesSizeFactor / 10)),
        from_rotation_mode='AUTO',
    )    
    leftEyeHandleTransformationConstraintEyeballLocationCorrectionMin = constraints.transformation(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        names.LEFT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MIN_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='ROTATION',
        from_range=((math.radians(0), math.radians(0)), (math.radians(0), math.radians(0)), (math.radians(0), math.radians(0))),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
        from_rotation_mode='AUTO',
    )
    leftEyeHandleTransformationConstraintEyeballLocationCorrectionMax = constraints.transformation(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        names.LEFT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MAX_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='ROTATION',
        from_range=((math.radians(0), math.radians(0)), (math.radians(0), math.radians(0)), (math.radians(0), math.radians(0))),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
        from_rotation_mode='AUTO',
    )
    leftEyeHandleCopyRotationConstraintEyeball = constraints.copy_rotation(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        names.LEFT_EYEBALL_BONE,
        name=names.COPY_ROTATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX,
        mix='AFTER',
        space='LOCAL',
        use=(False, True, False),
        invert=(False, False, False),
    )
    leftEyeHandleTransformationConstraintEyeballScale = constraints.transformation(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        names.LEFT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.SCALE_CONSTRAINT_SUFFIX,
        mix='MULTIPLY',
        space='LOCAL',
        map_from='SCALE',
        from_range=((0.0, 100.0), (1.0, 1.0), (0.0, 100.0)),
        map_to='SCALE',
        to_range=((0.0, 100.0), (1.0, 1.0), (0.0, 100.0)),
    )
    leftEyeHandleTransformationConstraintHandleLocationCorrectionMin = constraints.transformation(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        names.EYES_HANDLE_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MIN_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='LOCATION',
        from_range=((0, 0), (0, 0), (0, 0)),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
    )
    leftEyeHandleTransformationConstraintHandleLocationCorrectionMax = constraints.transformation(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        names.EYES_HANDLE_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MAX_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='LOCATION',
        from_range=((0, 0), (0, 0), (0, 0)),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
    )
    leftEyeHandleLimitLocationConstraint = constraints.limit_location(
        metarig,
        names.LEFT_EYE_HANDLE_BONE,
        name=names.LIMIT_LOCATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX,
        space='CUSTOM',
        space_bone=names.HEAD_BONE,
        min=(-eyesSizeFactor, -eyesSizeFactor, None),
        max=(eyesSizeFactor, eyesSizeFactor, None),
    )
    rightEyeHandleTransformationConstraintEyeballLocation = constraints.transformation(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        names.RIGHT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='ROTATION',
        from_range=((math.radians(-180), math.radians(180)), (math.radians(0), math.radians(0)), (math.radians(-180), math.radians(180))),
        map_to='LOCATION',
        to_range=((eyesSizeFactor / -10, eyesSizeFactor / 10), (0, 0), (eyesSizeFactor / -10, eyesSizeFactor / 10)),
        from_rotation_mode='AUTO',
    )    
    rightEyeHandleTransformationConstraintEyeballLocationCorrectionMin = constraints.transformation(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        names.RIGHT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MIN_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='ROTATION',
        from_range=((math.radians(0), math.radians(0)), (math.radians(0), math.radians(0)), (math.radians(0), math.radians(0))),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
        from_rotation_mode='AUTO',
    )
    rightEyeHandleTransformationConstraintEyeballLocationCorrectionMax = constraints.transformation(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        names.RIGHT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MAX_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='ROTATION',
        from_range=((math.radians(0), math.radians(0)), (math.radians(0), math.radians(0)), (math.radians(0), math.radians(0))),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
        from_rotation_mode='AUTO',
    )
    rightEyeHandleCopyRotationConstraintEyeball = constraints.copy_rotation(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        names.RIGHT_EYEBALL_BONE,
        name=names.COPY_ROTATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX,
        mix='AFTER',
        space='LOCAL',
        use=(False, True, False),
        invert=(False, False, False),
    )
    rightEyeHandleTransformationConstraintEyeballScale = constraints.transformation(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        names.RIGHT_EYEBALL_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.EYEBALL_CONSTRAINT_SUFFIX + names.SCALE_CONSTRAINT_SUFFIX,
        mix='MULTIPLY',
        space='LOCAL',
        map_from='SCALE',
        from_range=((0.0, 100.0), (1.0, 1.0), (0.0, 100.0)),
        map_to='SCALE',
        to_range=((0.0, 100.0), (1.0, 1.0), (0.0, 100.0)),
    )
    rightEyeHandleTransformationConstraintHandleLocationCorrectionMin = constraints.transformation(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        names.EYES_HANDLE_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MIN_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='LOCATION',
        from_range=((0, 0), (0, 0), (0, 0)),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
    )
    rightEyeHandleTransformationConstraintHandleLocationCorrectionMax = constraints.transformation(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        names.EYES_HANDLE_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX + names.LOCATION_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX + names.MAX_CONSTRAINT_SUFFIX,
        mix='ADD',
        space='LOCAL',
        map_from='LOCATION',
        from_range=((0, 0), (0, 0), (0, 0)),
        map_to='LOCATION',
        to_range=((0, 0), (0, 0), (0, 0)),
    )
    rightEyeHandleLimitLocationConstraint = constraints.limit_location(
        metarig,
        names.RIGHT_EYE_HANDLE_BONE,
        name=names.LIMIT_LOCATION_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX,
        space='CUSTOM',
        space_bone=names.HEAD_BONE,
        min=(-eyesSizeFactor, -eyesSizeFactor, None),
        max=(eyesSizeFactor, eyesSizeFactor, None),
    )
    eyesTrackTargetParentArmatureConstraint = constraints.armature(
        metarig,
        names.EYES_TRACK_TARGET_PARENT_BONE,
        [names.HEAD_BONE, placeholderTorsoBoneName, placeholderRootBoneName],
        name=names.ARMATURE_CONSTRAINT_BASE + names.PARENT_CONSTRAINT_SUFFIX,
    ) 
    eyeballsCopyRotationConstraintTrack = constraints.copy_rotation(
        metarig,
        names.EYEBALLS_BONE,
        names.EYEBALLS_TRACK_BONE,
        name=names.COPY_ROTATION_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX,
        mix='REPLACE',
        space='LOCAL',
        use=(True, False, True),
        invert=(False, False, False),
    )
    leftEyeballCopyRotationConstraintTrack = constraints.copy_rotation(
        metarig,
        names.LEFT_EYEBALL_BONE,
        names.LEFT_EYEBALL_TRACK_CORRECTION_BONE,
        name=names.COPY_ROTATION_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX,
        mix='REPLACE',
        space='LOCAL',
        use=(True, False, True),
        invert=(False, False, False),
    )
    rightEyeballCopyRotationConstraintTrack = constraints.copy_rotation(
        metarig,
        names.RIGHT_EYEBALL_BONE,
        names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE,
        name=names.COPY_ROTATION_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX + names.CORRECTION_CONSTRAINT_SUFFIX,
        mix='REPLACE',
        space='LOCAL',
        use=(True, False, True),
        invert=(False, False, False),
    )    
    eyeballsTrackDampedTrackConstraint = constraints.damped_track(
        metarig,
        names.EYEBALLS_TRACK_BONE,
        names.EYES_TRACK_TARGET_BONE,
        name=names.DAMPED_TRACK_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX,
    )
    leftEyeballTrackDampedTrackConstraint = constraints.damped_track(
        metarig,
        names.LEFT_EYEBALL_TRACK_BONE,
        names.EYES_TRACK_TARGET_BONE,
        name=names.DAMPED_TRACK_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX,
    )
    rightEyeballTrackDampedTrackConstraint = constraints.damped_track(
        metarig,
        names.RIGHT_EYEBALL_TRACK_BONE,
        names.EYES_TRACK_TARGET_BONE,
        name=names.DAMPED_TRACK_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX,
    )
    headTransformationConstraintHeadRotation = constraints.transformation(
        metarig,
        names.HEAD_BONE,
        names.HEAD_TRACK_BONE,
        name=names.TRANSFORMATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX + names.ROTATION_CONSTRAINT_SUFFIX,
        mix='REPLACE',
        space='LOCAL_WITH_PARENT',
        map_from='ROTATION',
        from_range=((math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180))),
        map_to='ROTATION',
        to_range=((math.radians(180), math.radians(-180)), (math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180))),
        from_rotation_mode='QUATERNION',
        to_euler_order='AUTO',
        map_to_from=('X', 'Z', 'Y'),
    )
    headLimitRotationConstraint = constraints.limit_rotation(
        metarig,
        names.HEAD_BONE,
        name=names.LIMIT_ROTATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX,
        space='LOCAL',
        limits=((math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180))),
    )
    headTrackTargetParentArmatureConstraint = constraints.armature(
        metarig,
        names.HEAD_TRACK_TARGET_PARENT_BONE,
        [placeholderHeadTweakBoneName, placeholderTorsoBoneName, placeholderRootBoneName],
        name=names.ARMATURE_CONSTRAINT_BASE + names.PARENT_CONSTRAINT_SUFFIX,
    ) 
    headTrackDampedTrackConstraint = constraints.damped_track(
        metarig,
        names.HEAD_TRACK_BONE,
        names.HEAD_TRACK_TARGET_BONE,
        name=names.DAMPED_TRACK_CONSTRAINT_BASE + names.TRACK_CONSTRAINT_SUFFIX,
    )
    
    eyelidsShapeKeyCopy = meshes.duplicate_shape_key(build.body, names.EYELIDS_SHAPE_KEY, names.EYELIDS_SHAPE_KEY_COPY)
    
    eyesHandleLocationXDriverVariable = drivers.Variable(
        'locX',
        'TRANSFORMS',
        metarig,
        bone=names.EYES_HANDLE_BONE,
        space='LOCAL_SPACE',
        transform='LOC_X',
    )
    eyesHandleDefaultEyelidsValueDriverVariable = drivers.Variable('default', 'SINGLE_PROP', metarig, data_path=eyesHandleDefaultEyelidsValueDataPath)
    eyesHandleMinEyelidsValueDriverVariable = drivers.Variable('min', 'SINGLE_PROP', metarig, data_path=eyesHandleMinEyelidsValueDataPath)
    eyesHandleMaxEyelidsValueDriverVariable = drivers.Variable('max', 'SINGLE_PROP', metarig, data_path=eyesHandleMaxEyelidsValueDataPath)
    eyesHandleEyelidsSpeedFactorDriverVariable = drivers.Variable('speed', 'SINGLE_PROP', metarig, data_path=eyesHandleEyelidsSpeedFactorDataPath)
    eyesHandleEyelidsAutomationDriverVariable = drivers.Variable('enabled', 'SINGLE_PROP', metarig, data_path=eyesHandleEyelidsAutomationDataPath)
    eyesHandleLimitLocationDriverVariable = drivers.Variable('limit', 'SINGLE_PROP', metarig, data_path=eyesHandleLimitLocationDataPath)
    eyesHandleEyesSizeFactorDriverVariable = drivers.Variable('sizeFactor', 'SINGLE_PROP', metarig, data_path=eyesHandleEyesSizeFactorDataPath)
    leftEyeHandleLimitLocationDriverVariable = drivers.Variable('limit_L', 'SINGLE_PROP', metarig, data_path=leftEyeHandleLimitLocationDataPath)
    leftEyeHandleMinXLocationDriverVariable = drivers.Variable('minX_L', 'SINGLE_PROP', metarig, data_path=leftEyeHandleMinXLocationDataPath)
    leftEyeHandleMaxXLocationDriverVariable = drivers.Variable('maxX_L', 'SINGLE_PROP', metarig, data_path=leftEyeHandleMaxXLocationDataPath)
    leftEyeHandleMinYLocationDriverVariable = drivers.Variable('minY_L', 'SINGLE_PROP', metarig, data_path=leftEyeHandleMinYLocationDataPath)
    leftEyeHandleMaxYLocationDriverVariable = drivers.Variable('maxY_L', 'SINGLE_PROP', metarig, data_path=leftEyeHandleMaxYLocationDataPath)
    leftEyeHandleSpeedCorrectionDriverVariable = drivers.Variable('corr_L', 'SINGLE_PROP', metarig, data_path=leftEyeHandleSpeedCorrectionDataPath)
    leftEyeHandleEyesHandleDistanceXDriverVariable = drivers.Variable(
        'distX_L',
        'LOC_DIFF',
        metarig,
        bone=names.EYES_HANDLE_MARKER_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.LEFT_EYE_HANDLE_MARKER_X_BONE,
        space2='WORLD_SPACE',
    )
    leftEyeHandleEyesHandleDistanceYDriverVariable = drivers.Variable(
        'distY_L',
        'LOC_DIFF',
        metarig,
        bone=names.EYES_HANDLE_MARKER_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.LEFT_EYE_HANDLE_MARKER_Z_BONE,
        space2='WORLD_SPACE',
    )
    leftEyeHandleHeadDistanceXDriverVariable = drivers.Variable(
        'headDistX_L',
        'LOC_DIFF',
        metarig,
        bone=names.HEAD_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.LEFT_HEAD_MARKER_X_BONE,
        space2='WORLD_SPACE',
    )
    leftEyeHandleHeadDistanceYDriverVariable = drivers.Variable(
        'headDistY_L',
        'LOC_DIFF',
        metarig,
        bone=names.HEAD_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.LEFT_HEAD_MARKER_Z_BONE,
        space2='WORLD_SPACE',
    )
    rightEyeHandleLimitLocationDriverVariable = drivers.Variable('limit_R', 'SINGLE_PROP', metarig, data_path=rightEyeHandleLimitLocationDataPath)
    rightEyeHandleMinXLocationDriverVariable = drivers.Variable('minX_R', 'SINGLE_PROP', metarig, data_path=rightEyeHandleMinXLocationDataPath)
    rightEyeHandleMaxXLocationDriverVariable = drivers.Variable('maxX_R', 'SINGLE_PROP', metarig, data_path=rightEyeHandleMaxXLocationDataPath)
    rightEyeHandleMinYLocationDriverVariable = drivers.Variable('minY_R', 'SINGLE_PROP', metarig, data_path=rightEyeHandleMinYLocationDataPath)
    rightEyeHandleMaxYLocationDriverVariable = drivers.Variable('maxY_R', 'SINGLE_PROP', metarig, data_path=rightEyeHandleMaxYLocationDataPath)
    rightEyeHandleSpeedCorrectionDriverVariable = drivers.Variable('corr_R', 'SINGLE_PROP', metarig, data_path=rightEyeHandleSpeedCorrectionDataPath)
    rightEyeHandleEyesHandleDistanceXDriverVariable = drivers.Variable(
        'distX_R',
        'LOC_DIFF',
        metarig,
        bone=names.EYES_HANDLE_MARKER_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.RIGHT_EYE_HANDLE_MARKER_X_BONE,
        space2='WORLD_SPACE',
    )
    rightEyeHandleEyesHandleDistanceYDriverVariable = drivers.Variable(
        'distY_R',
        'LOC_DIFF',
        metarig,
        bone=names.EYES_HANDLE_MARKER_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.RIGHT_EYE_HANDLE_MARKER_Z_BONE,
        space2='WORLD_SPACE',
    )
    rightEyeHandleHeadDistanceXDriverVariable = drivers.Variable(
        'headdDistX_R',
        'LOC_DIFF',
        metarig,
        bone=names.HEAD_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.RIGHT_HEAD_MARKER_X_BONE,
        space2='WORLD_SPACE',
    )
    rightEyeHandleHeadDistanceYDriverVariable = drivers.Variable(
        'headDistY_R',
        'LOC_DIFF',
        metarig,
        bone=names.HEAD_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.RIGHT_HEAD_MARKER_Z_BONE,
        space2='WORLD_SPACE',
    )
    eyesTrackTargetParentToHeadDriverVariable = drivers.Variable('parentHead', 'SINGLE_PROP', metarig, data_path=eyesTrackTargetParentToHeadDataPath)
    eyesTrackTargetParentToTorsoDriverVariable = drivers.Variable('parentTorso', 'SINGLE_PROP', metarig, data_path=eyesTrackTargetParentToTorsoDataPath)
    eyesTrackTargetParentToRootDriverVariable = drivers.Variable('parentRoot', 'SINGLE_PROP', metarig, data_path=eyesTrackTargetParentToRootDataPath)
    eyeballsSpeedFactorDriverVariable = drivers.Variable('rotSpeed', 'SINGLE_PROP', metarig, data_path=eyeballsSpeedFactorDataPath)
    eyeballsTrackTargetDriverVariable = drivers.Variable('track', 'SINGLE_PROP', metarig, data_path=eyeballsTrackTargetDataPath)
    eyeballsTrackSpeedFactorDriverVariable = drivers.Variable('trackSpeed', 'SINGLE_PROP', metarig, data_path=eyeballsTrackSpeedFactorDataPath)
    eyeballsNearbyTargetTrackCorrectionDriverVariable = drivers.Variable('trackCorr', 'SINGLE_PROP', metarig, data_path=eyeballsNearbyTargetTrackCorrectionDataPath)
    eyeballsNearbyTargetSizeFactorDriverVariable = drivers.Variable('factor', 'SINGLE_PROP', metarig, data_path=eyeballsNearbyTargetSizeFactorDataPath)
    leftEyeballRightEyeHandleMarkerDistanceDriverVariable = drivers.Variable(
        'orgDist_L',
        'LOC_DIFF',
        metarig,
        bone=names.LEFT_EYEBALL_TRACK_CORRECTION_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.LEFT_EYE_HANDLE_MARKER_BONE,
        space2='WORLD_SPACE',
    )
    rightEyeballRightEyeHandleMarkerDistanceDriverVariable = drivers.Variable(
        'orgDist_R',
        'LOC_DIFF',
        metarig,
        bone=names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.RIGHT_EYE_HANDLE_MARKER_BONE,
        space2='WORLD_SPACE',
    )
    leftEyeballEyesTrackTargetDistanceDriverVariable = drivers.Variable(
        'currDist_L',
        'LOC_DIFF',
        metarig,
        bone=names.LEFT_EYEBALL_TRACK_CORRECTION_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.EYES_TRACK_TARGET_BONE,
        space2='WORLD_SPACE',
    )
    rightEyeballEyesTrackTargetDistanceDriverVariable = drivers.Variable(
        'currDist_R',
        'LOC_DIFF',
        metarig,
        bone=names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE,
        space='WORLD_SPACE',
        target2=metarig,
        bone2=names.EYES_TRACK_TARGET_BONE,
        space2='WORLD_SPACE',
    )
    eyeballsTrackBoneRotationZDriverVariable = drivers.Variable(
        'rotZ',
        'TRANSFORMS',
        metarig,
        bone=names.EYEBALLS_TRACK_BONE,
        space='LOCAL_SPACE',
        transform='ROT_Z',
        rotation_mode='QUATERNION',
    )
    leftEyeballTrackBoneRotationZDriverVariable = drivers.Variable(
        'rotZ_L',
        'TRANSFORMS',
        metarig,
        bone=names.LEFT_EYEBALL_TRACK_BONE,
        space='LOCAL_SPACE',
        transform='ROT_Z',
        rotation_mode='QUATERNION',
    )
    rightEyeballTrackBoneRotationZDriverVariable = drivers.Variable(
        'rotZ_R',
        'TRANSFORMS',
        metarig,
        bone=names.RIGHT_EYEBALL_TRACK_BONE,
        space='LOCAL_SPACE',
        transform='ROT_Z',
        rotation_mode='QUATERNION',
    )
    headTrackTargetLimitRotationDriverVariable = drivers.Variable('limit', 'SINGLE_PROP', metarig, data_path=headTrackTargetLimitRotationDataPath)
    headTrackTargetMinXRotationDriverVariable = drivers.Variable('minX', 'SINGLE_PROP', metarig, data_path=headTrackTargetMinXRotationDataPath)
    headTrackTargetMaxXRotationDriverVariable = drivers.Variable('maxX', 'SINGLE_PROP', metarig, data_path=headTrackTargetMaxXRotationDataPath)
    headTrackTargetMinYRotationDriverVariable = drivers.Variable('minY', 'SINGLE_PROP', metarig, data_path=headTrackTargetMinYRotationDataPath)
    headTrackTargetMaxYRotationDriverVariable = drivers.Variable('maxY', 'SINGLE_PROP', metarig, data_path=headTrackTargetMaxYRotationDataPath)
    headTrackTargetMinZRotationDriverVariable = drivers.Variable('minZ', 'SINGLE_PROP', metarig, data_path=headTrackTargetMinZRotationDataPath)
    headTrackTargetMaxZRotationDriverVariable = drivers.Variable('maxZ', 'SINGLE_PROP', metarig, data_path=headTrackTargetMaxZRotationDataPath)
    headTrackTargetParentToHeadDriverVariable = drivers.Variable('parentHead', 'SINGLE_PROP', metarig, data_path=headTrackTargetParentToHeadDataPath)
    headTrackTargetParentToTorsoDriverVariable = drivers.Variable('parentTorso', 'SINGLE_PROP', metarig, data_path=headTrackTargetParentToTorsoDataPath)
    headTrackTargetParentToRootDriverVariable = drivers.Variable('parentRoot', 'SINGLE_PROP', metarig, data_path=headTrackTargetParentToRootDataPath)
    headTrackTargetDriverVariable = drivers.Variable('track', 'SINGLE_PROP', metarig, data_path=headTrackTargetTrackTargetDataPath)
    
    drivers.add(
        eyelidsShapeKeyCopy,
        'value',
        type='SCRIPTED',
        variables=[eyesHandleLocationXDriverVariable, eyesHandleDefaultEyelidsValueDriverVariable, eyesHandleMinEyelidsValueDriverVariable, eyesHandleMaxEyelidsValueDriverVariable, eyesHandleEyelidsSpeedFactorDriverVariable, eyesHandleEyelidsAutomationDriverVariable],
        expression=eyesHandleEyelidsAutomationDriverVariable.name + ' * (' + eyesHandleMinEyelidsValueDriverVariable.name + ' if (' + eyesHandleDefaultEyelidsValueDriverVariable.name + ' + ' + eyesHandleLocationXDriverVariable.name + ' * -' + eyesHandleEyelidsSpeedFactorDriverVariable.name + ' if ' + eyesHandleLocationXDriverVariable.name + ' < 0 else ' + eyesHandleDefaultEyelidsValueDriverVariable.name + ' - ' + eyesHandleLocationXDriverVariable.name + ' * ' + eyesHandleEyelidsSpeedFactorDriverVariable.name + ') < ' + eyesHandleMinEyelidsValueDriverVariable.name + ' else ' + eyesHandleMaxEyelidsValueDriverVariable.name + ' if (' + eyesHandleDefaultEyelidsValueDriverVariable.name + ' + ' + eyesHandleLocationXDriverVariable.name + ' * -' + eyesHandleEyelidsSpeedFactorDriverVariable.name + ' if ' + eyesHandleLocationXDriverVariable.name + ' < 0 else ' + eyesHandleDefaultEyelidsValueDriverVariable.name + ' - ' + eyesHandleLocationXDriverVariable.name + ' * ' + eyesHandleEyelidsSpeedFactorDriverVariable.name + ') > ' + eyesHandleMaxEyelidsValueDriverVariable.name + ' else (' + eyesHandleDefaultEyelidsValueDriverVariable.name + ' + ' + eyesHandleLocationXDriverVariable.name + ' * -' + eyesHandleEyelidsSpeedFactorDriverVariable.name + ' if ' + eyesHandleLocationXDriverVariable.name + ' < 0 else ' + eyesHandleDefaultEyelidsValueDriverVariable.name + ' - ' + eyesHandleLocationXDriverVariable.name + ' * ' + eyesHandleEyelidsSpeedFactorDriverVariable.name + '))',
    )
    drivers.add(
        eyesHandleLimitLocationConstraint,
        'influence',
        type='AVERAGE',
        variables=[eyesHandleLimitLocationDriverVariable],
    )
    drivers.add(
        eyesHandleLimitLocationConstraint,
        'min_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMinXLocationDriverVariable, rightEyeHandleMinXLocationDriverVariable, leftEyeHandleEyesHandleDistanceXDriverVariable, rightEyeHandleEyesHandleDistanceXDriverVariable],
        expression=leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceXDriverVariable.name + ' if ' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceXDriverVariable.name + ' <= ' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceXDriverVariable.name + ' else ' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceXDriverVariable.name,
    )
    drivers.add(
        eyesHandleLimitLocationConstraint,
        'max_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleEyesHandleDistanceXDriverVariable, rightEyeHandleEyesHandleDistanceXDriverVariable],
        expression=rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceXDriverVariable.name + ' if ' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceXDriverVariable.name + ' > ' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceXDriverVariable.name + ' else ' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceXDriverVariable.name,
    )
    drivers.add(
        eyesHandleLimitLocationConstraint,
        'min_y',
        type='SCRIPTED',
        variables=[leftEyeHandleMinYLocationDriverVariable, rightEyeHandleMinYLocationDriverVariable, leftEyeHandleEyesHandleDistanceYDriverVariable, rightEyeHandleEyesHandleDistanceYDriverVariable],
        expression=leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceYDriverVariable.name + ' if ' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceYDriverVariable.name + ' <= ' + rightEyeHandleMinYLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceYDriverVariable.name + ' else ' + rightEyeHandleMinYLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceYDriverVariable.name,
    )
    drivers.add(
        eyesHandleLimitLocationConstraint,
        'max_y',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleEyesHandleDistanceYDriverVariable, rightEyeHandleEyesHandleDistanceYDriverVariable],
        expression=rightEyeHandleMaxYLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceYDriverVariable.name + ' if ' + rightEyeHandleMaxYLocationDriverVariable.name + ' + ' + rightEyeHandleEyesHandleDistanceYDriverVariable.name + ' > ' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceYDriverVariable.name + ' else ' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleEyesHandleDistanceYDriverVariable.name,
    )
    drivers.add(
        eyesHandleTransformationConstraintEyeballLocation,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsSpeedFactorDriverVariable, eyeballsTrackTargetDriverVariable, eyeballsTrackSpeedFactorDriverVariable],
        expression=eyeballsSpeedFactorDriverVariable.name + ' * (1 - ' + eyeballsTrackTargetDriverVariable.name + ') + ' + eyeballsTrackSpeedFactorDriverVariable.name + ' * ' + eyeballsTrackTargetDriverVariable.name,
    )
    drivers.add(
        eyesHandleTransformationConstraintEyeballLocation,
        'to_min_x',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression='-' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        eyesHandleTransformationConstraintEyeballLocation,
        'to_max_x',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression=eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        eyesHandleTransformationConstraintEyeballLocation,
        'to_min_z',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression='-' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        eyesHandleTransformationConstraintEyeballLocation,
        'to_max_z',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression=eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleLimitLocationConstraint,
        'min_x',
        type='AVERAGE',
        variables=[leftEyeHandleMinXLocationDriverVariable],
    )
    drivers.add(
        leftEyeHandleLimitLocationConstraint,
        'max_x',
        type='AVERAGE',
        variables=[leftEyeHandleMaxXLocationDriverVariable],
    )
    drivers.add(
        leftEyeHandleLimitLocationConstraint,
        'min_y',
        type='AVERAGE',
        variables=[leftEyeHandleMinYLocationDriverVariable],
    )
    drivers.add(
        leftEyeHandleLimitLocationConstraint,
        'max_y',
        type='AVERAGE',
        variables=[leftEyeHandleMaxYLocationDriverVariable],
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'to_max_z',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleLimitLocationConstraint,
        'influence',
        type='AVERAGE',
        variables=[leftEyeHandleLimitLocationDriverVariable],
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'influence',
        type='AVERAGE',
        variables=[leftEyeHandleSpeedCorrectionDriverVariable],
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'from_max_z',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'from_min_z',
        type='SCRIPTED',
        variables=[leftEyeHandleMinXLocationDriverVariable, rightEyeHandleMinXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else -' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'to_min_z',
        type='SCRIPTED',
        variables=[leftEyeHandleMinXLocationDriverVariable, rightEyeHandleMinXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'influence',
        type='AVERAGE',
        variables=[leftEyeHandleSpeedCorrectionDriverVariable],
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'from_max_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'to_max_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'from_min_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMinYLocationDriverVariable, rightEyeHandleMinYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else -' + eyesHandleEyesSizeFactorDriverVariable.name + '',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'to_min_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMinYLocationDriverVariable, rightEyeHandleMinYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocation,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsSpeedFactorDriverVariable, eyeballsTrackTargetDriverVariable, eyeballsTrackSpeedFactorDriverVariable],
        expression=eyeballsSpeedFactorDriverVariable.name + ' * (1 - ' + eyeballsTrackTargetDriverVariable.name + ') + ' + eyeballsTrackSpeedFactorDriverVariable.name + ' * ' + eyeballsTrackTargetDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsSpeedFactorDriverVariable, eyeballsTrackTargetDriverVariable, leftEyeHandleSpeedCorrectionDriverVariable],
        expression=leftEyeHandleSpeedCorrectionDriverVariable.name + ' * (1 - ' + eyeballsTrackTargetDriverVariable.name + ') * ' + eyeballsSpeedFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsSpeedFactorDriverVariable, eyeballsTrackTargetDriverVariable, leftEyeHandleSpeedCorrectionDriverVariable],
        expression=leftEyeHandleSpeedCorrectionDriverVariable.name + ' * (1 - ' + eyeballsTrackTargetDriverVariable.name + ') * ' + eyeballsSpeedFactorDriverVariable.name,
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'to_max_z',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'to_max_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'from_max_z_rot',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(180)',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'from_max_x_rot',
        type='SCRIPTED',
        variables=[leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(180)',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'to_min_z',
        type='SCRIPTED',
        variables=[leftEyeHandleMinXLocationDriverVariable, rightEyeHandleMinXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'to_min_x',
        type='SCRIPTED',
        variables=[leftEyeHandleMinYLocationDriverVariable, rightEyeHandleMinYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'from_min_z_rot',
        type='SCRIPTED',
        variables=[leftEyeHandleMinXLocationDriverVariable, rightEyeHandleMinXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(-180)',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'from_min_x_rot',
        type='SCRIPTED',
        variables=[leftEyeHandleMinYLocationDriverVariable, rightEyeHandleMinYLocationDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(-180)',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocation,
        'to_min_x',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression='-' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocation,
        'to_max_x',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression=eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocation,
        'to_min_z',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression='-' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        leftEyeHandleTransformationConstraintEyeballLocation,
        'to_max_z',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression=eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleLimitLocationConstraint,
        'min_x',
        type='AVERAGE',
        variables=[rightEyeHandleMinXLocationDriverVariable],
    )
    drivers.add(
        rightEyeHandleLimitLocationConstraint,
        'max_x',
        type='AVERAGE',
        variables=[rightEyeHandleMaxXLocationDriverVariable],
    )
    drivers.add(
        rightEyeHandleLimitLocationConstraint,
        'min_y',
        type='AVERAGE',
        variables=[rightEyeHandleMinYLocationDriverVariable],
    )
    drivers.add(
        rightEyeHandleLimitLocationConstraint,
        'max_y',
        type='AVERAGE',
        variables=[rightEyeHandleMaxYLocationDriverVariable],
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'to_max_z',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleLimitLocationConstraint,
        'influence',
        type='AVERAGE',
        variables=[rightEyeHandleLimitLocationDriverVariable],
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'influence',
        type='AVERAGE',
        variables=[rightEyeHandleSpeedCorrectionDriverVariable],
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'from_max_z',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'from_min_z',
        type='SCRIPTED',
        variables=[rightEyeHandleMinXLocationDriverVariable, leftEyeHandleMinXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else -' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'to_min_z',
        type='SCRIPTED',
        variables=[rightEyeHandleMinXLocationDriverVariable, leftEyeHandleMinXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'influence',
        type='AVERAGE',
        variables=[rightEyeHandleSpeedCorrectionDriverVariable],
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'from_max_x',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMax,
        'to_max_x',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'from_min_x',
        type='SCRIPTED',
        variables=[rightEyeHandleMinYLocationDriverVariable, leftEyeHandleMinYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else -' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintHandleLocationCorrectionMin,
        'to_min_x',
        type='SCRIPTED',
        variables=[rightEyeHandleMinYLocationDriverVariable, leftEyeHandleMinYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocation,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsSpeedFactorDriverVariable, eyeballsTrackTargetDriverVariable, eyeballsTrackSpeedFactorDriverVariable],
        expression=eyeballsSpeedFactorDriverVariable.name + ' * (1 - ' + eyeballsTrackTargetDriverVariable.name + ') + ' + eyeballsTrackSpeedFactorDriverVariable.name + ' * ' + eyeballsTrackTargetDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsSpeedFactorDriverVariable, eyeballsTrackTargetDriverVariable, rightEyeHandleSpeedCorrectionDriverVariable],
        expression=rightEyeHandleSpeedCorrectionDriverVariable.name + ' * (1 - ' + eyeballsTrackTargetDriverVariable.name + ') * ' + eyeballsSpeedFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsSpeedFactorDriverVariable, eyeballsTrackTargetDriverVariable, rightEyeHandleSpeedCorrectionDriverVariable],
        expression=rightEyeHandleSpeedCorrectionDriverVariable.name + ' * (1 - ' + eyeballsTrackTargetDriverVariable.name + ') * ' + eyeballsSpeedFactorDriverVariable.name,
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'to_max_z',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'to_max_x',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') - ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'from_max_z_rot',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + rightEyeHandleMaxXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMaxXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(180)',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMax,
        'from_max_x_rot',
        type='SCRIPTED',
        variables=[rightEyeHandleMaxYLocationDriverVariable, leftEyeHandleMaxYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + rightEyeHandleMaxYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMaxYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') <= 0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(180)',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'to_min_z',
        type='SCRIPTED',
        variables=[rightEyeHandleMinXLocationDriverVariable, leftEyeHandleMinXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'to_min_x',
        type='SCRIPTED',
        variables=[rightEyeHandleMinYLocationDriverVariable, leftEyeHandleMinYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='0 if (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') * -' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10 / (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') + ' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'from_min_z_rot',
        type='SCRIPTED',
        variables=[rightEyeHandleMinXLocationDriverVariable, leftEyeHandleMinXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + rightEyeHandleMinXLocationDriverVariable.name + ' + ' + rightEyeHandleHeadDistanceXDriverVariable.name + ') - (' + leftEyeHandleMinXLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceXDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(-180)',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocationCorrectionMin,
        'from_min_x_rot',
        type='SCRIPTED',
        variables=[rightEyeHandleMinYLocationDriverVariable, leftEyeHandleMinYLocationDriverVariable, rightEyeHandleHeadDistanceYDriverVariable, leftEyeHandleHeadDistanceYDriverVariable, eyesHandleEyesSizeFactorDriverVariable],
        expression='radians(0) if (' + rightEyeHandleMinYLocationDriverVariable.name + ' - ' + rightEyeHandleHeadDistanceYDriverVariable.name + ') - (' + leftEyeHandleMinYLocationDriverVariable.name + ' - ' + leftEyeHandleHeadDistanceYDriverVariable.name + ') >= -0.000001 * ' + eyesHandleEyesSizeFactorDriverVariable.name + ' else radians(-180)',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocation,
        'to_min_x',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression='-' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocation,
        'to_max_x',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression=eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocation,
        'to_min_z',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression='-' + eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        rightEyeHandleTransformationConstraintEyeballLocation,
        'to_max_z',
        type='SCRIPTED',
        variables=[eyesHandleEyesSizeFactorDriverVariable],
        expression=eyesHandleEyesSizeFactorDriverVariable.name + ' / 10',
    )
    drivers.add(
        eyesTrackTargetParentArmatureConstraint.targets[0],
        'weight',
        type='AVERAGE',
        variables=[eyesTrackTargetParentToHeadDriverVariable],
    )
    drivers.add(
        eyesTrackTargetParentArmatureConstraint.targets[1],
        'weight',
        type='AVERAGE',
        variables=[eyesTrackTargetParentToTorsoDriverVariable],
    )
    drivers.add(
        eyesTrackTargetParentArmatureConstraint.targets[2],
        'weight',
        type='AVERAGE',
        variables=[eyesTrackTargetParentToRootDriverVariable],
    )
    drivers.add(
        eyeballsCopyRotationConstraintTrack,
        'influence',
        type='AVERAGE',
        variables=[eyeballsTrackTargetDriverVariable],
    )
    drivers.add(
        leftEyeballCopyRotationConstraintTrack,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsTrackTargetDriverVariable, eyeballsNearbyTargetTrackCorrectionDriverVariable],
        expression=eyeballsTrackTargetDriverVariable.name + ' * ' + eyeballsNearbyTargetTrackCorrectionDriverVariable.name,
    )
    drivers.add(
        rightEyeballCopyRotationConstraintTrack,
        'influence',
        type='SCRIPTED',
        variables=[eyeballsTrackTargetDriverVariable, eyeballsNearbyTargetTrackCorrectionDriverVariable],
        expression=eyeballsTrackTargetDriverVariable.name + ' * ' + eyeballsNearbyTargetTrackCorrectionDriverVariable.name,
    )
    drivers.add(
        metarig.pose.bones[names.LEFT_EYEBALL_TRACK_CORRECTION_BONE],
        'rotation_quaternion',
        type='SCRIPTED',
        variables=[leftEyeballRightEyeHandleMarkerDistanceDriverVariable, leftEyeballEyesTrackTargetDistanceDriverVariable, eyeballsTrackBoneRotationZDriverVariable, leftEyeballTrackBoneRotationZDriverVariable, leftEyeHandleSpeedCorrectionDriverVariable, leftEyeHandleMaxXLocationDriverVariable, rightEyeHandleMaxXLocationDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, eyeballsNearbyTargetSizeFactorDriverVariable],
        expression='0 if ' + leftEyeballRightEyeHandleMarkerDistanceDriverVariable.name + '-' + leftEyeballEyesTrackTargetDistanceDriverVariable.name + '<=0 else (radians(-45)+' + leftEyeballTrackBoneRotationZDriverVariable.name + ')*(' + leftEyeballRightEyeHandleMarkerDistanceDriverVariable.name + '-' + leftEyeballEyesTrackTargetDistanceDriverVariable.name + ')/' + eyeballsNearbyTargetSizeFactorDriverVariable.name + '*(' + eyeballsTrackBoneRotationZDriverVariable.name + '-' + leftEyeballTrackBoneRotationZDriverVariable.name + ')*20*(1 if (' + leftEyeHandleMaxXLocationDriverVariable.name + '-' + leftEyeHandleHeadDistanceXDriverVariable.name + ')-(' + rightEyeHandleMaxXLocationDriverVariable.name + '+' + rightEyeHandleHeadDistanceXDriverVariable.name + ')<=0.000001 else 1+' + leftEyeHandleSpeedCorrectionDriverVariable.name + '*(' + leftEyeHandleMaxXLocationDriverVariable.name + '-' + leftEyeHandleHeadDistanceXDriverVariable.name + ')/(' + rightEyeHandleMaxXLocationDriverVariable.name + '+' + rightEyeHandleHeadDistanceXDriverVariable.name + '))',
        index=3,
    )
    drivers.add(
        metarig.pose.bones[names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE],
        'rotation_quaternion',
        type='SCRIPTED',
        variables=[rightEyeballRightEyeHandleMarkerDistanceDriverVariable, rightEyeballEyesTrackTargetDistanceDriverVariable, eyeballsTrackBoneRotationZDriverVariable, rightEyeballTrackBoneRotationZDriverVariable, rightEyeHandleSpeedCorrectionDriverVariable, rightEyeHandleMinXLocationDriverVariable, leftEyeHandleMinXLocationDriverVariable, rightEyeHandleHeadDistanceXDriverVariable, leftEyeHandleHeadDistanceXDriverVariable, eyeballsNearbyTargetSizeFactorDriverVariable],
        expression='0 if ' + rightEyeballRightEyeHandleMarkerDistanceDriverVariable.name + '-' + rightEyeballEyesTrackTargetDistanceDriverVariable.name + '<=0 else (radians(45)+' + rightEyeballTrackBoneRotationZDriverVariable.name + ')*(' + rightEyeballRightEyeHandleMarkerDistanceDriverVariable.name + '-' + rightEyeballEyesTrackTargetDistanceDriverVariable.name + ')/' + eyeballsNearbyTargetSizeFactorDriverVariable.name + '*(' + rightEyeballTrackBoneRotationZDriverVariable.name + '-' + eyeballsTrackBoneRotationZDriverVariable.name + ')*20*(1 if (' + rightEyeHandleMinXLocationDriverVariable.name + '+' + rightEyeHandleHeadDistanceXDriverVariable.name + ')-(' + leftEyeHandleMinXLocationDriverVariable.name + '-' + leftEyeHandleHeadDistanceXDriverVariable.name + ')>=-0.000001 else 1+' + rightEyeHandleSpeedCorrectionDriverVariable.name + '*(' + rightEyeHandleMinXLocationDriverVariable.name + '+' + rightEyeHandleHeadDistanceXDriverVariable.name + ')/(' + leftEyeHandleMinXLocationDriverVariable.name + '-' + leftEyeHandleHeadDistanceXDriverVariable.name + '))',
        index=3,
    )
    drivers.add(
        headTransformationConstraintHeadRotation,
        'influence',
        type='AVERAGE',
        variables=[headTrackTargetDriverVariable],
    )
    drivers.add(
        headLimitRotationConstraint,
        'influence',
        type='AVERAGE',
        variables=[headTrackTargetLimitRotationDriverVariable],
    )
    drivers.add(
        headLimitRotationConstraint,
        'min_x',
        type='SCRIPTED',
        variables=[headTrackTargetMinXRotationDriverVariable],
        expression='radians(' + headTrackTargetMinXRotationDriverVariable.name + ')',
    )
    drivers.add(
        headLimitRotationConstraint,
        'max_x',
        type='SCRIPTED',
        variables=[headTrackTargetMaxXRotationDriverVariable],
        expression='radians(' + headTrackTargetMaxXRotationDriverVariable.name + ')',
    )
    drivers.add(
        headLimitRotationConstraint,
        'min_y',
        type='SCRIPTED',
        variables=[headTrackTargetMinYRotationDriverVariable],
        expression='radians(' + headTrackTargetMinYRotationDriverVariable.name + ')',
    )
    drivers.add(
        headLimitRotationConstraint,
        'max_y',
        type='SCRIPTED',
        variables=[headTrackTargetMaxYRotationDriverVariable],
        expression='radians(' + headTrackTargetMaxYRotationDriverVariable.name + ')',
    )
    drivers.add(
        headLimitRotationConstraint,
        'min_z',
        type='SCRIPTED',
        variables=[headTrackTargetMinZRotationDriverVariable],
        expression='radians(' + headTrackTargetMinZRotationDriverVariable.name + ')',
    )
    drivers.add(
        headLimitRotationConstraint,
        'max_z',
        type='SCRIPTED',
        variables=[headTrackTargetMaxZRotationDriverVariable],
        expression='radians(' + headTrackTargetMaxZRotationDriverVariable.name + ')',
    )    
    drivers.add(
        headTrackTargetParentArmatureConstraint.targets[0],
        'weight',
        type='AVERAGE',
        variables=[headTrackTargetParentToHeadDriverVariable],
    )
    drivers.add(
        headTrackTargetParentArmatureConstraint.targets[1],
        'weight',
        type='AVERAGE',
        variables=[headTrackTargetParentToTorsoDriverVariable],
    )
    drivers.add(
        headTrackTargetParentArmatureConstraint.targets[2],
        'weight',
        type='AVERAGE',
        variables=[headTrackTargetParentToRootDriverVariable],
    )
    
        
    finalizeEyeballBone(metarig, names.EYEBALLS_BONE)
    finalizeEyeballBone(metarig, names.LEFT_EYEBALL_BONE)
    finalizeEyeballBone(metarig, names.RIGHT_EYEBALL_BONE)


    # Ported: legacy put collection index 2 on panel row 1 here. The collections are now made in bone
    # order, so index 2 was whichever came third (Junk on KK, issue #25); Torso gets row 1 by name below.













    
    # The legacy importer turned its joint-correction constraints and swapped its shoulder drivers'
    # axes here, for its drivers on upright bones. Those drivers are gone (ADR 0038): the joint
    # corrections are taken off before these scripts and put back on the generated rig.












def objToBone(obj, rig, boneName):
    """ 
    Places an object at the location/rotation/scale of the given bone.
    """
    assert bpy.context.mode != 'EDIT_ARMATURE', "assert bpy.context.mode != 'EDIT_ARMATURE'"

    bone = rig.pose.bones[boneName]
    loc = bone.custom_shape_translation
    rot = bone.custom_shape_rotation_euler
    scale = Vector(bone.custom_shape_scale_xyz)

    if bone.use_custom_shape_bone_size:
        scale *= bone.length

    obj.rotation_mode = 'XYZ'
    
    shape_mat = Matrix.LocRotScale(loc, Euler(rot), scale)
    obj.matrix_basis = rig.matrix_world @ bone.bone.matrix_local @ shape_mat


def createWidget(build, objName, collectionName, rig, boneName):
    """ 
    Creates an empty widget object and returns the object.
    """
    # Ported: the widget goes into the Character's own widget collection, and another
    # Character's widget of the same name is left alone (Blender adds .001).
    mesh = bpy.data.meshes.new(objName)
    obj = bpy.data.objects.new(objName, mesh)
    build.widgets.objects.link(obj)
    objToBone(obj, rig, boneName)
    return obj


def createEyeWidget(build, objName, collectionName, rig, boneName, size = 1.0):
    obj = createWidget(build, objName, collectionName, rig, boneName)
    if obj is not None:
        verts = [(1.1920928955078125e-07*size, 0.5000000596046448*size, 0.0*size), (-0.12940943241119385*size, 0.482962965965271*size, 0.0*size), (-0.24999988079071045*size, 0.4330127537250519*size, 0.0*size), (-0.35355329513549805*size, 0.35355344414711*size, 0.0*size), (-0.43301260471343994*size, 0.2500000596046448*size, 0.0*size), (-0.4829627275466919*size, 0.12940959632396698*size, 0.0*size), (-0.49999988079071045*size, 1.0094120739267964e-07*size, 0.0*size), (-0.482962965965271*size, -0.12940940260887146*size, 0.0*size), (-0.43301260471343994*size, -0.24999986588954926*size, 0.0*size), (-0.3535534143447876*size, -0.35355323553085327*size, 0.0*size), (-0.25*size, -0.43301257491111755*size, 0.0*size), (-0.1294095516204834*size, -0.48296281695365906*size, 0.0*size), (-1.1920928955078125e-07*size, -0.4999999403953552*size, 0.0*size), (0.12940943241119385*size, -0.4829629063606262*size, 0.0*size), (0.24999988079071045*size, -0.4330127537250519*size, 0.0*size), (0.35355329513549805*size, -0.35355353355407715*size, 0.0*size), (0.4330127239227295*size, -0.25000008940696716*size, 0.0*size), (0.482962965965271*size, -0.12940965592861176*size, 0.0*size), (0.5000001192092896*size, -1.6926388468618825e-07*size, 0.0*size), (0.48296308517456055*size, 0.1294093281030655*size, 0.0*size), (0.4330129623413086*size, 0.24999980628490448*size, 0.0*size), (0.35355377197265625*size, 0.35355323553085327*size, 0.0*size), (0.25000035762786865*size, 0.43301260471343994*size, 0.0*size), (0.1294100284576416*size, 0.48296287655830383*size, 0.0*size), ]
        edges = [(1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 8), (10, 9), (11, 10), (12, 11), (13, 12), (14, 13), (15, 14), (16, 15), (17, 16), (18, 17), (19, 18), (20, 19), (21, 20), (22, 21), (23, 22), (0, 23), ]
        faces = []

        mesh = obj.data
        mesh.from_pydata(verts, edges, faces)
        mesh.update()
        return obj
    else:
        return None


def createEyesWidget(build, objName, collectionName, rig, boneName, size = 1.0):
    obj = createWidget(build, objName, collectionName, rig, boneName)
    if obj is not None:
        verts = [(0.8928930759429932*size, -0.7071065902709961*size, 0.0*size), (0.8928932547569275*size, 0.7071067690849304*size, 0.0*size), (-1.8588197231292725*size, -0.9659252762794495*size, 0.0*size), (-2.100001096725464*size, -0.8660248517990112*size, 0.0*size), (-2.3071072101593018*size, -0.7071059942245483*size, 0.0*size), (-2.4660258293151855*size, -0.49999913573265076*size, 0.0*size), (-2.5659260749816895*size, -0.258818119764328*size, 0.0*size), (-2.5999999046325684*size, 8.575012770961621e-07*size, 0.0*size), (-2.5659255981445312*size, 0.2588198482990265*size, 0.0*size), (-2.4660253524780273*size, 0.5000006556510925*size, 0.0*size), (-2.3071064949035645*size, 0.7071075439453125*size, 0.0*size), (-2.099999189376831*size, 0.866025984287262*size, 0.0*size), (-1.8588184118270874*size, 0.9659261703491211*size, 0.0*size), (-1.5999996662139893*size, 1.000000238418579*size, 0.0*size), (-1.341180443763733*size, 0.9659258723258972*size, 0.0*size), (-1.0999995470046997*size, 0.8660253882408142*size, 0.0*size), (-0.8928929567337036*size, 0.7071067094802856*size, 0.0*size), (-0.892893373966217*size, -0.7071066498756409*size, 0.0*size), (-1.100000262260437*size, -0.8660252690315247*size, 0.0*size), (-1.3411810398101807*size, -0.9659255743026733*size, 0.0*size), (1.600000023841858*size, 1.0*size, 0.0*size), (1.3411810398101807*size, 0.9659258127212524*size, 0.0*size), (1.100000023841858*size, 0.8660253882408142*size, 0.0*size), (-1.600000262260437*size, -0.9999997615814209*size, 0.0*size), (1.0999997854232788*size, -0.8660252690315247*size, 0.0*size), (1.341180682182312*size, -0.9659257531166077*size, 0.0*size), (1.5999996662139893*size, -1.0*size, 0.0*size), (1.8588186502456665*size, -0.965925931930542*size, 0.0*size), (2.0999996662139893*size, -0.8660256266593933*size, 0.0*size), (2.3071064949035645*size, -0.7071071863174438*size, 0.0*size), (2.4660253524780273*size, -0.5000002980232239*size, 0.0*size), (2.5659255981445312*size, -0.25881943106651306*size, 0.0*size), (2.5999999046325684*size, -4.649122899991198e-07*size, 0.0*size), (2.5659260749816895*size, 0.25881853699684143*size, 0.0*size), (2.4660258293151855*size, 0.4999994933605194*size, 0.0*size), (2.3071072101593018*size, 0.707106351852417*size, 0.0*size), (2.1000006198883057*size, 0.8660250902175903*size, 0.0*size), (1.8588197231292725*size, 0.9659256339073181*size, 0.0*size), (-1.8070557117462158*size, -0.7727401852607727*size, 0.0*size), (-2.0000009536743164*size, -0.6928198337554932*size, 0.0*size), (-2.1656856536865234*size, -0.5656847357749939*size, 0.0*size), (-2.292820692062378*size, -0.3999992609024048*size, 0.0*size), (-2.3727407455444336*size, -0.20705445110797882*size, 0.0*size), (-2.3999998569488525*size, 7.336847716032935e-07*size, 0.0*size), (-2.3727405071258545*size, 0.207055926322937*size, 0.0*size), (-2.2928202152252197*size, 0.40000057220458984*size, 0.0*size), (-2.1656851768493652*size, 0.5656861066818237*size, 0.0*size), (-1.9999992847442627*size, 0.6928208470344543*size, 0.0*size), (-1.8070547580718994*size, 0.7727410197257996*size, 0.0*size), (-1.5999996662139893*size, 0.8000002503395081*size, 0.0*size), (-1.3929443359375*size, 0.7727407813072205*size, 0.0*size), (-1.1999995708465576*size, 0.6928203701972961*size, 0.0*size), (-1.0343143939971924*size, 0.5656854510307312*size, 0.0*size), (-1.0343146324157715*size, -0.5656852722167969*size, 0.0*size), (-1.2000001668930054*size, -0.6928201913833618*size, 0.0*size), (-1.3929448127746582*size, -0.7727404236793518*size, 0.0*size), (-1.6000001430511475*size, -0.7999997735023499*size, 0.0*size), (1.8070557117462158*size, 0.772739827632904*size, 0.0*size), (2.0000009536743164*size, 0.6928195953369141*size, 0.0*size), (2.1656856536865234*size, 0.5656843781471252*size, 0.0*size), (2.292820692062378*size, 0.39999890327453613*size, 0.0*size), (2.3727407455444336*size, 0.20705409348011017*size, 0.0*size), (2.3999998569488525*size, -1.0960745839838637e-06*size, 0.0*size), (2.3727405071258545*size, -0.20705628395080566*size, 0.0*size), (2.2928202152252197*size, -0.4000009298324585*size, 0.0*size), (2.1656851768493652*size, -0.5656863451004028*size, 0.0*size), (1.9999992847442627*size, -0.692821204662323*size, 0.0*size), (1.8070547580718994*size, -0.7727413773536682*size, 0.0*size), (1.5999996662139893*size, -0.8000004887580872*size, 0.0*size), (1.3929443359375*size, -0.7727410197257996*size, 0.0*size), (1.1999995708465576*size, -0.6928204894065857*size, 0.0*size), (1.0343143939971924*size, -0.5656855702400208*size, 0.0*size), (1.0343146324157715*size, 0.5656850337982178*size, 0.0*size), (1.2000004053115845*size, 0.6928199529647827*size, 0.0*size), (1.3929448127746582*size, 0.7727401852607727*size, 0.0*size), (1.6000001430511475*size, 0.7999995350837708*size, 0.0*size), ]
        edges = [(24, 0), (1, 22), (16, 1), (17, 0), (23, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10), (10, 11), (11, 12), (12, 13), (21, 20), (22, 21), (13, 14), (14, 15), (15, 16), (17, 18), (18, 19), (19, 23), (25, 24), (26, 25), (27, 26), (28, 27), (29, 28), (30, 29), (31, 30), (32, 31), (33, 32), (34, 33), (35, 34), (36, 35), (37, 36), (20, 37), (56, 38), (38, 39), (39, 40), (40, 41), (41, 42), (42, 43), (43, 44), (44, 45), (45, 46), (46, 47), (47, 48), (48, 49), (49, 50), (50, 51), (51, 52), (53, 54), (54, 55), (55, 56), (75, 57), (57, 58), (58, 59), (59, 60), (60, 61), (61, 62), (62, 63), (63, 64), (64, 65), (65, 66), (66, 67), (67, 68), (68, 69), (69, 70), (70, 71), (72, 73), (73, 74), (74, 75), (52, 72), (53, 71), ]
        faces = []

        mesh = obj.data
        mesh.from_pydata(verts, edges, faces)
        mesh.update()
        return obj
    else:
        return None


def arrangeTripleWidgetSet(widgetCollectionName, parentWidget, leftChildWidget, rightChildWidget, snapGeometryToOrigin, 
vertexGroupObject, leftVertexGroupName, rightVertexGroupName, 
rotate, rotateXRadians, rotateYRadians, rotateZRadians, 
translate, vertexGroupMidXFactor, vertexGroupMinYFactor, parentWidgetTranslateZFactor, 
resize, parentWidgetResizeXFactor, parentWidgetResizeYFactor, parentWidgetResizeZFactor, 
createHandleBones, rig, parentBoneName, parentHandleBoneName, leftChildBoneName, leftChildHandleBoneName, rightChildBoneName, rightChildHandleBoneName):
    # Ported: the legacy script shaped the widgets in Edit Mode with transform operators around
    # each widget's bounding-box centre in global space; widgets.py does the same on the data API.
    bpy.context.view_layer.update()
    def shape(widget):
        if snapGeometryToOrigin:
            widgets.geometry_to_origin(widget)
        if rotate:
            for axis, degrees in (('X', rotateXRadians), ('Y', rotateYRadians), ('Z', rotateZRadians)):
                if degrees:
                    widgets.rotate(widget, axis, math.radians(degrees))
    shape(parentWidget)
    leftVertexGroupExtremities = meshes.group_bounds(vertexGroupObject, leftVertexGroupName)
    rightVertexGroupExtremities = meshes.group_bounds(vertexGroupObject, rightVertexGroupName)
    if not leftVertexGroupExtremities.max_z or not rightVertexGroupExtremities.max_z:
        leftVertexGroupExtremities = meshes.group_bounds(vertexGroupObject, 'cf_J_Eye07_s_L')
        rightVertexGroupExtremities = meshes.group_bounds(vertexGroupObject, 'cf_J_Eye07_s_R')

    leftVertexGroupMidZ = (leftVertexGroupExtremities.max_z + leftVertexGroupExtremities.min_z) / 2
    rightVertexGroupMidZ = (rightVertexGroupExtremities.max_z + rightVertexGroupExtremities.min_z) / 2
    averageVertexGroupMidZ = statistics.mean([leftVertexGroupMidZ, rightVertexGroupMidZ])
    averageVertexGroupMinY = statistics.mean([leftVertexGroupExtremities.min_y, rightVertexGroupExtremities.min_y])
    if translate and not createHandleBones:
        widgets.translate(parentWidget, (0, averageVertexGroupMinY * vertexGroupMinYFactor, -(parentWidget.location[2] - averageVertexGroupMidZ * parentWidgetTranslateZFactor)))
    leftVertexGroupMidX = (leftVertexGroupExtremities.max_x + leftVertexGroupExtremities.min_x) / 2
    rightVertexGroupMidX = (rightVertexGroupExtremities.max_x + rightVertexGroupExtremities.min_x) / 2
    if resize:
        widgets.resize(parentWidget, (parentWidgetResizeXFactor, parentWidgetResizeYFactor, parentWidgetResizeZFactor))

    shape(leftChildWidget)
    if translate and not createHandleBones:
        widgets.translate(leftChildWidget, (leftVertexGroupMidX * vertexGroupMidXFactor, leftVertexGroupExtremities.min_y * vertexGroupMinYFactor, -(leftChildWidget.location[2] - leftVertexGroupMidZ * parentWidgetTranslateZFactor)))
    leftVertexGroupLengthX = leftVertexGroupExtremities.max_x - leftVertexGroupExtremities.min_x
    rightVertexGroupLengthX = rightVertexGroupExtremities.max_x - rightVertexGroupExtremities.min_x
    averageVertexGroupLengthX = statistics.mean([leftVertexGroupLengthX, rightVertexGroupLengthX])
    leftVertexGroupLengthY = leftVertexGroupExtremities.max_y - leftVertexGroupExtremities.min_y
    rightVertexGroupLengthY = rightVertexGroupExtremities.max_y - rightVertexGroupExtremities.min_y
    averageVertexGroupLengthY = statistics.mean([leftVertexGroupLengthY, rightVertexGroupLengthY])
    leftVertexGroupLengthZ = leftVertexGroupExtremities.max_z - leftVertexGroupExtremities.min_z
    rightVertexGroupLengthZ = rightVertexGroupExtremities.max_z - rightVertexGroupExtremities.min_z
    averageVertexGroupLengthZ = statistics.mean([leftVertexGroupLengthZ, rightVertexGroupLengthZ])
    leftChildWidgetResizeXFactor = statistics.mean([parentWidgetResizeXFactor, parentWidgetResizeXFactor * (leftVertexGroupLengthX / averageVertexGroupLengthX)])
    leftChildWidgetResizeYFactor = statistics.mean([parentWidgetResizeYFactor, parentWidgetResizeYFactor * (leftVertexGroupLengthY / averageVertexGroupLengthY)])
    leftChildWidgetResizeZFactor = statistics.mean([parentWidgetResizeZFactor, parentWidgetResizeZFactor * (leftVertexGroupLengthZ / averageVertexGroupLengthZ)])
    if resize:
        widgets.resize(leftChildWidget, (leftChildWidgetResizeXFactor, leftChildWidgetResizeYFactor, leftChildWidgetResizeZFactor))

    shape(rightChildWidget)
    if translate and not createHandleBones:
        widgets.translate(rightChildWidget, (rightVertexGroupMidX * vertexGroupMidXFactor, rightVertexGroupExtremities.min_y * vertexGroupMinYFactor, -(rightChildWidget.location[2] - rightVertexGroupMidZ * parentWidgetTranslateZFactor)))
    rightChildWidgetResizeXFactor = statistics.mean([parentWidgetResizeXFactor, parentWidgetResizeXFactor * (rightVertexGroupLengthX / averageVertexGroupLengthX)])
    rightChildWidgetResizeYFactor = statistics.mean([parentWidgetResizeYFactor, parentWidgetResizeYFactor * (rightVertexGroupLengthY / averageVertexGroupLengthY)])
    rightChildWidgetResizeZFactor = statistics.mean([parentWidgetResizeZFactor, parentWidgetResizeZFactor * (rightVertexGroupLengthZ / averageVertexGroupLengthZ)])
    if resize:
        widgets.resize(rightChildWidget, (rightChildWidgetResizeXFactor, rightChildWidgetResizeYFactor, rightChildWidgetResizeZFactor))

    if createHandleBones:
        
        switch(rig, 'EDIT')
        parentHandleBone = bones.copy_bone(rig, parentBoneName, parentHandleBoneName)
        if translate:
            parentHandleBone.tail.y = parentHandleBone.tail.y + averageVertexGroupMinY * vertexGroupMinYFactor
            parentHandleBone.head.y = parentHandleBone.head.y + averageVertexGroupMinY * vertexGroupMinYFactor
            parentHandleBone.tail.z = parentHandleBone.tail.z - (parentWidget.location[2] - averageVertexGroupMidZ * parentWidgetTranslateZFactor)
            parentHandleBone.head.z = parentHandleBone.head.z - (parentWidget.location[2] - averageVertexGroupMidZ * parentWidgetTranslateZFactor)
        leftChildHandleBone = bones.copy_bone(rig, leftChildBoneName, leftChildHandleBoneName)
        if translate:
            leftChildHandleBone.tail.x = leftChildHandleBone.tail.x + leftVertexGroupMidX * vertexGroupMidXFactor
            leftChildHandleBone.head.x = leftChildHandleBone.head.x + leftVertexGroupMidX * vertexGroupMidXFactor
            leftChildHandleBone.tail.y = leftChildHandleBone.tail.y + leftVertexGroupExtremities.min_y * vertexGroupMinYFactor
            leftChildHandleBone.head.y = leftChildHandleBone.head.y + leftVertexGroupExtremities.min_y * vertexGroupMinYFactor
            leftChildHandleBone.tail.z = leftChildHandleBone.tail.z - (leftChildWidget.location[2] - leftVertexGroupMidZ * parentWidgetTranslateZFactor)
            leftChildHandleBone.head.z = leftChildHandleBone.head.z - (leftChildWidget.location[2] - leftVertexGroupMidZ * parentWidgetTranslateZFactor)
        leftChildHandleBone.parent = parentHandleBone
        rightChildHandleBone = bones.copy_bone(rig, rightChildBoneName, rightChildHandleBoneName)
        if translate:
            rightChildHandleBone.tail.x = rightChildHandleBone.tail.x + rightVertexGroupMidX * vertexGroupMidXFactor
            rightChildHandleBone.head.x = rightChildHandleBone.head.x + rightVertexGroupMidX * vertexGroupMidXFactor
            rightChildHandleBone.tail.y = rightChildHandleBone.tail.y + rightVertexGroupExtremities.min_y * vertexGroupMinYFactor
            rightChildHandleBone.head.y = rightChildHandleBone.head.y + rightVertexGroupExtremities.min_y * vertexGroupMinYFactor
            rightChildHandleBone.tail.z = rightChildHandleBone.tail.z - (rightChildWidget.location[2] - rightVertexGroupMidZ * parentWidgetTranslateZFactor)
            rightChildHandleBone.head.z = rightChildHandleBone.head.z - (rightChildWidget.location[2] - rightVertexGroupMidZ * parentWidgetTranslateZFactor)
        rightChildHandleBone.parent = parentHandleBone
        
        switch(rig, 'OBJECT')


def finalizeHandleBone(isEyeHandleBone, rig, boneName, handleBoneName, widget):
    rig.pose.bones[handleBoneName].custom_shape = widget
    if isEyeHandleBone:
        rig.pose.bones[handleBoneName].lock_location[1] = True
        rig.pose.bones[handleBoneName].lock_rotation[0] = True
        rig.pose.bones[handleBoneName].lock_rotation[2] = True
        rig.pose.bones[handleBoneName].lock_scale[1] = True
    constraints.copy_transforms(
        rig,
        boneName,
        handleBoneName,
        name=names.COPY_TRANSFORMS_CONSTRAINT_BASE + names.HANDLE_CONSTRAINT_SUFFIX,
        mix='REPLACE',
        space='LOCAL',
    )


def finalizeEyeballBone(rig, boneName):
    rig.pose.bones[boneName].lock_location[0] = True
    rig.pose.bones[boneName].lock_location[1] = True
    rig.pose.bones[boneName].lock_location[2] = True




















