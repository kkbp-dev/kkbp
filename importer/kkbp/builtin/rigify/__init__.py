"""Rigify: turns the Character's armature into a Rigify metarig and generates a control rig from it
(legacy `apply_rigify` and extras/rigifyscripts, D22 to D25).

The armature becomes the hidden metarig and stays `ch.armature`; the generated rig is the `rig` Part,
and every mesh, modifier and object that used the armature moves onto it. before.py, after.py and
commons.py are the legacy importer's own Rigify scripts, ported with as few changes as possible
(legacy.py says what they get instead of the legacy `common` module); prepare.py does what the
legacy armature Step did for them first.
"""

import bpy

from ... import compat
from ...pipeline.hooks import hook
from ...pipeline.options import Option
from . import after, before, commons, legacy, prepare

SWITCH = Option("use_rigify", bool, True, "Use Rigify armature",
                description="Generates a Rigify control rig, suitable for animating in Blender. Without it the "
                            "Character keeps the FK armature, which is easier to export")

# The rig's control that a bone-parented object follows, by the bone it was parented to.
FOLLOW = {"Head": "head"}
NSFW_COLLECTION, SFW_NAME = "NSFW", "Chest"
JUNK = "Junk {name}"  # what the Bone Widgets collection becomes: widgets and the metarig, hidden


@hook(name="Rigify", switch=SWITCH)
def rigify(ctx):
    ch = ctx.character
    if compat.enable_rigify():
        ctx.log.warning("Blender's Rigify add-on was off; it is on for this session (Preferences aren't saved)")
    metarig = ch.armature
    kk = prepare.kk_extras(ctx.bundle.skeleton)
    ctx.log.info("The skeleton has the joint-correction bones, so the KK-only Rigify parts run" if kk else
                 "The skeleton lacks some joint-correction bones, so the KK-only Rigify parts don't run (ADR 0022)")
    legacy.begin(ctx, kk)
    prepare.run(ctx, kk)
    before.main()

    generated_from = metarig.name  # Rigify names its widgets after it
    rig = compat.generate_rigify(metarig)
    ch.add_part(rig, "rig")
    rig.name = f"Rig {ch.name}"
    metarig.name = f"Metarig {ch.name}"
    _into(rig, ch.collection)
    _move_onto(ch, metarig, rig)
    after.main()
    _tidy(ch, metarig, generated_from)
    if ctx.options.sfw_mode if "sfw_mode" in ctx.options else False:
        collection = rig.data.collections_all.get(NSFW_COLLECTION)
        if collection is not None:
            collection.is_visible = False
            collection.name = SFW_NAME
    tools = bpy.context.scene.tool_settings
    tools.transform_pivot_point = "INDIVIDUAL_ORIGINS"
    tools.mesh_select_mode = (False, False, True)  # face select in Edit Mode, as legacy left it


def _into(obj, collection):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)


def _move_onto(ch, metarig, rig):
    """Everything that used the armature uses the rig: parents, armature modifiers, the eye UV warps
    and bone-parented objects such as the face cards' rig."""
    for obj in [o for o in bpy.data.objects if o.parent == metarig]:
        # The rig sits where the metarig does, so each object keeps its own transform, as in legacy.
        if obj.parent_type == "BONE":
            name = FOLLOW.get(obj.parent_bone, obj.parent_bone)
            obj.parent = rig
            obj.parent_bone = name if name in rig.data.bones else f"DEF-{name}"
        else:
            obj.parent = rig
    for obj in [o for o in ch.parts() if o.type == "MESH"]:
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object == metarig:
                modifier.object = rig
            if modifier.type == "UV_WARP" and modifier.object_from == metarig:
                modifier.object_from = modifier.object_to = rig
                modifier.bone_from = prepare.EYES_X
                modifier.bone_to = (commons.leftEyeBoneName if modifier.name == prepare.UV_WARPS["eye_l"]
                                    else commons.rightEyeBoneName)


def _tidy(ch, metarig, generated_from):
    """The Bone Widgets collection becomes the Character's Junk collection, excluded from the view
    layer as legacy excluded Bone Widgets, and takes Rigify's widget collection and the metarig."""
    junk = legacy.widget_collection()
    junk.name = JUNK.format(name=ch.name)
    for collection in [c for c in bpy.data.collections if c.name == f"WGTS_{generated_from}"]:
        _move_collection(collection, junk)
    _into(metarig, junk)
    layer = _layer(bpy.context.view_layer.layer_collection, junk)
    if layer is not None:
        layer.exclude = True


def _move_collection(collection, parent):
    for owner in [bpy.context.scene.collection, *bpy.data.collections]:
        if collection.name in owner.children and owner != parent:
            owner.children.unlink(collection)
    if collection.name not in parent.children:
        parent.children.link(collection)


def _layer(layer, collection):
    if layer.collection == collection:
        return layer
    for child in layer.children:
        found = _layer(child, collection)
        if found is not None:
            return found
    return None
