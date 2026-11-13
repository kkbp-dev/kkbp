import bpy
from typing import NamedTuple
import bmesh
from rna_prop_ui import rna_idprop_ui_create
import random
import string
from ...editing import switch
from . import names

def generateRandomAlphanumericString():
    randomString = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    return randomString


def duplicateShapeKey(obj, shapeKeyName, shapeKeyCopyName):
    object = obj
    for shapeKey in object.data.shape_keys.key_blocks:
        if shapeKey.name == shapeKeyName:
            shapeKey.mute = False
            oldShapeKeyValue = shapeKey.value
            shapeKey.value = 1
        elif shapeKey.name == shapeKeyCopyName:
            if object.data.shape_keys.animation_data:
                for driver in object.data.shape_keys.animation_data.drivers:
                    if driver.data_path.startswith("key_blocks"):
                        ownerName = driver.data_path.split('"')[1]
                        if ownerName == shapeKey.name:
                            object.data.shape_keys.animation_data.drivers.remove(driver)
            object.shape_key_remove(key = shapeKey)
        else:
            shapeKey.mute = True
    shapeKeyCopy = object.shape_key_add(name = shapeKeyCopyName, from_mix = True)
    shapeKeyCopy.value = 0
    for shapeKey in object.data.shape_keys.key_blocks:
        shapeKey.mute = False
        if shapeKey.name == shapeKeyName:
            shapeKey.value = oldShapeKeyValue
    return shapeKeyCopy

def isVertexGroupEmpty(vertexGroupName, obj):
    object = obj
    if not object.vertex_groups.get(vertexGroupName):
        return True
    vertexGroup = object.vertex_groups[vertexGroupName]
    return not any(vertexGroup.index in [g.group for g in v.groups] for v in object.data.vertices)
                
class Extremities:
    vertices = None
    coordinates = None
    minX = None
    minY = None
    minZ = None
    maxX = None
    maxY = None
    maxZ = None
    
def returnLower(value1, value2):
    if value1 is None or value2 < value1:
        return value2
    return value1

def returnHigher(value1, value2):
    if value1 is None or value2 > value1:
        return value2
    return value1
    
def findVertexGroupExtremities(vertexGroupName, obj):
    extremities = Extremities()
    object = obj
    coordinates = [(object.matrix_world @ v.co) for v in object.data.vertices]
    vertexGroupIndex = object.vertex_groups[vertexGroupName].index
    vertices = [ v for v in object.data.vertices if vertexGroupIndex in [ vg.group for vg in v.groups ] ]
    extremities.vertices = vertices
    extremities.coordinates = coordinates
    for vertex in vertices:
        extremities.minX = returnLower(extremities.minX, coordinates[vertex.index][0])
        extremities.minY = returnLower(extremities.minY, coordinates[vertex.index][1])
        extremities.minZ = returnLower(extremities.minZ, coordinates[vertex.index][2])
        extremities.maxX = returnHigher(extremities.maxX, coordinates[vertex.index][0])
        extremities.maxY = returnHigher(extremities.maxY, coordinates[vertex.index][1])
        extremities.maxZ = returnHigher(extremities.maxZ, coordinates[vertex.index][2])
    return extremities


def removeConstraint(rig, boneName, constraintName):
    constraint = rig.pose.bones[boneName].constraints.get(constraintName)
    if constraint:
        rig.pose.bones[boneName].constraints.remove(constraint)
        
def changeConstraintIndex(rig, boneName, constraintName, newIndex):
    bone = rig.pose.bones[boneName]
    for index, constraint in enumerate(bone.constraints):
        if constraint.name == constraintName:
            bone.constraints.move(index, newIndex)
            break

def addCopyTransformsConstraint(rig, boneName, subTargetBoneName, mixMode, space, constraintName):
    removeConstraint(rig, boneName, constraintName)
    copyTransformsConstraint = rig.pose.bones[boneName].constraints.new('COPY_TRANSFORMS')
    copyTransformsConstraint.name = constraintName
    copyTransformsConstraint.target = rig
    copyTransformsConstraint.subtarget = subTargetBoneName
    copyTransformsConstraint.mix_mode = mixMode
    copyTransformsConstraint.owner_space = space
    copyTransformsConstraint.target_space = space
    return copyTransformsConstraint
    
def addCopyRotationConstraint(rig, boneName, subTargetBoneName, mixMode, space, constraintName, 
useX, invertX, useY, invertY, useZ, invertZ):
    removeConstraint(rig, boneName, constraintName)
    copyRotationConstraint = rig.pose.bones[boneName].constraints.new('COPY_ROTATION')
    copyRotationConstraint.name = constraintName
    copyRotationConstraint.target = rig
    copyRotationConstraint.subtarget = subTargetBoneName
    copyRotationConstraint.mix_mode = mixMode
    copyRotationConstraint.owner_space = space
    copyRotationConstraint.target_space = space
    copyRotationConstraint.use_x = useX
    copyRotationConstraint.invert_x = invertX
    copyRotationConstraint.use_y = useY
    copyRotationConstraint.invert_y = invertY
    copyRotationConstraint.use_z = useZ
    copyRotationConstraint.invert_z = invertZ
    return copyRotationConstraint

        
def addTransformationConstraint(rig, boneName, subTargetBoneName, mixMode, space, constraintName, 
mapFrom, fromRotationMode, fromMinX, fromMaxX, fromMinY, fromMaxY, fromMinZ, fromMaxZ, 
mapTo, toEulerOrder, toMinX, toMaxX, toMinY, toMaxY, toMinZ, toMaxZ, 
mapToXFrom = 'X', mapToYFrom = 'Y', mapToZFrom = 'Z'):
    removeConstraint(rig, boneName, constraintName)
    transformationConstraint = rig.pose.bones[boneName].constraints.new('TRANSFORM')
    transformationConstraint.name = constraintName
    transformationConstraint.target = rig
    transformationConstraint.subtarget = subTargetBoneName
    transformationConstraint.owner_space = space
    transformationConstraint.target_space = space
    transformationConstraint.map_from = mapFrom
    if mapFrom == 'LOCATION':
        transformationConstraint.from_min_x = fromMinX
        transformationConstraint.from_max_x = fromMaxX
        transformationConstraint.from_min_y = fromMinY
        transformationConstraint.from_max_y = fromMaxY
        transformationConstraint.from_min_z = fromMinZ
        transformationConstraint.from_max_z = fromMaxZ
    elif mapFrom == 'ROTATION':
        transformationConstraint.from_rotation_mode = fromRotationMode
        transformationConstraint.from_min_x_rot = fromMinX
        transformationConstraint.from_max_x_rot = fromMaxX
        transformationConstraint.from_min_y_rot = fromMinY
        transformationConstraint.from_max_y_rot = fromMaxY
        transformationConstraint.from_min_z_rot = fromMinZ
        transformationConstraint.from_max_z_rot = fromMaxZ
    elif mapFrom == 'SCALE':
        transformationConstraint.from_min_x_scale = fromMinX
        transformationConstraint.from_max_x_scale = fromMaxX
        transformationConstraint.from_min_y_scale = fromMinY
        transformationConstraint.from_max_y_scale = fromMaxY
        transformationConstraint.from_min_z_scale = fromMinZ
        transformationConstraint.from_max_z_scale = fromMaxZ
    transformationConstraint.map_to = mapTo
    if mapTo == 'LOCATION':
        transformationConstraint.to_min_x = toMinX
        transformationConstraint.to_max_x = toMaxX
        transformationConstraint.to_min_y = toMinY
        transformationConstraint.to_max_y = toMaxY
        transformationConstraint.to_min_z = toMinZ
        transformationConstraint.to_max_z = toMaxZ
        transformationConstraint.mix_mode = mixMode
    elif mapFrom == 'ROTATION':
        transformationConstraint.to_euler_order = toEulerOrder
        transformationConstraint.to_min_x_rot = toMinX
        transformationConstraint.to_max_x_rot = toMaxX
        transformationConstraint.to_min_y_rot = toMinY
        transformationConstraint.to_max_y_rot = toMaxY
        transformationConstraint.to_min_z_rot = toMinZ
        transformationConstraint.to_max_z_rot = toMaxZ
        transformationConstraint.mix_mode_rot = mixMode
    elif mapFrom == 'SCALE':
        transformationConstraint.to_min_x_scale = toMinX
        transformationConstraint.to_max_x_scale = toMaxX
        transformationConstraint.to_min_y_scale = toMinY
        transformationConstraint.to_max_y_scale = toMaxY
        transformationConstraint.to_min_z_scale = toMinZ
        transformationConstraint.to_max_z_scale = toMaxZ
        transformationConstraint.mix_mode_scale = mixMode
    transformationConstraint.map_to_x_from = mapToXFrom
    transformationConstraint.map_to_y_from = mapToYFrom
    transformationConstraint.map_to_z_from = mapToZFrom
    return transformationConstraint
        
def addLimitLocationConstraint(rig, boneName, subTargetBoneName, space, constraintName, 
useMinX, minX, useMaxX, maxX, useMinY, minY, useMaxY, maxY, useMinZ, minZ, useMaxZ, maxZ):
    removeConstraint(rig, boneName, constraintName)
    limitLocationConstraint = rig.pose.bones[boneName].constraints.new('LIMIT_LOCATION')
    limitLocationConstraint.name = constraintName
    limitLocationConstraint.owner_space = space
    if space == 'CUSTOM':
        limitLocationConstraint.space_object = rig
        limitLocationConstraint.space_subtarget = subTargetBoneName
    limitLocationConstraint.use_min_x = useMinX
    limitLocationConstraint.min_x = minX
    limitLocationConstraint.use_max_x = useMaxX
    limitLocationConstraint.max_x = maxX
    limitLocationConstraint.use_min_y = useMinY
    limitLocationConstraint.min_y = minY
    limitLocationConstraint.use_max_y = useMaxY
    limitLocationConstraint.max_y = maxY
    limitLocationConstraint.use_min_z = useMinZ
    limitLocationConstraint.min_z = minZ
    limitLocationConstraint.use_max_z = useMaxZ
    limitLocationConstraint.max_z = maxZ
    return limitLocationConstraint

def addLimitRotationConstraint(rig, boneName, subTargetBoneName, space, constraintName, 
useX, minX, maxX, useY, minY, maxY, useZ, minZ, maxZ):
    removeConstraint(rig, boneName, constraintName)
    limitRotationConstraint = rig.pose.bones[boneName].constraints.new('LIMIT_ROTATION')
    limitRotationConstraint.name = constraintName
    limitRotationConstraint.owner_space = space
    if space == 'CUSTOM':
        limitRotationConstraint.space_object = rig
        limitRotationConstraint.space_subtarget = subTargetBoneName
    limitRotationConstraint.use_limit_x = useX
    limitRotationConstraint.min_x = minX
    limitRotationConstraint.max_x = maxX
    limitRotationConstraint.use_limit_y = useY
    limitRotationConstraint.min_y = minY
    limitRotationConstraint.max_y = maxY
    limitRotationConstraint.use_limit_z = useZ
    limitRotationConstraint.min_z = minZ
    limitRotationConstraint.max_z = maxZ
    return limitRotationConstraint
    
def addArmatureConstraint(rig, boneName, subTargetBoneNames, constraintName):
    removeConstraint(rig, boneName, constraintName)
    armatureConstraint = rig.pose.bones[boneName].constraints.new('ARMATURE')
    armatureConstraint.name = constraintName
    for index, subTargetBoneName in enumerate(subTargetBoneNames):
        armatureConstraint.targets.new()
        armatureConstraint.targets[index].target = rig
        armatureConstraint.targets[index].subtarget = subTargetBoneName
    return armatureConstraint
        
def addDampedTrackConstraint(rig, boneName, subTargetBoneName, constraintName):
    removeConstraint(rig, boneName, constraintName)
    dampedTrackConstraint = rig.pose.bones[boneName].constraints.new('DAMPED_TRACK')
    dampedTrackConstraint.name = constraintName
    dampedTrackConstraint.target = rig
    dampedTrackConstraint.subtarget = subTargetBoneName
    return dampedTrackConstraint

class DriverVariable(NamedTuple):
    name: str
    type: str
    targetObject1: bpy.types.Object
    targetBone1: str
    targetTransformSpace1: str
    targetObject2: bpy.types.Object
    targetBone2: str
    targetTransformSpace2: str
    targetCustomPropertyDataPath: str
    targetTransformType: str
    targetRotationMode: str
    
def addDriver(object, objectProperty, objectPropertyCoordinateIndex, driverType, driverVariables, driverExpression):
    if objectPropertyCoordinateIndex:
        driver = object.driver_add(objectProperty, objectPropertyCoordinateIndex)
    else:
        driver = object.driver_add(objectProperty)
    driver.driver.type = driverType
    for driverVariable in driverVariables:
        variable = driver.driver.variables.new()
        variable.name = driverVariable.name
        variable.type = driverVariable.type
        variable.targets[0].id = driverVariable.targetObject1
        if driverVariable.targetCustomPropertyDataPath:
            variable.targets[0].data_path = driverVariable.targetCustomPropertyDataPath
        if driverVariable.targetBone1:
            variable.targets[0].bone_target = driverVariable.targetBone1
        if driverVariable.targetTransformSpace1:
            variable.targets[0].transform_space = driverVariable.targetTransformSpace1
        if driverVariable.targetTransformType:
            variable.targets[0].transform_type = driverVariable.targetTransformType
        if driverVariable.targetRotationMode:
            variable.targets[0].rotation_mode = driverVariable.targetRotationMode
        if driverVariable.targetObject2:
            variable.targets[1].id = driverVariable.targetObject2
        if driverVariable.targetBone2:
            variable.targets[1].bone_target = driverVariable.targetBone2
        if driverVariable.targetTransformSpace2   :
            variable.targets[1].transform_space = driverVariable.targetTransformSpace2
        if driverExpression:         
            driver.driver.expression = driverExpression
    return driver

def removeAllConstraints(rig, boneName):
        boneToMute = rig.pose.bones[boneName]
        for constraint in boneToMute.constraints:
            boneToMute.constraints.remove(constraint)
            
def removeAllDrivers(rig, boneName):
    if rig.animation_data:
        for driver in rig.animation_data.drivers:
            if driver.data_path.startswith("pose.bones"):
                ownerName = driver.data_path.split('"')[1]
                if ownerName == boneName:
                    rig.animation_data.drivers.remove(driver)
            
def createBone(rig, newBoneName):
    newBone = rig.data.edit_bones.new(newBoneName)
    newBone.head = (0, 1, 1) # if the head and tail are the same, the bone is deleted
    newBone.tail = (0, 1, 2)
    return newBone

def deleteBone(rig, boneName):
    bone = rig.data.edit_bones.get(boneName)
    removeAllConstraints(rig, boneName)
    removeAllDrivers(rig, boneName)
    rig.data.edit_bones.remove(bone)

def copyBone(rig, sourceBoneName, newBoneName):
    newBone = rig.data.edit_bones.get(newBoneName)
    if newBone is not None:
        deleteBone(rig, newBoneName)	  
    newBone = rig.data.edit_bones.new(newBoneName)
    sourceBone = rig.data.edit_bones.get(sourceBoneName)
    newBone.tail = sourceBone.tail
    newBone.head = sourceBone.head
    newBone.roll = sourceBone.roll
    newBone.parent = sourceBone.parent
    return newBone

def addBoneCustomProperty(rig, boneName, propertyName, propertyTooltip, propertyValue, propertyMinValue, propertyMaxValue):
    """ Adds a custom property to a bone and returns the data path to it."""
    rna_idprop_ui_create(rig.pose.bones[boneName], propertyName, default = propertyValue, min = propertyMinValue, max = propertyMaxValue, soft_min = None, soft_max = None, description = propertyTooltip)
    return 'pose.bones["' + boneName + '"]["' + propertyName + '"]'
        
def copyObject(build, sourceObjectName, newObjectName):
    # Ported: the copy goes into the Character's own widget collection, and another Character's
    # widget of the same name is left alone (Blender adds .001).
    sourceObject = build.widget(sourceObjectName)
    newObject = sourceObject.copy()
    newObject.data = sourceObject.data.copy()
    newObject.name = newObjectName
    build.widgets.objects.link(newObject)
    return newObject


class RigifyLayer(NamedTuple):
        name: str
        row: int
        group: int
        
rigifyLayers = [
RigifyLayer(names.HAIR_LAYER, names.HAIR_LAYER, names.EXTRA_BONE_GROUP_INDEX),
RigifyLayer(names.HAIR_LAYER + names.DETAIL_LAYER_SUFFIX, 2, names.FK_BONE_GROUP_INDEX),
RigifyLayer(names.HAIR_LAYER + names.MCH_LAYER_SUFFIX, 3, names.ROOT_BONE_GROUP_INDEX),
RigifyLayer(names.EYES_LAYER + names.PRIMARY_LAYER_SUFFIX, 4, names.EXTRA_BONE_GROUP_INDEX),
RigifyLayer(names.EYES_LAYER + names.SECONDARY_LAYER_SUFFIX, 5, names.FK_BONE_GROUP_INDEX),
RigifyLayer(names.FACE_LAYER, 6, names.TWEAK_BONE_GROUP_INDEX),
RigifyLayer(names.FACE_LAYER + names.MCH_LAYER_SUFFIX, 7, names.ROOT_BONE_GROUP_INDEX),
RigifyLayer(names.TORSO_LAYER, 8, names.SPECIAL_BONE_GROUP_INDEX),
RigifyLayer(names.TORSO_LAYER + names.DETAIL_LAYER_SUFFIX, 9, names.TWEAK_BONE_GROUP_INDEX),
RigifyLayer(names.LEFT_ARM_LAYER + names.IK_LAYER_SUFFIX, 10, names.IK_BONE_GROUP_INDEX),
RigifyLayer(names.LEFT_ARM_LAYER + names.FK_LAYER_SUFFIX, 11, names.FK_BONE_GROUP_INDEX),
RigifyLayer(names.LEFT_ARM_LAYER + names.TWEAK_LAYER_SUFFIX, 12, names.TWEAK_BONE_GROUP_INDEX),
RigifyLayer(names.RIGHT_ARM_LAYER + names.IK_LAYER_SUFFIX, 10, names.IK_BONE_GROUP_INDEX),
RigifyLayer(names.RIGHT_ARM_LAYER + names.FK_LAYER_SUFFIX, 11, names.FK_BONE_GROUP_INDEX),
RigifyLayer(names.RIGHT_ARM_LAYER + names.TWEAK_LAYER_SUFFIX, 12, names.TWEAK_BONE_GROUP_INDEX),
RigifyLayer(names.FINGERS_LAYER, 13, names.EXTRA_BONE_GROUP_INDEX),
RigifyLayer(names.FINGERS_LAYER + names.DETAIL_LAYER_SUFFIX, 14, names.FK_BONE_GROUP_INDEX),
RigifyLayer(names.LEFT_LEG_LAYER + names.IK_LAYER_SUFFIX, 15, names.IK_BONE_GROUP_INDEX),
RigifyLayer(names.LEFT_LEG_LAYER + names.FK_LAYER_SUFFIX, 16, names.FK_BONE_GROUP_INDEX),
RigifyLayer(names.LEFT_LEG_LAYER + names.TWEAK_LAYER_SUFFIX, 17, names.TWEAK_BONE_GROUP_INDEX),
RigifyLayer(names.RIGHT_LEG_LAYER + names.IK_LAYER_SUFFIX, 15, names.IK_BONE_GROUP_INDEX),
RigifyLayer(names.RIGHT_LEG_LAYER + names.FK_LAYER_SUFFIX, 16, names.FK_BONE_GROUP_INDEX),
RigifyLayer(names.RIGHT_LEG_LAYER + names.TWEAK_LAYER_SUFFIX, 17, names.TWEAK_BONE_GROUP_INDEX),
RigifyLayer(names.SKIRT_LAYER, 18, names.EXTRA_BONE_GROUP_INDEX),
RigifyLayer(names.SKIRT_LAYER + names.DETAIL_LAYER_SUFFIX, 19, names.FK_BONE_GROUP_INDEX),
RigifyLayer("", 28, names.NONE_BONE_GROUP_INDEX),
RigifyLayer("", 28, names.NONE_BONE_GROUP_INDEX),
RigifyLayer(names.JUNK_LAYER, 29, names.NONE_BONE_GROUP_INDEX)
]


def getRigifyLayerIndexByName(rigifyLayerName):
    return rigifyLayerName

def setRigifyLayer(rig, index, rigifyLayer):
    if rig.data.collections_all.get(str(index)):
        rig.data.collections_all[str(index)].rigify_ui_title = rigifyLayer.name
        rig.data.collections_all[str(index)].rigify_ui_row = rigifyLayer.row
        rig.data.collections_all[str(index)].rigify_color_set_id = rigifyLayer.group
    
def setRootRigifyLayer(rig, boneGroupIndex):
    if rig.data.collections_all.get(str(names.ROOT_LAYER_INDEX)):
        rig.data.collections_all[str(names.ROOT_LAYER_INDEX)].rigify_color_set_id = boneGroupIndex


def assignSingleBoneLayer(rig, boneName: str, layerName: str):
    if bone := rig.data.bones.get(boneName):
        original_mode = rig.mode
        switch(rig, 'OBJECT')
        bone.collections.clear()
        if rig.data.collections.get(layerName):
            rig.data.collections[layerName].assign(bone)
        else:
            rig.data.collections.new(layerName)
            rig.data.collections[layerName].assign(bone)
        switch(rig, original_mode)

def setTweakLayer(rig, boneName, tweakLayerName):
    if boneName in rig.pose.bones:
        if not len(rig.pose.bones[boneName].rigify_parameters.tweak_coll_refs):
            rig.pose.bones[boneName].rigify_parameters.tweak_coll_refs.add()
        if not rig.data.collections.get(tweakLayerName):
            rig.data.collections.new(tweakLayerName)
        rig.pose.bones[boneName].rigify_parameters.tweak_coll_refs[0].name = tweakLayerName

def setFKLayer(rig, boneName, fkLayerName):
    if boneName in rig.pose.bones:
        if not len(rig.pose.bones[boneName].rigify_parameters.fk_coll_refs):
            rig.pose.bones[boneName].rigify_parameters.fk_coll_refs.add()
        if not rig.data.collections.get(fkLayerName):
            rig.data.collections.new(fkLayerName)
        rig.pose.bones[boneName].rigify_parameters.fk_coll_refs[0].name = fkLayerName


def getDeformBoneNames(rig, meshes):
    deformBoneNames = []
    for obj in meshes:
        if obj.type == 'MESH':
            me = obj.data
            bm = bmesh.new()
            bm.from_mesh(me)
            #groupIndex = obj.vertex_groups.active_index
            dvertLay = bm.verts.layers.deform.active
            vgIndexes = []
            if dvertLay is not None:
                for vert in bm.verts:
                    dvert = vert[dvertLay]
                    for tuple in dvert.items():
                        if tuple[1] != 0 and tuple[0] not in vgIndexes:
                            vgIndexes.append(tuple[0])
                            indexBone = rig.pose.bones.get(obj.vertex_groups[tuple[0]].name)
                            if indexBone is not None and indexBone.name not in deformBoneNames:
                                deformBoneNames.append(indexBone.name)
    return deformBoneNames

def getRelatedBoneNames(rig, boneName):
    relatedBoneNames = []
    if not rig.pose.bones.get(boneName):
        return []
    bone = rig.pose.bones[boneName]                          
    if bone.parent and bone.parent.name not in relatedBoneNames and rig.pose.bones.get(bone.parent.name):
        relatedBoneNames.append(bone.parent.name)
    for constraint in bone.constraints:
        subtarget = getattr(constraint, "subtarget", None)  # Armature and Limit constraints have none
        if subtarget is not None and subtarget not in relatedBoneNames and rig.pose.bones.get(subtarget):
            relatedBoneNames.append(subtarget)
    if rig.animation_data:
        for driver in rig.animation_data.drivers:
            if driver.data_path.startswith("pose.bones"):
                ownerName = driver.data_path.split('"')[1]
                if ownerName == boneName:
                    for variable in driver.driver.variables:
                        for target in variable.targets:
                            if target.bone_target not in relatedBoneNames and rig.pose.bones.get(target.bone_target):
                                relatedBoneNames.append(target.bone_target)
    return relatedBoneNames
        
def lockAllPoseTransforms(rig, boneName):
    rig.pose.bones[boneName].lock_location[0] = True
    rig.pose.bones[boneName].lock_location[1] = True
    rig.pose.bones[boneName].lock_location[2] = True
    rig.pose.bones[boneName].lock_rotation[0] = True
    rig.pose.bones[boneName].lock_rotation[1] = True
    rig.pose.bones[boneName].lock_rotation[2] = True
    rig.pose.bones[boneName].lock_rotation_w = True
    rig.pose.bones[boneName].lock_scale[0] = True
    rig.pose.bones[boneName].lock_scale[1] = True
    rig.pose.bones[boneName].lock_scale[2] = True

def unlockAllPoseTransforms(rig, boneName):
    rig.pose.bones[boneName].lock_location[0] = False
    rig.pose.bones[boneName].lock_location[1] = False
    rig.pose.bones[boneName].lock_location[2] = False
    rig.pose.bones[boneName].lock_rotation[0] = False
    rig.pose.bones[boneName].lock_rotation[1] = False
    rig.pose.bones[boneName].lock_rotation[2] = False
    rig.pose.bones[boneName].lock_rotation_w =  False
    rig.pose.bones[boneName].lock_scale[0] =    False
    rig.pose.bones[boneName].lock_scale[1] =    False
    rig.pose.bones[boneName].lock_scale[2] =    False


def setBoneCustomShapeScale(rig, boneName, scale):
    if rig.pose.bones.get(boneName):
        rig.pose.bones[boneName].custom_shape_scale_xyz = [scale, scale, scale]


