"""Link hair (D45): every hair material of the Character goes into edit and takes the active hair
edit material's light and dark settings, so all the hair can be recoloured at once."""

from __future__ import annotations

from .. import templates
from ..character import ROLE
from . import edit_material


def can_link(material) -> bool:
    """Whether `material` is a hair material being edited."""
    source = edit_material.original(material) if edit_material.is_edit(material) else None
    return source is not None and source.get(ROLE) == "hair"


def link_hair(ch, source, *, log=print) -> list:
    """Copies `source`'s (a hair edit material) params to every other hair material, put into edit
    first. Returns the edit materials it changed."""
    if not can_link(source):
        raise edit_material.EditError(f"{source.name} isn't a hair material being edited")
    original = edit_material.original(source)
    params = [name for name in templates.template_of(source).params if name.endswith((".light", ".dark"))]
    linked = []
    for mat in ch.materials("hair"):
        if mat == original or not _used(mat):
            continue
        edit = edit_material.edit(ch, mat, log=log)
        for name in params:
            templates.param(edit, name).default_value = templates.param(source, name).default_value
        linked.append(edit)
    log(f"Linked {len(linked)} hair materials to {source.name}")
    return linked


def _used(material):
    return material.users > (1 if material.use_fake_user else 0)
