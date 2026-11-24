"""Face cards: flat eyes and mouth on cards in front of the face, posed by their own small rig, with
the Character's own eye textures (legacy `import_face_cards`, D20). They come from
library/face_cards.blend; their Collection starts excluded from the view layer, as in the legacy
importer, so they are there when wanted and out of the way otherwise. SVS has no eyelines, so its
eyelash takes the upper eyeline's place, and its eye white gets a mask cut for SVS's eye UVs (ADR 0037).
"""

import math

import bpy

from .. import appending, templates
from ..collection_colors import color
from ..library import hook_assets
from ..pipeline.hooks import hook
from ..pipeline.options import Option

SWITCH = Option("use_face_cards", bool, False, "Face cards",
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
    color(collection, "face")
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
    ch, assets = ctx.character, hook_assets.FACE_CARDS
    materials = {appending.base_name(s.material.name): s.material for obj in meshes for s in obj.material_slots
                 if s.material}
    eye_white = None
    for (card, node_name), roles in assets.textures.items():
        tree = materials[card].node_tree
        node = tree.nodes[node_name]
        source, image = _light_texture(ch, roles)
        if image is None:
            _draw_nothing(tree, node)
            ctx.log.info(f"No {' or '.join(roles)} light texture for the face cards' {card}; "
                         f"its {node_name} draws nothing")
            continue
        node.image = image
        if "eye_white" in roles:
            eye_white = source
    if eye_white is not None:
        _use_the_eye_white_mask(ctx, materials, eye_white)


def _light_texture(ch, roles):
    """The first of the roles' materials with a light texture, and that texture, or (None, None)."""
    for role in roles:
        source = next((m for m in ch.materials(roles=role) if m.get(templates.TEMPLATE)), None)
        light = templates.texture(source, "main", "light") if source is not None else None
        if light is not None and light.image is not None:
            return source, light.image
    return None, None


def _draw_nothing(tree, node):
    """Unlinks an image node with no image, which would draw opaque black, so the sticker group's
    alpha input falls back to 0 for that layer."""
    for output in node.outputs:
        for link in list(output.links):
            if link.to_socket.type == "VALUE":
                link.to_socket.default_value = 0.0
            tree.links.remove(link)


def _use_the_eye_white_mask(ctx, materials, eye_white):
    """The mask that cuts the eye white out of its texture follows the eye white's template, because
    the texture is laid out by that Game's eye UVs (ADR 0037)."""
    card, node_name = hook_assets.FACE_CARDS.eye_white_mask
    template = templates.template_of(eye_white).name
    mask = hook_assets.FACE_CARDS.eye_white_masks.get(template)
    if mask is None:
        ctx.log.info(f"No face card eye white mask for the template {template}; the card keeps KK's")
        return
    node = materials[card].node_tree.nodes[node_name]
    if node.image is None or appending.base_name(node.image.name) != mask:
        node.image = _image(mask)


def _image(name):
    """An image from face_cards.blend, appended once per file."""
    found = appending.existing("images", name)
    if found is None:
        appending.append(hook_assets.FACE_CARDS.path, "images", name, hook_assets.VERSION_PROP)
        found = appending.existing("images", name)
        found.use_fake_user = False  # the file keeps it alive this way; the card's node does here
    return found


def _layer(collection, layer=None):
    layer = layer or bpy.context.view_layer.layer_collection
    if layer.collection == collection:
        return layer
    for child in layer.children:
        found = _layer(collection, child)
        if found is not None:
            return found
    return None
