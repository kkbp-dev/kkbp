import bpy
import bmesh
from ...editing import switch
from . import names


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


        

    

        
        

    
        

    

            
            


        
def copyObject(build, sourceObjectName, newObjectName):
    # Ported: the copy goes into the Character's own widget collection, and another Character's
    # widget of the same name is left alone (Blender adds .001).
    sourceObject = build.widget(sourceObjectName)
    newObject = sourceObject.copy()
    newObject.data = sourceObject.data.copy()
    newObject.name = newObjectName
    build.widgets.objects.link(newObject)
    return newObject


        


def getRigifyLayerIndexByName(rigifyLayerName):
    return rigifyLayerName

    


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


