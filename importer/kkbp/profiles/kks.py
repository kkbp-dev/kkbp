"""Koikatsu Sunshine (KKS). It differs from KK only in what the bundle already says, and in how some of
its shaders bake (importer/tools/game_shaders/models.py):

- Koikano/main_eyew bakes as KK's toon_eyew with other ambient values (`models.KKS`).
- Koikano/hair_main_sun and hair_main_sun_front, though larger shaders, bake as KK's main_hair and
  main_hair_front with KK's own values, and Koikano/main_eye as KK's toon_eye_lod0.
- Koikano/main_clothes_opaque comes closest as KK's main_opaque with KK's values, and Koikano/main_skin
  as KK's main_skin with its own (`models.KKS_SKIN`). Both blend in a physically based term and
  light probes KK's don't have; KK's templates bake them closer than the legacy ones, not exactly.
- Koikano/main_clothes_item (the teeth, the tongue) comes closest as KK's main_item without its
  line-mask darkening; its fourth colour and detail overlay change nothing in the sample.
- Koikano/create_topN, create_skinbody and create_skinface composite as KK's create shaders.

These are measured on the KKS Golden Sample, not modelled."""

from . import kk

GAME = "KKS"
EXTENDS = "KK"

# Koikano/main_eyew's and Koikano/main_skin's Maker Lights: the ambient colour, its strength and the
# shadow's floor, fitted to the KKS Golden Sample's bakes.
_EYEW_LIGHT = {"ambient": [0.225, 0.216, 0.203, 1.0], "ambient_strength": 0.175, "shadow_floor": 0.2}
_SKIN_LIGHT = {"ambient": [0.145, 0.145, 0.145, 1.0], "ambient_strength": 0.07, "shadow_floor": 0.28}

EDIT = {**kk.EDIT, "shader_templates": {**kk.EDIT["shader_templates"], "main_clothes_opaque": "KK main_opaque",
                                         "main_clothes_item": "KK main_item"},
        "values": [
    *kk.EDIT["values"],
    ["shader:main_eyew", _EYEW_LIGHT],
    ["shader:main_skin", _SKIN_LIGHT],
    # Koikano/main_clothes_item doesn't darken by the line mask's blue, as KK's main_item does.
    ["shader:main_clothes_item", {"line_blue": 0.0}],
    ["shader:hair_main_sun_front", {"front": 1.0}],
]}
