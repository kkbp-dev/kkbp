"""Koikatsu Sunshine (KKS). It differs from KK only in what the bundle already says, and in its
Maker Light: Koikano/main_eyew bakes as KK's toon_eyew does with KKS's ambient values
(importer/tools/game_shaders/models.py, `KKS`). The Roles whose shaders aren't modelled yet use the
legacy edit templates, as KK's do (issue 30)."""

from . import kk

GAME = "KKS"
EXTENDS = "KK"

# The ambient colour, its strength and the shadow's floor, fitted to the KKS Golden Sample's bakes.
_MAKER_LIGHT = {"ambient": [0.225, 0.216, 0.203, 1.0], "ambient_strength": 0.175, "shadow_floor": 0.2}

EDIT = {**kk.EDIT, "values": [*kk.EDIT["values"], ["", _MAKER_LIGHT]]}
