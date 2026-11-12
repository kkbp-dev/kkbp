"""Koikatsu Sunshine (KKS). It differs from KK only in what the bundle already says, and in how two of
its shaders bake (issue 30, importer/tools/game_shaders/models.py):

- Koikano/main_eyew bakes as KK's toon_eyew with other ambient values (`models.KKS`).
- Koikano/hair_main_sun and hair_main_sun_front, though larger shaders, bake as KK's main_hair and
  main_hair_front with KK's own values, and Koikano/main_eye as KK's toon_eye_lod0 (measured on the
  KKS Golden Sample; not modelled).

The Roles whose shaders aren't modelled yet use the legacy edit templates, as KK's do."""

from . import kk

GAME = "KKS"
EXTENDS = "KK"

# Koikano/main_eyew's Maker Light: the ambient colour, its strength and the shadow's floor, fitted to
# the KKS Golden Sample's bakes.
_EYEW_LIGHT = {"ambient": [0.225, 0.216, 0.203, 1.0], "ambient_strength": 0.175, "shadow_floor": 0.2}

EDIT = {**kk.EDIT, "values": [
    *kk.EDIT["values"],
    ["shader:main_eyew", _EYEW_LIGHT],
    ["shader:hair_main_sun_front", {"front": 1.0}],
]}
