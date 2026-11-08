"""Koikatsu (KK). Data only; see profiles/__init__.py for what each field means."""

GAME = "KK"
EXTENDS = None

TEMPLATE_SET = "KK"

# Raw Properties with no Texture Role that a template has a slot for.
RAW_TEXTURES = {
    "_expression": "expression",  # the eyes' expression overlays (cf_t_expression_00, _01)
}

# Material values an expression sets (its material_changes) that a template has a parameter for.
# A vector's component is written `.x`, `.y`, `.z` or `.w`.
PATTERN_VALUES = {
    "_AngleSpeed": "angle_speed",
    "_SizeSpeed": "size_speed",
    "_SizeWidth": "size_width",
    "_TileAnimation.x": "tile_x",
    "_TileAnimation.y": "tile_y",
}

_LIMB_ROLES = [
    "body_root", "hips", "spine", "chest", "upper_chest", "neck", "head",
    "left_shoulder", "right_shoulder", "left_upper_arm", "right_upper_arm",
    "left_lower_arm", "right_lower_arm", "left_hand", "right_hand",
    "left_upper_leg", "right_upper_leg", "left_lower_leg", "right_lower_leg",
    "left_foot", "right_foot", "left_toes", "right_toes",
    "left_hand_ik", "right_hand_ik", "left_foot_ik", "right_foot_ik",
    "left_elbow_pole", "right_elbow_pole", "left_knee_pole", "right_knee_pole",
]
_FINGER_ROLES = [f"{side}_{finger}_{joint}" for side in ("left", "right")
                 for finger in ("thumb", "index", "middle", "ring", "little")
                 for joint in ("proximal", "intermediate", "distal")]

# Bone tails and roll (ADR 0017). The lengths are the legacy importer's.
BONES = {
    "aim_length": 0.074,
    "upright": [
        {"roles": _LIMB_ROLES + _FINGER_ROLES, "length": 0.1},
        {"groups": ["eye", "eyebrow"], "length": 0.01},
        {"groups": ["mouth"], "outside": "tongue_root", "length": 0.01},
        {"groups": ["face"], "under": "face_root", "length": 0.01},
        {"roles": ["face_root"], "length": 0.01},
        {"groups": ["nsfw"], "length": 0.02},
        {"groups": ["hair", "accessory"], "length": 0.05},
    ],
    "chains": {"skirt": 0.05},
}

# The eyes' highlights, from the colours the game draws them with (D41).
_EYE_COLORS = [
    ["highlight_up_color", ["own:_overcolor1"], "plain"],
    ["highlight_up_intensity", ["own:_overcolor1"], "alpha"],
    ["highlight_down_color", ["own:_overcolor2"], "plain"],
    ["highlight_down_intensity", ["own:_overcolor2"], "alpha"],
]

# The edit material tool (D38-D41). Sources are `create:` (the material's Create Material) or `own:`
# (the material itself), then a Texture Role or a Raw Property (with `[pattern]` for one pattern),
# tried in order; `current:` is the slot's image in the material being edited, which keeps an
# Outfit's body alpha mask.
EDIT = {
    # Material Role (None: none) -> edit template. Roles not listed, and glasses, aren't editable.
    "templates": {
        "body": "KK Body", "face": "KK Face", "hair": "KK Hair",
        "eye_l": "KK EyeL (hitomi)", "eye_r": "KK EyeR (hitomi)", "eye_white": "KK Eyewhites (sirome)",
        "eyebrow": "KK Eyebrows (mayuge)", "nose_line": "KK Nose", "teeth": "KK Teeth (tooth)",
        "eyeline_upper": "KK Eyeline up", "eyeline_lower": "KK Eyeline up", "eyeline_shadow": "KK Eyeline up",
        "tongue": "KK General", None: "KK General",
    },
    "not_editable_blend_modes": ["glasses"],
    # Edit slot -> where its texture comes from. `main.dark` is made from `main`, and
    # `color_mask.plain` takes `color_mask` for the plain-mask shaders below.
    "textures": {
        "main": ["own:main"],
        "plain": ["create:main", "own:main"],
        "color_mask": ["create:color_mask", "own:color_mask"],
        "detail_mask": ["own:detail_mask"],
        "line_mask": ["own:line_mask"],
        "normal": ["current:normal", "own:normal"],
        "detail_normal": ["current:detail_normal", "own:detail_normal"],
        "alpha_mask": ["current:alpha_mask", "own:alpha_mask"],
        "texture3": ["create:_Texture3"], "texture4": ["create:_Texture4"], "texture5": ["create:_Texture5"],
        "texture6": ["create:_Texture6"], "texture7": ["create:_Texture7"],
        "overlay1": ["own:_overtex1"], "overlay1.left": ["own:_overtex1"],
        "overlay2": ["own:_overtex2"], "overlay3": ["own:_overtex3"],
        "pattern_mask1": ["create:_PatternMask1"], "pattern_mask2": ["create:_PatternMask2"],
        "pattern_mask3": ["create:_PatternMask3"],
        "hair_gloss": ["own:_HairGloss"],
        "expression.0": ["own:_expression[cf_t_expression_00]"],
        "expression.1": ["own:_expression[cf_t_expression_01]"],
    },
    # Slots saturated through the game's colour grade, as legacy saturated its main textures.
    "saturated": ["main", "plain"],
    # Material Roles that saturate by default (ADR 0026): their templates draw from colours alone, and
    # saturated they bake closest to the game's own light and dark textures. The rest don't.
    "saturated_roles": ["hair", "eyebrow"],
    # These shaders draw no colour mask, though the game gives them one: it goes in the plain slot.
    "plain_color_mask_shaders": ["Shader Forge/main_opaque", "Shader Forge/main_opaque2",
                                 "Shader Forge/main_opaque_low", "Koikano/main_clothes_opaque",
                                 "xukmi/MainOpaquePlus", "xukmi/MainOpaquePlusTess"],
    # The colour the dark versions are shaded with.
    "shadow": ["own:_ShadowColor", "own:_shadowcolor"],
    # Edit template -> [param, sources, how]. How: `item` sets `param.light` and `param.dark` (the
    # dark one shaded with the shadow), `skin` the same with the skin's shadow, `light` and `dark`
    # one param, `eyew_dark` one param shaded as the eyebrow shader (toon_eyew) does, `plain` the
    # colour as it is, `alpha` the colour's alpha.
    "colors": {
        "KK Body": [
            ["skin_color", ["create:_Color"], "skin"],
            ["detail_color", ["create:_Color2"], "item"],
            ["line_mask_color", ["create:_Color2"], "item"],
            ["nail_color", ["create:_Color5"], "item"],
        ],
        "KK Face": [
            ["skin_color", ["create:_Color"], "skin"],
            ["detail_color", ["create:_Color2"], "item"],
            ["light_blush_color", ["own:_overcolor2"], "item"],
            ["lipstick_multiplier", ["own:_overcolor1"], "item"],
        ],
        "KK General": [
            ["color_mask_red", ["create:_Color", "own:_Color"], "item"],
            ["color_mask_green", ["create:_Color2", "own:_Color2"], "item"],
            ["color_mask_blue", ["create:_Color3", "own:_Color3"], "item"],
            ["pattern_color_red", ["create:_Color1_2"], "item"],
            ["pattern_color_green", ["create:_Color2_2"], "item"],
            ["pattern_color_blue", ["create:_Color3_2"], "item"],
        ],
        "KK Hair": [
            ["hair_color", ["own:_Color"], "item"],
            ["color_mask_root", ["own:_Color2"], "item"],
            ["color_mask_tip", ["own:_Color3"], "item"],
        ],
        "KK EyeL (hitomi)": _EYE_COLORS,
        "KK EyeR (hitomi)": _EYE_COLORS,
        "KK Eyebrows (mayuge)": [
            ["eyebrow_color", ["own:_Color"], "light"],
            ["eyebrow_color_dark", ["own:_Color"], "eyew_dark"],
        ],
        "KK Eyeline up": [["eyeline_fade_color", ["own:_Color"], "light"]],
    },
    # Values set when every condition holds: `role:R`, `raw:P` (the material has slot P),
    # `missing:S` and `has:S` (edit slot S is or isn't filled). Params a template lacks are skipped.
    "values": [
        ["role:tongue", {"maintex_saturation": 0.6, "detail_intensity_green": 0.01,
                         "color_mask_base": [1.0, 1.0, 1.0, 1.0]}],
        # An AnotherRamp texture makes the red detail metallic, which no template draws.
        ["raw:_AnotherRamp", {"detail_intensity_shine": 0.0}],
        ["missing:main", {"use_main_texture": 0.0}],
        # The game draws the eyebrows as their texture times their colour, and the hair's root and
        # tip colours through its colour mask; the templates' switches for both are off.
        ["role:eyebrow has:main", {"use_main_texture_color": 1.0}],
        ["role:hair has:color_mask", {"use_color_mask": 1.0}],
        ["missing:main has:plain", {"use_plain_main_texture": 1.0}],
        # Each eyeline shows its own texture in the main slot.
        ["role:eyeline_upper", {"use_kage_texture": 0.0, "use_down_texture": 0.0}],
        ["role:eyeline_lower", {"use_kage_texture": 0.0, "use_down_texture": 0.0}],
        ["role:eyeline_shadow", {"use_kage_texture": 0.0, "use_down_texture": 0.0}],
    ],
}
