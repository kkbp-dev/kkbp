import bpy
from typing import NamedTuple
import bmesh
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


