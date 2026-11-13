from ...editing import switch
from . import names


                
    

    


        

    

        
        

    
        

    

            
            


        
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


