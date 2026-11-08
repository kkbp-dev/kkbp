"""Summer Vacation Scramble (SVS). Data only; see profiles/__init__.py for what each field means."""

from . import kk

GAME = "SVS"
EXTENDS = "KK"

TEMPLATE_SET = "SVS"

RAW_TEXTURES = {
    "_Cloth_alpha_bot": "alpha_mask_bottom",  # the lower half of the body alpha mask an Outfit sets
}

# As KK's, with SVS's most common legacy aimed-bone length.
BONES = {**kk.BONES, "aim_length": 0.077}

# No edit templates yet (D46).
EDIT = {**kk.EDIT, "templates": {}}
