"""Rigify: turns the Character's armature into a Rigify metarig and generates a control rig from it
(legacy `apply_rigify` and extras/rigifyscripts, D22 to D25).

The armature becomes the hidden metarig and stays `ch.armature`; the generated rig is the `rig` Part,
and every mesh, modifier and object that used the armature moves onto it.

The Hook makes a RigBuild (build.py) for the Character and hands it to each phase: prepare.py does
what the legacy armature Step did first, metarig/ turns the armature into the metarig, Rigify
generates the rig, and finish/ fixes it up. The rig keeps the legacy importer's bone, constraint,
property and driver names (ADR 0023, ADR 0043); names.py holds them all.
"""

import bpy

from ... import compat, joint_corrections
from ...collection_colors import color
from ...pipeline.hooks import hook
from ...pipeline.options import Option
from . import prepare
from .finish import finish_rig
from .metarig import build_metarig
from .build import RigBuild

SWITCH = Option("use_rigify", bool, True, "Use Rigify armature",
                description="Generates a Rigify control rig, suitable for animating in Blender. Without it the "
                            "Character keeps the FK armature, which is easier to export")

# The rig's control that a bone-parented object follows, by the bone it was parented to.
FOLLOW = {"Head": "head"}
NSFW_COLLECTION, SFW_NAME = "NSFW", "Chest"
# An empty collection beside NSFW in the Rig Layers panel, for bones the user adds (issue #7).
CUSTOM_COLLECTION = "Custom"
JUNK = "Junk {name}"  # what the Bone Widgets collection becomes: the face board labels and WIDGETS
WIDGETS = "Widgets {name}"  # inside Junk, excluded from the view layer: the widgets and the metarig


@hook(name="Rigify", switch=SWITCH)
def rigify(ctx):
    ch = ctx.character
    if compat.enable_rigify():
        ctx.log.warning("Blender's Rigify add-on was off; it is on for this session (Preferences aren't saved)")
    metarig = ch.armature
    kk = prepare.kk_extras(ctx.bundle.skeleton)
    ctx.log.info("The skeleton has the joint-correction bones, so the KK-only Rigify parts run" if kk else
                 "The skeleton lacks some joint-correction bones, so the KK-only Rigify parts don't run (ADR 0022); "
                 "the hands are aimed from the meshes (ADR 0045)")
    # The legacy scripts count and re-aim bones, so the joint corrections' helper bones come off
    # first and go back on the generated rig, where the deforming bones are (ADR 0038).
    joint_corrections.remove(metarig)
    build = RigBuild(ctx, metarig, kk_extras=kk)
    prepare.run(ctx)
    build_metarig(build)
    _add_custom_collection(metarig)

    generated_from = metarig.name  # Rigify names its widgets after it
    rig = compat.generate_rigify(metarig)
    ch.add_part(rig, "rig")
    build.rig = rig
    rig.name = f"Rig {ch.name}"
    metarig.name = f"Metarig {ch.name}"
    _into(rig, ch.collection)
    _move_onto(ch, metarig, rig)
    finish_rig(build)
    if joint_corrections.has_corrections(metarig):
        count, missing = joint_corrections.refresh(rig, source=metarig)
        ctx.log.info(f"Put the joint corrections back on the rig: {count} bones"
                     + (f"; none need {', '.join(missing)}, which the rig lacks" if missing else ""))
    _tidy(build, generated_from)
    if ctx.options.sfw_mode if "sfw_mode" in ctx.options else False:
        collection = rig.data.collections_all.get(NSFW_COLLECTION)
        if collection is not None:
            collection.is_visible = False
            collection.name = SFW_NAME
    tools = bpy.context.scene.tool_settings
    tools.transform_pivot_point = "INDIVIDUAL_ORIGINS"
    tools.mesh_select_mode = (False, False, True)  # face select in Edit Mode, as legacy left it


def _add_custom_collection(metarig):
    """Made after NSFW so the panel draws it to NSFW's right; after.py hides it with the rest."""
    collections = metarig.data.collections_all
    custom = collections.get(CUSTOM_COLLECTION) or metarig.data.collections.new(CUSTOM_COLLECTION)
    custom.rigify_ui_row = collections[NSFW_COLLECTION].rigify_ui_row


def _into(obj, collection):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)


def _move_onto(ch, metarig, rig):
    """Everything that used the armature uses the rig: parents, armature modifiers and bone-parented
    objects such as the face cards' rig."""
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


def _tidy(build, generated_from):
    """The Bone Widgets collection becomes the Character's Junk collection. Junk stays in the view
    layer for the face board labels, which show and hide with the board's bone collection; the
    widgets, Rigify's widget collection and the metarig go in its Widgets collection, excluded from
    the view layer as legacy excluded Bone Widgets."""
    ch, metarig = build.character, build.metarig
    junk = build.widgets
    junk.name = JUNK.format(name=ch.name)
    color(junk, "junk")
    hidden = bpy.data.collections.new(WIDGETS.format(name=ch.name))
    junk.children.link(hidden)
    for obj in list(junk.objects):
        _into(obj, hidden)
    for collection in [c for c in bpy.data.collections if c.name == f"WGTS_{generated_from}"]:
        _move_collection(collection, hidden)
    _into(metarig, hidden)
    layer = _layer(bpy.context.view_layer.layer_collection, hidden)
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
