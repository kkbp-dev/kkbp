
#Switch to Object Mode and select Generated Rig

import bpy, math
from mathutils import Vector
from . import commons as koikatsuCommons
from . import names
from . import constraints, drivers
from ...editing import switch
from .bones import copy_tags, delete_bone, outfit_of
from .finish import ground
    
def main(build):		   
    # Ported: the Hook names the metarig and the rig and moves the Character's meshes onto the rig
    # (hook.py); the legacy script found the metarig by its random id bone among every armature.
    generatedRig = build.rig
    metarig = build.metarig
    switch(generatedRig, 'OBJECT')

    generatedRig.show_in_front = True
    generatedRig.display_type = 'TEXTURED'

    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.EYES_TRACK_TARGET_BONE, 1.5)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.HEAD_TWEAK_BONE, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_BREAST_DEFORM_BONE1, 0.4)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_BREAST_DEFORM_BONE1, 0.4)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_BREAST_BONE2, 3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_BREAST_BONE2, 3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_BREAST_DEFORM_BONE2, 0.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_BREAST_DEFORM_BONE2, 0.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_BREAST_BONE3, 2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_BREAST_BONE3, 2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_BREAST_DEFORM_BONE3, 0.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_BREAST_DEFORM_BONE3, 0.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_NIPPLE_BONE1, 1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_NIPPLE_BONE1, 1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_NIPPLE_DEFORM_BONE1, 0.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_NIPPLE_DEFORM_BONE1, 0.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_NIPPLE_BONE2, 0.5)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_NIPPLE_BONE2, 0.5)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_NIPPLE_DEFORM_BONE2, 0.05)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_NIPPLE_DEFORM_BONE2, 0.05)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_SHOULDER_BONE, 1.25)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_SHOULDER_BONE, 1.25)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_THUMB_BONE1, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_THUMB_BONE1, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_THUMB_BONE2, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_THUMB_BONE2, 1.3)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_THUMB_BONE3, 1.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_THUMB_BONE3, 1.2)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_INDEX_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_INDEX_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_INDEX_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_INDEX_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_MIDDLE_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_MIDDLE_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_MIDDLE_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_MIDDLE_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_RING_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_RING_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_RING_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_RING_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_LITTLE_FINGER_PALM_BONE, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_LITTLE_FINGER_PALM_BONE, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_LITTLE_FINGER_PALM_FK_BONE, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_LITTLE_FINGER_PALM_FK_BONE, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_LITTLE_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_LITTLE_FINGER_BONE2, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_LITTLE_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_LITTLE_FINGER_BONE3, 1.1)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.ROOT_BONE, 0.25)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.EYES_HANDLE_BONE, 0.72)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.LEFT_EYE_HANDLE_BONE, 0.72)
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, names.RIGHT_EYE_HANDLE_BONE, 0.72)

    for bone_name in [i.name for i in generatedRig.data.bones if i.name.startswith('cf_J_Va''gi''na_')]:
        koikatsuCommons.setBoneCustomShapeScale(generatedRig, bone_name, 0.5)

    this_list = ['cf_j_bust02_L', 'cf_j_bust02_R', 'cf_j_bust03_L', 'cf_j_bust03_R', 'cf_j_bnip02root_L', 'cf_j_bnip02root_R', 'cf_j_bnip02_L', 'cf_j_bnip02_R']
    for bone_name in this_list:
        if bone := generatedRig.pose.bones.get(bone_name):
            bone.custom_shape_rotation_euler[0] = math.pi/2

    for bone in [i for i in generatedRig.pose.bones if i.name.endswith(' Buttock handle')]:
        bone.custom_shape_rotation_euler[0] = math.pi/4
        bone.custom_shape_rotation_euler[1] = 0.436 if 'Right' in bone.name else -0.436

    for bone_name in build.face_bone_names():
        if bone := generatedRig.pose.bones.get(bone_name):
            bone.custom_shape_rotation_euler[0] = math.pi/2
    koikatsuCommons.setBoneCustomShapeScale(generatedRig, 'cf_j_kokan', 0.2)

    headBone = generatedRig.pose.bones[names.ORIGINAL_BONE_PREFIX + names.HEAD_BONE]
    constraints.move(
        generatedRig,
        headBone.name,
        names.TRANSFORMATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX + names.ROTATION_CONSTRAINT_SUFFIX,
        len(headBone.constraints) - 1,
    )
    constraints.move(
        generatedRig,
        headBone.name,
        names.LIMIT_ROTATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX,
        len(headBone.constraints) - 1,
    )
    
    headTweakLimitRotationConstraint = constraints.limit_rotation(
        generatedRig,
        names.HEAD_TWEAK_BONE,
        name=names.LIMIT_ROTATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX,
        space='LOCAL',
        limits=((math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180)), (math.radians(-180), math.radians(180))),
    )
    
    for driver in generatedRig.animation_data.drivers:
        if driver.data_path.startswith("pose.bones"):
            driverOwnerName = driver.data_path.split('"')[1]
            driverProperty = driver.data_path.rsplit('.', 1)[1]
            if driverOwnerName == headBone.name:
                constraintName = driver.data_path.split('"')[3]
                if constraintName == names.LIMIT_ROTATION_CONSTRAINT_BASE + names.HEAD_CONSTRAINT_SUFFIX:
                    variable = driver.driver.variables[0]
                    newVariable = drivers.Variable(
                        variable.name,
                        variable.type,
                        generatedRig,
                        bone=variable.targets[0].bone_target,
                        data_path=variable.targets[0].data_path,
                    )																																											  
                    drivers.add(
                        headTweakLimitRotationConstraint,
                        driverProperty,
                        type=driver.driver.type,
                        variables=[newVariable],
                        expression=driver.driver.expression,
                    )
        
    for bone in generatedRig.pose.bones:
        for constraint in bone.constraints:
            if constraint.type == 'ARMATURE':
                for target in constraint.targets:
                    if target.subtarget:
                        target.target = generatedRig
                        if target.subtarget.endswith(names.PLACEHOLDER_BONE_SUFFIX):
                            target.subtarget = target.subtarget[:-len(names.PLACEHOLDER_BONE_SUFFIX)]
    
    for driver in build.body.data.shape_keys.animation_data.drivers:
        if driver.data_path.startswith("key_blocks"):
            ownerName = driver.data_path.split('"')[1]
            if ownerName == names.EYELIDS_SHAPE_KEY_COPY:
                for variable in driver.driver.variables:
                    for target in variable.targets:
                        if target.id == metarig:
                            target.id = generatedRig 
    
    for driver in generatedRig.animation_data.drivers:    
        if driver.data_path.startswith("pose.bones"):
            driverOwnerName = driver.data_path.split('"')[1]
            driverProperty = driver.data_path.rsplit('.', 1)[1]
            if driverOwnerName in names.BONES_WITH_DRIVERS and driverProperty == "location":
                for variable in driver.driver.variables:
                    for target in variable.targets:
                        for targetToChange in names.TARGETS_TO_CHANGE:
                            if target.bone_target == names.ORIGINAL_BONE_PREFIX + targetToChange:
                                target.bone_target = names.DEFORM_BONE_PREFIX + targetToChange
                                
    switch(generatedRig, 'EDIT')

    for bone in generatedRig.data.edit_bones:
        if bone.collections.get(koikatsuCommons.getRigifyLayerIndexByName(names.JUNK_LAYER)):
            delete_bone(generatedRig, bone.name)
            continue
        if bone.collections.get(names.DEF_LAYER_INDEX) or bone.collections.get(names.NSFW_LAYER) or bone.name == 'cf_s_waist02':
            bone.use_deform = True

    #move the rigged tongue bones back to the rigged tongue layer
    for bone in generatedRig.data.edit_bones:
        if bone.collections.get(names.RIGGED_TONGUE_LAYER) or bone.name in ['cf_j_tang_02_master', 'cf_j_tang_02', 'cf_j_tang_01']:
            generatedRig.data.collections[names.EYES_LAYER].assign(bone)

    #face bones deform and unlock bones
    for bone in generatedRig.data.edit_bones:
        if bone.collections.get(names.FACE_LAYER) or bone.collections.get(names.EYES_LAYER):
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
            generatedRig.data.collections[names.EYES_LAYER].unassign(bone)
            generatedRig.data.collections[names.FACE_LAYER + names.MCH_LAYER_SUFFIX].assign(bone)
    
    #other bones deform
    for bone in generatedRig.data.edit_bones:
        if (bone.collections.get(names.FACE_LAYER + names.MCH_LAYER_SUFFIX) or 
            bone.collections.get(names.NSFW_LAYER) or
            bone.collections.get(names.DEFORM_LAYER) or
            bone.collections.get(names.CHARAMAKER_LAYER)):
            koikatsuCommons.unlockAllPoseTransforms(generatedRig, bone.name)
            bone.use_deform = True
    
    if generatedRig.data.edit_bones.get('cf_s_siri_R'):
        generatedRig.data.edit_bones['cf_s_siri_R'].use_deform = True
        generatedRig.data.edit_bones['cf_s_siri_L'].use_deform = True

    generatedRig.data.edit_bones[names.EYES_TRACK_TARGET_PARENT_BONE].parent = None
    generatedRig.data.edit_bones[names.HEAD_TRACK_TARGET_PARENT_BONE].parent = None

    switch(generatedRig, 'OBJECT')
        
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
        if (bone.get('id') or outfit_of(bone) is not None) and bone.name.startswith('ORG-'):
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
                    copy_tags(bone, generatedRig.data.bones[bone_name])
                    #also add the id to the .001 tail bone that appears sometimes
                    if 'MCH-' in bone_name and '_drv' in bone_name:
                        if first_child := generatedRig.data.bones[bone_name].children:
                            if second_child := first_child[0].children:
                                copy_tags(bone, second_child[0])

    if not build.kk_extras:
        #rotate the hand bones since a lot of things are missing right now
        for bone in ['Left wrist_ik', 'Right wrist_ik']:
            if b := build.rig.pose.bones.get(bone):
                b.custom_shape_rotation_euler[0] = 1.0472 if 'Left' in bone else 2.0944
                b.custom_shape_rotation_euler[2] = -1.5708
                b.custom_shape_scale_xyz = (.6, .6, .6)
        for bone in ['Right wrist_ik_wrist', 'Left wrist_ik_wrist']:
            if b := build.rig.pose.bones.get(bone):
                b.custom_shape_scale_xyz = (.6, .6, .6)
                b.custom_shape_translation = (0, -0.04, 0)

    #Finally, extract the accessory bones for different outfits to their own layers... 
    #I won't put these in the Rigify UI, but they'll still be accessible in the bone collection section
    # Ported: the legacy objects and bones carried their Outfit as an 'id' string; Parts and bones
    # carry it as kkbp_outfit (D29).
    outfit_ids = sorted({outfit_of(o) for o in list(build.character.outfits) + list(build.character.hairs) if outfit_of(o) is not None})
    for bone in generatedRig.data.bones:
        outfit = outfit_of(bone)
        if outfit is None or not outfit_ids or outfit == min(outfit_ids) or not bone.collections:
            continue
        if names.HAIR_LAYER in bone.collections[0].name:
            koikatsuCommons.assignSingleBoneLayer(generatedRig, bone.name, bone.collections[0].name + f' {outfit:02d}')
            bone.collections[0].is_visible = False

    #turn off IK stretch by default
    generatedRig.pose.bones["Left arm_parent"]["IK_Stretch"] = 0
    generatedRig.pose.bones["Left leg_parent"]["IK_Stretch"] = 0
    generatedRig.pose.bones["Right arm_parent"]["IK_Stretch"] = 0
    generatedRig.pose.bones["Right leg_parent"]["IK_Stretch"] = 0

    #####################################################
    switch(generatedRig, 'EDIT')
    try:
        # setup emotion bones
        #create the mouth shape key controller bone on the face layer
        mouth_location = generatedRig.data.edit_bones[names.EYES_HANDLE_BONE].head + Vector((0.2, 0.1, 0))
        bone = generatedRig.data.edit_bones.new(names.MOUTH_WIDGET_CONTROLLER_BONE)
        #then put it to the right of the Eyes handle bone
        bone.head = mouth_location
        bone.tail = bone.head + Vector((0,0.1,0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        #create the mouth guide bone
        bone = generatedRig.data.edit_bones.new(names.FACE_WIDGET_MOUTH_GUIDE_BONE)
        #then put it to the right of the Eyes handle bone
        bone.head = mouth_location
        bone.tail = bone.head + Vector((0,0.1,0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        #create the eye/eyebrow shape key controller bone on the face layer
        eye_location = generatedRig.data.edit_bones[names.EYES_HANDLE_BONE].head + Vector((-0.2, 0.1, 0)) 
        bone = generatedRig.data.edit_bones.new(names.EYE_WIDGET_CONTROLLER_BONE)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        #create the eye guide bone
        bone = generatedRig.data.edit_bones.new(names.FACE_WIDGET_EYES_GUIDE_BONE)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        #create custom key bone #1
        eye_location = generatedRig.data.edit_bones[names.EYES_HANDLE_BONE].head + Vector((-0.25, 0.1, 0)) 
        bone = generatedRig.data.edit_bones.new(names.CUSTOM1_WIDGET_CONTROLLER_BONE)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        #create custom key guide bone #1
        bone = generatedRig.data.edit_bones.new(names.CUSTOM1_GUIDE_BONE)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        #create custom key bone #2
        eye_location = generatedRig.data.edit_bones[names.EYES_HANDLE_BONE].head + Vector((-0.3, 0.1, 0)) 
        bone = generatedRig.data.edit_bones.new(names.CUSTOM2_WIDGET_CONTROLLER_BONE)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        #create custom key guide bone #2
        bone = generatedRig.data.edit_bones.new(names.CUSTOM2_GUIDE_BONE)
        bone.head = eye_location
        bone.tail = bone.head + Vector((0, 0.1, 0))
        bone.parent = generatedRig.data.edit_bones[names.HEAD_TWEAK_BONE]
        bone.use_deform = False

        switch(generatedRig, 'OBJECT')
        
        #put the mouth guide into the Bone Widgets scene collection
        def setup_widget_guide(controller_name, guide_name, shape_name, lock_2d):
            generatedRig.pose.bones[controller_name].lock_location = [lock_2d, True, False]
            generatedRig.pose.bones[controller_name].custom_shape_scale_xyz = [2, 2, 2]
            generatedRig.pose.bones[controller_name].custom_shape = build.widget('WidgetSpine')
            generatedRig.pose.bones[guide_name].lock_location = [True, True, True]
            generatedRig.pose.bones[guide_name].lock_rotation = [True, True, True]
            generatedRig.pose.bones[guide_name].lock_scale = [True, True, True]
            generatedRig.pose.bones[guide_name].custom_shape = build.widget(shape_name)

        setup_widget_guide(names.MOUTH_WIDGET_CONTROLLER_BONE, names.FACE_WIDGET_MOUTH_GUIDE_BONE, 'Mouth Grid', lock_2d = False)
        setup_widget_guide(names.EYE_WIDGET_CONTROLLER_BONE, names.FACE_WIDGET_EYES_GUIDE_BONE, 'Eye Grid', lock_2d = True)
        setup_widget_guide(names.CUSTOM1_WIDGET_CONTROLLER_BONE, names.CUSTOM1_GUIDE_BONE, 'Custom1 Grid', lock_2d = True)
        setup_widget_guide(names.CUSTOM2_WIDGET_CONTROLLER_BONE, names.CUSTOM2_GUIDE_BONE, 'Custom2 Grid', lock_2d = True)

        #move to correct layer
        bones = [
            names.MOUTH_WIDGET_CONTROLLER_BONE,
            names.FACE_WIDGET_MOUTH_GUIDE_BONE,
            names.EYE_WIDGET_CONTROLLER_BONE,
            names.FACE_WIDGET_EYES_GUIDE_BONE,
            names.CUSTOM1_GUIDE_BONE,
            names.CUSTOM1_WIDGET_CONTROLLER_BONE,
            names.CUSTOM2_GUIDE_BONE,
            names.CUSTOM2_WIDGET_CONTROLLER_BONE,

            names.EYES_HANDLE_BONE,
            names.LEFT_EYE_HANDLE_BONE,
            names.RIGHT_EYE_HANDLE_BONE,

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
                generatedRig.data.collections[names.EMOTIONS_LAYER].assign(bone)


        # Ported: the mouth grid drives the copies of the mouth shape keys on Body, which holds the
        # tongue too (ADR 0039), so the mouth and tongue move together.
        def rig_mouth(mesh):
            ############################################################################################################
            #first, create copies of each mouth shape key
            for shapekey in [shapekey for shapekey in mesh.data.shape_keys.key_blocks if shapekey.name in names.MOUTH_SHAPEKEYS_TO_COPY]:
                new_shapekey = mesh.data.shape_keys.key_blocks.get(shapekey.name + names.MOUTH_SHAPEKEYS_COPY_SUFFIX)
                if not new_shapekey:
                    new_shapekey = mesh.shape_key_add(name=shapekey.name + names.MOUTH_SHAPEKEYS_COPY_SUFFIX)
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
                    name + names.MOUTH_SHAPEKEYS_COPY_SUFFIX
                )
                for name in names.MOUTH_SHAPEKEYS_TO_COPY
            ]
            copied_mouth_keys = [key for key in copied_mouth_keys if key]

            mouth_pairs = [
                (names.MOUTH_SHAPEKEY_A, names.MOUTH_SHAPEKEY_A2),
                (names.MOUTH_SHAPEKEY_I, names.MOUTH_SHAPEKEY_I2),
                (names.MOUTH_SHAPEKEY_U, names.MOUTH_SHAPEKEY_U2),
                (names.MOUTH_SHAPEKEY_E, names.MOUTH_SHAPEKEY_E2),
                (names.MOUTH_SHAPEKEY_O, names.MOUTH_SHAPEKEY_O2),
            ]

            shape_keys = mesh.data.shape_keys
            controller_name = names.MOUTH_WIDGET_CONTROLLER_BONE
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
                    base_name + names.MOUTH_SHAPEKEYS_COPY_SUFFIX
                )
                secondary_key = shape_keys.key_blocks.get(
                    secondary_name + names.MOUTH_SHAPEKEYS_COPY_SUFFIX
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

        if build.body.data.shape_keys:
            rig_mouth(build.body)

        ##########################################################################################
        #first, create copies of each eye shape key
        for shapekey in [shapekey for shapekey in build.body.data.shape_keys.key_blocks if shapekey.name in names.EYE_SHAPEKEYS_TO_COPY]:
            new_shapekey = build.body.data.shape_keys.key_blocks.get(shapekey.name + names.EYE_SHAPEKEYS_COPY_SUFFIX)
            if not new_shapekey:
                new_shapekey = build.body.shape_key_add(name=shapekey.name + names.EYE_SHAPEKEYS_COPY_SUFFIX)
            new_shapekey.value = 0
            for i in range(len(shapekey.data)):
                new_shapekey.data[i].co = shapekey.data[i].co

        shape_keys = build.body.data.shape_keys
        controller_name = names.EYE_WIDGET_CONTROLLER_BONE

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
        add_eye_driver(names.EYE_SHAPEKEY_CLOSED1 + names.EYE_SHAPEKEYS_COPY_SUFFIX, f'max(0,min(0.35,-z/{activation_distance}))')
        add_eye_driver(names.EYE_SHAPEKEY_CLOSED2 + names.EYE_SHAPEKEYS_COPY_SUFFIX, f'max(0,min(0.7,-z/{activation_distance}))')
        # Positive Z activates UP.
        add_eye_driver(names.EYE_SHAPEKEY_CLOSED3 + names.EYE_SHAPEKEYS_COPY_SUFFIX, f'max(0,min(1,z/{activation_distance}))')
        add_eye_driver(names.EYE_SHAPEKEY_CLOSED4 + names.EYE_SHAPEKEYS_COPY_SUFFIX, f'max(0,min(0.5,z/{(activation_distance*2)}))')


        ##########################################################################################
        #first, create drivers for each custom shape key
        for shapekey_name in names.CUSTOM_SHAPEKEYS_TO_CREATE:
            new_shapekey = build.body.shape_key_add(name=shapekey_name)
            new_shapekey.value = 0

        shape_keys = build.body.data.shape_keys

        # Distance at which the expression reaches 1.0.
        activation_distance = 0.09

        # Negative Z activates DOWN.
        controller_name = names.CUSTOM1_WIDGET_CONTROLLER_BONE
        add_eye_driver(names.CUSTOM_SHAPEKEYS_TO_CREATE[1], f'max(0,min(1,-z/{activation_distance}))')
        controller_name = names.CUSTOM2_WIDGET_CONTROLLER_BONE
        add_eye_driver(names.CUSTOM_SHAPEKEYS_TO_CREATE[3], f'max(0,min(1,-z/{activation_distance}))')
        # Positive Z activates UP.
        controller_name = names.CUSTOM1_WIDGET_CONTROLLER_BONE
        add_eye_driver(names.CUSTOM_SHAPEKEYS_TO_CREATE[0], f'max(0,min(1,z/{activation_distance}))')
        controller_name = names.CUSTOM2_WIDGET_CONTROLLER_BONE
        add_eye_driver(names.CUSTOM_SHAPEKEYS_TO_CREATE[2], f'max(0,min(1,z/{activation_distance}))')

    except Exception as ex:
        switch(generatedRig, 'OBJECT')
        build.log.warning(f'Failed to generate emotion grid bones: {type(ex).__name__}: {ex}')

    #always put the feet on the ground
    # Ported: the legacy script put the root bone 4 cm under the left ankle IK bone, which sank the
    # KK sample's shoes 1.9 cm under the floor. The root goes to the lowest vertex of the visible
    # Parts instead, so whatever the Character stands on touches the floor (ADR 0027).
    floor = ground.lowest_point(generatedRig)
    switch(generatedRig, 'EDIT')
    rootBone = generatedRig.data.edit_bones[names.ROOT_BONE]
    root = generatedRig.matrix_world @ rootBone.head
    root.z = floor
    rootLength = rootBone.tail - rootBone.head
    rootBone.head = generatedRig.matrix_world.inverted() @ root
    rootBone.tail = rootBone.head + rootLength
    switch(generatedRig, 'OBJECT')
    # Ported: the legacy script put the rig's origin at the root bone (origin_set to the 3D cursor)
    # and then the rig at the world origin, which moves the rig and everything on it by the root's
    # position. The same, on the data API:
    ground.move_rig(generatedRig, -root)
