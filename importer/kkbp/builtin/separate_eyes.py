"""Separate Eyes: moves the eyes and the eyebrows out of Body into their own objects, whose
expression keys Body's drive, so they can be drawn through the hair with the compositor (legacy
linkshapekeys, D35; a Hook since issue 16). On the data API: each new object is a copy of Body
keeping only its faces. The new Parts go in an `Eyes and Eyebrows` Collection."""

from __future__ import annotations

import bmesh
from mathutils import Matrix

from ..character import ROLE
from ..pipeline.hooks import hook
from ..pipeline.options import Option
from ..steps.mesh import child_collection, move_to_collection
from .separate import remove_unused_slots

SWITCH = Option("separate_eyes", bool, False, "Separate eyes",
                description="Moves the eyes and eyebrows out of Body into their own objects, with their shape keys "
                            "following Body's, so they can show through the hair with the compositor")

PARTS = {
    "eyes": (("eye_l", "eye_r", "eye_white", "eyeline_upper", "eyeline_lower", "eyeline_shadow"), "Eyes {name}"),
    "eyebrows": (("eyebrow",), "Eyebrows {name}"),
}
OUTLINE = "Outline Modifier"
UV_WARP = "UV_WARP"


@hook(name="Separate Eyes", switch=SWITCH)
def separate_eyes(ctx):
    made = separate(ctx.character)
    ctx.log.info(f"Separated {', '.join(o.name for o in made) or 'nothing'}")


def separate(ch) -> list:
    """Makes the eyes and eyebrows Parts of their own; returns them."""
    body = ch.body
    if body is None:
        raise ValueError(f"{ch.name} has no body")
    made = []
    for role, (material_roles, name) in PARTS.items():
        slots = {i for i, s in enumerate(body.material_slots) if s.material and s.material.get(ROLE) in material_roles}
        if not slots or not any(p.material_index in slots for p in body.data.polygons):
            continue
        part = body.copy()
        part.data = body.data.copy()
        part.name = part.data.name = name.format(name=ch.name)
        for collection in body.users_collection:
            collection.objects.link(part)
        _keep_faces(part, slots)
        remove_unused_slots(part)  # Body keeps its slots: the outline's material offset counts them
        _keep_faces(body, set(range(len(body.material_slots))) - slots)
        ch.add_part(part, role)
        # Its vertices are in Body's space, so it sits on Body with no offset of its own: the copy's
        # transform (Body's, relative to the armature) would otherwise be applied a second time.
        part.parent = body
        part.matrix_parent_inverse = Matrix.Identity(4)
        part.matrix_basis = Matrix.Identity(4)
        for modifier in [m for m in part.modifiers if m.name == OUTLINE]:
            modifier.show_viewport = modifier.show_render = False
        if role != "eyes":
            for modifier in [m for m in part.modifiers if m.type == UV_WARP]:
                part.modifiers.remove(modifier)
        made.append(part)
    if any(p.get(ROLE) == "eyes" for p in made):
        for modifier in [m for m in body.modifiers if m.type == UV_WARP]:  # they move to the eyes
            body.modifiers.remove(modifier)
    for part in made:
        _drive_keys(body, part)
    if made:
        move_to_collection(made, child_collection(ch.collection, f"Eyes and Eyebrows {ch.name}"), hide=False)
    return made


def _keep_faces(obj, slots):
    """Deletes the faces whose material isn't in `slots`, with the vertices only they used, and the
    material slots no face uses any more."""
    bm = bmesh.new()
    try:
        bm.from_mesh(obj.data)
        doomed = [f for f in bm.faces if f.material_index not in slots]
        bmesh.ops.delete(bm, geom=doomed, context="FACES")
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(obj.data)
    finally:
        bm.free()
    obj.data.update()


def _drive_keys(body, part):
    """Each of the part's keys follows Body's key of the same name, value and mute."""
    source = body.data.shape_keys
    keys = part.data.shape_keys
    if source is None or keys is None:
        return
    for key in list(keys.key_blocks)[1:]:
        if key.name not in source.key_blocks:
            continue
        for prop in ("value", "mute"):
            driver = key.driver_add(prop).driver
            driver.type = "AVERAGE"
            for v in list(driver.variables):
                driver.variables.remove(v)
            var = driver.variables.new()
            var.name = prop
            var.type = "SINGLE_PROP"
            var.targets[0].id_type = "KEY"
            var.targets[0].id = source
            quoted = key.name.replace("\\", "\\\\").replace('"', '\\"')
            var.targets[0].data_path = f'key_blocks["{quoted}"].{prop}'
