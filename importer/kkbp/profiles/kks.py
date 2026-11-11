"""Koikatsu Sunshine (KKS). It differs from KK only in what the bundle already says, and in its
shaders: until they are modelled (issue 30), its edit materials use the legacy templates."""

from . import kk

GAME = "KKS"
EXTENDS = "KK"

EDIT = {**kk.EDIT, "templates": kk.LEGACY_EDIT_TEMPLATES, "saturated_roles": ["hair", "eyebrow"]}
