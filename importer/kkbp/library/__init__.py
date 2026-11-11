"""The Material Template library: library.blend, the Template Descriptions and the Template Sets
(docs/design/material-template.md).

A Template Description says which texture slot goes to which image node and which named parameter
is which node socket, so code never names nodes or sockets. A Template Set picks a template per
material from its Material Role and Blend Mode. `templates` (the bpy side) uses both.

This package never imports bpy and uses relative imports only, so host tests import it directly.
library.blend is built by scripts/build-library.sh (ADR 0040); a harness test checks every
description against it.
"""

from __future__ import annotations

from pathlib import Path

from .descriptions import EDIT_TEMPLATES, POSITION_SOCKETS, TEMPLATES, Chain, Patterns, Template
from .sets import SETS, Row, TemplateSet, choose, resolve

LIBRARY = Path(__file__).resolve().parent / "library.blend"
# Datablocks in library.blend that aren't part of a template, which the convert-shaders Hook adds:
# name -> (kind, datablock name).
EXTRAS = {
    "black": ("images", "Template: Black"),  # Cycles shows a missing image pink; this fills it
    "neck_shadow": ("images", "Template: Body neck shadow"),  # Eevee Mod: the face's shadow on the neck
    "sdf": ("node_groups", ".SDF_Cel_Shader"),  # Eevee Mod: the face's signed-distance-field shading
    "light_rotation": ("node_groups", ".Light Rotation Catcher"),  # Eevee Mod: geometry nodes the SDF reads
    "lut": ("images", "Lut_TimeDay.png"),  # edit materials: the game's colour grade (D42)
}
TEMPLATE_VERSION = 1  # the kkbp_template_version every template and group in library.blend carries
VERSION_PROP = "kkbp_template_version"


def slot(role: str | None, variant: str | None = None) -> str | None:
    """The texture slot name of a Texture Role and Variant: `main`, `main.light`, `alpha_mask`."""
    if role is None:
        return None
    return role if variant is None else f"{role}.{variant}"


__all__ = ["EDIT_TEMPLATES", "EXTRAS", "POSITION_SOCKETS", "LIBRARY", "SETS", "TEMPLATES", "TEMPLATE_VERSION", "VERSION_PROP", "Chain", "Patterns", "Row",
           "Template", "TemplateSet", "choose", "resolve", "slot"]
