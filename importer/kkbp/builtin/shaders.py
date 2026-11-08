"""Convert shaders: puts one of the templates' shader variants in place of the Eevee shader, with the
legacy importer's adjustments by Material Role (legacy `apply_cycles`, `apply_eeveemod` and
`apply_principled`, D18). Everything goes through `templates`; no node is looked up by name.
"""

from collections import defaultdict

import bpy
from mathutils import Vector

from .. import templates
from ..character import ROLE
from ..pipeline.hooks import hook
from ..pipeline.options import Option

SWITCH = Option(
    "convert_shaders", str, "off", "Shader",
    description="Which shaders the Character's materials use",
    choices=(("off", "Eevee", "Keeps the Eevee shaders"),
             ("eevee_mod", "Eevee+", "Uses a modified shader setup for Eevee"),
             ("cycles", "Cycles (toon)", "Toon shaders for Cycles"),
             ("cycles_classic", "Cycles (classic)", "The classic shaders for Cycles"),
             ("principled", "Principled BSDF", "A very simple material setup")))

# The Parts whose materials are converted: the legacy importer's body, hair, clothes and
# alternate clothes. The tears, gag eyes and tongue keep their own templates.
PARTS = ("body", "hair", "outfit", "alt_outfit")

# Cycles: these draw without shadows (legacy `shadowless_mats`).
CYCLES_SHADOWLESS = ("eyeline_upper", "eyeline_lower", "eyebrow")
# Cycles: the eyelines move forward a little so they don't sink into the face (metres, legacy).
CYCLES_EYELINE_OFFSET = {"eyeline_lower": 0.0002, "eyeline_upper": 0.0003}
CYCLES_PREVIEW_SAMPLES = 10

# Eevee Mod: these keep the Eevee shader and are always lit (legacy `ignore_list`).
EEVEE_MOD_KEPT = ("eyebrow", "eye_l", "eye_r", "eyeline_upper", "eye_white")
ALWAYS_LIT = (1.0, 0.0, 0.0, 1.0)  # a pure red permalight mask
EEVEE_MOD_FRESNEL_OFF = "Disable fresnel"
LIGHT_ROTATION_MODIFIER = "Light Rotation Catcher"
# Eevee Mod: the faces whose normals are reset, so no ambient-occlusion seam shows at the neck.
EEVEE_MOD_NORMALS = ("face", "body")


@hook(name="Convert shaders", switch=SWITCH)
def convert_shaders(ctx):
    ch, variant = ctx.character, ctx.options.convert_shaders
    materials = [m for m in ch.materials(parts=PARTS) if _has_variants(m)]
    if variant in ("cycles", "cycles_classic"):
        _cycles(ctx, materials, variant)
    elif variant == "eevee_mod":
        _eevee_mod(ctx, materials)
    elif variant == "principled":
        _swap_all(ctx, materials, "principled")


def _cycles(ctx, materials, variant):
    ch = ctx.character
    shadowless = [m for m in materials if m.get(ROLE) in CYCLES_SHADOWLESS]
    _swap_all(ctx, [m for m in materials if m not in shadowless], variant)
    _swap_all(ctx, shadowless, "cycles_no_shadows")
    black = templates.extra("black")
    for mat in materials:
        for slot in templates.template_of(mat).textures:
            node = templates.texture_node(mat, slot)
            if node is not None and node.image is None:
                node.image = black  # Cycles shows a missing image pink
    if ch.body is not None:
        _move_faces(ch.body, {m: Vector((0.0, -CYCLES_EYELINE_OFFSET[m.get(ROLE)], 0.0))
                              for m in materials if m.get(ROLE) in CYCLES_EYELINE_OFFSET})
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.preview_samples = CYCLES_PREVIEW_SAMPLES


def _eevee_mod(ctx, materials):
    ch = ctx.character
    kept = [m for m in materials if m.get(ROLE) in EEVEE_MOD_KEPT]
    _swap_all(ctx, [m for m in materials if m not in kept], "eevee_mod")
    for mat in kept:
        socket = templates.param(mat, "permalight_mask")
        for link in list(socket.links):
            mat.node_tree.links.remove(link)
        socket.default_value = ALWAYS_LIT
    body = ch.body
    on_body = {s.material for s in body.material_slots if s.material} if body else set()
    for mat in [m for m in materials if m not in kept]:
        if mat in on_body:
            templates.param(mat, "fresnel").default_value = EEVEE_MOD_FRESNEL_OFF
        role = mat.get(ROLE)
        if role == "body":
            node = templates.texture_node(mat, "permalight_mask")
            if node is not None:
                node.image = templates.extra("neck_shadow")
            templates.param(mat, "disable_permalight_mask").default_value = True
        elif role == "face":
            if body is not None and LIGHT_ROTATION_MODIFIER not in body.modifiers:
                modifier = body.modifiers.new(LIGHT_ROTATION_MODIFIER, "NODES")
                modifier.node_group = templates.extra("light_rotation")
                modifier.show_expanded = False
            sdf = mat.node_tree.nodes.new("ShaderNodeGroup")
            sdf.node_tree = templates.extra("sdf")
            sdf.name = sdf.label = "sdf"
            mat.node_tree.links.new(sdf.outputs[0], templates.param(mat, "permalight_mask"))
            templates.param(mat, "disable_permalight_mask").default_value = True
    if body is not None:
        _reset_normals(body, set(ch.materials(roles=EEVEE_MOD_NORMALS)))


def _swap_all(ctx, materials, variant):
    lost = defaultdict(set)
    count = 0
    for mat in materials:
        template = templates.template_of(mat)
        if variant not in template.variants:
            continue
        for name in templates.swap(mat, variant):
            lost[template.name].add(name)
        count += 1
    for template, names in sorted(lost.items()):
        many = len(names) > 1
        ctx.log.warning(f"The {variant} shader has no {' or '.join(sorted(names))} input{'s' if many else ''}, "
                        f"so {template} materials lose {'them' if many else 'it'}")
    ctx.log.info(f"{count} materials use the {variant} shader")


def _has_variants(mat):
    return mat.get(templates.TEMPLATE) is not None and bool(templates.template_of(mat).variants)


def _move_faces(obj, offsets):
    """Moves the vertices of the faces with each material by its offset, in every shape key too."""
    mesh = obj.data
    by_index = {i: offsets[s.material] for i, s in enumerate(obj.material_slots) if s.material in offsets}
    moves = {}
    for poly in mesh.polygons:
        if poly.material_index in by_index:
            for v in poly.vertices:
                moves[v] = by_index[poly.material_index]
    layers = [mesh.vertices] + ([k.data for k in mesh.shape_keys.key_blocks] if mesh.shape_keys else [])
    for layer in layers:
        for v, offset in moves.items():
            layer[v].co += offset


def _reset_normals(obj, materials):
    """Resets the custom normals of the faces with these materials to the mesh's own."""
    mesh = obj.data
    slots = {i for i, s in enumerate(obj.material_slots) if s.material in materials}
    if not slots or not mesh.has_custom_normals:
        return
    normals = [tuple(n.vector) for n in mesh.corner_normals]
    for poly in mesh.polygons:
        if poly.material_index in slots:
            for loop in poly.loop_indices:
                normals[loop] = (0.0, 0.0, 0.0)  # zero means "the mesh's own normal"
    mesh.normals_split_custom_set(normals)
