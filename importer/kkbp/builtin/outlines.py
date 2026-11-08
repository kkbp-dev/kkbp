"""Outlines: a black outline around the body, hair and clothes, drawn by a Solidify modifier with
flipped normals and outline copies of the Part's materials (legacy `apply_outlines`, D19).

Each outline material is a copy of a Part's material with its light and dark textures replaced by
black, so it keeps the material's alpha. It is tagged with the Character Key, and with the Id of the
material it was copied from as `kkbp_outline`, not as a bundle Id, so `ch.material(id)` still finds
one material per Id.
"""

import bpy

from .. import appending, templates
from ..character import ID, KEY, ROLE
from ..library import hook_assets
from ..pipeline.hooks import hook
from ..pipeline.options import Option

SWITCH = Option("use_outlines", bool, True, "Use outlines",
                description="Gives the body, hair and clothes an outline material for each of their materials")

OUTLINE = "kkbp_outline"  # on an outline material: the bundle Id of the material it outlines
MODIFIER = "Outline Modifier"
THICKNESS = 0.0005  # metres, the legacy importer's
# The shaders that draw outlines badly, so the Hook leaves them out, as the legacy importer did.
NO_OUTLINES_WITH = ("cycles", "cycles_classic", "principled")
BLACK = (0.0, 0.0, 0.0, 1.0)
FACE_FORCE_VISIBILITY = 2
# The Parts with their own outline material per material that shows a texture or an alpha mask.
TEXTURED_PARTS = ("hair", "outfit", "alt_outfit")
# A material shows a texture or an alpha mask when one of these slots holds a bundle image.
TEXTURED_SLOTS = ("main.light", "alpha_mask", "alpha_mask_bottom")


@hook(name="Outlines", switch=SWITCH)
def outlines(ctx):
    shader = ctx.options.convert_shaders if "convert_shaders" in ctx.options else "off"
    if shader in NO_OUTLINES_WITH:
        ctx.log.info(f"No outlines with the {shader} shader")
        return
    ch = ctx.character
    if ch.body is not None:
        _body(ctx, ch, ch.body)
    shared = {}  # source material -> its outline, so a material on several Parts has one outline
    for obj in ch.parts(TEXTURED_PARTS):
        _textured(ctx, ch, obj, shared)


def _body(ctx, ch, body):
    """The face and the body get one outline material each. The Solidify modifier's material offset
    is the slot count, so the face's faces (slot 0) get the first outline and every other slot the
    last, the body's (Blender clamps a material index past the last slot)."""
    slots = len(body.material_slots)
    face = next(iter(ch.materials(roles="face", parts="body")), None)
    skin = next(iter(ch.materials(roles="body", parts="body")), None)
    if not _light_dark(face) or not _light_dark(skin):
        ctx.log.warning("Body has no baked face or body material, so it has no outline")
        return
    if body.material_slots[0].material != face:
        ctx.log.warning("The face isn't Body's first material, so Body's outline may use the wrong material")
    _modifier(body, offset=0.0, material_offset=slots)
    face_outline = _outline(ch, face, f"Outline {face.get(ID)}")
    face_outline_mask = hook_assets.OUTLINES.face_masks.get(templates.template_of(face).name)
    mask = templates.texture_node(face_outline, "alpha_mask")
    if face_outline_mask and mask is not None:
        mask.image = _image(face_outline_mask)  # no outline around the eyes
    templates.param(face_outline, "force_visibility").default_value = FACE_FORCE_VISIBILITY
    body.data.materials.append(face_outline)
    body.data.materials.append(_outline(ch, skin, f"Outline {skin.get(ID)}"))


def _textured(ctx, ch, obj, outlines_of):
    """Every material that shows a texture or an alpha mask gets its own outline, which keeps its
    alpha; the others share one. Those materials move to the front so the modifier's material
    offset reaches their outline; the rest reach the shared one, in the last slot."""
    mesh = obj.data
    materials = [s.material for s in obj.material_slots]
    textured = [m for m in materials if m is not None and _is_textured(ch, m)]
    _sort_slots(obj, textured)
    start = len(mesh.materials)
    for mat in textured:
        if mat not in outlines_of:
            outline = _outline(ch, mat, f"Outline {mat.get(ID, mat.name)}", keep_textures=True)
            if _blend_mode(ctx, mat) == "glasses":
                _unlink(outline, templates.param(outline, "light_alpha"))
            outlines_of[mat] = outline
        mesh.materials.append(outlines_of[mat])
    first = mesh.materials[0] if len(mesh.materials) else None
    if not _light_dark(first):
        return
    _modifier(obj, offset=1.0, material_offset=start)
    shared = _outline(ch, first, f"Outline {obj.name}")
    alpha = templates.texture_node(shared, "alpha_mask")
    if alpha is not None:
        alpha.image = _image(hook_assets.OUTLINES.placeholder)
    mesh.materials.append(shared)


def _outline(ch, source, name, keep_textures=False):
    """A black outline copy of `source`. With `keep_textures`, the textures stay linked for their
    alpha and the shader's light and dark colours are set black instead."""
    mat = source.copy()
    mat.name = name
    for prop in (ID, ROLE, "id"):
        mat.pop(prop, None)
    mat[KEY] = ch.key
    mat[OUTLINE] = source.get(ID, source.name)
    mat.use_backface_culling = True
    mat.use_backface_culling_shadow = True
    mat.diffuse_color = (0.0, 0.0, 0.0, 0.0)
    if keep_textures:
        for param in ("light", "dark"):
            socket = templates.param(mat, param)
            _unlink(mat, socket)
            socket.default_value = BLACK
    else:
        black = _image(hook_assets.OUTLINES.black)
        for variant in ("light", "dark"):
            node = templates.texture(mat, "main", variant)
            if node is not None:
                node.image = black
    return mat


def _modifier(obj, offset, material_offset):
    modifier = obj.modifiers.new(MODIFIER, "SOLIDIFY")
    modifier.thickness = THICKNESS
    modifier.offset = offset
    modifier.material_offset = material_offset
    modifier.use_flip_normals = True
    modifier.use_rim = False
    modifier.show_expanded = False
    return modifier


def _light_dark(mat):
    """Whether the material has a template with light and dark textures, which an outline can black out."""
    return mat is not None and mat.get(templates.TEMPLATE) is not None and \
        "main.light" in templates.template_of(mat).textures


def _is_textured(ch, mat):
    if not _light_dark(mat):
        return False
    for slot in TEXTURED_SLOTS:
        node = templates.texture_node(mat, slot)
        if node is not None and node.image is not None and node.image.get(KEY) == ch.key:
            return True
    return False


def _blend_mode(ctx, mat):
    bundle_material = ctx.bundle.material(mat.get(ID)) if mat.get(ID) else None
    return bundle_material.blend_mode if bundle_material else None


def _unlink(mat, socket):
    for link in list(socket.links):
        mat.node_tree.links.remove(link)


def _image(name):
    """An image from outlines.blend, appended once per file."""
    found = appending.existing("images", name)
    if found is None:
        appending.append(hook_assets.OUTLINES.path, "images", name, hook_assets.VERSION_PROP)
        found = appending.existing("images", name)
    return found


def _sort_slots(obj, first):
    """Puts the materials in `first` at the front of the object's slots, keeping each face's material."""
    mesh = obj.data
    materials = list(mesh.materials)
    order = sorted(range(len(materials)), key=lambda i: (materials[i] not in first, i))
    if order == list(range(len(materials))):
        return
    new_index = {old: new for new, old in enumerate(order)}
    indices = [0] * len(mesh.polygons)
    mesh.polygons.foreach_get("material_index", indices)
    mesh.materials.clear()
    for old in order:
        mesh.materials.append(materials[old])
    mesh.polygons.foreach_set("material_index", [new_index[i] for i in indices])
    mesh.update()
