
#Switch to Object Mode and select Generated Rig

import bpy, math
from mathutils import Vector
from . import commons as koikatsuCommons
from . import legacy as c
    
def main():		   
    # Ported: the Hook names the metarig and the rig and moves the Character's meshes onto the rig
    # (hook.py); the legacy script found the metarig by its random id bone among every armature.
    generatedRig = c.get_rig()
    metarig = c.get_armature()
    c.switch(generatedRig, 'OBJECT')

    generatedRig.show_in_front = True
    generatedRig.display_type = 'TEXTURED'

    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.eyesTrackTargetBoneName, 1.5)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.headTweakBoneName, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftBreastDeformBone1Name, 0.4)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightBreastDeformBone1Name, 0.4)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftBreastBone2Name, 3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightBreastBone2Name, 3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftBreastDeformBone2Name, 0.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightBreastDeformBone2Name, 0.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftBreastBone3Name, 2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightBreastBone3Name, 2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftBreastDeformBone3Name, 0.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightBreastDeformBone3Name, 0.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftNippleBone1Name, 1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightNippleBone1Name, 1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftNippleDeformBone1Name, 0.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightNippleDeformBone1Name, 0.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftNippleBone2Name, 0.5)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightNippleBone2Name, 0.5)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftNippleDeformBone2Name, 0.05)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightNippleDeformBone2Name, 0.05)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftShoulderBoneName, 1.25)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightShoulderBoneName, 1.25)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftThumbBone1Name, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightThumbBone1Name, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftThumbBone2Name, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightThumbBone2Name, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftThumbBone3Name, 1.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightThumbBone3Name, 1.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftIndexFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightIndexFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftIndexFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightIndexFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftMiddleFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightMiddleFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftMiddleFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightMiddleFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftRingFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightRingFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftRingFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightRingFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftLittleFingerPalmBoneName, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightLittleFingerPalmBoneName, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftLittleFingerPalmFkBoneName, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightLittleFingerPalmFkBoneName, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftLittleFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightLittleFingerBone2Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftLittleFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightLittleFingerBone3Name, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rootBoneName, 0.25)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.eyesHandleBoneName, 0.72)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.leftEyeHandleBoneName, 0.72)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, koikatsuCommons.rightEyeHandleBoneName, 0.72)

    for bone_name in [i.name for i in generatedRig.data.bones if i.name.startswith('cf_J_Va''gi''na_')]:
        koikatsuCommons.setBoneCustomShapeScale(generatedRig, bone_name, 0.5)

    this_list = ['cf_j_bust02_L', 'cf_j_bust02_R', 'cf_j_bust03_L', 'cf_j_bust03_R', 'cf_j_bnip02root_L', 'cf_j_bnip02root_R', 'cf_j_bnip02_L', 'cf_j_bnip02_R']
    for bone_name in this_list:
        if bone := generatedRig.pose.bones.get(bone_name):
            bone.custom_shape_rotation_euler[0] = math.pi/2

    for bone in [i for i in generatedRig.pose.bones if i.name.endswith(' Buttock handle')]:
        bone.custom_shape_rotation_euler[0] = math.pi/4
        bone.custom_shape_rotation_euler[1] = 0.436 if 'Right' in bone.name else -0.436

    for bone_name in c.face_bone_names():
        if bone := generatedRig.pose.bones.get(bone_name):
            bone.custom_shape_rotation_euler[0] = math.pi/2
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, 'cf_j_kokan', 0.2)

    headBone = generatedRig.pose.bones[koikatsuCommons.originalBonePrefix + koikatsuCommons.headBoneName]
    koikatsuCommons.changeConstraintIndex(generatedRig, headBone.name, koikatsuCommons.transformationConstraintBaseName + koikatsuCommons.headConstraintSuffix + koikatsuCommons.rotationConstraintSuffix, len(headBone.constraints) - 1)
    koikatsuCommons.changeConstraintIndex(generatedRig, headBone.name, koikatsuCommons.limitRotationConstraintBaseName + koikatsuCommons.headConstraintSuffix, len(headBone.constraints) - 1)
    
    headTweakLimitRotationConstraint = koikatsuCommons.addLimitRotationConstraint(generatedRig, koikatsuCommons.headTweakBoneName, None, 'LOCAL', koikatsuCommons.limitRotationConstraintBaseName + koikatsuCommons.headConstraintSuffix, 
    True, math.radians(-180), math.radians(180), True, math.radians(-180), math.radians(180), True, math.radians(-180), math.radians(180))
    
    for driver in generatedRig.animation_data.drivers:
        if driver.data_path.startswith("pose.bones"):
            driverOwnerName = driver.data_path.split('"')[1]
            driverProperty = driver.data_path.rsplit('.', 1)[1]
            if driverOwnerName == headBone.name:
                constraintName = driver.data_path.split('"')[3]
                if constraintName == koikatsuCommons.limitRotationConstraintBaseName + koikatsuCommons.headConstraintSuffix:
                    variable = driver.driver.variables[0]
                    newVariable = koikatsuCommons.DriverVariable(variable.name, variable.type, generatedRig, variable.targets[0].bone_target, None, None, None, None, variable.targets[0].data_path, None, None)																																											  
                    koikatsuCommons.addDriver(headTweakLimitRotationConstraint, driverProperty, None, driver.driver.type, [newVariable], 
                    driver.driver.expression)
        
    for bone in generatedRig.pose.bones:
        for constraint in bone.constraints:
            if constraint.type == 'ARMATURE':
                for target in constraint.targets:
                    if target.subtarget:
                        target.target = generatedRig
                        if target.subtarget.endswith(koikatsuCommons.placeholderBoneSuffix):
                            target.subtarget = target.subtarget[:-len(koikatsuCommons.placeholderBoneSuffix)]
    
    for driver in bpy.data.objects[koikatsuCommons.bodyName()].data.shape_keys.animation_data.drivers:
        if driver.data_path.startswith("key_blocks"):
            ownerName = driver.data_path.split('"')[1]
            if ownerName == koikatsuCommons.eyelidsShapeKeyCopyName:
                for variable in driver.driver.variables:
                    for target in variable.targets:
                        if target.id == metarig:
                            target.id = generatedRig 
    
    for driver in generatedRig.animation_data.drivers:    
        if driver.data_path.startswith("pose.bones"):
            driverOwnerName = driver.data_path.split('"')[1]
            driverProperty = driver.data_path.rsplit('.', 1)[1]
            if driverOwnerName in koikatsuCommons.bonesWithDrivers and driverProperty == "location":
                for variable in driver.driver.variables:
                    for target in variable.targets:
                        for targetToChange in koikatsuCommons.targetsToChange:
                            if target.bone_target == koikatsuCommons.originalBonePrefix + targetToChange:
                                target.bone_target = koikatsuCommons.deformBonePrefix + targetToChange
                                
    c.switch(generatedRig, 'EDIT')

    for bone in generatedRig.data.edit_bones:
        if bone.collections.get(koikatsuCommons.getRigifyLayerIndexByName(koikatsuCommons.junkLayerName)):
            koikatsuCommons.deleteBone(generatedRig, bone.name)
            continue
        if bone.collections.get(koikatsuCommons.defLayerIndex) or bone.collections.get(koikatsuCommons.nsfwLayerName) or bone.name == 'cf_s_waist02':
            bone.use_deform = True

    #move the rigged tongue bones back to the rigged tongue layer
    for bone in generatedRig.data.edit_bones:
        if bone.collections.get(koikatsuCommons.riggedTongueLayerName) or bone.name in ['cf_j_tang_02_master', 'cf_j_tang_02', 'cf_j_tang_01']:
            generatedRig.data.collections[koikatsuCommons.eyesLayerName].assign(bone)

    #face bones deform and unlock bones
    for bone in generatedRig.data.edit_bones:
        if bone.collections.get(koikatsuCommons.faceLayerName) or bone.collections.get(koikatsuCommons.eyesLayerName):
            bone.use_deform = True
            generatedRig.pose.bones[bone.name].lock_location = [False, False, False]
            generatedRig.pose.bones[bone.name].lock_rotation_w = False
            generatedRig.pose.bones[bone.name].lock_rotation = [False, False, False]
            generatedRig.pose.bones[bone.name].lock_scale = [False, False, False]

    #move the other rigged tongue bones to the face MCH layer
    for bone in generatedRig.data.edit_bones:
        if bone.name in [
            'cf_j_tang_R_03', 'cf_j_tang_R_04', 'cf_j_tang_R_05',
            'cf_j_tang_L_03', 'cf_j_tang_L_04', 'cf_j_tang_L_05',
            ]:
            generatedRig.data.collections[koikatsuCommons.eyesLayerName].unassign(bone)
            generatedRig.data.collections[koikatsuCommons.faceLayerName + koikatsuCommons.mchLayerSuffix].assign(bone)
    
    #other bones deform
    for bone in generatedRig.data.edit_bones:
        if (bone.collections.get(koikatsuCommons.faceLayerName + koikatsuCommons.mchLayerSuffix) or 
            bone.collections.get(koikatsuCommons.nsfwLayerName) or
            bone.collections.get(koikatsuCommons.deformLayerName) or
            bone.collections.get(koikatsuCommons.charamakerLayerName)):
            koikatsuCommons.unlockAllPoseTransforms(generatedRig, bone.name)
            bone.use_deform = True
    
    if generatedRig.data.edit_bones.get('cf_s_siri_R'):
        generatedRig.data.edit_bones['cf_s_siri_R'].use_deform = True
        generatedRig.data.edit_bones['cf_s_siri_L'].use_deform = True

    generatedRig.data.edit_bones[koikatsuCommons.eyesTrackTargetParentBoneName].parent = None
    generatedRig.data.edit_bones[koikatsuCommons.headTrackTargetParentBoneName].parent = None

    c.switch(generatedRig, 'OBJECT')
        
    generatedRig.pose.bones["root"].color.palette = 'CUSTOM'
    #needs to be done for data and pose
    generatedRig.data.bones['root'].color.custom.normal = (0.956863, 0.788235, 0.047059)
    generatedRig.data.bones['root'].color.custom.select = (0.313989, 0.783538, 1.000000)
    generatedRig.data.bones['root'].color.custom.active = (0.552011, 1.000000, 1.000000)

    generatedRig.pose.bones['root'].color.custom.active = (0.552011, 1.000000, 1.000000)
    generatedRig.pose.bones['root'].color.custom.normal = (0.956863, 0.788235, 0.047059)
    generatedRig.pose.bones['root'].color.custom.select = (0.313989, 0.783538, 1.000000)

    #set layer visibility
    for collection in generatedRig.data.collections_all:
        collection.is_visible = False
    for layer in ['Torso', 'Arm.L IK', 'Arm.R IK', 'Leg.L IK', 'Leg.R IK', 'Root']:
        generatedRig.data.collections_all[layer].is_visible = True

    #Take the IDs from all org bones and copy them over to the generated / helper bones
    for bone in generatedRig.data.bones:
        if (bone.get('id') or c.outfit_of(bone) is not None) and bone.name.startswith('ORG-'):
            bone_base_name = bone.name[4:]  # Remove 'ORG-' prefix
            for bone_name in [
                bone_base_name,
                'DEF-' + bone_base_name,
                bone_base_name + '_ik', 
                bone_base_name + '_ik.parent', 
                bone_base_name + '_master', 
                'MCH-' + bone_base_name,
                'MCH-' + bone_base_name + '_drv',
                ]:
                if generatedRig.data.bones.get(bone_name):
                    c.copy_tags(bone, generatedRig.data.bones[bone_name])
                    #also add the id to the .001 tail bone that appears sometimes
                    if 'MCH-' in bone_name and '_drv' in bone_name:
                        if first_child := generatedRig.data.bones[bone_name].children:
                            if second_child := first_child[0].children:
                                c.copy_tags(bone, second_child[0])

    if not c.is_kk():
        #rotate the hand bones since a lot of things are missing right now
        for bone in ['Left wrist_ik', 'Right wrist_ik']:
            if b := c.get_rig().pose.bones.get(bone):
                b.custom_shape_rotation_euler[0] = 1.0472 if 'Left' in bone else 2.0944
                b.custom_shape_rotation_euler[2] = -1.5708
                b.custom_shape_scale_xyz = (.6, .6, .6)
        for bone in ['Right wrist_ik_wrist', 'Left wrist_ik_wrist']:
            if b := c.get_rig().pose.bones.get(bone):
                b.custom_shape_scale_xyz = (.6, .6, .6)
                b.custom_shape_translation = (0, -0.04, 0)

    #Finally, extract the accessory bones for different outfits to their own layers... 
    #I won't put these in the Rigify UI, but they'll still be accessible in the bone collection section
    # Ported: the legacy objects and bones carried their Outfit as an 'id' string; Parts and bones
    # carry it as kkbp_outfit (D29).
    outfit_ids = sorted({c.outfit_of(o) for o in c.get_outfits() + c.get_hairs() if c.outfit_of(o) is not None})
    for bone in generatedRig.data.bones:
        outfit = c.outfit_of(bone)
        if outfit is None or not outfit_ids or outfit == min(outfit_ids) or not bone.collections:
            continue
        if koikatsuCommons.hairLayerName in bone.collections[0].name:
            koikatsuCommons.assignSingleBoneLayer(generatedRig, bone.name, bone.collections[0].name + f' {outfit:02d}')
            bone.collections[0].is_visible = False

    #turn off IK stretch by default
    generatedRig.pose.bones["Left arm_parent"]["IK_Stretch"] = 0
    generatedRig.pose.bones["Left leg_parent"]["IK_Stretch"] = 0
    generatedRig.pose.bones["Right arm_parent"]["IK_Stretch"] = 0
    generatedRig.pose.bones["Right leg_parent"]["IK_Stretch"] = 0

    #####################################################
    c.switch(generatedRig, 'EDIT')
    try:
        # setup emotion bones
        #create the mouth shape key controller bone on the face layer
        mouth_location = generatedRig.data.edit_bones[koikatsuCommons.eyesHandleBoneName].head + Vector((0.2, 0.1, 0))
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.mouthWidgetControllerBoneName)
        #then put it to the right of the Eyes handle bone
        bone.head = mouth_location
        bone.tail = bone.head + Vector((0,0.1,0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        #create the mouth guide bone
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.faceWidgetMouthGuideBoneName)
        #then put it to the right of the Eyes handle bone
        bone.head = mouth_location
        bone.tail = bone.head + Vector((0,0.1,0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        #create the eye/eyebrow shape key controller bone on the face layer
        eye_location = generatedRig.data.edit_bones[koikatsuCommons.eyesHandleBoneName].head + Vector((-0.2, 0.1, 0)) 
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.eyeWidgetControllerBoneName)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        #create the eye guide bone
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.faceWidgetEyesGuideBoneName)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        #create custom key bone #1
        eye_location = generatedRig.data.edit_bones[koikatsuCommons.eyesHandleBoneName].head + Vector((-0.25, 0.1, 0)) 
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.custom1WidgetControllerBoneName)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        #create custom key guide bone #1
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.custom1GuideBoneName)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        #create custom key bone #2
        eye_location = generatedRig.data.edit_bones[koikatsuCommons.eyesHandleBoneName].head + Vector((-0.3, 0.1, 0)) 
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.custom2WidgetControllerBoneName)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        #create custom key guide bone #2
        bone = generatedRig.data.edit_bones.new(koikatsuCommons.custom2GuideBoneName)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[koikatsuCommons.headTweakBoneName]
        bone.use_deform = False

        c.switch(generatedRig, 'OBJECT')
        
        #put the mouth guide into the Bone Widgets scene collection
        def setup_widget_guide(controller_name, guide_name, shape_name, lock_2d):
            generatedRig.pose.bones[controller_name].lock_location = [lock_2d, True, False]
            generatedRig.pose.bones[controller_name].custom_shape_scale_xyz = [2, 2, 2]
            generatedRig.pose.bones[controller_name].custom_shape = c.widget('WidgetSpine')
            generatedRig.pose.bones[guide_name].lock_location = [True, True, True]
            generatedRig.pose.bones[guide_name].lock_rotation = [True, True, True]
            generatedRig.pose.bones[guide_name].lock_scale = [True, True, True]
            generatedRig.pose.bones[guide_name].custom_shape = c.widget(shape_name)

        setup_widget_guide(koikatsuCommons.mouthWidgetControllerBoneName, koikatsuCommons.faceWidgetMouthGuideBoneName, 'Mouth Grid', lock_2d = False)
        setup_widget_guide(koikatsuCommons.eyeWidgetControllerBoneName, koikatsuCommons.faceWidgetEyesGuideBoneName, 'Eye Grid', lock_2d = True)
        setup_widget_guide(koikatsuCommons.custom1WidgetControllerBoneName, koikatsuCommons.custom1GuideBoneName, 'Custom1 Grid', lock_2d = True)
        setup_widget_guide(koikatsuCommons.custom2WidgetControllerBoneName, koikatsuCommons.custom2GuideBoneName, 'Custom2 Grid', lock_2d = True)

        #move to correct layer
        bones = [
            koikatsuCommons.mouthWidgetControllerBoneName,
            koikatsuCommons.faceWidgetMouthGuideBoneName,
            koikatsuCommons.eyeWidgetControllerBoneName,
            koikatsuCommons.faceWidgetEyesGuideBoneName,
            koikatsuCommons.custom1GuideBoneName,
            koikatsuCommons.custom1WidgetControllerBoneName,
            koikatsuCommons.custom2GuideBoneName,
            koikatsuCommons.custom2WidgetControllerBoneName,

            koikatsuCommons.eyesHandleBoneName,
            koikatsuCommons.leftEyeHandleBoneName,
            koikatsuCommons.rightEyeHandleBoneName,

            'cf_J_Mayu_R',
            'cf_J_MayuTip_s_R',
            'cf_J_MayuMid_s_R',
            'cf_J_Mayu_L',
            'cf_J_MayuTip_s_L',
            'cf_J_MayuMid_s_L',
            ]
        for bone_name in bones:
            if bone := generatedRig.data.bones.get(bone_name):
                bone.collections.clear()
                generatedRig.data.collections[koikatsuCommons.emotionsLayerName].assign(bone)


        # Ported: the mouth grid drives the copies of the mouth shape keys on Body and, so the mouth
        # and tongue move together, on the rigged tongue (legacy drove Body's only).
        def rig_mouth(mesh):
            ############################################################################################################
            #first, create copies of each mouth shape key
            for shapekey in [shapekey for shapekey in mesh.data.shape_keys.key_blocks if shapekey.name in koikatsuCommons.mouthShapekeysToCopy]:
                new_shapekey = mesh.data.shape_keys.key_blocks.get(shapekey.name + koikatsuCommons.mouthShapekeysCopySuffix)
                if not new_shapekey:
                    new_shapekey = mesh.shape_key_add(name=shapekey.name + koikatsuCommons.mouthShapekeysCopySuffix)
                new_shapekey.value = 0
                for i in range(len(shapekey.data)):
                    new_shapekey.data[i].co = shapekey.data[i].co

            #then, create a driver for each of the mouth shape keys that uses the XZ location of the controller bone to drive the shape key value.
            #the shape keys will be available in a five ring formation, so the A shape key will be activated when the controller bone is moved upwards, 
            # the O shape key will be activated when the controller is moved up and to the right by about 70 degrees, 
            # the U shape key will be activated when the controller is moved to the right and downwards by about 70 degrees, 
            # the E shape key will be activated when the controller is moved to the left and downwards by about 70 degrees, 
            # and the I shape key will be activated when the controller is moved to the left and upwards by about 70 degrees.
            # Create directional drivers for the copied mouth shape keys.
            mouth_directions = {
                'A': math.radians(90),
                'O': math.radians(18),
                'U': math.radians(-54),
                'E': math.radians(-126),
                'I': math.radians(162),
            }

            copied_mouth_keys = [
                mesh.data.shape_keys.key_blocks.get(
                    name + koikatsuCommons.mouthShapekeysCopySuffix
                )
                for name in koikatsuCommons.mouthShapekeysToCopy
            ]
            copied_mouth_keys = [key for key in copied_mouth_keys if key]

            mouth_pairs = [
                (koikatsuCommons.mouthShapekeyA, koikatsuCommons.mouthShapekeyA2),
                (koikatsuCommons.mouthShapekeyI, koikatsuCommons.mouthShapekeyI2),
                (koikatsuCommons.mouthShapekeyU, koikatsuCommons.mouthShapekeyU2),
                (koikatsuCommons.mouthShapekeyE, koikatsuCommons.mouthShapekeyE2),
                (koikatsuCommons.mouthShapekeyO, koikatsuCommons.mouthShapekeyO2),
            ]

            shape_keys = mesh.data.shape_keys
            controller_name = koikatsuCommons.mouthWidgetControllerBoneName
            radius = f'sqrt(x*x+z*z)'

            # thresholds: 0 -> r1 ramps shape key #1 up, r1 -> r2 crossfades to #2
            r1 = 0.045
            r2 = 0.09

            def add_mouth_driver(shapekey, expression):
                data_path = f'key_blocks["{shapekey.name}"].value'
                shape_keys.driver_remove(data_path)

                fcurve = shape_keys.driver_add(data_path)
                driver = fcurve.driver
                driver.type = 'SCRIPTED'

                for variable_name, axis in [('x', 'x'), ('z', 'z')]:
                    variable = driver.variables.new()
                    variable.name = variable_name
                    variable.type = 'SINGLE_PROP'
                    variable.targets[0].id = generatedRig
                    variable.targets[0].data_path = (
                        f'pose.bones["{controller_name}"].location.{axis}'
                    )

                driver.expression = expression

            for base_name, secondary_name in mouth_pairs:
                direction = mouth_directions[
                    next(key for key in mouth_directions if key in base_name[-1:])
                ]
                direction_x = f'{math.cos(direction):.4f}'
                direction_z = f'{math.sin(direction):.4f}'

                angle = (
                    f'max(0,1-acos((x*{direction_x}+z*{direction_z})/'
                    f'({radius}+.0001))/1.2566)'
                )

                # 0 -> 1 as radius goes 0 -> r1, then holds at 1
                ramp = f'max(0,min(1,{radius}/{r1}))'
                # 0 -> 1 as radius goes r1 -> r2
                crossfade = f'max(0,min(1,({radius}-{r1})/{r2 - r1}))'

                base_key = shape_keys.key_blocks.get(
                    base_name + koikatsuCommons.mouthShapekeysCopySuffix
                )
                secondary_key = shape_keys.key_blocks.get(
                    secondary_name + koikatsuCommons.mouthShapekeysCopySuffix
                )

                if base_key:
                    add_mouth_driver(
                        base_key,
                        f'(1-{crossfade})*{ramp}*{angle}',
                    )

                if secondary_key:
                    add_mouth_driver(
                        secondary_key,
                        f'{crossfade}*{angle}',
                    )

        for mesh in [m for m in (c.get_body(), c.get_tongue()) if m is not None and m.data.shape_keys]:
            rig_mouth(mesh)

        ##########################################################################################
        #first, create copies of each eye shape key
        for shapekey in [shapekey for shapekey in c.get_body().data.shape_keys.key_blocks if shapekey.name in koikatsuCommons.eyeShapekeysToCopy]:
            new_shapekey = c.get_body().data.shape_keys.key_blocks.get(shapekey.name + koikatsuCommons.eyeShapekeysCopySuffix)
            if not new_shapekey:
                new_shapekey = c.get_body().shape_key_add(name=shapekey.name + koikatsuCommons.eyeShapekeysCopySuffix)
            new_shapekey.value = 0
            for i in range(len(shapekey.data)):
                new_shapekey.data[i].co = shapekey.data[i].co

        shape_keys = c.get_body().data.shape_keys
        controller_name = koikatsuCommons.eyeWidgetControllerBoneName

        # Distance at which the expression reaches 1.0.
        activation_distance = 0.09

        def remove_driver(shapekey):
            if shapekey:
                data_path = f'key_blocks["{shapekey.name}"].value'
                shape_keys.driver_remove(data_path)

        def add_eye_driver(shapekey_name, expression):
            if not shapekey_name:
                return

            data_path = f'key_blocks["{shapekey_name}"].value'
            shape_keys.driver_remove(data_path)

            fcurve = shape_keys.driver_add(data_path)
            driver = fcurve.driver
            driver.type = 'SCRIPTED'

            variable = driver.variables.new()
            variable.name = 'z'
            variable.type = 'SINGLE_PROP'
            variable.targets[0].id = generatedRig
            variable.targets[0].data_path = (
                f'pose.bones["{controller_name}"].location.z'
            )

            driver.expression = expression

        # Negative Z activates DOWN.
        add_eye_driver(koikatsuCommons.eyeShapekeyClosed1 + koikatsuCommons.eyeShapekeysCopySuffix, f'max(0,min(0.35,-z/{activation_distance}))')
        add_eye_driver(koikatsuCommons.eyeShapekeyClosed2 + koikatsuCommons.eyeShapekeysCopySuffix, f'max(0,min(0.7,-z/{activation_distance}))')
        # Positive Z activates UP.
        add_eye_driver(koikatsuCommons.eyeShapekeyClosed3 + koikatsuCommons.eyeShapekeysCopySuffix, f'max(0,min(1,z/{activation_distance}))')
        add_eye_driver(koikatsuCommons.eyeShapekeyClosed4 + koikatsuCommons.eyeShapekeysCopySuffix, f'max(0,min(0.5,z/{(activation_distance*2)}))')


        ##########################################################################################
        #first, create drivers for each custom shape key
        for shapekey_name in koikatsuCommons.customShapekeysToCreate:
            new_shapekey = c.get_body().shape_key_add(name=shapekey_name)
            new_shapekey.value = 0

        shape_keys = c.get_body().data.shape_keys

        # Distance at which the expression reaches 1.0.
        activation_distance = 0.09

        # Negative Z activates DOWN.
        controller_name = koikatsuCommons.custom1WidgetControllerBoneName
        add_eye_driver(koikatsuCommons.customShapekeysToCreate[1], f'max(0,min(1,-z/{activation_distance}))')
        controller_name = koikatsuCommons.custom2WidgetControllerBoneName
        add_eye_driver(koikatsuCommons.customShapekeysToCreate[3], f'max(0,min(1,-z/{activation_distance}))')
        # Positive Z activates UP.
        controller_name = koikatsuCommons.custom1WidgetControllerBoneName
        add_eye_driver(koikatsuCommons.customShapekeysToCreate[0], f'max(0,min(1,z/{activation_distance}))')
        controller_name = koikatsuCommons.custom2WidgetControllerBoneName
        add_eye_driver(koikatsuCommons.customShapekeysToCreate[2], f'max(0,min(1,z/{activation_distance}))')

    except Exception as ex:
        c.switch(generatedRig, 'object')
        c.kklog(f'Failed to generate emotion grid bones: {type(ex).__name__}: {ex}', 'error')

    #always put the feet on the ground
    # Ported: the legacy script put the root bone 4 cm under the left ankle IK bone, which sank the
    # KK sample's shoes 1.9 cm under the floor. The root goes to the lowest vertex of the visible
    # Parts instead, so whatever the Character stands on touches the floor (ADR 0027).
    floor = c.lowest_point(generatedRig)
    c.switch(generatedRig, 'edit')
    rootBone = generatedRig.data.edit_bones[koikatsuCommons.rootBoneName]
    root = generatedRig.matrix_world @ rootBone.head
    root.z = floor
    rootLength = rootBone.tail - rootBone.head
    rootBone.head = generatedRig.matrix_world.inverted() @ root
    rootBone.tail = rootBone.head + rootLength
    c.switch(generatedRig, 'object')
    # Ported: the legacy script put the rig's origin at the root bone (origin_set to the 3D cursor)
    # and then the rig at the world origin, which moves the rig and everything on it by the root's
    # position. The same, on the data API:
    c.move_rig(generatedRig, -root)
