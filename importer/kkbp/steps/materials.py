"""Material Steps: Material Templates for every bundle material, the textures Outfits put on the body,
what expressions change on materials, and the scene settings the templates assume.
"""

from __future__ import annotations

from collections import defaultdict

import bpy

from .. import outfit_textures, templates
from . import gag
from .mesh import FACE_PARTS, drive_param, material_id

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
    skin under its clothes, into those materials. With more than one Outfit, each of those materials
    also stores every Outfit's, so showing another Outfit puts its own in (ADR 0055)."""
    ch, bundle = ctx.character, ctx.bundle
    outfits = sorted((p for p in bundle.passes if p.kind == "outfit"), key=lambda p: p.outfit)
    if not outfits:
        return
    filled = defaultdict(dict)  # (material, slot) -> {Outfit: its texture}
    for p in outfits:
        for body_texture in p.body_textures:
            mat = ch.material(body_texture.material)
            if mat is None:
                continue
            slot = templates.slot_of(ch, body_texture.texture)
            if slot is None or templates.texture_node(mat, slot) is None:
                ctx.log.info(f"Outfit {p.outfit:02d}'s {body_texture.texture.raw} has no slot in "
                             f"{body_texture.material}'s template")
                continue
            filled[(mat, slot)][p.outfit] = body_texture.texture
    for (mat, slot), by_outfit in filled.items():
        node = templates.texture_node(mat, slot)
        own = (node.image, tuple(node.texture_mapping.translation[:2]), tuple(node.texture_mapping.scale[:2]))
        for p in outfits:
            texture = by_outfit.get(p.outfit)
            if texture is not None:  # loads it; the first Outfit's goes back in below
                owner = f"{material_id(mat)} Outfit {p.outfit:02d}" if len(outfits) > 1 else None
                templates.set_texture(ch, mat, slot, texture, owner=owner)
            if len(outfits) > 1:
                image, offset, scale = (node.image, texture.offset, texture.scale) if texture is not None else own
                outfit_textures.store(mat, ch.key, slot, p.outfit, image, offset, scale)
        outfit_textures.put(mat, outfits[0].outfit)


def drive_material_changes(ctx):
    """Drives what expressions change on materials (docs/design/export-bundle.md, "Expressions"):
    which pattern a material shows, each pattern's animation values, and hiding the meshes an
    expression `hides` (such as the pupils behind gag eyes)."""
    ch, bundle, profile = ctx.character, ctx.bundle, ctx.profile
    picks = defaultdict(list)  # material -> [(expression key owner, target, pattern index)]
    hides = defaultdict(list)  # material -> [(owner, target)]
    # Once the gag keys are one key, its dropdown picks the gag expression (ADR 0042): drive_gag_eyes
    # picks their patterns, and the meshes they hide are hidden while it picks one of them.
    picked = gag.selection(ch, bundle)
    gag_targets = set(picked.expressions) if picked else set()
    gag_hides = defaultdict(list)  # material -> [gag expression]
    for effect in bundle.expressions.effects:
        if effect.target in gag_targets:
            for mesh_id in effect.hides:
                for mat in _hideable(ch, bundle, mesh_id):
                    gag_hides[mat].append(effect.target)
            continue
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
                gag.set_pattern_values(mat, index, change, profile)
        for mesh_id in effect.hides:
            for mat in _hideable(ch, bundle, mesh_id):
                hides[mat].append((owner, effect.target))

    for mat, chosen in picks.items():
        off = templates.choice_value(mat, None)
        terms = [(owner, target, templates.choice_value(mat, index) - off) for owner, target, index in chosen]

        def expression(names, terms=terms, off=off):
            # One expression is on at a time: off + (its value - off).
            return f"{off}" + "".join(f"{delta:+d}*({name}>0)" for name, (_, _, delta) in zip(names, terms))

        _drive(ctx, mat, templates.template_of(mat).patterns.choice, _key_targets([(o, t) for o, t, _ in terms]),
               expression, start=off)
    for mat in list(hides) + [m for m in gag_hides if m not in hides]:
        sources, gags = hides.get(mat, []), gag_hides.get(mat, [])
        targets = _key_targets(sources) + (picked.targets if gags else [])

        def expression(names, count=len(sources), gags=gags):
            tests = [f"{' + '.join(names[:count])} > 0"] if count else []
            if gags:
                tests.append(picked.on(names[count:], gags))
            return f"1 if {' or '.join(tests)} else 0"

        _drive(ctx, mat, "hidden", targets, expression, keep=True)


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

def _hideable(ch, bundle, mesh_id):
    """The materials of bundle mesh `mesh_id` whose templates can be hidden."""
    mesh = bundle.mesh(mesh_id)
    found = []
    for material in (mesh.materials if mesh else ()):
        mat = ch.material(material)
        if mat is not None and "hidden" in templates.template_of(mat).params:
            found.append(mat)
    return found


def _key_targets(sources):
    return [(owner.data.shape_keys, f'key_blocks["{_quote(target)}"].value') for owner, target in sources]


def _drive(ctx, mat, name, targets, expression, start=0, keep=False):
    """Drives the material's parameter `name` on every object of the Character that uses the material."""
    drivers = drive_param(ctx.character, mat, name, targets, expression, start, keep)
    if drivers and len(drivers[0].driver.expression) > 255:
        ctx.log.warning(f"{mat.name}: the driver for {name} is too long for Blender ({len(targets)} expressions)")


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
