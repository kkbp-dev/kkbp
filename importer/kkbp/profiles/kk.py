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

def _corrections():
    """Studio's `ExpressionBone.LateUpdate` (profiles/corrections.py says how to read this, and
    docs/design/joint-corrections.md where it comes from). `m` is 1 on the left and -1 on the right,
    for the signs the game mirrors. Bones are named exactly: no Bone Role or Group marks them."""
    inputs = {
        "height": ("rest_scale", "cf_n_height", "y"),
        **{f"spine_{a}": ("euler", "cf_j_spine03", "zyx", a) for a in "xyz"},
        "head_x": ("euler", "cf_j_head", "zyx", "x"),
        "head_z": ("euler", "cf_j_head", "zyx", "z"),
    }
    values, outputs = {}, []
    for s, m in (("L", "1"), ("R", "(-1)")):
        sign = 1.0 if s == "L" else -1.0
        elbow_frame = ("under", f"cf_j_shoulder_{s}", (0.0, 0.3, 0.0))
        knee_frame = ("under", "cf_j_waist02", (-0.083 * sign, 0.4, -0.008))
        inputs.update({
            f"arm_x_{s}": ("euler", f"cf_j_arm00_{s}", "zyx", "x"),
            f"elbow_{s}": ("euler", f"cf_j_forearm01_{s}", "zxy", "y"),
            f"hand_x_{s}": ("euler", f"cf_j_hand_{s}", "zyx", "x"),
            f"thigh_y_{s}": ("euler", f"cf_j_thigh00_{s}", "zyx", "y"),
            f"knee_{s}": ("euler", f"cf_j_leg01_{s}", "zyx", "x"),
            f"ankle_y_{s}": ("euler", f"cf_j_leg03_{s}", "zyx", "y"),
            # the elbow, seen from a point above the shoulder
            f"elbow_py_{s}": ("point", f"cf_j_forearm01_{s}", None, elbow_frame, "y"),
            f"elbow_pz_{s}": ("point", f"cf_j_forearm01_{s}", None, elbow_frame, "z"),
            f"arm_px_{s}": ("rest_position", f"cf_j_arm00_{s}", "x"),
            # the middle finger, seen from the wrist with the forearm's rotation
            f"finger_y_{s}": ("point", f"cf_j_middle01_{s}", None, ("at", f"cf_j_hand_{s}", f"cf_j_forearm01_{s}"), "y"),
            # a point on the back of the hand, seen from the forearm
            **{f"back_{a}_{s}": ("point", f"cf_j_hand_{s}", (-0.01 * sign, 0.01, 0.0), ("bone", f"cf_j_forearm01_{s}"), a)
               for a in "yz"},
            # the knee, seen from the hip with the waist's rotation, and from a point above the hip
            f"knee_up_{s}": ("point", f"cf_j_leg01_{s}", None, ("at", f"cf_j_thigh00_{s}", "cf_j_waist02"), "y"),
            **{f"knee_p{a}_{s}": ("point", f"cf_j_leg01_{s}", None, knee_frame, a) for a in "xyz"},
        })
        values.update({
            f"sd_{s}": f"max(0, 0.3 - abs(elbow_py_{s}))",
            f"wf_{s}": f"radians(max(0, finger_y_{s}) * 100)",
            f"vx_{s}": f"knee_px_{s} * -10",
            f"vz_{s}": f"knee_pz_{s} * -10",
            f"k_{s}": f"8.849 + knee_py_{s} * 10",
            f"n_{s}": f"max(0, knee_up_{s} / height * 10)",
        })
        outputs += [
            ("position", f"cf_d_shoulder02_{s}", {
                "x": f"arm_px_{s} - {m} * (sd_{s} + abs(elbow_pz_{s})) * 0.03",
                "y": f"sd_{s} * 0.2",
                "z": f"elbow_pz_{s} * -0.06"}),
            ("rotation", f"cf_d_shoulder02_{s}", "yzx", {"y": f"{m} * elbow_pz_{s} * 50", "z": f"{m} * sd_{s} * -250"}),
            ("rotation", f"cf_d_arm01_{s}", "zyx", {"x": f"arm_x_{s} * -0.6"}),
            ("rotation", f"cf_d_arm02_{s}", "zyx", {"x": f"arm_x_{s} * -0.5"}),
            ("rotation", f"cf_d_arm03_{s}", "zyx", {"x": f"arm_x_{s} * -0.125"}),
            ("rotation", f"cf_s_elbo_{s}", "zxy", {"y": f"elbow_{s} * -0.5"}),
            ("position", f"cf_s_elbo_{s}", {
                "x": f"sin(elbow_{s} * 0.015) * 0.022",
                "z": f"-0.025 + {m} * sin((elbow_{s} - 1) * 0.006) * 0.018"}),
            ("rotation", f"cf_s_elboback_{s}", "zxy", {"y": f"elbow_{s} * -0.5"}),
            ("position", f"cf_s_elboback_{s}", {
                "x": f"tan(elbow_{s} * 0.0039) * -1.2",
                "z": f"0.03 + {m} * (sin(elbow_{s} * 0.009) * 0.76 - tan(elbow_{s} * 0.0022) * 1.6)"}),
            ("position", f"cf_d_hand_{s}", {"x": f"{m} * (sin(wf_{s}) * 1.5 - 0.025)", "y": f"sin(wf_{s}) * 1.5"}),
            ("rotation", f"cf_d_wrist_{s}", "yxz", {"x": f"degrees(atan2(back_z_{s}, back_y_{s}))"}),
            ("rotation", f"cf_d_forearm02_{s}", "zyx", {"x": f"hand_x_{s} * 0.45"}),
            ("position", f"cf_s_leg_{s}", {
                "x": f"({m} + vx_{s} * 0.2 + {m} * (abs(vz_{s} * 1.1) - k_{s}) * 0.06) * -0.1",
                "y": f"(1 + k_{s} * 0.4 + {m} * vx_{s} * 0.2 + n_{s} * 0.6) * 0.1",
                "z": f"(vz_{s} * -0.2 + {m} * vx_{s} * 0.05 - n_{s} * 0.4) * 0.1"}),
            ("rotation", f"cf_s_leg_{s}", "zyx", {
                "x": f"vz_{s} * 6 - {m} * vx_{s} * 2 - n_{s} * 5",
                "y": f"vx_{s} * -12 - {m} * vz_{s} * 3",
                "z": f"-vx_{s}"}),
            ("scale", f"cf_s_leg_{s}", {
                "x": f"1 + abs(vz_{s}) * 0.2",
                "y": f"1 + n_{s} * 0.4",
                "z": f"1 + abs(vz_{s}) * 0.3 + n_{s} * 0.3"}),
            ("position", f"cf_d_siri_{s}", {
                "x": f"({m} * -0.7 + vx_{s} * 0.01 - {m} * (abs(vx_{s}) * 0.02 + abs(vz_{s}) * 0.005)) * 0.1",
                "y": f"(k_{s} * 0.01 + abs(vz_{s}) * 0.02 + {m} * vx_{s} * 0.04) * 0.1",
                "z": f"(k_{s} * -0.03 - (vz_{s} - n_{s} * 3) * 0.03 - abs(vx_{s}) * 0.02) * 0.1"}),
            ("scale", f"cf_d_siri_{s}", {"x": f"1 + abs(vz_{s}) * 0.02", "y": f"1 + n_{s} * 0.01"}),
            ("rotation", f"cf_d_thigh01_{s}", "zyx", {"y": f"thigh_y_{s} * -0.75"}),
            ("rotation", f"cf_d_thigh02_{s}", "zyx", {"y": f"thigh_y_{s} * -0.5"}),
            ("rotation", f"cf_d_thigh03_{s}", "zyx", {"y": f"thigh_y_{s} * -0.25"}),
            ("rotation", f"cf_s_kneeB_{s}", "zyx", {"x": f"knee_{s} * -0.5", "z": f"{m} * knee_{s} * 0.1"}),
            ("position", f"cf_s_kneeB_{s}", {
                "y": f"(knee_{s} * -0.048 + sin(knee_{s} * 0.01) * 1.1) * 0.1",
                "z": f"(-0.6 - sin(knee_{s} * 0.0115) * 4 + tan(knee_{s} * 0.0032) * 5) * 0.1"}),
            ("rotation", f"cf_d_kneeF_{s}", "zyx", {"x": f"knee_{s} * -0.5"}),
            ("position", f"cf_d_kneeF_{s}", {
                "y": f"(sin(knee_{s} * 0.012) * 1.8 - tan(knee_{s} * 0.00335) * 4.5) * 0.1",
                "z": f"(0.4 + knee_{s} * 0.0125 - tan(knee_{s} * 0.0032) * 4.5) * 0.1"}),
            ("rotation", f"cf_d_leg02_{s}", "zyx", {"y": f"ankle_y_{s} * 0.5"}),
        ]
    outputs += [
        ("rotation", "cf_d_bust00", "zyx", {a: f"spine_{a} * -0.35" for a in "xyz"}),
        ("position", "cf_d_bust00", {"y": "(spine_x * 0.003 - 0.081) * 0.1", "z": "spine_x * 0.0004"}),
        ("position", "a_n_neck", {"x": "head_z * 0.0002", "z": "(-0.08 - head_x * 0.002) * 0.1"}),
    ]
    return {"inputs": inputs, "values": values, "outputs": outputs}


# The joint corrections (docs/design/joint-corrections.md).
CORRECTIONS = _corrections()

_SKIN_COLORS = [
    ["detail_normal_map_scale", ["own:_DetailNormalMapScale"], "float"],
    ["shadow_extend", ["own:_ShadowExtend"], "float"],
    ["line_tex_on", ["own:_linetexon"], "float"],
    *[[f"overlay_color{k}", [f"own:_overcolor{k}"], "plain"] for k in (1, 2, 3)],
    *[[f"overlay_color{k}_alpha", [f"own:_overcolor{k}"], "alpha"] for k in (1, 2, 3)],
    ["nip_specular", ["own:_nip_specular"], "float"], ["tex1_mask", ["own:_tex1mask"], "float"],
    ["nip", ["own:_nip"], "float"], ["nip_size", ["own:_nipsize"], "float"],
    ["paint1", ["create:_paint1"], "vector"], ["paint1_w", ["create:_paint1"], "vector_w"],
    ["paint2", ["create:_paint2"], "vector"], ["paint2_w", ["create:_paint2"], "vector_w"],
]

# create_topN's colours and pattern scales (main_opaque's and main_alpha's create stage).
_CREATE_TOPN_COLORS = [
    ["color", ["create:_Color"], "plain"], ["color2", ["create:_Color2"], "plain"],
    ["color3", ["create:_Color3"], "plain"],
    *[[f"pattern_color{k}", [f"create:_Color{k}_2"], "plain"] for k in (1, 2, 3)],
    *[[f"pattern_color{k}_alpha", [f"create:_Color{k}_2"], "alpha"] for k in (1, 2, 3)],
    *[[f"pattern_scale{k}{a}", [f"create:_PatternScale{k}{a}"], "float"] for k in (1, 2, 3) for a in "uv"],
]

# main_opaque's and main_item's own values.
_ITEM_COLORS = [
    ["shadow_color", ["own:_ShadowColor"], "plain"],
    ["shadow_extend", ["own:_ShadowExtend"], "float"],
    ["shadow_extend_another", ["own:_ShadowExtendAnother"], "float"],
    ["detail_r_line_r", ["own:_DetailRLineR"], "float"],
    ["detail_b_line_g", ["own:_DetailBLineG"], "float"],
]

# toon_eyew's colours: the texture's tint and the shadow colour.
_EYEW_COLORS = [["color", ["own:_Color"], "plain"], ["shadow_color", ["own:_shadowcolor"], "plain"]]

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
# The legacy edit templates by Material Role (D38), for the Roles whose shaders aren't modelled yet
# (issue 30).
LEGACY_EDIT_TEMPLATES = {
    "body": "KK Body", "face": "KK Face", "hair": "KK Hair",
    "eye_l": "KK EyeL (hitomi)", "eye_r": "KK EyeR (hitomi)", "eye_white": "KK Eyewhites (sirome)",
    "eyebrow": "KK Eyebrows (mayuge)", "nose_line": "KK Nose", "teeth": "KK Teeth (tooth)",
    "eyeline_upper": "KK Eyeline up", "eyeline_lower": "KK Eyeline up", "eyeline_shadow": "KK Eyeline up",
    "tongue": "KK General", None: "KK General",
}

EDIT = {
    # Material Role (None: none) -> edit template. Roles not listed, and glasses, aren't editable. The
    # templates named after a game shader follow it (importer/tools/game_shaders/models.py).
    "templates": {
        **LEGACY_EDIT_TEMPLATES,
        "eye_white": "KK create_eyewhite", "eyebrow": "KK toon_eyew", "nose_line": "KK toon_nose",
        "hair": "KK main_hair", "eye_l": "KK toon_eye", "eye_r": "KK toon_eye",
        "body": "KK create_body", "face": "KK create_head",
        "eyeline_upper": "KK toon_eyew", "eyeline_lower": "KK toon_eyew", "eyeline_shadow": "KK toon_eyew",
    },
    # Shader (after its last `/`) -> edit template, before the Role's: one Role draws with several.
    "shader_templates": {"main_opaque": "KK main_opaque", "main_alpha": "KK main_alpha", "main_item": "KK main_item",
                         "main_emblem": "KK main_emblem"},
    "not_editable_blend_modes": ["glasses"],
    # Edit slot -> where its texture comes from. `main.dark` is made from `main`, and
    # `color_mask.plain` takes `color_mask` for the plain-mask shaders below.
    "textures": {
        "main": ["own:main"],
        "create_main": ["create:main"],
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
        "paint_mask": ["create:_paintmask"],
        "pattern_mask1": ["create:_PatternMask1"], "pattern_mask2": ["create:_PatternMask2"],
        "pattern_mask3": ["create:_PatternMask3"],
        "hair_gloss": ["own:_HairGloss"],
        "another_ramp": ["own:_AnotherRamp"],
        "expression.0": ["own:_expression[cf_t_expression_00]"],
        "expression.1": ["own:_expression[cf_t_expression_01]"],
    },
    # Slots saturated through the game's colour grade, as legacy saturated its main textures.
    "saturated": ["main", "plain"],
    # Material Roles that saturate by default (ADR 0026): their templates draw from colours alone, and
    # saturated they bake closest to the game's own light and dark textures. The rest don't.
    "saturated_roles": [],
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
        # The game's own colours, linear, as its shaders see them.
        "KK toon_eyew": _EYEW_COLORS,
        "KK create_eyewhite": [*_EYEW_COLORS, ["create_color", ["create:_Color"], "plain"],
                               ["create_color2", ["create:_Color2"], "plain"]],
        "KK toon_nose": [["color", ["own:_Color"], "plain"], ["color_alpha", ["own:_Color"], "alpha"]],
        "KK create_body": [
            *[[("color" if k == 1 else f"color{k}"), [f"create:_Color{'' if k == 1 else k}"], "plain"] for k in range(1, 7)],
            *[[f"color{k}_alpha", [f"create:_Color{k}"], "alpha"] for k in (2, 3, 4, 6)],
            *_SKIN_COLORS,
        ],
        "KK create_head": [
            *[[("color" if k == 1 else f"color{k}"), [f"create:_Color{'' if k == 1 else k}"], "plain"] for k in range(1, 8)],
            *[[f"color{k}_alpha", [f"create:_Color{k}"], "alpha"] for k in range(3, 8)],
            ["tex4uv", ["create:_tex4uv"], "vector"], ["tex4uv_w", ["create:_tex4uv"], "vector_w"],
            ["tex5uv", ["create:_tex5uv"], "vector"], ["tex5uv_w", ["create:_tex5uv"], "vector_w"],
            ["hokuro", ["create:_hokuro"], "vector"], ["hokuro_w", ["create:_hokuro"], "vector_w"],
            *_SKIN_COLORS,
        ],
        "KK toon_eye": [
            ["overlay_color1", ["own:_overcolor1"], "plain"], ["overlay_color1_alpha", ["own:_overcolor1"], "alpha"],
            ["overlay_color2", ["own:_overcolor2"], "plain"], ["overlay_color2_alpha", ["own:_overcolor2"], "alpha"],
            ["shadow_color", ["own:_shadowcolor"], "plain"],
            ["highlight", ["own:_isHighLight"], "float"], ["rotation", ["own:_rotation"], "float"],
        ],
        "KK main_opaque": [
            *_CREATE_TOPN_COLORS,
            *_ITEM_COLORS,
        ],
        "KK main_alpha": [
            *_CREATE_TOPN_COLORS,
            ["shadow_color", ["own:_ShadowColor"], "plain"], ["specular_color", ["own:_SpecularColor"], "plain"],
            ["shadow_extend", ["own:_ShadowExtend"], "float"], ["detail_b_line_ga", ["own:_DetailBLineGA"], "float"],
        ],
        "KK main_item": [
            ["color", ["own:_Color"], "plain"], ["color2", ["own:_Color2"], "plain"], ["color3", ["own:_Color3"], "plain"],
            ["another_ramp_full", ["own:_AnotherRampFull"], "float"],
            ["not_use_tex_specular", ["own:_notusetexspecular"], "float"],
            *_ITEM_COLORS,
        ],
        "KK main_hair": [
            ["color", ["own:_Color"], "plain"], ["color2", ["own:_Color2"], "plain"],
            ["color3", ["own:_Color3"], "plain"], ["shadow_color", ["own:_ShadowColor"], "plain"],
            ["shadow_extend", ["own:_ShadowExtend"], "float"],
        ],
    },
    # Values set when every condition holds: `role:R`, `raw:P` (the material has slot P), `shader:S`
    # (the material's shader is S, after its last `/`),
    # `missing:S` and `has:S` (edit slot S is or isn't filled), `create:S` (the material's create
    # material's shader is S, after its last `/`). Params a template lacks are skipped.
    "values": [
        ["role:tongue", {"maintex_saturation": 0.6, "detail_intensity_green": 0.01,
                         "color_mask_base": [1.0, 1.0, 1.0, 1.0]}],
        # An AnotherRamp texture makes the red detail metallic, which no template draws.
        ["raw:_AnotherRamp", {"detail_intensity_shine": 0.0}],
        ["missing:main", {"use_main_texture": 0.0}],
        # The game draws the eyebrows as their texture times their colour (the legacy template),
        # and the hair's root and tip colours through its colour mask; the templates' switches are off.
        ["role:eyebrow has:main", {"use_main_texture_color": 1.0}],
        ["role:hair has:color_mask", {"use_color_mask": 1.0}],
        ["missing:main has:plain", {"use_plain_main_texture": 1.0}],
        # Each eyeline shows its own texture in the main slot.
        ["role:eyeline_upper", {"use_kage_texture": 0.0, "use_down_texture": 0.0}],
        ["role:eyeline_lower", {"use_kage_texture": 0.0, "use_down_texture": 0.0}],
        ["role:eyeline_shadow", {"use_kage_texture": 0.0, "use_down_texture": 0.0}],
        # An image node without an image reads black, opaque: a decal or overlay whose texture is
        # missing is switched off by its colour's alpha, as the game's transparent default is.
        ["missing:overlay1", {"overlay_color1_alpha": 0.0}],
        ["missing:overlay2", {"overlay_color2_alpha": 0.0}],
        ["missing:overlay3", {"overlay_color3_alpha": 0.0}],
        ["missing:texture3", {"color3_alpha": 0.0}],
        ["missing:texture5", {"color5_alpha": 0.0}],
        ["missing:texture6", {"color6_alpha": 0.0}],
        ["missing:texture7", {"color7_alpha": 0.0}],
        ["role:face missing:texture4", {"color4_alpha": 0.0}],
        # main_item reads its other ramp where it has one.
        ["has:another_ramp", {"use_another_ramp": 1.0}],
        # create_body reads white where the tan lines are missing.
        ["role:body missing:texture4", {"tan_present": 0.0}],
        # create_topN reads white where a pattern mask is missing.
        ["missing:pattern_mask1", {"pattern1_present": 0.0}],
        ["missing:pattern_mask2", {"pattern2_present": 0.0}],
        ["missing:pattern_mask3", {"pattern3_present": 0.0}],
        # main_hair_front reads its gloss further along than main_hair.
        ["shader:main_hair_front", {"front": 1.0}],
    ],
}
