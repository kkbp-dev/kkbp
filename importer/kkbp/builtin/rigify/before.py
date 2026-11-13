
#Switch to Object Mode and select Metarig

import bpy
import math
from math import radians
import statistics
from mathutils import Matrix, Vector, Euler
from . import commons as koikatsuCommons
from . import names
from . import constraints, drivers
from ... import compat
from ...editing import switch
from . import widgets
from .build import Features
    
def main(build):
    """Turns the Character's armature into the Rigify metarig, phase by phase. Each phase
    leaves Blender in the mode the next expects, as the one long function did."""
    _reserved_names(build)
    _features(build)
    _eye_and_body_bones(build)
    _widgets_and_handles(build)
    _eyes(build)
    _rigify_layers(build)
    _deform_vertex_groups(build)
    accessories = _accessories(build)
    _tongue_side_bones(build)
    _head_and_hips(build)
    _limbs(build)
    _skirt(build)
    _rigify_types(build)
    lists = _bone_lists(build, accessories)
    _bone_collections(build, lists)
    _rigify_ui(build)


def _reserved_names(build):
    """Accessory bones can be called anything; ones named like the rig's own bones give way."""
    metarig = build.metarig
    switch(metarig, 'OBJECT')

    #set the active bone collection to the Core collection so new bones are added there
    metarig.data.collections.active_index = metarig.data.collections[names.ORIGINAL_FK_LAYER_INDEX].index

    #Accessory bones can be named anything, so if they overlap with bones used in the rig they'll cause issues
    reservedBoneNames = [names.ROOT_BONE, names.TORSO_BONE, names.HEAD_TWEAK_BONE]
        
    for boneName in reservedBoneNames:
        if bone := metarig.pose.bones.get(boneName):
            bone.name = bone.name + names.RENAMED_NAME_SUFFIX
                
    
    fixDuplicateBoneName(build, names.HEAD_BONE, names.ORIGINAL_EYES_BONE)
    fixDuplicateBoneName(build, names.NECK_BONE, names.HEAD_BONE)
    fixDuplicateBoneName(build, names.UPPER_CHEST_BONE, names.NECK_BONE)
    fixDuplicateBoneName(build, names.CHEST_BONE, names.UPPER_CHEST_BONE)
    fixDuplicateBoneName(build, names.SPINE_BONE, names.CHEST_BONE)
    fixDuplicateBoneName(build, names.HIPS_BONE, names.SPINE_BONE)
        
    # Check for optional features


def _features(build):
    """What this Character has: skirt, rigged tongue, Better Penetration bones, head mod, male."""
    metarig = build.metarig
    hasSkirt = True    
    if names.SKIRT_PARENT_BONE not in metarig.pose.bones:
        hasSkirt = False
    else:
        for primaryIndex in range(8):
            if names.skirt_bone(True, primaryIndex) not in metarig.pose.bones:
                hasSkirt = False
                break
            for secondaryIndex in range(6):
                if names.skirt_bone(False, primaryIndex, secondaryIndex) not in metarig.pose.bones:
                    hasSkirt = False
                    break
    
    # The tongue rig reads Body, which holds the tongue (ADR 0039), when it is weighted to the tongue bones.
    hasRiggedTongue = (metarig.pose.bones.get(names.RIGGED_TONGUE_BONE1) is not None and build.body is not None
                       and names.RIGGED_TONGUE_BONE1 in build.body.vertex_groups)
    hasBetterPenetrationMod = metarig.pose.bones.get(names.BETTER_PENETRATION_ROOT_CROTCH_BONE)
    hasHeadMod = koikatsuCommons.isVertexGroupEmpty(names.ORIGINAL_FACE_UP_DEFORM_BONE, build.body)
    isMale = koikatsuCommons.isVertexGroupEmpty(names.LEFT_NIPPLE_DEFORM_BONE1, build.body)
    build.features = Features(skirt=bool(hasSkirt), rigged_tongue=bool(hasRiggedTongue), better_penetration=bool(hasBetterPenetrationMod), head_mod=bool(hasHeadMod), male=bool(isMale))


def _eye_and_body_bones(build):
    """The eye bones, and the breasts and buttocks bones the handles move."""
    metarig = build.metarig
    switch(metarig, 'EDIT')
    
    #get the metagrig ID bone
    metarigIdBoneName = None
    for bone in metarig.data.edit_bones:
        if bone.name.startswith(names.METARIG_ID_BONE_PREFIX):
            metarigIdBoneName = bone.name
    if not metarigIdBoneName:
        metarigIdBoneName = names.METARIG_ID_BONE_PREFIX + koikatsuCommons.generateRandomAlphanumericString()
        koikatsuCommons.createBone(metarig, metarigIdBoneName)
    
    #create the eye bones
    eyesBone = koikatsuCommons.copyBone(metarig, names.ORIGINAL_EYES_BONE, names.EYES_BONE)
    leftEyeBone = koikatsuCommons.copyBone(metarig, names.ORIGINAL_EYES_BONE, names.LEFT_EYE_BONE)
    rightEyeBone = koikatsuCommons.copyBone(metarig, names.ORIGINAL_EYES_BONE, names.RIGHT_EYE_BONE)
    leftEyeBone.parent = eyesBone
    rightEyeBone.parent = eyesBone
    
    #adjust the chest bones
    breastsBone = metarig.data.edit_bones[names.BREASTS_BONE]
    leftBreastBone1 = metarig.data.edit_bones[names.LEFT_BREAST_BONE1]
    rightBreastBone1 = metarig.data.edit_bones[names.RIGHT_BREAST_BONE1]
    breastsBone.head.y = statistics.mean([leftBreastBone1.head.y, rightBreastBone1.head.y])
    breastsBone.tail.y = statistics.mean([leftBreastBone1.tail.y, rightBreastBone1.tail.y])
    
    #create the butt bones
    buttocksBone = koikatsuCommons.copyBone(metarig, names.WAIST_BONE, names.BUTTOCKS_BONE)
    buttocksBone.parent = metarig.data.edit_bones[names.WAIST_BONE]
    leftButtockBone = metarig.data.edit_bones[names.LEFT_BUTTOCK_BONE]
    leftButtockBone.parent = buttocksBone
    leftButtockBone.length = buttocksBone.length
    rightButtockBone = metarig.data.edit_bones[names.RIGHT_BUTTOCK_BONE]
    rightButtockBone.parent = buttocksBone
    rightButtockBone.length = buttocksBone.length
    buttocksBone.head.y = statistics.mean([leftButtockBone.head.y, rightButtockBone.head.y])
    buttocksBone.tail.y = statistics.mean([leftButtockBone.tail.y, rightButtockBone.tail.y])
    
    switch(metarig, 'OBJECT')
    build.metarig_id_bone = metarigIdBoneName


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
    eyesTrackTargetBone = koikatsuCommons.copyBone(metarig, names.EYES_HANDLE_BONE, names.EYES_TRACK_TARGET_BONE)
    eyesTrackTargetParentBone = koikatsuCommons.copyBone(metarig, names.EYES_HANDLE_BONE, names.EYES_TRACK_TARGET_PARENT_BONE)
    eyesHandleMarkerBone = koikatsuCommons.copyBone(metarig, names.EYES_HANDLE_BONE, names.EYES_HANDLE_MARKER_BONE)
    leftEyeHandleMarkerBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYE_HANDLE_MARKER_BONE)
    rightEyeHandleMarkerBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_MARKER_BONE)
    leftEyeHandleMarkerXBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYE_HANDLE_MARKER_X_BONE)
    rightEyeHandleMarkerXBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_MARKER_X_BONE)
    leftEyeHandleMarkerXBone.head.z = eyesHandleMarkerBone.head.z
    rightEyeHandleMarkerXBone.head.z = eyesHandleMarkerBone.head.z
    leftEyeHandleMarkerXBone.tail.z = eyesHandleMarkerBone.head.z
    rightEyeHandleMarkerXBone.tail.z = eyesHandleMarkerBone.head.z
    leftEyeHandleMarkerZBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYE_HANDLE_MARKER_Z_BONE)
    rightEyeHandleMarkerZBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYE_HANDLE_MARKER_Z_BONE)
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
    eyeballsBone = koikatsuCommons.copyBone(metarig, names.EYES_HANDLE_BONE, names.EYEBALLS_BONE)
    eyeballsBone.roll = radians(0)
    leftEyeballBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_EYEBALL_BONE)
    rightEyeballBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_EYEBALL_BONE)
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
    eyeballsTrackBone = koikatsuCommons.copyBone(metarig, names.EYEBALLS_BONE, names.EYEBALLS_TRACK_BONE)
    leftEyeballTrackBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYEBALL_BONE, names.LEFT_EYEBALL_TRACK_BONE)
    rightEyeballTrackBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYEBALL_BONE, names.RIGHT_EYEBALL_TRACK_BONE)
    leftEyeballTrackCorrectionBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYEBALL_TRACK_BONE, names.LEFT_EYEBALL_TRACK_CORRECTION_BONE)
    rightEyeballTrackCorrectionBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYEBALL_TRACK_BONE, names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE)
    leftHeadMarkerXBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_HEAD_MARKER_X_BONE)
    rightHeadMarkerXBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_HEAD_MARKER_X_BONE)
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
    leftHeadMarkerZBone = koikatsuCommons.copyBone(metarig, names.LEFT_EYE_HANDLE_BONE, names.LEFT_HEAD_MARKER_Z_BONE)
    rightHeadMarkerZBone = koikatsuCommons.copyBone(metarig, names.RIGHT_EYE_HANDLE_BONE, names.RIGHT_HEAD_MARKER_Z_BONE)
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
    headTrackTargetBone = koikatsuCommons.copyBone(metarig, names.EYES_HANDLE_BONE, names.HEAD_TRACK_TARGET_BONE)
    headTrackTargetBone.length = headBone.length
    headTrackTargetParentBone = koikatsuCommons.copyBone(metarig, names.HEAD_TRACK_TARGET_BONE, names.HEAD_TRACK_TARGET_PARENT_BONE)
    headTrackTargetBone.parent = headTrackTargetParentBone
    headTrackTargetParentBone.parent = None
    headTrackBone = koikatsuCommons.copyBone(metarig, names.EYEBALLS_BONE, names.HEAD_TRACK_BONE)
    headTrackBone.parent = None
    headTrackBone.head.y = headBone.head.y
    placeholderHeadTweakBone = koikatsuCommons.createBone(metarig, names.HEAD_TWEAK_BONE + names.PLACEHOLDER_BONE_SUFFIX)
    placeholderTorsoBone = koikatsuCommons.createBone(metarig, names.TORSO_BONE + names.PLACEHOLDER_BONE_SUFFIX)
    placeholderRootBone = koikatsuCommons.createBone(metarig, names.ROOT_BONE + names.PLACEHOLDER_BONE_SUFFIX)
        
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
    
    eyelidsShapeKeyCopy = koikatsuCommons.duplicateShapeKey(build.body, names.EYELIDS_SHAPE_KEY, names.EYELIDS_SHAPE_KEY_COPY)
    
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


def _rigify_layers(build):
    """Rigify's colour sets and layer table."""
    metarig = build.metarig
    """
    Begin Rigifying
    """
    
    compat.add_rigify_color_sets(metarig)
    # Ported: legacy put collection index 2 on panel row 1 here. The collections are now made in bone
    # order, so index 2 was whichever came third (Junk on KK, issue #25); Torso gets row 1 by name below.

    for index, rigifyLayer in enumerate(koikatsuCommons.rigifyLayers):
        koikatsuCommons.setRigifyLayer(metarig, index, rigifyLayer)
    koikatsuCommons.setRootRigifyLayer(metarig, names.ROOT_BONE_GROUP_INDEX)


def _deform_vertex_groups(build):
    """The vertex groups take the names of the Rigify deform bones that will move them."""
    metarig = build.metarig
    hasSkirt = build.features.skirt
    switch(metarig, 'EDIT')
    

    removeAllConstraints(metarig, names.LEFT_ELBOW_BONE)
    removeAllConstraints(metarig, names.RIGHT_ELBOW_BONE)
    removeAllConstraints(metarig, names.LEFT_WRIST_BONE)
    removeAllConstraints(metarig, names.RIGHT_WRIST_BONE)
    removeAllConstraints(metarig, names.LEFT_TOE_BONE)
    removeAllConstraints(metarig, names.RIGHT_TOE_BONE)
    removeAllConstraints(metarig, names.LEFT_ANKLE_BONE)
    removeAllConstraints(metarig, names.RIGHT_ANKLE_BONE)
    removeAllConstraints(metarig, names.LEFT_KNEE_BONE)
    removeAllConstraints(metarig, names.RIGHT_KNEE_BONE)

    
    renameAllVertexGroups(build, names.ORIGINAL_HEAD_DEFORM_BONE, names.HEAD_DEFORM_BONE)
    renameAllVertexGroups(build, names.ORIGINAL_NECK_DEFORM_BONE, names.NECK_DEFORM_BONE)
    renameAllVertexGroups(build, names.ORIGINAL_UPPER_CHEST_DEFORM_BONE, names.UPPER_CHEST_DEFORM_BONE)
    renameAllVertexGroups(build, names.ORIGINAL_CHEST_DEFORM_BONE, names.CHEST_DEFORM_BONE)
    renameAllVertexGroups(build, names.ORIGINAL_SPINE_DEFORM_BONE, names.SPINE_DEFORM_BONE)
    renameAllVertexGroups(build, names.ORIGINAL_HIPS_DEFORM_BONE, names.HIPS_DEFORM_BONE)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_ARM_DEFORM_BONE1, names.LEFT_ARM_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_ARM_DEFORM_BONE1, names.RIGHT_ARM_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_ARM_DEFORM_BONE2, names.LEFT_ARM_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_ARM_DEFORM_BONE2, names.RIGHT_ARM_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_ARM_DEFORM_BONE3, names.LEFT_ARM_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_ARM_DEFORM_BONE3, names.RIGHT_ARM_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_ELBOW_DEFORM_BONE1, names.LEFT_ELBOW_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_ELBOW_DEFORM_BONE1, names.RIGHT_ELBOW_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_ELBOW_DEFORM_BONE2, names.LEFT_ELBOW_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_ELBOW_DEFORM_BONE2, names.RIGHT_ELBOW_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_ELBOW_DEFORM_BONE3, names.LEFT_ELBOW_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_ELBOW_DEFORM_BONE3, names.RIGHT_ELBOW_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_WRIST_DEFORM_BONE, names.LEFT_WRIST_DEFORM_BONE)    
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_WRIST_DEFORM_BONE, names.RIGHT_WRIST_DEFORM_BONE)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_THUMB_DEFORM_BONE1, names.LEFT_THUMB_DEFORM_BONE1)  
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_THUMB_DEFORM_BONE1, names.RIGHT_THUMB_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_THUMB_DEFORM_BONE2, names.LEFT_THUMB_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_THUMB_DEFORM_BONE2, names.RIGHT_THUMB_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_THUMB_DEFORM_BONE3, names.LEFT_THUMB_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_THUMB_DEFORM_BONE3, names.RIGHT_THUMB_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_INDEX_FINGER_DEFORM_BONE1, names.LEFT_INDEX_FINGER_DEFORM_BONE1)   
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_INDEX_FINGER_DEFORM_BONE1, names.RIGHT_INDEX_FINGER_DEFORM_BONE1)  
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_INDEX_FINGER_DEFORM_BONE2, names.LEFT_INDEX_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_INDEX_FINGER_DEFORM_BONE2, names.RIGHT_INDEX_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_INDEX_FINGER_DEFORM_BONE3, names.LEFT_INDEX_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_INDEX_FINGER_DEFORM_BONE3, names.RIGHT_INDEX_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_MIDDLE_FINGER_DEFORM_BONE1, names.LEFT_MIDDLE_FINGER_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_MIDDLE_FINGER_DEFORM_BONE1, names.RIGHT_MIDDLE_FINGER_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_MIDDLE_FINGER_DEFORM_BONE2, names.LEFT_MIDDLE_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_MIDDLE_FINGER_DEFORM_BONE2, names.RIGHT_MIDDLE_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_MIDDLE_FINGER_DEFORM_BONE3, names.LEFT_MIDDLE_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_MIDDLE_FINGER_DEFORM_BONE3, names.RIGHT_MIDDLE_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_RING_FINGER_DEFORM_BONE1, names.LEFT_RING_FINGER_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_RING_FINGER_DEFORM_BONE1, names.RIGHT_RING_FINGER_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_RING_FINGER_DEFORM_BONE2, names.LEFT_RING_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_RING_FINGER_DEFORM_BONE2, names.RIGHT_RING_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_RING_FINGER_DEFORM_BONE3, names.LEFT_RING_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_RING_FINGER_DEFORM_BONE3, names.RIGHT_RING_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_LITTLE_FINGER_DEFORM_BONE1, names.LEFT_LITTLE_FINGER_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_LITTLE_FINGER_DEFORM_BONE1, names.RIGHT_LITTLE_FINGER_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_LITTLE_FINGER_DEFORM_BONE2, names.LEFT_LITTLE_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_LITTLE_FINGER_DEFORM_BONE2, names.RIGHT_LITTLE_FINGER_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_LITTLE_FINGER_DEFORM_BONE3, names.LEFT_LITTLE_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_LITTLE_FINGER_DEFORM_BONE3, names.RIGHT_LITTLE_FINGER_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_THIGH_DEFORM_BONE1, names.LEFT_THIGH_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_THIGH_DEFORM_BONE1, names.RIGHT_THIGH_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_THIGH_DEFORM_BONE2, names.LEFT_THIGH_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_THIGH_DEFORM_BONE2, names.RIGHT_THIGH_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_THIGH_DEFORM_BONE3, names.LEFT_THIGH_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_THIGH_DEFORM_BONE3, names.RIGHT_THIGH_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_LEG_DEFORM_BONE1, names.LEFT_LEG_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_LEG_DEFORM_BONE1, names.RIGHT_LEG_DEFORM_BONE1)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_LEG_DEFORM_BONE2, names.LEFT_LEG_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_LEG_DEFORM_BONE2, names.RIGHT_LEG_DEFORM_BONE2)
    renameAllVertexGroups(build, names.ORIGINAL_LEFT_LEG_DEFORM_BONE3, names.LEFT_LEG_DEFORM_BONE3)
    renameAllVertexGroups(build, names.ORIGINAL_RIGHT_LEG_DEFORM_BONE3, names.RIGHT_LEG_DEFORM_BONE3)
    renameAllVertexGroups(build, names.LEFT_ANKLE_BONE, names.LEFT_ANKLE_DEFORM_BONE)
    renameAllVertexGroups(build, names.RIGHT_ANKLE_BONE, names.RIGHT_ANKLE_DEFORM_BONE)
    renameAllVertexGroups(build, names.LEFT_TOE_BONE, names.LEFT_TOE_DEFORM_BONE)
    renameAllVertexGroups(build, names.RIGHT_TOE_BONE, names.RIGHT_TOE_DEFORM_BONE)

    if hasSkirt:
        for primaryIndex in range(8):
            for secondaryIndex in range(6):
                renameAllVertexGroups(build, names.skirt_bone(False, primaryIndex, secondaryIndex), names.skirt_deform_bone(primaryIndex, secondaryIndex))


def _accessories(build):
    """Accessory bone orientations, the MCH bone lists and the connected chains."""
    metarig = build.metarig
    hasRiggedTongue = build.features.rigged_tongue
    
    fix_bone_orientations(build, metarig)

    '''Put all Mch bones into an array'''

    accessoryBoneNames = []
    accessoryMchBoneNames = []
    faceMchBoneNames = []
    for bone in metarig.data.edit_bones:
        if metarig.data.bones[bone.name].collections.get(names.ORIGINAL_UPPER_FACE_LAYER_INDEX) or metarig.data.bones[bone.name].collections.get(names.ORIGINAL_LOWER_FACE_LAYER_INDEX):
            if metarig.data.bones[bone.parent.name].collections.get(names.ORIGINAL_MCH_LAYER_INDEX) and bone.parent.name not in faceMchBoneNames and not metarig.data.bones[bone.parent.name].collections.get(names.ORIGINAL_UPPER_FACE_LAYER_INDEX) and not metarig.data.bones[bone.parent.name].collections.get(names.ORIGINAL_LOWER_FACE_LAYER_INDEX):
                faceMchBoneNames.append(bone.parent.name)
        if metarig.data.bones[bone.name].collections.get(names.ORIGINAL_ACCESSORY_LAYER_INDEX):
            accessoryBoneNames.append(bone.name)
            if metarig.data.bones[bone.parent.name].collections.get(str(names.ORIGINAL_MCH_LAYER_INDEX)) and not metarig.data.bones[bone.parent.name].collections.get(str(names.ORIGINAL_ACCESSORY_LAYER_INDEX)):
                accessoryMchBoneNames.append(bone.parent.name)
    
            
    finalizeMchList(build, metarig, faceMchBoneNames, names.ORIGINAL_MCH_LAYER_INDEX, [names.ORIGINAL_UPPER_FACE_LAYER_INDEX, names.ORIGINAL_LOWER_FACE_LAYER_INDEX])
    finalizeMchList(build, metarig, accessoryMchBoneNames, names.ORIGINAL_MCH_LAYER_INDEX, [names.ORIGINAL_ACCESSORY_LAYER_INDEX], faceMchBoneNames)    
            
    accessoryBoneConnectedChildNames = [] 
    accessoryBoneConnectedParentNames = [] 
    accessoryMchConnectedParentNames = []
    for boneName in accessoryBoneNames:
        renameAllVertexGroups(build, boneName, names.DEFORM_BONE_PREFIX + boneName)
        bone = metarig.data.edit_bones[boneName]
        if bone.use_connect == False or bone.parent.name not in accessoryBoneNames:
            for childBone in bone.children:
                if childBone.use_connect == True and childBone.name in accessoryBoneNames:
                    accessoryBoneConnectedParentNames.append(bone.name)
                    break
            if bone.use_connect == True and bone.parent.name in accessoryMchBoneNames:
                accessoryMchConnectedParentNames.append(bone.parent.name)
        elif bone.use_connect == True:
            accessoryBoneConnectedChildNames.append(bone.name)
            if bone.parent.name in accessoryMchBoneNames:
                accessoryMchConnectedParentNames.append(bone.parent.name)
    
    
    if hasRiggedTongue:
        connectAndParentBones(metarig, names.RIGGED_TONGUE_BONE5, names.RIGGED_TONGUE_BONE4, True)
        connectAndParentBones(metarig, names.RIGGED_TONGUE_BONE4, names.RIGGED_TONGUE_BONE3, True)
        connectAndParentBones(metarig, names.RIGGED_TONGUE_BONE3, names.RIGGED_TONGUE_BONE2, True)
        connectAndParentBones(metarig, names.RIGGED_TONGUE_BONE2, names.RIGGED_TONGUE_BONE1, False)
    connectAndParentBones(metarig, names.HEAD_BONE, names.NECK_BONE, True)
    connectAndParentBones(metarig, names.NECK_BONE, names.UPPER_CHEST_BONE, False)
    connectAndParentBones(metarig, names.UPPER_CHEST_BONE, names.CHEST_BONE, True)
    connectAndParentBones(metarig, names.CHEST_BONE, names.SPINE_BONE, True)
    connectAndParentBones(metarig, names.SPINE_BONE, names.HIPS_BONE, True) 
    connectAndParentBones(metarig, names.LEFT_WRIST_BONE, names.LEFT_ELBOW_BONE, True) 
    connectAndParentBones(metarig, names.RIGHT_WRIST_BONE, names.RIGHT_ELBOW_BONE, True) 
    connectAndParentBones(metarig, names.LEFT_ELBOW_BONE, names.LEFT_ARM_BONE, True) 
    connectAndParentBones(metarig, names.RIGHT_ELBOW_BONE, names.RIGHT_ARM_BONE, True) 
    connectAndParentBones(metarig, names.LEFT_ARM_BONE, names.LEFT_SHOULDER_BONE, False)
    connectAndParentBones(metarig, names.RIGHT_ARM_BONE, names.RIGHT_SHOULDER_BONE, False)
    connectAndParentBones(metarig, names.LEFT_THUMB_BONE3, names.LEFT_THUMB_BONE2, True)  
    connectAndParentBones(metarig, names.RIGHT_THUMB_BONE3, names.RIGHT_THUMB_BONE2, True)  
    connectAndParentBones(metarig, names.LEFT_THUMB_BONE2, names.LEFT_THUMB_BONE1, True)  
    connectAndParentBones(metarig, names.RIGHT_THUMB_BONE2, names.RIGHT_THUMB_BONE1, True)  
    connectAndParentBones(metarig, names.LEFT_INDEX_FINGER_BONE3, names.LEFT_INDEX_FINGER_BONE2, True)
    connectAndParentBones(metarig, names.RIGHT_INDEX_FINGER_BONE3, names.RIGHT_INDEX_FINGER_BONE2, True)
    connectAndParentBones(metarig, names.LEFT_INDEX_FINGER_BONE2, names.LEFT_INDEX_FINGER_BONE1, True)
    connectAndParentBones(metarig, names.RIGHT_INDEX_FINGER_BONE2, names.RIGHT_INDEX_FINGER_BONE1, True)
    connectAndParentBones(metarig, names.LEFT_MIDDLE_FINGER_BONE3, names.LEFT_MIDDLE_FINGER_BONE2, True) 
    connectAndParentBones(metarig, names.RIGHT_MIDDLE_FINGER_BONE3, names.RIGHT_MIDDLE_FINGER_BONE2, True) 
    connectAndParentBones(metarig, names.LEFT_MIDDLE_FINGER_BONE2, names.LEFT_MIDDLE_FINGER_BONE1, True)   
    connectAndParentBones(metarig, names.RIGHT_MIDDLE_FINGER_BONE2, names.RIGHT_MIDDLE_FINGER_BONE1, True)   
    connectAndParentBones(metarig, names.LEFT_RING_FINGER_BONE3, names.LEFT_RING_FINGER_BONE2, True) 
    connectAndParentBones(metarig, names.RIGHT_RING_FINGER_BONE3, names.RIGHT_RING_FINGER_BONE2, True) 
    connectAndParentBones(metarig, names.LEFT_RING_FINGER_BONE2, names.LEFT_RING_FINGER_BONE1, True)   
    connectAndParentBones(metarig, names.RIGHT_RING_FINGER_BONE2, names.RIGHT_RING_FINGER_BONE1, True)   
    connectAndParentBones(metarig, names.LEFT_LITTLE_FINGER_BONE3, names.LEFT_LITTLE_FINGER_BONE2, True) 
    connectAndParentBones(metarig, names.RIGHT_LITTLE_FINGER_BONE3, names.RIGHT_LITTLE_FINGER_BONE2, True)  
    connectAndParentBones(metarig, names.LEFT_LITTLE_FINGER_BONE2, names.LEFT_LITTLE_FINGER_BONE1, True)       
    connectAndParentBones(metarig, names.RIGHT_LITTLE_FINGER_BONE2, names.RIGHT_LITTLE_FINGER_BONE1, True)      
    connectAndParentBones(metarig, names.LEFT_TOE_BONE, names.LEFT_ANKLE_BONE, True)
    connectAndParentBones(metarig, names.RIGHT_TOE_BONE, names.RIGHT_ANKLE_BONE, True)
    connectAndParentBones(metarig, names.LEFT_ANKLE_BONE, names.LEFT_KNEE_BONE, True)
    connectAndParentBones(metarig, names.RIGHT_ANKLE_BONE, names.RIGHT_KNEE_BONE, True)
    connectAndParentBones(metarig, names.LEFT_KNEE_BONE, names.LEFT_LEG_BONE, True)
    connectAndParentBones(metarig, names.RIGHT_KNEE_BONE, names.RIGHT_LEG_BONE, True)
    return (accessoryBoneNames, accessoryMchBoneNames, faceMchBoneNames, accessoryBoneConnectedChildNames, accessoryBoneConnectedParentNames, accessoryMchConnectedParentNames)


def _tongue_side_bones(build):
    """The rigged tongue's side bones, placed from their vertex groups."""
    metarig = build.metarig
    hasRiggedTongue = build.features.rigged_tongue
    
    tongueSideBones = (names.RIGGED_TONGUE_BONE2, names.RIGGED_TONGUE_BONE5,
                       names.RIGGED_TONGUE_LEFT_BONE3, names.RIGGED_TONGUE_RIGHT_BONE3,
                       names.RIGGED_TONGUE_LEFT_BONE4, names.RIGGED_TONGUE_RIGHT_BONE4,
                       names.RIGGED_TONGUE_LEFT_BONE5, names.RIGGED_TONGUE_RIGHT_BONE5)
    # The side bones are placed from the left ones' vertex groups on Body.
    tongueSideGroups = (names.RIGGED_TONGUE_LEFT_BONE3, names.RIGGED_TONGUE_LEFT_BONE4, names.RIGGED_TONGUE_LEFT_BONE5)
    if hasRiggedTongue and not (all(b in metarig.data.edit_bones for b in tongueSideBones) and
                                not any(koikatsuCommons.isVertexGroupEmpty(g, build.body) for g in tongueSideGroups)):
        build.log.info("The tongue lacks some side bones or their vertex groups, so its side bones keep their places")
    elif hasRiggedTongue:
        riggedTongueBone2 = metarig.data.edit_bones[names.RIGGED_TONGUE_BONE2]
        finalizeRiggedTongueSideBones(build, metarig, names.RIGGED_TONGUE_LEFT_BONE3, names.RIGGED_TONGUE_RIGHT_BONE3, riggedTongueBone2.length, 0.75)
        finalizeRiggedTongueSideBones(build, metarig, names.RIGGED_TONGUE_LEFT_BONE4, names.RIGGED_TONGUE_RIGHT_BONE4, riggedTongueBone2.length, 0.65, 0.5, 0.5)
        finalizeRiggedTongueSideBones(build, metarig, names.RIGGED_TONGUE_LEFT_BONE5, names.RIGGED_TONGUE_RIGHT_BONE5, riggedTongueBone2.length, 0.65, 0.2, 0.3)
        riggedTongueBone5 = metarig.data.edit_bones[names.RIGGED_TONGUE_BONE5]
        riggedTongueLeftBone5VertexGroupExtremities = koikatsuCommons.findVertexGroupExtremities(names.RIGGED_TONGUE_LEFT_BONE5, build.body)
        riggedTongueBone5.tail.z = riggedTongueLeftBone5VertexGroupExtremities.minZ + math.dist([riggedTongueLeftBone5VertexGroupExtremities.minZ], [riggedTongueLeftBone5VertexGroupExtremities.maxZ]) * 0.17
        riggedTongueBone5.tail.y = riggedTongueLeftBone5VertexGroupExtremities.minY


def _head_and_hips(build):
    """The head's height from its vertex groups, and the hips' head at the waist."""
    metarig = build.metarig
    hasHeadMod = build.features.head_mod
    if not hasHeadMod:
        metarig.data.edit_bones[names.HEAD_BONE].tail.z = koikatsuCommons.findVertexGroupExtremities(names.ORIGINAL_FACE_UP_DEFORM_BONE, build.body).maxZ
    else:
        metarig.data.edit_bones[names.HEAD_BONE].tail.z = koikatsuCommons.findVertexGroupExtremities(names.ORIGINAL_FACE_BASE_DEFORM_BONE, build.body).maxZ
    metarig.data.edit_bones[names.HIPS_BONE].head = metarig.data.edit_bones[names.WAIST_BONE].head


def _limbs(build):
    """The KK-only elbow, knee and wrist edits, palms and fingers, and the toes and ankles."""
    metarig = build.metarig
    if build.kk_extras:
        leftShoulderJointCorrectionBone = metarig.data.edit_bones[names.LEFT_SHOULDER_JOINT_CORRECTION_BONE]
        rightShoulderJointCorrectionBone = metarig.data.edit_bones[names.RIGHT_SHOULDER_JOINT_CORRECTION_BONE]
        midLeftElbowJointCorrectionBone = metarig.data.edit_bones[names.MID_LEFT_ELBOW_JOINT_CORRECTION_BONE]
        midRightElbowJointCorrectionBone = metarig.data.edit_bones[names.MID_RIGHT_ELBOW_JOINT_CORRECTION_BONE]
        backLeftElbowJointCorrectionBone = metarig.data.edit_bones[names.BACK_LEFT_ELBOW_JOINT_CORRECTION_BONE]
        backRightElbowJointCorrectionBone = metarig.data.edit_bones[names.BACK_RIGHT_ELBOW_JOINT_CORRECTION_BONE]
        frontLeftElbowJointCorrectionBone = metarig.data.edit_bones[names.FRONT_LEFT_ELBOW_JOINT_CORRECTION_BONE]
        frontRightElbowJointCorrectionBone = metarig.data.edit_bones[names.FRONT_RIGHT_ELBOW_JOINT_CORRECTION_BONE]
    leftShoulderDeformBone = metarig.data.edit_bones[names.LEFT_SHOULDER_DEFORM_BONE]
    rightShoulderDeformBone = metarig.data.edit_bones[names.RIGHT_SHOULDER_DEFORM_BONE]
    leftArmBone = metarig.data.edit_bones[names.LEFT_ARM_BONE]
    rightArmBone = metarig.data.edit_bones[names.RIGHT_ARM_BONE]
    leftElbowBone = metarig.data.edit_bones[names.LEFT_ELBOW_BONE]
    rightElbowBone = metarig.data.edit_bones[names.RIGHT_ELBOW_BONE]
    if build.kk_extras:
        leftElbowBone.head.y = midLeftElbowJointCorrectionBone.head.y + math.dist([midLeftElbowJointCorrectionBone.head.y], [frontLeftElbowJointCorrectionBone.head.y]) * 0.33
        rightElbowBone.head.y = midRightElbowJointCorrectionBone.head.y + math.dist([midRightElbowJointCorrectionBone.head.y], [frontRightElbowJointCorrectionBone.head.y]) * 0.33
        leftElbowBone.roll = radians(0)
        rightElbowBone.roll = radians(0)
        frontLeftElbowJointCorrectionBone.roll = radians(180)
        backLeftElbowJointCorrectionBone.roll = radians(180)
        leftShoulderJointCorrectionBone.tail = leftArmBone.tail
        rightShoulderJointCorrectionBone.tail = rightArmBone.tail
        leftShoulderJointCorrectionBone.roll = radians(90)
        rightShoulderJointCorrectionBone.roll = radians(-90)
        leftShoulderDeformBone.tail = leftArmBone.tail
        rightShoulderDeformBone.tail = rightArmBone.tail
        leftShoulderDeformBone.roll = radians(90)
        rightShoulderDeformBone.roll = radians(-90)
        leftWristBone = metarig.data.edit_bones[names.LEFT_WRIST_BONE]
        rightWristBone = metarig.data.edit_bones[names.RIGHT_WRIST_BONE]
        leftWristBone.head.y = midLeftElbowJointCorrectionBone.head.y - math.dist([midLeftElbowJointCorrectionBone.head.y], [backLeftElbowJointCorrectionBone.head.y]) * 0.15
        rightWristBone.head.y = midRightElbowJointCorrectionBone.head.y - math.dist([midRightElbowJointCorrectionBone.head.y], [backRightElbowJointCorrectionBone.head.y]) * 0.15
        if leftWristBone.tail.z != leftWristBone.head.z:
            leftWristBone.tail.y = leftWristBone.head.y
            leftWristBone.tail.z = leftWristBone.head.z
            leftWristGroupExtremities = koikatsuCommons.findVertexGroupExtremities(names.LEFT_WRIST_DEFORM_BONE, build.body)
            leftWristBone.tail.x = leftWristGroupExtremities.minX + math.dist([leftWristGroupExtremities.minX], [leftWristGroupExtremities.maxX]) * 0.66
        if rightWristBone.tail.z != rightWristBone.head.z:
            rightWristBone.tail.y = rightWristBone.head.y
            rightWristBone.tail.z = rightWristBone.head.z
            rightWristGroupExtremities = koikatsuCommons.findVertexGroupExtremities(names.RIGHT_WRIST_DEFORM_BONE, build.body)
            rightWristBone.tail.x = rightWristGroupExtremities.maxX - math.dist([rightWristGroupExtremities.minX], [rightWristGroupExtremities.maxX]) * 0.66
    leftToeBone = metarig.data.edit_bones[names.LEFT_TOE_BONE]
    rightToeBone = metarig.data.edit_bones[names.RIGHT_TOE_BONE]
    leftToeBone.tail.z = leftToeBone.head.z
    rightToeBone.tail.z = rightToeBone.head.z
    leftToeBone.tail.y = koikatsuCommons.findVertexGroupExtremities(names.LEFT_TOE_DEFORM_BONE, build.body).minY
    rightToeBone.tail.y = koikatsuCommons.findVertexGroupExtremities(names.RIGHT_TOE_DEFORM_BONE, build.body).minY
    leftAnkleGroupExtremities = koikatsuCommons.findVertexGroupExtremities(names.LEFT_ANKLE_DEFORM_BONE, build.body)
    rightAnkleGroupExtremities = koikatsuCommons.findVertexGroupExtremities(names.RIGHT_ANKLE_DEFORM_BONE, build.body)
    if build.kk_extras:
        midLeftKneeJointCorrectionBone = metarig.data.edit_bones[names.MID_LEFT_KNEE_JOINT_CORRECTION_BONE]
        midRightKneeJointCorrectionBone = metarig.data.edit_bones[names.MID_RIGHT_KNEE_JOINT_CORRECTION_BONE]
        backLeftKneeJointCorrectionBone = metarig.data.edit_bones[names.BACK_LEFT_KNEE_JOINT_CORRECTION_BONE]
        backRightKneeJointCorrectionBone = metarig.data.edit_bones[names.BACK_RIGHT_KNEE_JOINT_CORRECTION_BONE]
        metarig.data.edit_bones[names.LEFT_LEG_BONE].head.y = midLeftKneeJointCorrectionBone.head.y + math.dist([midLeftKneeJointCorrectionBone.head.y], [backLeftKneeJointCorrectionBone.head.y]) * 0.33
        metarig.data.edit_bones[names.RIGHT_LEG_BONE].head.y = midRightKneeJointCorrectionBone.head.y + math.dist([midRightKneeJointCorrectionBone.head.y], [backRightKneeJointCorrectionBone.head.y]) * 0.33
    leftHeelBone = koikatsuCommons.copyBone(metarig, names.ORIGINAL_LEFT_HEEL_BONE, names.LEFT_HEEL_BONE)
    rightHeelBone = koikatsuCommons.copyBone(metarig, names.ORIGINAL_RIGHT_HEEL_BONE, names.RIGHT_HEEL_BONE)
    leftHeelBone.head.x = leftAnkleGroupExtremities.minX
    rightHeelBone.head.x = rightAnkleGroupExtremities.maxX
    leftHeelBone.head.y = leftAnkleGroupExtremities.maxY
    rightHeelBone.head.y = rightAnkleGroupExtremities.maxY
    leftHeelBone.head.z = leftAnkleGroupExtremities.minZ
    rightHeelBone.head.z = rightAnkleGroupExtremities.minZ
    leftHeelBone.tail.x = leftAnkleGroupExtremities.maxX
    rightHeelBone.tail.x = rightAnkleGroupExtremities.minX
    leftHeelBone.tail.y = leftAnkleGroupExtremities.maxY
    rightHeelBone.tail.y = rightAnkleGroupExtremities.maxY
    leftHeelBone.tail.z = leftAnkleGroupExtremities.minZ
    rightHeelBone.tail.z = rightAnkleGroupExtremities.minZ
    leftHeelBone.parent = metarig.data.edit_bones[names.LEFT_ANKLE_BONE]
    rightHeelBone.parent = metarig.data.edit_bones[names.RIGHT_ANKLE_BONE]
    leftAnkleBone = metarig.data.edit_bones[names.LEFT_ANKLE_BONE]
    rightAnkleBone = metarig.data.edit_bones[names.RIGHT_ANKLE_BONE]
    originalLeftLegDeformBone3 = metarig.data.edit_bones[names.ORIGINAL_LEFT_LEG_DEFORM_BONE3]
    originalRightLegDeformBone3 = metarig.data.edit_bones[names.ORIGINAL_RIGHT_LEG_DEFORM_BONE3]
    leftAnkleBone.head.z = leftAnkleBone.tail.z + math.dist([leftAnkleBone.tail.z], [originalLeftLegDeformBone3.head.z]) * 0.7
    rightAnkleBone.head.z = rightAnkleBone.tail.z + math.dist([rightAnkleBone.tail.z], [originalRightLegDeformBone3.head.z]) * 0.7
    leftAnkleBone.head.y = originalLeftLegDeformBone3.head.y + math.dist([originalLeftLegDeformBone3.head.y], [leftHeelBone.head.y]) * 0.2
    rightAnkleBone.head.y = originalRightLegDeformBone3.head.y + math.dist([originalRightLegDeformBone3.head.y], [rightHeelBone.head.y]) * 0.2
    
    
    leftIndexFingerBone1 = metarig.data.edit_bones[names.LEFT_INDEX_FINGER_BONE1]
    rightIndexFingerBone1 = metarig.data.edit_bones[names.RIGHT_INDEX_FINGER_BONE1]
    leftMiddleFingerBone1 = metarig.data.edit_bones[names.LEFT_MIDDLE_FINGER_BONE1]
    rightMiddleFingerBone1 = metarig.data.edit_bones[names.RIGHT_MIDDLE_FINGER_BONE1]
    leftRingFingerBone1 = metarig.data.edit_bones[names.LEFT_RING_FINGER_BONE1]
    rightRingFingerBone1 = metarig.data.edit_bones[names.RIGHT_RING_FINGER_BONE1]
    leftLittleFingerBone1 = metarig.data.edit_bones[names.LEFT_LITTLE_FINGER_BONE1]
    rightLittleFingerBone1 = metarig.data.edit_bones[names.RIGHT_LITTLE_FINGER_BONE1]
    if build.kk_extras:
        leftPalmMinX = leftWristBone.tail.x - math.dist([leftWristBone.head.x], [leftWristBone.tail.x]) * 0.85
        rightPalmMaxX = rightWristBone.tail.x + math.dist([rightWristBone.head.x], [rightWristBone.tail.x]) * 0.85
        createPalmVertexGroups(build, names.LEFT_WRIST_DEFORM_BONE, names.LEFT_INDEX_FINGER_PALM_DEFORM_BONE, False, leftPalmMinX, None, leftIndexFingerBone1.head.y, None, leftMiddleFingerBone1.head.y)
        createPalmVertexGroups(build, names.RIGHT_WRIST_DEFORM_BONE, names.RIGHT_INDEX_FINGER_PALM_DEFORM_BONE, True, None, rightPalmMaxX, rightIndexFingerBone1.head.y, None, rightMiddleFingerBone1.head.y)
        createPalmVertexGroups(build, names.LEFT_WRIST_DEFORM_BONE, names.LEFT_MIDDLE_FINGER_PALM_DEFORM_BONE, False, leftPalmMinX, None, leftMiddleFingerBone1.head.y, None, leftRingFingerBone1.head.y)
        createPalmVertexGroups(build, names.RIGHT_WRIST_DEFORM_BONE, names.RIGHT_MIDDLE_FINGER_PALM_DEFORM_BONE, True, None, rightPalmMaxX, rightMiddleFingerBone1.head.y, None, rightRingFingerBone1.head.y)
        createPalmVertexGroups(build, names.LEFT_WRIST_DEFORM_BONE, names.LEFT_RING_FINGER_PALM_DEFORM_BONE, False, leftPalmMinX, None, leftRingFingerBone1.head.y, None, leftLittleFingerBone1.head.y)
        createPalmVertexGroups(build, names.RIGHT_WRIST_DEFORM_BONE, names.RIGHT_RING_FINGER_PALM_DEFORM_BONE, True, None, rightPalmMaxX, rightRingFingerBone1.head.y, None, rightLittleFingerBone1.head.y)
        createPalmVertexGroups(build, names.LEFT_WRIST_DEFORM_BONE, names.LEFT_LITTLE_FINGER_PALM_DEFORM_BONE, False, leftPalmMinX, None, leftLittleFingerBone1.head.y, None, None)
        createPalmVertexGroups(build, names.RIGHT_WRIST_DEFORM_BONE, names.RIGHT_LITTLE_FINGER_PALM_DEFORM_BONE, True, None, rightPalmMaxX, rightLittleFingerBone1.head.y, None, None)
    
    
    if build.kk_extras:
        finalizeFingerBones(True, metarig, names.LEFT_WRIST_BONE, names.LEFT_INDEX_FINGER_PALM_BONE, names.LEFT_INDEX_FINGER_BONE1, names.LEFT_INDEX_FINGER_BONE2, names.LEFT_INDEX_FINGER_BONE3, names.LEFT_INDEX_FINGER_DEFORM_BONE1, names.LEFT_INDEX_FINGER_DEFORM_BONE2, names.LEFT_INDEX_FINGER_DEFORM_BONE3, build.body, radians(0), radians(0), radians(5), radians(10))
        finalizeFingerBones(False, metarig, names.RIGHT_WRIST_BONE, names.RIGHT_INDEX_FINGER_PALM_BONE, names.RIGHT_INDEX_FINGER_BONE1, names.RIGHT_INDEX_FINGER_BONE2, names.RIGHT_INDEX_FINGER_BONE3, names.RIGHT_INDEX_FINGER_DEFORM_BONE1, names.RIGHT_INDEX_FINGER_DEFORM_BONE2, names.RIGHT_INDEX_FINGER_DEFORM_BONE3, build.body, radians(0), radians(0), radians(-5), radians(-10))
        finalizeFingerBones(True, metarig, names.LEFT_WRIST_BONE, names.LEFT_MIDDLE_FINGER_PALM_BONE, names.LEFT_MIDDLE_FINGER_BONE1, names.LEFT_MIDDLE_FINGER_BONE2, names.LEFT_MIDDLE_FINGER_BONE3, names.LEFT_MIDDLE_FINGER_DEFORM_BONE1, names.LEFT_MIDDLE_FINGER_DEFORM_BONE2, names.LEFT_MIDDLE_FINGER_DEFORM_BONE3, build.body, radians(0), radians(-10), radians(-2), radians(6), True)
        finalizeFingerBones(False, metarig, names.RIGHT_WRIST_BONE, names.RIGHT_MIDDLE_FINGER_PALM_BONE, names.RIGHT_MIDDLE_FINGER_BONE1, names.RIGHT_MIDDLE_FINGER_BONE2, names.RIGHT_MIDDLE_FINGER_BONE3, names.RIGHT_MIDDLE_FINGER_DEFORM_BONE1, names.RIGHT_MIDDLE_FINGER_DEFORM_BONE2, names.RIGHT_MIDDLE_FINGER_DEFORM_BONE3, build.body, radians(0), radians(10), radians(2), radians(-6), True)
        finalizeFingerBones(True, metarig, names.LEFT_WRIST_BONE, names.LEFT_RING_FINGER_PALM_BONE, names.LEFT_RING_FINGER_BONE1, names.LEFT_RING_FINGER_BONE2, names.LEFT_RING_FINGER_BONE3, names.LEFT_RING_FINGER_DEFORM_BONE1, names.LEFT_RING_FINGER_DEFORM_BONE2, names.LEFT_RING_FINGER_DEFORM_BONE3, build.body, radians(0), radians(-15), radians(-10), radians(-5))
        finalizeFingerBones(False, metarig, names.RIGHT_WRIST_BONE, names.RIGHT_RING_FINGER_PALM_BONE, names.RIGHT_RING_FINGER_BONE1, names.RIGHT_RING_FINGER_BONE2, names.RIGHT_RING_FINGER_BONE3, names.RIGHT_RING_FINGER_DEFORM_BONE1, names.RIGHT_RING_FINGER_DEFORM_BONE2, names.RIGHT_RING_FINGER_DEFORM_BONE3, build.body, radians(0), radians(15), radians(10), radians(5))
        finalizeFingerBones(True, metarig, names.LEFT_WRIST_BONE, names.LEFT_LITTLE_FINGER_PALM_BONE, names.LEFT_LITTLE_FINGER_BONE1, names.LEFT_LITTLE_FINGER_BONE2, names.LEFT_LITTLE_FINGER_BONE3, names.LEFT_LITTLE_FINGER_DEFORM_BONE1, names.LEFT_LITTLE_FINGER_DEFORM_BONE2, names.LEFT_LITTLE_FINGER_DEFORM_BONE3, build.body, radians(0), radians(-20), radians(-18), radians(-16))
        finalizeFingerBones(False, metarig, names.RIGHT_WRIST_BONE, names.RIGHT_LITTLE_FINGER_PALM_BONE, names.RIGHT_LITTLE_FINGER_BONE1, names.RIGHT_LITTLE_FINGER_BONE2, names.RIGHT_LITTLE_FINGER_BONE3, names.RIGHT_LITTLE_FINGER_DEFORM_BONE1, names.RIGHT_LITTLE_FINGER_DEFORM_BONE2, names.RIGHT_LITTLE_FINGER_DEFORM_BONE3, build.body, radians(0), radians(20), radians(18), radians(16))
        finalizeFingerBones(True, metarig, names.LEFT_WRIST_BONE, names.LEFT_INDEX_FINGER_PALM_BONE, names.LEFT_THUMB_BONE1, names.LEFT_THUMB_BONE2, names.LEFT_THUMB_BONE3, names.LEFT_THUMB_DEFORM_BONE1, names.LEFT_THUMB_DEFORM_BONE2, names.LEFT_THUMB_DEFORM_BONE3, build.body, None, radians(-257), radians(-260), radians(-263), False, True)
        finalizeFingerBones(False, metarig, names.RIGHT_WRIST_BONE, names.RIGHT_INDEX_FINGER_PALM_BONE, names.RIGHT_THUMB_BONE1, names.RIGHT_THUMB_BONE2, names.RIGHT_THUMB_BONE3, names.RIGHT_THUMB_DEFORM_BONE1, names.RIGHT_THUMB_DEFORM_BONE2, names.RIGHT_THUMB_DEFORM_BONE3, build.body, None, radians(-103), radians(-106), radians(-109), False, True)


def _skirt(build):
    """The skirt's parent copy and palm bones."""
    metarig = build.metarig
    hasSkirt = build.features.skirt
    skirtPalmBoneRatioReferences = [Vector((-0.0000, -0.0083, 0.0287)), Vector((-0.0057, -0.0080, 0.0294)), Vector((-0.0136, -0.0002, 0.0317)), Vector((-0.0094, 0.0151, 0.0360)), Vector((-0.0010, 0.0153, 0.0333)), Vector((0.0094, 0.0151, 0.0360)), Vector((0.0136, -0.0002, 0.0317)), Vector((0.0057, -0.0080, 0.0294))]
    if hasSkirt and not metarig.data.edit_bones.get(names.SKIRT_PARENT_BONE_COPY):
        koikatsuCommons.copyBone(metarig, names.SKIRT_PARENT_BONE, names.SKIRT_PARENT_BONE_COPY)
        for primaryIndex in range(8):
            skirtPalmBone = metarig.data.edit_bones[names.skirt_bone(True, primaryIndex)]
            skirtBone0 = metarig.data.edit_bones[names.skirt_bone(False, primaryIndex, 0)]
            skirtBone4 = metarig.data.edit_bones[names.skirt_bone(False, primaryIndex, 4)]
            skirtBone5 = metarig.data.edit_bones[names.skirt_bone(False, primaryIndex, 5)]
            skirtPalmBone.tail = skirtPalmBone.head - skirtPalmBoneRatioReferences[primaryIndex]
            skirtPalmBone.length = skirtBone0.length / 2
            headPos = skirtPalmBone.head.copy()
            skirtPalmBone.head = skirtPalmBone.tail
            skirtPalmBone.tail = headPos            
            skirtBone5.tail = skirtBone5.head - (skirtBone4.head - skirtBone4.tail)            
            skirtPalmBoneLength = skirtPalmBone.length
            shrinkFactorX = skirtPalmBone.head.x * 0.1
            shrinkFactorY = skirtPalmBone.head.y * 0.1
            skirtPalmBone.head = skirtPalmBone.head - Vector((shrinkFactorX, shrinkFactorY, 0))
            skirtPalmBone.tail = skirtPalmBone.tail - Vector((shrinkFactorX, shrinkFactorY, 0))
            skirtBoneLengths = []
            skirtBoneOrientations = []
            for secondaryIndex in range(6):
                skirtBone = metarig.data.edit_bones[names.skirt_bone(False, primaryIndex, secondaryIndex)]
                skirtBoneLengths.append(skirtBone.length)
                skirtBoneOrientations.append(skirtBone.tail - skirtBone.head)
                shrinkFactorX = skirtBone.head.x * 0.1
                shrinkFactorY = skirtBone.head.y * 0.1
                skirtBone.head = skirtBone.head - Vector((shrinkFactorX, shrinkFactorY, 0))
                skirtBone.tail = skirtBone.tail - Vector((shrinkFactorX, shrinkFactorY, 0))
            skirtPalmBone.length = skirtPalmBoneLength
            previousBoneOrientation = skirtPalmBone.tail - skirtPalmBone.head
            for secondaryIndex in range(6):
                skirtBone = metarig.data.edit_bones[names.skirt_bone(False, primaryIndex, secondaryIndex)]
                if secondaryIndex == 0:
                    skirtBone.tail = skirtBone.head + previousBoneOrientation * Vector((0.4, 0.4, 0.4)) + skirtBoneOrientations[secondaryIndex] * Vector((0.6, 0.6, 0.6))
                else:
                    skirtBone.tail = skirtBone.head + previousBoneOrientation * Vector((0.5, 0.5, 0.5)) + skirtBoneOrientations[secondaryIndex] * Vector((0, 0, 0.5))
                skirtBone.length = skirtBoneLengths[secondaryIndex]
                previousBoneOrientation = skirtBone.tail - skirtBone.head
    
    switch(metarig, 'OBJECT')
    
    # The legacy importer turned its joint-correction constraints and swapped its shoulder drivers'
    # axes here, for its drivers on upright bones. Those drivers are gone (ADR 0038): the joint
    # corrections are taken off before these scripts and put back on the generated rig.


def _rigify_types(build):
    """Each bone's Rigify type and parameters."""
    metarig = build.metarig
    hasRiggedTongue = build.features.rigged_tongue
    hasBetterPenetrationMod = build.features.better_penetration
    '''Apply rigify bone type to all bones'''

    for bone in metarig.pose.bones[:]:
        bone.rigify_type = "basic.raw_copy"
                       
    
    metarig.pose.bones[names.EYES_TRACK_TARGET_BONE].rigify_parameters.optional_widget_type = "pivot_cross"
    metarig.pose.bones[names.EYEBALLS_BONE].rigify_parameters.optional_widget_type = "bone"
    metarig.pose.bones[names.LEFT_EYEBALL_BONE].rigify_parameters.optional_widget_type = "bone"
    metarig.pose.bones[names.RIGHT_EYEBALL_BONE].rigify_parameters.optional_widget_type = "bone"   
    if hasRiggedTongue:
        metarig.pose.bones[names.RIGGED_TONGUE_BONE1].rigify_parameters.optional_widget_type = "jaw" 
        metarig.pose.bones[names.RIGGED_TONGUE_BONE2].rigify_type = "limbs.super_finger"
        metarig.pose.bones[names.RIGGED_TONGUE_BONE2].rigify_parameters.primary_rotation_axis = "-X"
        metarig.pose.bones[names.RIGGED_TONGUE_BONE2].rigify_parameters.make_extra_ik_control = True
        metarig.pose.bones[names.RIGGED_TONGUE_BONE3].rigify_type = ""
        metarig.pose.bones[names.RIGGED_TONGUE_LEFT_BONE3].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.RIGGED_TONGUE_RIGHT_BONE3].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.RIGGED_TONGUE_BONE4].rigify_type = ""
        metarig.pose.bones[names.RIGGED_TONGUE_LEFT_BONE4].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.RIGGED_TONGUE_RIGHT_BONE4].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.RIGGED_TONGUE_BONE5].rigify_type = ""
        metarig.pose.bones[names.RIGGED_TONGUE_LEFT_BONE5].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.RIGGED_TONGUE_RIGHT_BONE5].rigify_parameters.optional_widget_type = "sphere"

    metarig.pose.bones[names.HEAD_BONE].rigify_type = ""
    metarig.pose.bones[names.HEAD_TRACK_BONE].rigify_parameters.relink_constraints = True
    metarig.pose.bones[names.HEAD_TRACK_BONE].rigify_parameters.parent_bone = names.HEAD_TWEAK_BONE
    metarig.pose.bones[names.HEAD_TRACK_TARGET_BONE].rigify_parameters.optional_widget_type = "pivot_cross"  
    metarig.pose.bones[names.NECK_BONE].rigify_type = "spines.super_head"
    metarig.pose.bones[names.NECK_BONE].rigify_parameters.connect_chain = True
    metarig.pose.bones[names.UPPER_CHEST_BONE].rigify_type = ""
    metarig.pose.bones[names.CHEST_BONE].rigify_type = ""
    metarig.pose.bones[names.SPINE_BONE].rigify_type = ""
    metarig.pose.bones[names.HIPS_BONE].rigify_type = "spines.basic_spine"
    metarig.pose.bones[names.HIPS_BONE].rigify_parameters.pivot_pos = 1
    metarig.pose.bones[names.WAIST_BONE].rigify_parameters.optional_widget_type = "diamond"
    metarig.pose.bones[names.CROTCH_BONE].rigify_parameters.optional_widget_type = "sphere"
    metarig.pose.bones[names.ANUS_BONE].rigify_parameters.optional_widget_type = "sphere"
    if hasBetterPenetrationMod:
        metarig.pose.bones[names.BETTER_PENETRATION_ROOT_CROTCH_BONE].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_FRONT_CROTCH_BONE].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_LEFT_CROTCH_BONE1].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_RIGHT_CROTCH_BONE1].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_LEFT_CROTCH_BONE2].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_RIGHT_CROTCH_BONE2].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_LEFT_CROTCH_BONE3].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_RIGHT_CROTCH_BONE3].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_LEFT_CROTCH_BONE4].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_RIGHT_CROTCH_BONE4].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_LEFT_CROTCH_BONE5].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_RIGHT_CROTCH_BONE5].rigify_parameters.optional_widget_type = "circle"
        metarig.pose.bones[names.BETTER_PENETRATION_BACK_CROTCH_BONE].rigify_parameters.optional_widget_type = "circle"   
    metarig.pose.bones[names.LEFT_BREAST_DEFORM_BONE1].rigify_parameters.optional_widget_type = "sphere"
    metarig.pose.bones[names.RIGHT_BREAST_DEFORM_BONE1].rigify_parameters.optional_widget_type = "sphere"
    widgetFace = build.widget(names.WIDGET_FACE)
    metarig.pose.bones[names.LEFT_BREAST_BONE2].custom_shape = widgetFace
    metarig.pose.bones[names.RIGHT_BREAST_BONE2].custom_shape = widgetFace
    koikatsuCommons.assignSingleBoneLayer(metarig, names.LEFT_BREAST_BONE2, names.ORIGINAL_FK_LAYER_INDEX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.RIGHT_BREAST_BONE2, names.ORIGINAL_FK_LAYER_INDEX)
    metarig.pose.bones[names.LEFT_BREAST_DEFORM_BONE2].rigify_parameters.optional_widget_type = "sphere"
    metarig.pose.bones[names.RIGHT_BREAST_DEFORM_BONE2].rigify_parameters.optional_widget_type = "sphere"
    metarig.pose.bones[names.LEFT_BREAST_BONE3].custom_shape = widgetFace
    metarig.pose.bones[names.RIGHT_BREAST_BONE3].custom_shape = widgetFace
    metarig.pose.bones[names.LEFT_BREAST_DEFORM_BONE3].rigify_parameters.optional_widget_type = "sphere"
    metarig.pose.bones[names.RIGHT_BREAST_DEFORM_BONE3].rigify_parameters.optional_widget_type = "sphere"
    if build.kk_extras:
        metarig.pose.bones[names.LEFT_NIPPLE_BONE1].custom_shape = widgetFace
        metarig.pose.bones[names.RIGHT_NIPPLE_BONE1].custom_shape = widgetFace
        metarig.pose.bones[names.LEFT_NIPPLE_DEFORM_BONE1].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.RIGHT_NIPPLE_DEFORM_BONE1].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.LEFT_NIPPLE_BONE2].custom_shape = widgetFace
        metarig.pose.bones[names.RIGHT_NIPPLE_BONE2].custom_shape = widgetFace
        metarig.pose.bones[names.LEFT_NIPPLE_DEFORM_BONE2].rigify_parameters.optional_widget_type = "sphere"
        metarig.pose.bones[names.RIGHT_NIPPLE_DEFORM_BONE2].rigify_parameters.optional_widget_type = "sphere"
    metarig.pose.bones[names.LEFT_SHOULDER_BONE].rigify_parameters.optional_widget_type = "shoulder"
    metarig.pose.bones[names.RIGHT_SHOULDER_BONE].rigify_parameters.optional_widget_type = "shoulder"
    metarig.pose.bones[names.LEFT_ARM_BONE].rigify_type = "limbs.arm"
    metarig.pose.bones[names.RIGHT_ARM_BONE].rigify_type = "limbs.arm"
    metarig.pose.bones[names.LEFT_ARM_BONE].rigify_parameters.segments = 3
    metarig.pose.bones[names.RIGHT_ARM_BONE].rigify_parameters.segments = 3
    metarig.pose.bones[names.LEFT_ARM_BONE].rigify_parameters.rotation_axis = "automatic"
    metarig.pose.bones[names.RIGHT_ARM_BONE].rigify_parameters.rotation_axis = "automatic"
    metarig.pose.bones[names.LEFT_ARM_BONE].rigify_parameters.limb_uniform_scale = True
    metarig.pose.bones[names.RIGHT_ARM_BONE].rigify_parameters.limb_uniform_scale = True
    metarig.pose.bones[names.LEFT_ARM_BONE].rigify_parameters.auto_align_extremity = True
    metarig.pose.bones[names.RIGHT_ARM_BONE].rigify_parameters.auto_align_extremity = True
    metarig.pose.bones[names.LEFT_ARM_BONE].rigify_parameters.make_ik_wrist_pivot = True
    metarig.pose.bones[names.RIGHT_ARM_BONE].rigify_parameters.make_ik_wrist_pivot = True
    metarig.pose.bones[names.LEFT_ELBOW_BONE].rigify_type = ""
    metarig.pose.bones[names.RIGHT_ELBOW_BONE].rigify_type = ""
    metarig.pose.bones[names.LEFT_WRIST_BONE].rigify_type = ""
    metarig.pose.bones[names.RIGHT_WRIST_BONE].rigify_type = ""
    if build.kk_extras:
        metarig.pose.bones[names.FRONT_LEFT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.FRONT_RIGHT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.FRONT_LEFT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.LEFT_ELBOW_DEFORM_BONE1
        metarig.pose.bones[names.FRONT_RIGHT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.RIGHT_ELBOW_DEFORM_BONE1
        metarig.pose.bones[names.MID_LEFT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.MID_RIGHT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.MID_LEFT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.LEFT_ELBOW_DEFORM_BONE1
        metarig.pose.bones[names.MID_RIGHT_ELBOW_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.RIGHT_ELBOW_DEFORM_BONE1
        metarig.pose.bones[names.LEFT_INDEX_FINGER_PALM_BONE].rigify_type = "limbs.super_palm"
        metarig.pose.bones[names.RIGHT_INDEX_FINGER_PALM_BONE].rigify_type = "limbs.super_palm"
        metarig.pose.bones[names.LEFT_INDEX_FINGER_PALM_BONE].rigify_parameters.palm_both_sides = True
        metarig.pose.bones[names.RIGHT_INDEX_FINGER_PALM_BONE].rigify_parameters.palm_both_sides = True
        metarig.pose.bones[names.LEFT_INDEX_FINGER_PALM_BONE].rigify_parameters.palm_rotation_axis = 'X'
        metarig.pose.bones[names.RIGHT_INDEX_FINGER_PALM_BONE].rigify_parameters.palm_rotation_axis = 'X'
        metarig.pose.bones[names.LEFT_INDEX_FINGER_PALM_BONE].rigify_parameters.make_extra_control = True
        metarig.pose.bones[names.RIGHT_INDEX_FINGER_PALM_BONE].rigify_parameters.make_extra_control = True
        metarig.pose.bones[names.LEFT_MIDDLE_FINGER_PALM_BONE].rigify_type = ""
        metarig.pose.bones[names.RIGHT_MIDDLE_FINGER_PALM_BONE].rigify_type = ""
        metarig.pose.bones[names.LEFT_RING_FINGER_PALM_BONE].rigify_type = ""
        metarig.pose.bones[names.RIGHT_RING_FINGER_PALM_BONE].rigify_type = ""
        metarig.pose.bones[names.LEFT_LITTLE_FINGER_PALM_BONE].rigify_type = ""
        metarig.pose.bones[names.RIGHT_LITTLE_FINGER_PALM_BONE].rigify_type = ""
    finalizeFingerBoneParameters(build, metarig, names.LEFT_THUMB_BONE1, names.LEFT_THUMB_BONE2, names.LEFT_THUMB_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.RIGHT_THUMB_BONE1, names.RIGHT_THUMB_BONE2, names.RIGHT_THUMB_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.LEFT_INDEX_FINGER_BONE1, names.LEFT_INDEX_FINGER_BONE2, names.LEFT_INDEX_FINGER_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.RIGHT_INDEX_FINGER_BONE1, names.RIGHT_INDEX_FINGER_BONE2, names.RIGHT_INDEX_FINGER_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.LEFT_MIDDLE_FINGER_BONE1, names.LEFT_MIDDLE_FINGER_BONE2, names.LEFT_MIDDLE_FINGER_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.RIGHT_MIDDLE_FINGER_BONE1, names.RIGHT_MIDDLE_FINGER_BONE2, names.RIGHT_MIDDLE_FINGER_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.LEFT_RING_FINGER_BONE1, names.LEFT_RING_FINGER_BONE2, names.LEFT_RING_FINGER_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.RIGHT_RING_FINGER_BONE1, names.RIGHT_RING_FINGER_BONE2, names.RIGHT_RING_FINGER_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.LEFT_LITTLE_FINGER_BONE1, names.LEFT_LITTLE_FINGER_BONE2, names.LEFT_LITTLE_FINGER_BONE3)
    finalizeFingerBoneParameters(build, metarig, names.RIGHT_LITTLE_FINGER_BONE1, names.RIGHT_LITTLE_FINGER_BONE2, names.RIGHT_LITTLE_FINGER_BONE3)
    metarig.pose.bones[names.LEFT_LEG_BONE].rigify_type = "limbs.leg"
    metarig.pose.bones[names.RIGHT_LEG_BONE].rigify_type = "limbs.leg"
    metarig.pose.bones[names.LEFT_LEG_BONE].rigify_parameters.extra_ik_toe = True
    metarig.pose.bones[names.RIGHT_LEG_BONE].rigify_parameters.extra_ik_toe = True
    metarig.pose.bones[names.LEFT_LEG_BONE].rigify_parameters.segments = 3
    metarig.pose.bones[names.RIGHT_LEG_BONE].rigify_parameters.segments = 3
    metarig.pose.bones[names.LEFT_LEG_BONE].rigify_parameters.rotation_axis = "automatic"
    metarig.pose.bones[names.RIGHT_LEG_BONE].rigify_parameters.rotation_axis = "automatic"
    metarig.pose.bones[names.LEFT_LEG_BONE].rigify_parameters.limb_uniform_scale = True
    metarig.pose.bones[names.RIGHT_LEG_BONE].rigify_parameters.limb_uniform_scale = True
    metarig.pose.bones[names.LEFT_KNEE_BONE].rigify_type = ""
    metarig.pose.bones[names.RIGHT_KNEE_BONE].rigify_type = ""
    metarig.pose.bones[names.LEFT_ANKLE_BONE].rigify_type = ""
    metarig.pose.bones[names.RIGHT_ANKLE_BONE].rigify_type = ""
    metarig.pose.bones[names.LEFT_TOE_BONE].rigify_type = ""
    metarig.pose.bones[names.RIGHT_TOE_BONE].rigify_type = ""
    metarig.pose.bones[names.LEFT_HEEL_BONE].rigify_type = ""
    metarig.pose.bones[names.RIGHT_HEEL_BONE].rigify_type = ""
    koikatsuCommons.assignSingleBoneLayer(metarig, names.LEFT_HEEL_BONE, names.ORIGINAL_FK_LAYER_INDEX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.RIGHT_HEEL_BONE, names.ORIGINAL_FK_LAYER_INDEX)
    if build.kk_extras:
        metarig.pose.bones[names.FRONT_LEFT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.FRONT_RIGHT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.FRONT_LEFT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.LEFT_LEG_DEFORM_BONE1
        metarig.pose.bones[names.FRONT_RIGHT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.RIGHT_LEG_DEFORM_BONE1
        metarig.pose.bones[names.MID_LEFT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.MID_RIGHT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.relink_constraints = True
        metarig.pose.bones[names.MID_LEFT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.LEFT_LEG_DEFORM_BONE1
        metarig.pose.bones[names.MID_RIGHT_KNEE_JOINT_CORRECTION_BONE].rigify_parameters.parent_bone = names.RIGHT_LEG_DEFORM_BONE1


def _bone_lists(build, accessories):
    """This Character's control, useful and deform bone lists, and the types and layers they set."""
    metarig = build.metarig
    hasSkirt = build.features.skirt
    hasRiggedTongue = build.features.rigged_tongue
    hasBetterPenetrationMod = build.features.better_penetration
    isMale = build.features.male
    (accessoryBoneNames, accessoryMchBoneNames, faceMchBoneNames, accessoryBoneConnectedChildNames, accessoryBoneConnectedParentNames, accessoryMchConnectedParentNames) = accessories
    metarigIdBoneName = build.metarig_id_bone
    torsoLayerBoneNames = list(names.TORSO_LAYER_BONE_NAMES)  # this Character's copy, as below
    if isMale:
        torsoLayerBoneNames.remove(names.BREASTS_HANDLE_BONE)
        torsoLayerBoneNames.remove(names.LEFT_BREAST_HANDLE_BONE)
        torsoLayerBoneNames.remove(names.RIGHT_BREAST_HANDLE_BONE)
        
    # This Character's copies: the legacy scripts removed these names from the module's own lists,
    # which then stayed short for the next Character imported in the session.
    eyesPrimaryLayerBoneNames = list(names.EYES_PRIMARY_LAYER_BONE_NAMES)
    eyesSecondaryLayerBoneNames = list(names.EYES_SECONDARY_LAYER_BONE_NAMES)
    torsoTweakLayerBoneNames = list(names.TORSO_TWEAK_LAYER_BONE_NAMES)
    if not hasRiggedTongue:
        eyesPrimaryLayerBoneNames.remove(names.RIGGED_TONGUE_BONE1)
        eyesPrimaryLayerBoneNames.remove(names.RIGGED_TONGUE_BONE2)
        eyesPrimaryLayerBoneNames.remove(names.RIGGED_TONGUE_BONE3)
        eyesPrimaryLayerBoneNames.remove(names.RIGGED_TONGUE_BONE4)
        eyesPrimaryLayerBoneNames.remove(names.RIGGED_TONGUE_BONE5)
        eyesSecondaryLayerBoneNames.remove(names.RIGGED_TONGUE_LEFT_BONE3)
        eyesSecondaryLayerBoneNames.remove(names.RIGGED_TONGUE_RIGHT_BONE3)
        eyesSecondaryLayerBoneNames.remove(names.RIGGED_TONGUE_LEFT_BONE4)
        eyesSecondaryLayerBoneNames.remove(names.RIGGED_TONGUE_RIGHT_BONE4)
        eyesSecondaryLayerBoneNames.remove(names.RIGGED_TONGUE_LEFT_BONE5)
        eyesSecondaryLayerBoneNames.remove(names.RIGGED_TONGUE_RIGHT_BONE5)
               
    if not hasBetterPenetrationMod:
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_ROOT_CROTCH_BONE)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_FRONT_CROTCH_BONE)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_LEFT_CROTCH_BONE1)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_RIGHT_CROTCH_BONE1)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_LEFT_CROTCH_BONE2)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_RIGHT_CROTCH_BONE2)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_LEFT_CROTCH_BONE3)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_RIGHT_CROTCH_BONE3)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_LEFT_CROTCH_BONE4)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_RIGHT_CROTCH_BONE4)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_LEFT_CROTCH_BONE5)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_RIGHT_CROTCH_BONE5)
        torsoTweakLayerBoneNames.remove(names.BETTER_PENETRATION_BACK_CROTCH_BONE)
                
    ctrlBoneNames = []
    ctrlBoneNames.extend(eyesPrimaryLayerBoneNames)
    ctrlBoneNames.extend(eyesSecondaryLayerBoneNames)
    ctrlBoneNames.extend(torsoLayerBoneNames)
    ctrlBoneNames.extend(torsoTweakLayerBoneNames)
    ctrlBoneNames.extend(names.LEFT_ARM_IK_LAYER_BONE_NAMES)
    ctrlBoneNames.extend(names.RIGHT_ARM_IK_LAYER_BONE_NAMES)
    ctrlBoneNames.extend(names.FINGERS_LAYER_BONE_NAMES)
    ctrlBoneNames.extend(names.LEFT_LEG_IK_LAYER_BONE_NAMES)
    ctrlBoneNames.extend(names.RIGHT_LEG_IK_LAYER_BONE_NAMES)
    
    for bone in metarig.data.bones:
        if bone.collections.get(names.ORIGINAL_UPPER_FACE_LAYER_INDEX) or bone.collections.get(names.ORIGINAL_LOWER_FACE_LAYER_INDEX):
            if bone.name == names.ORIGINAL_ROOT_UPPER_BONE:
                continue
            if bone.name not in ctrlBoneNames:
                ctrlBoneNames.append(bone.name)
        
    usefulBoneNames = [metarigIdBoneName, names.EYES_X_BONE, names.EYES_BONE, names.LEFT_EYE_BONE, names.RIGHT_EYE_BONE, names.EYES_TRACK_TARGET_PARENT_BONE, 
    names.EYES_HANDLE_MARKER_BONE, names.LEFT_EYE_HANDLE_MARKER_BONE, names.RIGHT_EYE_HANDLE_MARKER_BONE, names.LEFT_EYE_HANDLE_MARKER_X_BONE, names.RIGHT_EYE_HANDLE_MARKER_X_BONE, 
    names.LEFT_EYE_HANDLE_MARKER_Z_BONE, names.RIGHT_EYE_HANDLE_MARKER_Z_BONE, names.EYEBALLS_TRACK_BONE, names.LEFT_EYEBALL_TRACK_BONE, names.RIGHT_EYEBALL_TRACK_BONE, 
    names.LEFT_EYEBALL_TRACK_CORRECTION_BONE, names.RIGHT_EYEBALL_TRACK_CORRECTION_BONE, names.LEFT_HEAD_MARKER_X_BONE, names.RIGHT_HEAD_MARKER_X_BONE, names.LEFT_HEAD_MARKER_Z_BONE, 
    names.RIGHT_HEAD_MARKER_Z_BONE, names.HEAD_TRACK_BONE, names.HEAD_TRACK_TARGET_PARENT_BONE]
    usefulBoneNames.extend(ctrlBoneNames)
    
    defBoneNames = koikatsuCommons.getDeformBoneNames(metarig, build.meshes())
    
    for name in defBoneNames:
        if name not in usefulBoneNames:
            usefulBoneNames.append(name)
    
    '''Setup rigify type and layers'''
    
    if hasSkirt:
        for primaryIndex in range(8):
            skirtPalmBoneName = names.skirt_bone(True, primaryIndex)
            if skirtPalmBoneName not in ctrlBoneNames:
                ctrlBoneNames.append(skirtPalmBoneName)
            if skirtPalmBoneName not in usefulBoneNames:
                usefulBoneNames.append(skirtPalmBoneName)
            koikatsuCommons.assignSingleBoneLayer(metarig, skirtPalmBoneName, names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX)
            if primaryIndex == 2:
                metarig.pose.bones[skirtPalmBoneName].rigify_type = "limbs.super_palm"
                metarig.pose.bones[skirtPalmBoneName].rigify_parameters.palm_both_sides = True
                metarig.pose.bones[skirtPalmBoneName].rigify_parameters.palm_rotation_axis = 'X'
                metarig.pose.bones[skirtPalmBoneName].rigify_parameters.make_extra_control = True
                koikatsuCommons.setTweakLayer(metarig, skirtPalmBoneName, names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX)
            else:
                metarig.pose.bones[skirtPalmBoneName].rigify_type = ""
            for secondaryIndex in range(6):
                skirtBoneName = names.skirt_bone(False, primaryIndex, secondaryIndex)
                if skirtBoneName not in ctrlBoneNames:
                    ctrlBoneNames.append(skirtBoneName)
                if skirtBoneName not in usefulBoneNames:
                    usefulBoneNames.append(skirtBoneName)
                koikatsuCommons.assignSingleBoneLayer(metarig, skirtBoneName, names.SKIRT_LAYER)
                koikatsuCommons.setTweakLayer(metarig, skirtBoneName, names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX)
                if secondaryIndex == 0:
                    metarig.pose.bones[skirtBoneName].rigify_type = "limbs.super_finger"
                    metarig.pose.bones[skirtBoneName].rigify_parameters.make_extra_ik_control = True
                else:
                    metarig.pose.bones[skirtBoneName].rigify_type = ""
    
    for boneName in accessoryBoneNames:
        if boneName not in usefulBoneNames:
            usefulBoneNames.append(boneName)
        if boneName == names.ORIGINAL_ROOT_UPPER_BONE:
            continue
        if boneName not in ctrlBoneNames:
            ctrlBoneNames.append(boneName)
        bone = metarig.pose.bones[boneName]
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, koikatsuCommons.getRigifyLayerIndexByName(names.HAIR_LAYER + names.MCH_LAYER_SUFFIX))
        koikatsuCommons.setTweakLayer(metarig, boneName, names.HAIR_LAYER)

        if boneName in accessoryBoneConnectedParentNames:
            bone.rigify_type = "limbs.super_finger"
            bone.rigify_parameters.make_extra_ik_control = True
            koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.HAIR_LAYER)
            koikatsuCommons.setTweakLayer(metarig, boneName, names.HAIR_LAYER + names.DETAIL_LAYER_SUFFIX)
        elif boneName in accessoryBoneConnectedChildNames:
            bone.rigify_type = ""
        else:
            bone.rigify_type = "basic.super_copy"
            bone.rigify_parameters.make_control = True
            bone.rigify_parameters.make_widget = True
            bone.rigify_parameters.super_copy_widget_type = "limb"  
            bone.rigify_parameters.make_deform = True

    accessoryMchPalmBoneNames = []
    for boneName in accessoryMchBoneNames:
        if boneName not in ctrlBoneNames:
            ctrlBoneNames.append(boneName)
        if boneName not in usefulBoneNames:
            usefulBoneNames.append(boneName)
        bone = metarig.pose.bones[boneName]
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, koikatsuCommons.getRigifyLayerIndexByName(names.HAIR_LAYER + names.MCH_LAYER_SUFFIX))
        if boneName in accessoryMchPalmBoneNames:
            continue
        if boneName in accessoryMchConnectedParentNames:
            accessoryMchPalmBones = []
            for connectedParentBoneName in accessoryMchConnectedParentNames:
                if boneName == connectedParentBoneName:
                    continue
                connectedParentBone = metarig.pose.bones[connectedParentBoneName]
                if bone.parent == connectedParentBone.parent:
                    accessoryMchPalmBoneNames.append(connectedParentBone.name)
                    accessoryMchPalmBones.append(connectedParentBone)
                    connectedParentBone.rigify_type = ""
            if accessoryMchPalmBones:
                accessoryMchPalmBoneNames.append(bone.name)
                accessoryMchPalmBones.append(bone)
                bone.rigify_type = ""
                maxHeadDistance = 0
                for palmBone1 in accessoryMchPalmBones:
                    for palmBone2 in accessoryMchPalmBones:
                        headDistance = (palmBone1.head - palmBone2.head).length
                        if headDistance > maxHeadDistance:
                            bone = palmBone1
                            maxHeadDistance = headDistance                    
                bone.rigify_type = "limbs.super_palm"
                bone.rigify_parameters.palm_both_sides = True
                bone.rigify_parameters.make_extra_control = True
                continue
            bone.rigify_parameters.optional_widget_type  = "limb"
        else:
            bone.rigify_parameters.optional_widget_type = "limb"
            
    for boneName in faceMchBoneNames:
        if boneName not in ctrlBoneNames:
            ctrlBoneNames.append(boneName)
        if boneName not in usefulBoneNames:
            usefulBoneNames.append(boneName)
        bone = metarig.pose.bones[boneName]
        bone.rigify_parameters.optional_widget_type = "pivot"

    for bone in metarig.pose.bones:
        if metarig.data.bones[bone.name].collections.get(names.ORIGINAL_UPPER_FACE_LAYER_INDEX):
            bone.rigify_parameters.optional_widget_type = 'circle'
    
    for bone in metarig.pose.bones:
        if metarig.data.bones[bone.name].collections.get(names.ORIGINAL_LOWER_FACE_LAYER_INDEX):
            bone.rigify_parameters.optional_widget_type = 'sphere'
    
    metarig.pose.bones[names.PELVIS_BONE].rigify_parameters.optional_widget_type = 'sphere'

    for boneName in usefulBoneNames:
        if boneName in defBoneNames:
            koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.DEF_LAYER_INDEX)
            if boneName in ctrlBoneNames:
                koikatsuCommons.lockAllPoseTransforms(metarig, boneName)
        else:
            if boneName not in ctrlBoneNames:
                koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.MCH_LAYER_INDEX)
                koikatsuCommons.lockAllPoseTransforms(metarig, boneName)                
        relatedBoneNames = koikatsuCommons.getRelatedBoneNames(metarig, boneName)
        for relatedBoneName in relatedBoneNames:
            if relatedBoneName not in usefulBoneNames:
                usefulBoneNames.append(relatedBoneName)       
    
    for bone in metarig.pose.bones:
        if bone.name not in usefulBoneNames:
            koikatsuCommons.assignSingleBoneLayer(metarig, bone.name, koikatsuCommons.getRigifyLayerIndexByName(names.JUNK_LAYER))
            continue
        if bone.rigify_type == "basic.raw_copy" or bone.rigify_type == "basic.super_copy":
            for targetToChange in names.TARGETS_TO_CHANGE:
                if bone.parent == targetToChange:
                    bone.rigify_parameters.relink_constraints = True
                    bone.rigify_parameters.parent_bone = names.DEFORM_BONE_PREFIX + targetToChange
            for constraint in bone.constraints:
                for targetToChange in names.TARGETS_TO_CHANGE:
                    # Armature and Limit constraints have no subtarget.
                    if getattr(constraint, "subtarget", None) == targetToChange:
                        bone.rigify_parameters.relink_constraints = True
                        if "@" in constraint.name:
                            index = constraint.name.index("@")
                            constraint.name = constraint.name[:index] + "@" + names.DEFORM_BONE_PREFIX + targetToChange
                        else:
                            constraint.name = constraint.name + "@" + names.DEFORM_BONE_PREFIX + targetToChange
    return (defBoneNames, usefulBoneNames, eyesSecondaryLayerBoneNames, torsoLayerBoneNames, torsoTweakLayerBoneNames)


def _bone_collections(build, lists):
    """Which bone collection each bone goes in, deform flags and locks."""
    metarig = build.metarig
    (defBoneNames, usefulBoneNames, eyesSecondaryLayerBoneNames, torsoLayerBoneNames, torsoTweakLayerBoneNames) = lists
    switch(metarig, 'OBJECT')
    #Move all cf_s bones to the Charamaker layer
    for bone in metarig.data.bones:
        if bone.name.startswith('cf_s_'):
            koikatsuCommons.assignSingleBoneLayer(metarig, bone.name, names.CHARAMAKER_LAYER)

    #Move all cf_d bones to the Deform layer
    for bone in metarig.data.bones:
        if bone.name.startswith('cf_d_'):
            koikatsuCommons.assignSingleBoneLayer(metarig, bone.name, names.DEFORM_LAYER)
    
    #Move torso bones to the torso layer
    for boneName in torsoLayerBoneNames:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.TORSO_LAYER)

    #Move torso tweak bones to the nsfw layer
    for boneName in torsoTweakLayerBoneNames:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.NSFW_LAYER)

    #Set FK bones to the FK layer
    for boneName in names.LEFT_ARM_IK_LAYER_BONE_NAMES:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX)
        koikatsuCommons.setTweakLayer(metarig, boneName, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)
        koikatsuCommons.setFKLayer(metarig, boneName, names.LEFT_ARM_LAYER + names.FK_LAYER_SUFFIX)

    #Set FK bones to the FK layer
    for boneName in names.RIGHT_ARM_IK_LAYER_BONE_NAMES:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX)
        koikatsuCommons.setTweakLayer(metarig, boneName, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)
        koikatsuCommons.setFKLayer(metarig, boneName, names.RIGHT_ARM_LAYER + names.FK_LAYER_SUFFIX)

    #Set FK bones to the FK layer
    for boneName in names.LEFT_LEG_IK_LAYER_BONE_NAMES:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX)
        koikatsuCommons.setTweakLayer(metarig, boneName, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)
        koikatsuCommons.setFKLayer(metarig, boneName, names.LEFT_LEG_LAYER + names.FK_LAYER_SUFFIX)

    #Set FK bones to the FK layer
    for boneName in names.RIGHT_LEG_IK_LAYER_BONE_NAMES:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX)
        koikatsuCommons.setTweakLayer(metarig, boneName, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)
        koikatsuCommons.setFKLayer(metarig, boneName, names.RIGHT_LEG_LAYER + names.FK_LAYER_SUFFIX)

    #set finger bones to the fingers layer
    for boneName in names.FINGERS_LAYER_BONE_NAMES:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.FINGERS_LAYER)
        koikatsuCommons.setTweakLayer(metarig, boneName, names.FINGERS_LAYER + names.DETAIL_LAYER_SUFFIX)
    
    #set eye bones to the eyes layer
    for boneName in eyesSecondaryLayerBoneNames:
        koikatsuCommons.assignSingleBoneLayer(metarig, boneName, names.EYES_LAYER)
    
    #set the eye controller to be part of the Face layer
    koikatsuCommons.assignSingleBoneLayer(metarig, names.EYES_HANDLE_BONE, names.FACE_LAYER)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.LEFT_EYE_HANDLE_BONE, names.FACE_LAYER)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.RIGHT_EYE_HANDLE_BONE, names.FACE_LAYER)

    #get rid of the head track target
    koikatsuCommons.assignSingleBoneLayer(metarig, names.HEAD_TRACK_TARGET_BONE, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)

    #set the tweak layers for the torso bones
    koikatsuCommons.setTweakLayer(metarig, names.HIPS_BONE, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)
    koikatsuCommons.setFKLayer(metarig, names.HIPS_BONE, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)

    #do the same for the neck bone
    koikatsuCommons.setTweakLayer(metarig, names.NECK_BONE, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)

    #move the breast handle and butt handle bones to the torso tweak layer
    koikatsuCommons.assignSingleBoneLayer(metarig, names.BREASTS_HANDLE_BONE, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.LEFT_BREAST_HANDLE_BONE, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.RIGHT_BREAST_HANDLE_BONE, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.BUTTOCKS_HANDLE_BONE, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.LEFT_BUTTOCK_HANDLE_BONE, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.RIGHT_BUTTOCK_HANDLE_BONE, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)
    koikatsuCommons.assignSingleBoneLayer(metarig, names.WAIST_BONE, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)

    face_bones = ['cf_J_CheekUp_s_L', 'cf_J_CheekUp_s_R', 'cf_J_CheekLow_s_L', 'cf_J_CheekLow_s_R', 
                  'cf_J_Chin_s', 'cf_J_ChinTip_Base', 'cf_J_ChinLow', 'cf_J_MouthCavity', 'cf_J_MouthMove', 
                  'cf_J_Mouth_L', 'cf_J_Mouth_R', 'cf_J_MouthLow', 'cf_J_Mouthup', 'cf_J_EarBase_ry_L', 
                  'cf_J_EarLow_L', 'cf_J_EarUp_L', 'cf_J_EarBase_ry_R', 'cf_J_EarLow_R', 'cf_J_EarUp_R', 
                  'cf_J_Eye_rz_L', 'cf_J_CheekUp2_L', 'cf_J_Eye01_s_L', 'cf_J_Eye02_s_L', 'cf_J_Eye03_s_L', 
                  'cf_J_Eye04_s_L', 'cf_J_Eye05_s_L', 'cf_J_Eye06_s_L', 'cf_J_Eye07_s_L', 'cf_J_Eye08_s_L', 
                  'cf_J_Eye_rz_R', 'cf_J_CheekUp2_R', 'cf_J_Eye01_s_R', 'cf_J_Eye02_s_R', 'cf_J_Eye03_s_R', 
                  'cf_J_Eye04_s_R', 'cf_J_Eye05_s_R', 'cf_J_Eye06_s_R', 'cf_J_Eye07_s_R', 'cf_J_Eye08_s_R', 
                  'cf_J_Mayu_L', 'cf_J_MayuMid_s_L', 'cf_J_MayuTip_s_L', 'cf_J_Mayu_R', 'cf_J_MayuMid_s_R', 
                  'cf_J_MayuTip_s_R', 'cf_J_NoseBase', 'cf_J_Nose_tip', 'cf_J_NoseBridge_rx']

    #face bones
    for boneName in face_bones:
        if bone := metarig.data.bones.get(boneName):
            koikatsuCommons.assignSingleBoneLayer(metarig, bone.name, names.FACE_LAYER)
            koikatsuCommons.unlockAllPoseTransforms(metarig, bone.name)
            bone.use_deform = True
    
    for bone in metarig.data.bones:
        if bone.collections.get(names.FACE_LAYER + names.MCH_LAYER_SUFFIX) or bone.collections.get(names.NSFW_LAYER):
            koikatsuCommons.unlockAllPoseTransforms(metarig, bone.name)
            bone.use_deform = True

    switch(metarig, 'EDIT')
    
    for bone in metarig.data.edit_bones:
        if bone.name in defBoneNames or bone.collections.get(names.NSFW_LAYER):
            bone.use_deform = True
        else:
            bone.use_deform = False
            if bone.name not in usefulBoneNames and bone.parent and bone.parent.name in usefulBoneNames:
                bone.use_connect = False #may otherwise cause Rigify generation failure if part of a finger chain
    
    if metarig.data.bones.get('cf_s_siri_R'):
        metarig.data.bones['cf_s_siri_R'].use_deform = True
        metarig.data.bones['cf_s_siri_L'].use_deform = True

    #setup appearance and locks
    switch(metarig, 'OBJECT')
    
    #then assign the bone to a new "Emotions" bone collection
    metarig.data.collections.new(names.EMOTIONS_LAYER)


def _rigify_ui(build):
    """The Rigify UI: collection order, rows and colour sets, and the toe roll."""
    metarig = build.metarig
    '''Set up rigify UI'''
    
    
    #move the IK bone collections above the FK collections in the bone collection list or the UI will look weird
    for collection in [
        names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX,
        names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX,
        names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX,
        names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX,
        names.EMOTIONS_LAYER,
        ]:
            metarig.data.collections.move(get_rigify_index(build, collection), 0)

    metarig.data.collections_all[get_rigify_index(build, names.KOIKATSU_DEFORM_BONES_LAYER)].rigify_ui_row = 0 #remove charamaker bones from UI
    metarig.data.collections_all[get_rigify_index(build, names.JUNK_LAYER)].rigify_ui_row = 0 #remove junk from UI (issue #25)

    metarig.data.collections_all[get_rigify_index(build, names.TORSO_LAYER)].rigify_ui_row = 1 #move torso
    metarig.data.collections_all[get_rigify_index(build, names.TORSO_LAYER + names.FK_LAYER_SUFFIX)].rigify_ui_row = 1 #move torso fk

    metarig.data.collections_all[get_rigify_index(build, names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX)].rigify_ui_row = 2 #move arm L IK
    metarig.data.collections_all[get_rigify_index(build, names.LEFT_ARM_LAYER + names.FK_LAYER_SUFFIX)].rigify_ui_row = 2 #arm L fk
    
    metarig.data.collections_all[get_rigify_index(build, names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX)].rigify_ui_row = 3 #move arm R IK
    metarig.data.collections_all[get_rigify_index(build, names.RIGHT_ARM_LAYER + names.FK_LAYER_SUFFIX)].rigify_ui_row = 3 #arm R FK

    metarig.data.collections_all[get_rigify_index(build, names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX)].rigify_ui_row = 2 #move leg L IK
    metarig.data.collections_all[get_rigify_index(build, names.LEFT_LEG_LAYER + names.FK_LAYER_SUFFIX)].rigify_ui_row = 2 #move leg L FK

    metarig.data.collections_all[get_rigify_index(build, names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX)].rigify_ui_row = 3 #move leg R IK
    metarig.data.collections_all[get_rigify_index(build, names.RIGHT_LEG_LAYER + names.FK_LAYER_SUFFIX)].rigify_ui_row = 3 #move leg R FK

    metarig.data.collections_all[get_rigify_index(build, names.FINGERS_LAYER)].rigify_ui_row = 6 #fingers
    metarig.data.collections_all[get_rigify_index(build, names.EMOTIONS_LAYER)].rigify_ui_row = 6 #move emotions
    metarig.data.collections_all[get_rigify_index(build, names.HAIR_LAYER)].rigify_ui_row = 6 #move hair / accessories

    metarig.data.collections_all[get_rigify_index(build, names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX)].rigify_ui_row = 7 #move torso tweak
    metarig.data.collections_all[get_rigify_index(build, names.FINGERS_LAYER + names.DETAIL_LAYER_SUFFIX)].rigify_ui_row = 7 #move fingers detail

    metarig.data.collections_all[get_rigify_index(build, names.HAIR_LAYER + names.DETAIL_LAYER_SUFFIX)].rigify_ui_row = 8 #move hair detail to same layer

    metarig.data.collections_all[get_rigify_index(build, names.HAIR_LAYER + names.MCH_LAYER_SUFFIX)].rigify_ui_row = 8 #move hair mch to same layer

    metarig.data.collections_all[get_rigify_index(build, names.SKIRT_LAYER)].rigify_ui_row = 9 #move skirt
    metarig.data.collections_all[get_rigify_index(build, names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX)].rigify_ui_row = 9 #move skirt detail
    metarig.data.collections_all[get_rigify_index(build, names.EYES_LAYER)].rigify_ui_row = 10 #move eyes primary
    metarig.data.collections_all[get_rigify_index(build, names.FACE_LAYER)].rigify_ui_row = 10 #move face
    metarig.data.collections_all[get_rigify_index(build, names.FACE_LAYER + names.MCH_LAYER_SUFFIX)].rigify_ui_row = 10 #move face mch

    metarig.data.collections_all[get_rigify_index(build, names.NSFW_LAYER)].rigify_ui_row = 14 #move nsfw

    #set new checkbox for the toe lock
    metarig.pose.bones[names.LEFT_LEG_BONE].rigify_parameters.extra_toe_roll  = True
    metarig.pose.bones[names.RIGHT_LEG_BONE].rigify_parameters.extra_toe_roll = True

    #add missing color groups
    #Tweak = blue, root = purple, IK = red, FK = green, Extra = orange, special = yellow
    metarig.data.collections_all[names.TORSO_LAYER].rigify_color_set_name = "Special"
    metarig.data.collections_all[names.TORSO_LAYER + names.TWEAK_LAYER_SUFFIX].rigify_color_set_name = "Tweak"
    metarig.data.collections_all[names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX].rigify_color_set_name = "IK"
    metarig.data.collections_all[names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX].rigify_color_set_name = "IK"
    metarig.data.collections_all[names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX].rigify_color_set_name = "IK"
    metarig.data.collections_all[names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX].rigify_color_set_name = "IK"
    metarig.data.collections_all[names.RIGHT_ARM_LAYER + names.FK_LAYER_SUFFIX].rigify_color_set_name = "FK"
    metarig.data.collections_all[names.RIGHT_LEG_LAYER + names.FK_LAYER_SUFFIX].rigify_color_set_name = "FK"
    metarig.data.collections_all[names.LEFT_ARM_LAYER +  names.FK_LAYER_SUFFIX].rigify_color_set_name = "FK"
    metarig.data.collections_all[names.LEFT_LEG_LAYER +  names.FK_LAYER_SUFFIX].rigify_color_set_name = "FK"
    metarig.data.collections_all[names.FINGERS_LAYER].rigify_color_set_name                                  = "Special"
    metarig.data.collections_all[names.FINGERS_LAYER + names.DETAIL_LAYER_SUFFIX].rigify_color_set_name = "Special"
    metarig.data.collections_all[names.NSFW_LAYER].rigify_color_set_name = "Tweak"
    if skirtDetail := metarig.data.collections_all.get(names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX):
        skirtDetail.rigify_color_set_name = "FK"
    metarig.data.collections_all[names.SKIRT_LAYER].rigify_color_set_name = "Special"
    metarig.data.collections_all[names.FACE_LAYER].rigify_color_set_name = "Special"
    metarig.data.collections_all[names.FACE_LAYER + names.MCH_LAYER_SUFFIX].rigify_color_set_name = "Tweak"
    metarig.data.collections_all[names.EYES_LAYER].rigify_color_set_name = "Extra"
    for suffix, colourSet in (("", "Special"), (names.MCH_LAYER_SUFFIX, "Tweak"), (names.DETAIL_LAYER_SUFFIX, "FK")):
        if hairCollection := metarig.data.collections_all.get(names.HAIR_LAYER + suffix):
            hairCollection.rigify_color_set_name = colourSet


def fixDuplicateBoneName(build, boneName, childBoneName):
    metarig = build.metarig
    childBone = metarig.pose.bones.get(childBoneName)
    if childBone.parent.name != boneName:
        metarig.pose.bones.get(boneName).name = boneName + names.RENAMED_NAME_SUFFIX
        metarig.pose.bones.get(childBone.parent.name).name = boneName


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
    leftVertexGroupExtremities = koikatsuCommons.findVertexGroupExtremities(leftVertexGroupName, vertexGroupObject)
    rightVertexGroupExtremities = koikatsuCommons.findVertexGroupExtremities(rightVertexGroupName, vertexGroupObject)
    if not leftVertexGroupExtremities.maxZ or not rightVertexGroupExtremities.maxZ:
        leftVertexGroupExtremities = koikatsuCommons.findVertexGroupExtremities('cf_J_Eye07_s_L', vertexGroupObject)
        rightVertexGroupExtremities = koikatsuCommons.findVertexGroupExtremities('cf_J_Eye07_s_R', vertexGroupObject)

    leftVertexGroupMidZ = (leftVertexGroupExtremities.maxZ + leftVertexGroupExtremities.minZ) / 2
    rightVertexGroupMidZ = (rightVertexGroupExtremities.maxZ + rightVertexGroupExtremities.minZ) / 2
    averageVertexGroupMidZ = statistics.mean([leftVertexGroupMidZ, rightVertexGroupMidZ])
    averageVertexGroupMinY = statistics.mean([leftVertexGroupExtremities.minY, rightVertexGroupExtremities.minY])
    if translate and not createHandleBones:
        widgets.translate(parentWidget, (0, averageVertexGroupMinY * vertexGroupMinYFactor, -(parentWidget.location[2] - averageVertexGroupMidZ * parentWidgetTranslateZFactor)))
    leftVertexGroupMidX = (leftVertexGroupExtremities.maxX + leftVertexGroupExtremities.minX) / 2
    rightVertexGroupMidX = (rightVertexGroupExtremities.maxX + rightVertexGroupExtremities.minX) / 2
    if resize:
        widgets.resize(parentWidget, (parentWidgetResizeXFactor, parentWidgetResizeYFactor, parentWidgetResizeZFactor))

    shape(leftChildWidget)
    if translate and not createHandleBones:
        widgets.translate(leftChildWidget, (leftVertexGroupMidX * vertexGroupMidXFactor, leftVertexGroupExtremities.minY * vertexGroupMinYFactor, -(leftChildWidget.location[2] - leftVertexGroupMidZ * parentWidgetTranslateZFactor)))
    leftVertexGroupLengthX = leftVertexGroupExtremities.maxX - leftVertexGroupExtremities.minX
    rightVertexGroupLengthX = rightVertexGroupExtremities.maxX - rightVertexGroupExtremities.minX
    averageVertexGroupLengthX = statistics.mean([leftVertexGroupLengthX, rightVertexGroupLengthX])
    leftVertexGroupLengthY = leftVertexGroupExtremities.maxY - leftVertexGroupExtremities.minY
    rightVertexGroupLengthY = rightVertexGroupExtremities.maxY - rightVertexGroupExtremities.minY
    averageVertexGroupLengthY = statistics.mean([leftVertexGroupLengthY, rightVertexGroupLengthY])
    leftVertexGroupLengthZ = leftVertexGroupExtremities.maxZ - leftVertexGroupExtremities.minZ
    rightVertexGroupLengthZ = rightVertexGroupExtremities.maxZ - rightVertexGroupExtremities.minZ
    averageVertexGroupLengthZ = statistics.mean([leftVertexGroupLengthZ, rightVertexGroupLengthZ])
    leftChildWidgetResizeXFactor = statistics.mean([parentWidgetResizeXFactor, parentWidgetResizeXFactor * (leftVertexGroupLengthX / averageVertexGroupLengthX)])
    leftChildWidgetResizeYFactor = statistics.mean([parentWidgetResizeYFactor, parentWidgetResizeYFactor * (leftVertexGroupLengthY / averageVertexGroupLengthY)])
    leftChildWidgetResizeZFactor = statistics.mean([parentWidgetResizeZFactor, parentWidgetResizeZFactor * (leftVertexGroupLengthZ / averageVertexGroupLengthZ)])
    if resize:
        widgets.resize(leftChildWidget, (leftChildWidgetResizeXFactor, leftChildWidgetResizeYFactor, leftChildWidgetResizeZFactor))

    shape(rightChildWidget)
    if translate and not createHandleBones:
        widgets.translate(rightChildWidget, (rightVertexGroupMidX * vertexGroupMidXFactor, rightVertexGroupExtremities.minY * vertexGroupMinYFactor, -(rightChildWidget.location[2] - rightVertexGroupMidZ * parentWidgetTranslateZFactor)))
    rightChildWidgetResizeXFactor = statistics.mean([parentWidgetResizeXFactor, parentWidgetResizeXFactor * (rightVertexGroupLengthX / averageVertexGroupLengthX)])
    rightChildWidgetResizeYFactor = statistics.mean([parentWidgetResizeYFactor, parentWidgetResizeYFactor * (rightVertexGroupLengthY / averageVertexGroupLengthY)])
    rightChildWidgetResizeZFactor = statistics.mean([parentWidgetResizeZFactor, parentWidgetResizeZFactor * (rightVertexGroupLengthZ / averageVertexGroupLengthZ)])
    if resize:
        widgets.resize(rightChildWidget, (rightChildWidgetResizeXFactor, rightChildWidgetResizeYFactor, rightChildWidgetResizeZFactor))

    if createHandleBones:
        
        switch(rig, 'EDIT')
        parentHandleBone = koikatsuCommons.copyBone(rig, parentBoneName, parentHandleBoneName)
        if translate:
            parentHandleBone.tail.y = parentHandleBone.tail.y + averageVertexGroupMinY * vertexGroupMinYFactor
            parentHandleBone.head.y = parentHandleBone.head.y + averageVertexGroupMinY * vertexGroupMinYFactor
            parentHandleBone.tail.z = parentHandleBone.tail.z - (parentWidget.location[2] - averageVertexGroupMidZ * parentWidgetTranslateZFactor)
            parentHandleBone.head.z = parentHandleBone.head.z - (parentWidget.location[2] - averageVertexGroupMidZ * parentWidgetTranslateZFactor)
        leftChildHandleBone = koikatsuCommons.copyBone(rig, leftChildBoneName, leftChildHandleBoneName)
        if translate:
            leftChildHandleBone.tail.x = leftChildHandleBone.tail.x + leftVertexGroupMidX * vertexGroupMidXFactor
            leftChildHandleBone.head.x = leftChildHandleBone.head.x + leftVertexGroupMidX * vertexGroupMidXFactor
            leftChildHandleBone.tail.y = leftChildHandleBone.tail.y + leftVertexGroupExtremities.minY * vertexGroupMinYFactor
            leftChildHandleBone.head.y = leftChildHandleBone.head.y + leftVertexGroupExtremities.minY * vertexGroupMinYFactor
            leftChildHandleBone.tail.z = leftChildHandleBone.tail.z - (leftChildWidget.location[2] - leftVertexGroupMidZ * parentWidgetTranslateZFactor)
            leftChildHandleBone.head.z = leftChildHandleBone.head.z - (leftChildWidget.location[2] - leftVertexGroupMidZ * parentWidgetTranslateZFactor)
        leftChildHandleBone.parent = parentHandleBone
        rightChildHandleBone = koikatsuCommons.copyBone(rig, rightChildBoneName, rightChildHandleBoneName)
        if translate:
            rightChildHandleBone.tail.x = rightChildHandleBone.tail.x + rightVertexGroupMidX * vertexGroupMidXFactor
            rightChildHandleBone.head.x = rightChildHandleBone.head.x + rightVertexGroupMidX * vertexGroupMidXFactor
            rightChildHandleBone.tail.y = rightChildHandleBone.tail.y + rightVertexGroupExtremities.minY * vertexGroupMinYFactor
            rightChildHandleBone.head.y = rightChildHandleBone.head.y + rightVertexGroupExtremities.minY * vertexGroupMinYFactor
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


def removeAllConstraints(rig, boneName):
    boneToEmpty = rig.pose.bones[boneName]
    for constraint in boneToEmpty.constraints:
        constraints.remove(rig, boneName, constraint.name)


def renameAllVertexGroups(build, vertexGroupNameOld, vertexGroupNameNew):
    for obj in build.meshes(): 
        if obj.type == 'MESH':
            vertexGroup = obj.vertex_groups.get(vertexGroupNameOld)
            if vertexGroup is not None:
                vertexGroup.name = vertexGroupNameNew


def fix_bone_orientations(build, armature):
    # Connect all bones with their children if they have exactly one
    metarig = build.metarig
    for bone in armature.data.edit_bones:
        if len(bone.children) == 1 and (metarig.data.bones[bone.name].collections.get(names.ORIGINAL_ACCESSORY_LAYER_INDEX) or metarig.data.bones[bone.name].collections.get(str(names.ORIGINAL_MCH_LAYER_INDEX))):
            p1 = bone.head
            p2 = bone.children[0].head
            dist = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2) ** (1/2)

            # Only connect them if the other bone is a certain distance away, otherwise blender will delete them
            if dist > 0.005:
                bone.tail = bone.children[0].head
                if len(bone.parent.children) == 1:  # if the bone's parent bone only has one child, connect the bones (Don't connect them all because that would mess up hand/finger bones)
                    bone.use_connect = True


def finalizeMchList(build, rig, mchBoneNames, sourceLayerIndex, excludedLayerIndexes, excludedList = None):
    metarig = build.metarig
    for childBoneName in mchBoneNames:
        childBone = metarig.data.edit_bones[childBoneName]
        #childBone.length = childBone.length / 4
        if childBone.name == 'Center':
            continue
        if rig.data.bones[childBone.parent.name].collections.get(sourceLayerIndex) and childBone.parent.name not in mchBoneNames:
            insideExcludedLayer = False
            for excludedLayerIndex in excludedLayerIndexes:
                if rig.data.bones[childBone.parent.name].collections.get(str(excludedLayerIndex)):
                    insideExcludedLayer = True
                    break
            if not insideExcludedLayer and (excludedList is None or childBone.parent.name not in excludedList):
                mchBoneNames.append(childBone.parent.name)


def connectAndParentBones(rig, childBoneName, parentBoneName, connected):
    childBone = rig.data.edit_bones[childBoneName]
    parentBone = rig.data.edit_bones[parentBoneName]
    parentBone.tail = childBone.head
    childBone.parent = parentBone
    childBone.use_connect = connected


#using left vertex groups as reference for right bones because of inconsistent right group values
def finalizeRiggedTongueSideBones(build, rig, leftBoneName, rightBoneName, length, factorX, factorY = None, factorZ = None):
    leftBone = rig.data.edit_bones[leftBoneName]
    rightBone = rig.data.edit_bones[rightBoneName]
    riggedTongueLeftBoneVertexGroupExtremities = koikatsuCommons.findVertexGroupExtremities(leftBoneName, build.body)
    leftBone.head.x = riggedTongueLeftBoneVertexGroupExtremities.minX + math.dist([riggedTongueLeftBoneVertexGroupExtremities.minX], [riggedTongueLeftBoneVertexGroupExtremities.maxX]) * factorX
    leftBone.tail.x = leftBone.head.x
    rightBone.head.x = -leftBone.head.x
    rightBone.tail.x = rightBone.head.x
    if factorY:
        leftBone.head.y = riggedTongueLeftBoneVertexGroupExtremities.minY + math.dist([riggedTongueLeftBoneVertexGroupExtremities.minY], [riggedTongueLeftBoneVertexGroupExtremities.maxY]) * factorY
        leftBone.tail.y = leftBone.head.y
        rightBone.head.y = leftBone.head.y
        rightBone.tail.y = rightBone.head.y
    if factorZ:
        leftBone.head.z = riggedTongueLeftBoneVertexGroupExtremities.minZ + math.dist([riggedTongueLeftBoneVertexGroupExtremities.minZ], [riggedTongueLeftBoneVertexGroupExtremities.maxZ]) * factorZ
        rightBone.head.z = leftBone.head.z
    leftBone.length = length
    rightBone.length = length


def createPalmVertexGroups(build, wristVertexGroupName, palmVertexGroupName, rightSide, palmMinX, palmMaxX, palmMidY, lowerPalmMidY, higherPalmMidY):
    for object in build.meshes(): 
        if object.type == 'MESH':
            wristVertexGroup = object.vertex_groups.get(wristVertexGroupName)
            if wristVertexGroup is not None:
                wristVertexGroupExtremities = koikatsuCommons.findVertexGroupExtremities(wristVertexGroupName, object)
                palmVertexGroup = object.vertex_groups.get(palmVertexGroupName)
                if palmVertexGroup is None:
                    palmVertexGroup = object.vertex_groups.new(name = palmVertexGroupName)
                for vertex in wristVertexGroupExtremities.vertices:
                    if (not rightSide and wristVertexGroupExtremities.coordinates[vertex.index][0] > palmMinX) or (rightSide and wristVertexGroupExtremities.coordinates[vertex.index][0] < palmMaxX):
                        if lowerPalmMidY is None or math.dist([wristVertexGroupExtremities.coordinates[vertex.index][1]], [palmMidY]) < math.dist([wristVertexGroupExtremities.coordinates[vertex.index][1]], [lowerPalmMidY]):
                            if higherPalmMidY is None or math.dist([wristVertexGroupExtremities.coordinates[vertex.index][1]], [palmMidY]) < math.dist([wristVertexGroupExtremities.coordinates[vertex.index][1]], [higherPalmMidY]):
                                palmVertexGroup.add([vertex.index], wristVertexGroup.weight(vertex.index), 'REPLACE')
                                wristVertexGroup.remove([vertex.index])


def finalizeFingerBones(leftSide, rig, wristBoneName, fingerPalmBoneName, fingerBone1Name, fingerBone2Name, fingerBone3Name, fingerDeformBone1Name, fingerDeformBone2Name, fingerDeformBone3Name, mesh, palmBoneRoll, fingerBone1Roll, fingerBone2Roll, fingerBone3Roll, middle = False, thumb = False):
    fingerBone1 = rig.data.edit_bones[fingerBone1Name]
    fingerBone2 = rig.data.edit_bones[fingerBone2Name]
    fingerBone3 = rig.data.edit_bones[fingerBone3Name]
    fingerDeformBone1Extremities = koikatsuCommons.findVertexGroupExtremities(fingerDeformBone1Name, mesh)
    fingerDeformBone2Extremities = koikatsuCommons.findVertexGroupExtremities(fingerDeformBone2Name, mesh)
    fingerDeformBone3Extremities = koikatsuCommons.findVertexGroupExtremities(fingerDeformBone3Name, mesh)
    if not thumb:
        if not middle:
            fingerBone1.head.z = fingerDeformBone1Extremities.minZ + math.dist([fingerDeformBone1Extremities.minZ], [fingerDeformBone1Extremities.maxZ]) * 0.4
        else:
            fingerBone1.head.z = fingerDeformBone1Extremities.minZ + math.dist([fingerDeformBone1Extremities.minZ], [fingerDeformBone1Extremities.maxZ]) * 0.5
        fingerBone2.head.z = fingerDeformBone2Extremities.minZ + math.dist([fingerDeformBone2Extremities.minZ], [fingerDeformBone2Extremities.maxZ]) * 0.6
        fingerBone3.head.z = fingerDeformBone3Extremities.minZ + math.dist([fingerDeformBone3Extremities.minZ], [fingerDeformBone3Extremities.maxZ]) * 0.6
        if leftSide:
            fingerBone3.tail.x = fingerDeformBone3Extremities.minX + math.dist([fingerDeformBone3Extremities.minX], [fingerDeformBone3Extremities.maxX]) * 0.95
        else:
            fingerBone3.tail.x = fingerDeformBone3Extremities.maxX - math.dist([fingerDeformBone3Extremities.minX], [fingerDeformBone3Extremities.maxX]) * 0.95
        fingerBone3.tail.y = fingerBone3.head.y + (fingerBone2.tail.y - fingerBone2.head.y)
        fingerBone3.tail.z = fingerDeformBone3Extremities.minZ + math.dist([fingerDeformBone3Extremities.minZ], [fingerDeformBone3Extremities.maxZ]) * 0.4
        wristBone = rig.data.edit_bones[wristBoneName]
        fingerPalmBone = koikatsuCommons.copyBone(rig, fingerBone1Name, fingerPalmBoneName)
        fingerPalmBone.parent = rig.data.edit_bones[wristBoneName]
        connectAndParentBones(rig, fingerBone1Name, fingerPalmBoneName, False)            
        fingerPalmBone.head.z = fingerPalmBone.tail.z
        if leftSide:
            fingerPalmBone.head.x = wristBone.tail.x - math.dist([wristBone.tail.x], [wristBone.head.x]) * 0.6
        else:
            fingerPalmBone.head.x = wristBone.tail.x + math.dist([wristBone.tail.x], [wristBone.head.x]) * 0.6
        fingerPalmBone.head.y = fingerPalmBone.head.y + (fingerBone1.head.y - fingerBone1.tail.y)
        fingerPalmBone.roll = palmBoneRoll
    else:
        if leftSide:
            fingerBone1.head.x = fingerDeformBone1Extremities.minX + math.dist([fingerDeformBone1Extremities.minX], [fingerDeformBone1Extremities.maxX]) * 0.2
            fingerBone2.head.x = fingerDeformBone2Extremities.minX + math.dist([fingerDeformBone2Extremities.minX], [fingerDeformBone2Extremities.maxX]) * 0.5
            fingerBone3.head.x = fingerDeformBone3Extremities.minX + math.dist([fingerDeformBone3Extremities.minX], [fingerDeformBone3Extremities.maxX]) * 0.4
            fingerBone3.tail.x = fingerDeformBone3Extremities.minX + math.dist([fingerDeformBone3Extremities.minX], [fingerDeformBone3Extremities.maxX]) * 0.95
        else:
            fingerBone1.head.x = fingerDeformBone1Extremities.maxX - math.dist([fingerDeformBone1Extremities.minX], [fingerDeformBone1Extremities.maxX]) * 0.2
            fingerBone2.head.x = fingerDeformBone2Extremities.maxX - math.dist([fingerDeformBone2Extremities.minX], [fingerDeformBone2Extremities.maxX]) * 0.5
            fingerBone3.head.x = fingerDeformBone3Extremities.maxX - math.dist([fingerDeformBone3Extremities.minX], [fingerDeformBone3Extremities.maxX]) * 0.4
            fingerBone3.tail.x = fingerDeformBone3Extremities.maxX - math.dist([fingerDeformBone3Extremities.minX], [fingerDeformBone3Extremities.maxX]) * 0.95
        fingerBone1.head.y = fingerDeformBone1Extremities.minY + math.dist([fingerDeformBone1Extremities.minY], [fingerDeformBone1Extremities.maxY]) * 0.45
        fingerBone1.head.z = fingerDeformBone1Extremities.minZ + math.dist([fingerDeformBone1Extremities.minZ], [fingerDeformBone1Extremities.maxZ]) * 0.35
        fingerBone2.head.y = fingerDeformBone2Extremities.minY + math.dist([fingerDeformBone2Extremities.minY], [fingerDeformBone2Extremities.maxY]) * 0.35
        fingerBone2.head.z = fingerDeformBone2Extremities.minZ + math.dist([fingerDeformBone2Extremities.minZ], [fingerDeformBone2Extremities.maxZ]) * 0.3
        fingerBone3.head.y = fingerDeformBone3Extremities.minY + math.dist([fingerDeformBone3Extremities.minY], [fingerDeformBone3Extremities.maxY]) * 0.4
        fingerBone3.head.z = fingerDeformBone3Extremities.minZ + math.dist([fingerDeformBone3Extremities.minZ], [fingerDeformBone3Extremities.maxZ]) * 0.45
        fingerBone3.tail.y = fingerDeformBone3Extremities.minY + math.dist([fingerDeformBone3Extremities.minY], [fingerDeformBone3Extremities.maxY]) * 0.1
        fingerBone3.tail.z = fingerDeformBone3Extremities.minZ + math.dist([fingerDeformBone3Extremities.minZ], [fingerDeformBone3Extremities.maxZ]) * 0.25
        fingerBone1.parent = rig.data.edit_bones[fingerPalmBoneName]
    fingerBone1.roll = fingerBone1Roll
    fingerBone2.roll = fingerBone2Roll
    fingerBone3.roll = fingerBone3Roll


def finalizeFingerBoneParameters(build, rig, fingerBone1Name, fingerBone2Name, fingerBone3Name):
    metarig = build.metarig
    metarig.pose.bones[fingerBone1Name].rigify_type = "limbs.super_finger"
    metarig.pose.bones[fingerBone1Name].rigify_parameters.primary_rotation_axis = "-X"
    metarig.pose.bones[fingerBone1Name].rigify_parameters.make_extra_ik_control = True
    metarig.pose.bones[fingerBone2Name].rigify_type = ""
    metarig.pose.bones[fingerBone3Name].rigify_type = ""


def get_rigify_index(build, collection_name):
    # Ported: a collection the Character has no bones for is made empty, as the legacy armature had it.
    metarig = build.metarig
    collection = metarig.data.collections_all.get(str(collection_name)) or metarig.data.collections.new(str(collection_name))
    return collection.index
