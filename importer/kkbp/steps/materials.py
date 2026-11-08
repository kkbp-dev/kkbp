"""Material Steps: Material Templates for every bundle material, the textures Outfits put on the body,
what expressions change on materials, and the scene settings the templates assume.
"""

from __future__ import annotations

from collections import defaultdict

import bpy

from .. import templates
from .mesh import FACE_PARTS, add_driver, material_id

# Every nth pixel in each direction is sampled for a material's viewport colour.
COLOR_SAMPLE_STEP = 200


def apply_templates(ctx):
    """Rebuilds every glTF placeholder material from its Material Template (docs/design/material-template.md)."""
    ch, bundle = ctx.character, ctx.bundle
    placeholders = {}
    for obj in ch.parts():
        if obj.type != "MESH":
            continue
        for slot in obj.material_slots:
            if slot.material is not None and slot.material.get(templates.TEMPLATE) is None:
                placeholders[slot.material.name] = slot.material
    for placeholder in placeholders.values():
        id = placeholder.get("id")
        bundle_material = bundle.material(id) if isinstance(id, str) else None
        if bundle_material is None:
            ctx.log.warning(f"Material {placeholder.name} isn't in materials.json, so it keeps glTF's placeholder")
            continue
        templates.apply(ch, placeholder, bundle_material, warn=ctx.log.warning)


def apply_outfit_body_textures(ctx):
    """Puts the textures the first Outfit sets on body materials, such as the alpha mask that hides
    skin under its clothes, into those materials."""
    ch, bundle = ctx.character, ctx.bundle
    outfits = sorted((p for p in bundle.passes if p.kind == "outfit"), key=lambda p: p.outfit)
    if not outfits:
        return
    for body_texture in outfits[0].body_textures:
        mat = ch.material(body_texture.material)
        if mat is None:
            continue
        slot = templates.slot_of(ch, body_texture.texture)
        if slot is None or not templates.set_texture(ch, mat, slot, body_texture.texture):
            ctx.log.info(f"Outfit {outfits[0].outfit:02d}'s {body_texture.texture.raw} has no slot in "
                         f"{body_texture.material}'s template")


def drive_material_changes(ctx):
    """Drives what expressions change on materials (docs/design/export-bundle.md, "Expressions"):
    which pattern a material shows, each pattern's animation values, and hiding the meshes an
    expression `hides` (such as the pupils behind gag eyes)."""
    ch, bundle, profile = ctx.character, ctx.bundle, ctx.profile
    picks = defaultdict(list)  # material -> [(expression key owner, target, pattern index)]
    hides = defaultdict(list)  # material -> [(owner, target)]
    for effect in bundle.expressions.effects:
        owner = _expression_owner(ch, effect.target)
        if owner is None:
            ctx.log.warning(f"Expression {effect.target} has effects but no shape key")
            continue
        for change in effect.material_changes:
            mat = ch.material(change.material)
            if mat is None or mat.get(templates.TEMPLATE) is None:
                continue
            pattern_slot = templates.template_of(mat).patterns
            names = templates.patterns(mat)
            for texture in change.textures:
                if pattern_slot is None or texture.pattern not in names:
                    continue
                index = names.index(texture.pattern)
                picks[mat].append((owner, effect.target, index))
                _set_pattern_values(ctx, mat, index, change, profile)
        for mesh_id in effect.hides:
            mesh = bundle.mesh(mesh_id)
            for material in (mesh.materials if mesh else ()):
                mat = ch.material(material)
                if mat is not None and "hidden" in templates.template_of(mat).params:
                    hides[mat].append((owner, effect.target))

    for mat, chosen in picks.items():
        off = templates.choice_value(mat, None)
        terms = [(owner, target, templates.choice_value(mat, index) - off) for owner, target, index in chosen]
        socket = templates.param(mat, templates.template_of(mat).patterns.choice)

        def expression(names, terms=terms, off=off):
            # One expression is on at a time: off + (its value - off).
            return f"{off}" + "".join(f"{delta:+d}*({name}>0)" for name, (_, _, delta) in zip(names, terms))

        _drive(ctx, socket, [(o, t) for o, t, _ in terms], expression)
    for mat, sources in hides.items():
        socket = templates.param(mat, "hidden")
        _drive(ctx, socket, sources, lambda names: f"1 if {' + '.join(names)} > 0 else 0")


def set_viewport_colors(ctx):
    """Gives each material the average colour of its light texture as its Solid-mode colour."""
    for mat in ctx.character.materials():
        node = templates.texture(mat, "main", variant="light") if mat.get(templates.TEMPLATE) else None
        image = node.image if node is not None else None
        if image is not None and image.get("kkbp_key") is not None:
            mat.diffuse_color = _average_color(image)


def set_view_transform(ctx):
    """Standard view transform, as the templates' colours assume (the legacy importer set it too)."""
    scene = bpy.context.scene
    scene.display_settings.display_device = "sRGB"
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"


# --- helpers ------------------------------------------------------------------------------

def _set_pattern_values(ctx, mat, index, change, profile):
    values = {}
    for raw, value in change.floats.items():
        if raw in profile.pattern_values:
            values[profile.pattern_values[raw]] = value
    for raw, vector in change.vectors.items():
        for component, value in zip("xyzw", vector):
            name = profile.pattern_values.get(f"{raw}.{component}")
            if name:
                values[name] = value
    patterns = templates.template_of(mat).patterns
    if not values or patterns.chain is None:
        return
    for name, value in values.items():
        socket = templates.pattern_param(mat, index, name)
        socket.default_value = value


def _drive(ctx, socket, sources, expression):
    targets = [(owner.data.shape_keys, f'key_blocks["{_quote(target)}"].value') for owner, target in sources]
    fcurve = add_driver(socket, "default_value", targets, expression)
    if len(fcurve.driver.expression) > 255:
        ctx.log.warning(f"{socket.node.id_data.name}: the driver for {socket.name} is too long for Blender "
                        f"({len(targets)} expressions)")


def _expression_owner(ch, target):
    for obj in [p for p in (ch.body,) if p] + ch.parts(FACE_PARTS):
        if obj.data.shape_keys and target in obj.data.shape_keys.key_blocks:
            return obj
    return None


def _quote(name):
    return name.replace("\\", "\\\\").replace('"', '\\"')


def _average_color(image):
    """The alpha-weighted average colour of every COLOR_SAMPLE_STEP-th pixel."""
    import numpy as np

    width, height = image.size
    if not width or not height:
        return (0.0, 0.0, 0.0, 1.0)
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    sampled = pixels.reshape((height, width, 4))[::COLOR_SAMPLE_STEP, ::COLOR_SAMPLE_STEP]
    weight = sampled[:, :, 3]
    total = float(weight.sum())
    if total == 0:
        return (0.0, 0.0, 0.0, 1.0)
    rgb = (sampled[:, :, :3] * weight[:, :, None]).sum(axis=(0, 1)) / total
    return (float(rgb[0]), float(rgb[1]), float(rgb[2]), 1.0)


__all__ = ["apply_templates", "apply_outfit_body_textures", "drive_material_changes", "set_viewport_colors",
           "set_view_transform", "material_id"]
