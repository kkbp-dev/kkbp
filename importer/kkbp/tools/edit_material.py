"""Edit material: swaps a Light Dark material for an editable copy of its legacy edit template, which
rebuilds the game's colouring from the bundle's textures, the Create Material and the material's
colours, so they can be changed and baked again (D37-D46, ADR 0025).

    edit(ch, material)     # the edit material, made once and reused
    cancel(edit_material)  # back to the original; the edit copy goes
    reset(ch, edit_material)
    save(ch, edit_material)  # bakes light and dark into the original, then cancels

What fills each slot and parameter is the Game Profile's EDIT tables; which node is which is the
Template Descriptions'. The colour maths is kkbp/shading/. Saturated and dark textures are written
into the Cache (`kkbp_cache/edit/`), so a second edit reuses them.
"""

from __future__ import annotations

import hashlib

import bpy
import numpy as np

from .. import profiles, shading, templates
from ..character import ID

EDIT_OF = "kkbp_edit_of"  # on an edit material: the name of the material it edits
EDIT_KEY = "kkbp_edit_key"  # on an edit material: its Character's Key (not KEY: it isn't a bundle material)
FILLED = "kkbp_edit_filled"  # on an edit material: the slots edit() filled
NAME = "Edit {}"
CACHE = "edit"
# D42, ADR 0026: edit materials saturate their main textures and colours through the game's colour
# grade, as legacy did, only for the profile's `saturated_roles` unless asked. Measured on the KK and
# KKS samples, the others bake closer to the bundle's own light and dark textures without it.


class EditError(Exception):
    pass


# --- which material ----------------------------------------------------------------------------

def template_for(profile, bundle_material) -> str | None:
    """The edit template for a bundle material, or None if it can't be edited."""
    if bundle_material.blend_mode in profile.edit.not_editable_blend_modes:
        return None
    return profile.edit.templates.get(bundle_material.role)


def saturates(profile, bundle_material) -> bool:
    """Whether an edit of this bundle material saturates when the user doesn't say (ADR 0026)."""
    return bundle_material.role in profile.edit.saturated_roles


def is_edit(material) -> bool:
    return material is not None and EDIT_OF in material


def original(edit_material):
    """The material an edit material edits."""
    return bpy.data.materials.get(edit_material[EDIT_OF])


def edit_of(material):
    """The edit material of `material`, or None."""
    return next((m for m in bpy.data.materials if m.get(EDIT_OF) == material.name), None)


def editable(ch, material) -> str | None:
    """Why `material` can't be edited, or None if it can."""
    if is_edit(material):
        return None
    if material.get(ID) is None:
        return f"{material.name} isn't a KKBP material"
    bm = ch.bundle().material(material[ID])
    if bm is None:
        return f"{material.name} isn't in {ch.name}'s Export Bundle"
    profile = profiles.get(ch.game)
    if not profile.edit.templates:
        return f"Edit material isn't available for {ch.game} yet"
    if template_for(profile, bm) is None:
        return f"{material.name} ({bm.role or bm.blend_mode}) has no edit template"
    return None


# --- edit, cancel, reset -----------------------------------------------------------------------

def edit(ch, material, *, saturate: bool | None = None, log=print):
    """The edit material for `material`, put in its place everywhere it is used. A material that
    is being edited already gives its edit material back."""
    if is_edit(material):
        return material
    reason = editable(ch, material)
    if reason:
        raise EditError(reason)
    existing = edit_of(material)
    if existing is not None:
        material.user_remap(existing)
        material.use_fake_user = True
        existing.use_fake_user = False
        return existing

    profile = profiles.get(ch.game)
    bm = ch.bundle().material(material[ID])
    if saturate is None:
        saturate = saturates(profile, bm)
    name = template_for(profile, bm)
    mat = templates.template_material(name).copy()
    mat.use_fake_user = False
    mat.name = NAME.format(material.name)
    mat[templates.TEMPLATE] = name
    mat[EDIT_OF] = material.name
    mat[EDIT_KEY] = ch.key
    mat.surface_render_method = material.surface_render_method
    mat.use_transparent_shadow = material.use_transparent_shadow
    templates.copy_groups(mat)

    filled = _fill_textures(ch, mat, material, bm, profile, saturate, log)
    mat[FILLED] = sorted(filled)
    _set_colors(mat, bm, profile, saturate)
    _set_values(mat, bm, profile, filled)

    material.user_remap(mat)  # moves the fake user too, so it is set after
    material.use_fake_user = True  # kept while its slots hold the edit material
    mat.use_fake_user = False
    return mat


def cancel(edit_material):
    """Puts the original material back everywhere and removes the edit material and its groups."""
    source = original(edit_material)
    if source is not None:
        edit_material.user_remap(source)
        source.use_fake_user = False
    groups = templates.own_groups(edit_material)
    bpy.data.materials.remove(edit_material)
    for group in reversed(groups):
        if group.users == 0:
            bpy.data.node_groups.remove(group)
    return source


def reset(ch, edit_material, **kwargs):
    """A fresh edit material in place of `edit_material`, from the bundle again."""
    return edit(ch, cancel(edit_material), **kwargs)


def save(ch, edit_material, *, log=print):
    """Bakes the edit material's light and dark versions into the original Light Dark material,
    then removes the edit material. Returns the original."""
    from . import bake  # it renders, so only saving loads it

    source = original(edit_material)
    current = templates.texture(source, "main", "light")
    size = tuple(current.image.size) if current is not None and current.image is not None else (0, 0)
    light, dark = bake.bake(ch, edit_material, source.name, at_least=size, log=log)
    for variant, image in (("light", light), ("dark", dark)):
        node = templates.texture(source, "main", variant)
        if node is not None:
            node.image = image
    cancel(edit_material)
    return source


# --- textures --------------------------------------------------------------------------------

def _fill_textures(ch, mat, material, bm, profile, saturate, log):
    rules = profile.edit
    slots = set(templates.slots(mat))
    found = {}
    for slot, sources in rules.textures.items():
        if slot in slots:
            hit = _texture(material, bm, sources)
            if hit is not None:
                found[slot] = hit
    if bm.shader in rules.plain_color_mask_shaders and "color_mask" in found and "color_mask.plain" in slots:
        found["color_mask.plain"] = found.pop("color_mask")

    lut = _lut() if saturate else None
    owner = material.get(ID, material.name)
    for slot, hit in found.items():
        if isinstance(hit, bpy.types.Image):  # current: the image the material already shows
            templates.texture_node(mat, slot).image = hit
        elif saturate and slot in rules.saturated:
            image = _derived(ch, hit, "saturated", lambda px: shading.saturate(px, lut))
            _put(mat, slot, image, hit)
        else:
            templates.set_texture(ch, mat, slot, hit, owner=owner)
            templates.set_position(mat, slot, hit.offset, hit.scale)
    if "main" in found and "main.dark" in slots and not isinstance(found["main"], bpy.types.Image):
        main, shadow = found["main"], _shadow(bm, profile)
        tag = "saturated." if saturate else ""
        dark = _derived(ch, main, f"{tag}dark.{_hash(shadow)}",
                        lambda px: shading.dark_pixels(shading.saturate(px, lut) if saturate else px, shadow))
        _put(mat, "main.dark", dark, main)
        found["main.dark"] = main
    log(f"{mat.name}: filled {', '.join(sorted(found)) or 'no slots'}")
    return set(found)


def _texture(material, bm, sources):
    """The first source that has a texture: a bundle Texture, or (for `current`) an image."""
    for s in sources:
        if s.where == "current":
            node = templates.texture(material, s.key) if not s.raw else None
            if node is not None and node.image is not None:
                return node.image
            continue
        holder = bm.create if s.where == "create" else bm
        if holder is None:
            continue
        if s.raw:
            hits = [t for t in holder.textures_for(s.key) if t.variant is None and t.pattern == s.pattern]
        else:
            hits = [t for t in holder.textures_with_role(s.key) if t.variant is None and t.pattern == s.pattern]
        if hits:
            return hits[0]
    return None


def _put(mat, slot, image, texture):
    node = templates.texture_node(mat, slot)
    node.image = image
    if not templates.set_position(mat, slot, texture.offset, texture.scale):
        node.texture_mapping.translation[:2] = texture.offset
        node.texture_mapping.scale[:2] = texture.scale


def _derived(ch, texture, kind, make):
    """The image `make` turns a bundle texture's pixels into, written once into the Cache."""
    id = f"{CACHE}/{texture.file.stem}.{kind}.png"
    image = ch.image(id)
    if image is not None:
        return image
    path = ch.bundle().cache_dir(CACHE) / f"{texture.file.stem}.{kind}.png"
    if not path.is_file():
        source = bpy.data.images.load(str(texture.file), check_existing=False)
        try:
            pixels = _pixels(source)
            out = bpy.data.images.new(path.name, source.size[0], source.size[1], alpha=True)
            out.pixels.foreach_set(make(pixels).ravel())
            out.filepath_raw = str(path)
            out.file_format = "PNG"
            out.save()
            bpy.data.images.remove(out)
        finally:
            bpy.data.images.remove(source)
    image = bpy.data.images.load(str(path), check_existing=False)
    image.name = path.name
    image.pack()
    ch.tag_image(image, id)
    return image


def _pixels(image) -> np.ndarray:
    w, h = image.size
    pixels = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    return pixels.reshape(h, w, 4)


def _lut():
    return _pixels(templates.extra("lut"))


def _hash(color) -> str:
    return hashlib.sha1(",".join(f"{c:.4f}" for c in color[:3]).encode()).hexdigest()[:8]


# --- colours and values ------------------------------------------------------------------------

def _shadow(bm, profile):
    return _color(bm, profile.edit.shadow) or shading.DEFAULT_SHADOW


def _color(bm, sources):
    for s in sources:
        holder = bm.create if s.where == "create" else bm if s.where == "own" else None
        if holder is not None and s.key in holder.colors:
            return holder.colors[s.key]
    return None


def _set_colors(mat, bm, profile, saturate):
    lut = _lut() if saturate else None
    shadow = _shadow(bm, profile)
    out = (lambda c: shading.saturate_color(c, lut)) if saturate else _linear
    params = templates.template_of(mat).params
    for c in profile.edit.colors.get(mat[templates.TEMPLATE], ()):
        color = _color(bm, c.sources)
        if color is None:
            continue
        if c.how in ("item", "skin"):
            dark = shading.skin_dark_color(color) if c.how == "skin" else shading.dark_color(color, shadow)
            _set(mat, f"{c.param}.light", out(color))
            _set(mat, f"{c.param}.dark", out(dark))
            continue
        value = {"light": lambda: out(color), "dark": lambda: out(shading.dark_color(color, shadow)),
                 "eyew_dark": lambda: out(shading.eyew_dark_color(color, shadow)),
                 "plain": lambda: _linear(color), "alpha": lambda: float(color[3])}[c.how]()
        for name in ([c.param] if c.param in params else [f"{c.param}.light", f"{c.param}.dark"]):
            _set(mat, name, value)


def _set_values(mat, bm, profile, filled):
    params = templates.template_of(mat).params
    raws = {t.raw for t in bm.textures} | ({t.raw for t in bm.create.textures} if bm.create else set())
    for terms, values in profile.edit.values:
        if not all(_holds(term, bm, raws, filled) for term in terms):
            continue
        for name, value in values.items():
            for p in ([name] if name in params else [f"{name}.light", f"{name}.dark"]):
                if p in params:
                    _set(mat, p, tuple(value) if isinstance(value, (list, tuple)) else value)


def _holds(term, bm, raws, filled):
    kind, _, value = term.partition(":")
    return {"role": lambda: bm.role == value, "raw": lambda: value in raws,
            "missing": lambda: value not in filled, "has": lambda: value in filled}[kind]()


def _set(mat, name, value):
    templates.param(mat, name).default_value = value


def _linear(color):
    c = np.asarray(color[:3], dtype=np.float64)
    lin = np.where(c <= 0.04045, c / 12.92, ((np.maximum(c, 0) + 0.055) / 1.055) ** 2.4)
    return (*(float(v) for v in lin), 1.0)
