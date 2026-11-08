"""Face cards: flat eyes and mouth on cards in front of the face, posed by their own small rig, with
the Character's own eye textures (legacy `import_face_cards`, D20). They come from
library/face_cards.blend; their Collection starts excluded from the view layer, as in the legacy
importer, so they are there when wanted and out of the way otherwise.
"""

import math

import bpy

from .. import appending, templates
from ..library import hook_assets
from ..pipeline.hooks import hook
from ..pipeline.options import Option

SWITCH = Option("use_face_cards", bool, True, "Face cards",
                description="Adds 2D eye and mouth cards in front of the face, with the Character's eye textures. "
                            "Their Collection starts hidden")

# Where the card rig sits on the head bone, as the legacy importer placed it. The rest position is in
# the delta transform, so clearing the location (Alt+G) puts the cards back in front of the face.
HEAD_TAIL = 0.3
DELTA_LOCATION = (0.0, 0.0, 0.15)
DELTA_ROTATION = (-math.pi / 2, 0.0, 0.0)


@hook(name="Face cards", switch=SWITCH)
def face_cards(ctx):
    ch, assets = ctx.character, hook_assets.FACE_CARDS
    images_before = set(bpy.data.images)
    added = appending.append(assets.path, "collections", assets.collection, hook_assets.VERSION_PROP)
    collection = next(c for c in added if appending.base_name(c.name) == assets.collection)
    bone_shapes = next(c for c in added if appending.base_name(c.name) == assets.bone_shapes)
    ch.collection.children.link(collection)
    collection.name = f"{assets.collection} {ch.name}"
    for layer in (_layer(collection), _layer(bone_shapes)):
        if layer is not None:
            layer.exclude = True

    objects = {appending.base_name(o.name): o for o in collection.objects}
    rig = objects[assets.rig]
    for obj in [rig] + [objects[name] for name in assets.meshes]:
        ch.add_part(obj, "face_card")
    _parent_to_head(ctx, rig)
    _use_the_characters_textures(ctx, [objects[name] for name in assets.meshes])
    for image in [i for i in bpy.data.images if i not in images_before and i.users == 0]:
        bpy.data.images.remove(image)  # the card templates' own textures, replaced above


def _parent_to_head(ctx, rig):
    head = ctx.bundle.skeleton.by_role("head")
    armature = ctx.character.armature
    if head is None or armature is None or head.id not in armature.data.bones:
        ctx.log.warning("The skeleton has no head bone, so the face cards aren't attached to the head")
        return
    rig.parent = armature
    rig.parent_type = "BONE"
    rig.parent_bone = head.id
    rig.parent_bone_head_tail_factor = HEAD_TAIL
    rig.location = (0.0, 0.0, 0.0)
    rig.delta_location = DELTA_LOCATION
    rig.delta_rotation_euler = DELTA_ROTATION


def _use_the_characters_textures(ctx, meshes):
    ch = ctx.character
    materials = {appending.base_name(s.material.name): s.material for obj in meshes for s in obj.material_slots
                 if s.material}
    for (card, node_name), role in hook_assets.FACE_CARDS.textures.items():
        node = materials[card].node_tree.nodes[node_name]
        source = next((m for m in ch.materials(roles=role) if m.get(templates.TEMPLATE)), None)
        light = templates.texture(source, "main", "light") if source is not None else None
        if light is None or light.image is None:
            ctx.log.info(f"No {role} light texture for the face cards' {card}; it keeps its own")
            continue
        node.image = light.image


def _layer(collection, layer=None):
    layer = layer or bpy.context.view_layer.layer_collection
    if layer.collection == collection:
        return layer
    for child in layer.children:
        found = _layer(collection, child)
        if found is not None:
            return found
    return None
