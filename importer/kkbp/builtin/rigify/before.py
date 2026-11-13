
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
from .metarig import accessories, deform, eyes, features, layout, limbs, torso, types
from .metarig import lists as bone_lists
    
def main(build):
    """Turns the Character's armature into the Rigify metarig, phase by phase. Each phase
    leaves Blender in the mode the next expects, as the one long function did."""
    metarig = build.metarig
    features.reserved_names(build)
    features.detect(build)
    with editing(metarig, "EDIT"):
        features.id_bone(build)
        eyes.eye_bones(build)
        torso.breasts_and_buttocks(build)
    _widgets_and_handles(build)
    with editing(metarig, "EDIT"):
        measures = eyes.tracking_bones(build)
    eyes.mechanism(build, measures)
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






















