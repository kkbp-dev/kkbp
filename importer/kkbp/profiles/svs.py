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

def _face_part_colors(prefix):
    """The eyebrow's and eyelash's colours: `<prefix>1` to `3` and `_Line_color`, the last three with
    their alpha."""
    raws = [f"{prefix}{k}" for k in (1, 2, 3)] + ["_Line_color"]
    names = ["color1", "color2", "color3", "line_color"]
    return [*[[n, [f"own:{r}"], "plain"] for n, r in zip(names, raws)],
            *[[f"{n}_alpha", [f"own:{r}"], "alpha"] for n, r in zip(names[1:], raws[1:])]]


# lif_main_eye's texture slots and colours.
_EYE_TEXTURES = {"shadow_mask": ["own:_Shadow_mask"], "iris_mask": ["own:_Eye_mask"], "pupil": ["own:_Pipil_texture"],
                 "grade": ["own:_Grade_texture"],
                 **{f"highlight{k}": [f"own:_Highlight_texture_0{k}"] for k in (1, 2, 3)}}
_EYE_COLORS = [
    *[[name, [f"own:{raw}"], "plain"] for name, raw in (
        ("eye_white1", "_Eye_white_color_01"), ("eye_white2", "_Eye_white_color_02"), ("eye1", "_Eye_color_01"),
        ("eye2", "_Eye_color_02"), ("eye3", "_Eye_color_03"), ("pupil1", "_Piple_color_01"), ("pupil2", "_Piple_color_02"),
        ("pupil3", "_Piple_color_03"), ("line_color", "_Line_color"), ("grade_color", "_Grade_color"),
        ("highlight_color1", "_Highlight_color_01"), ("highlight_color2", "_Highlight_color_02"),
        ("highlight_color3", "_Highlight_color_03"))],
    *[[f"{name}_alpha", [f"own:{raw}"], "alpha"] for name, raw in (
        ("eye_white2", "_Eye_white_color_02"), ("eye2", "_Eye_color_02"), ("eye3", "_Eye_color_03"),
        ("pupil1", "_Piple_color_01"), ("pupil2", "_Piple_color_02"), ("pupil3", "_Piple_color_03"),
        ("line_color", "_Line_color"), ("grade_color", "_Grade_color"), ("highlight_color1", "_Highlight_color_01"),
        ("highlight_color2", "_Highlight_color_02"), ("highlight_color3", "_Highlight_color_03"))],
    *[[name, [f"own:{raw}"], "float"] for name, raw in (
        ("shadow_power", "_Shadow_power"), ("highlight_power", "_Highlight_power"), ("rotation", "_rotation"),
        ("mirror", "_Eye_postion_rebers"), ("eye_open", "_Eye_open"), ("grade_position", "_Grade_position"),
        ("grade_size", "_Grade_size"), ("parallax", "_Parallax"),
        *[(f"highlight{k}_rotation", f"_Highlight_0{k}_rotation") for k in (1, 2, 3)])],
    *[[name, [f"own:{raw}"], how] for base, raw in (
        ("eye_position", "_Eye_position"), ("eye_position_add", "_Eye_position_add"), ("pupil_size", "_Pipil_size"),
        *[(f"highlight{k}_position", f"_Highlight_0{k}_position") for k in (1, 2, 3)])
      for name, how in ((base, "vector"), (f"{base}_w", "vector_w")) if not (base == "pupil_size" and how == "vector_w")],
]


_HAIR_COLORS = (("main_color", "_Main_color"), ("sub_color1", "_Sub_color_01"), ("sub_color2", "_Sub_color_02"),
                ("add_skin_color", "_Add_skin_color"), ("ex_hair_color", "_Ex_hair_color"), ("ex_hair_color2", "_Ex_hair_color2"),
                ("shadow_color", "_Shadow_color"), ("shadow_color2", "_ShadowColor"))


def _plain(*pairs, alpha=()):
    """Colour rows: `[name, own:raw, plain]` for each (name, raw), and `name_alpha` for those in `alpha`.
    A raw starting `create:` reads the create material."""
    src = lambda raw: raw if raw.startswith("create:") else f"own:{raw}"  # noqa: E731
    return [*[[n, [src(r)], "plain"] for n, r in pairs], *[[f"{n}_alpha", [src(r)], "alpha"] for n, r in pairs if n in alpha]]


def _floats(*pairs):
    return [[n, [r if r.startswith("create:") else f"own:{r}"], "float"] for n, r in pairs]


def _vectors(*pairs):
    return [[f"{n}{tail}", [r if r.startswith("create:") else f"own:{r}"], how] for n, r in pairs
            for tail, how in (("", "vector"), ("_w", "vector_w"))]


# What the skin and nail shaders light with, as lif_main_acs's.
_SKIN_LIGHT = [
    *_plain(("shadow_color", "_ShadowColor")),
    ["shadow_setting", ["own:_ShadowSetting"], "vector"], ["shadow_setting_w", ["own:_ShadowSetting"], "vector_w"],
    *_floats(("shadow_power", "_Shadow_power"), ("shadow_color_on", "_ShadowColorON")),
]
# The skin's, which also pull and push the shadow by a detail mask.
_SKIN_DETAIL = [["shadow_pull", ["own:_ShadowSetting"], "vector_z"], *_floats(("shadow_extend", "_shadowextend"))]
_CREATE_PAINTS = [
    *_plain(*[(f"create_paint_color{k}", f"create:_Paint_color_0{k}") for k in (1, 2, 3)],
            alpha=[f"create_paint_color{k}" for k in (1, 2, 3)]),
    *_vectors(*[(f"create_paint{k}_position", f"create:_Paint_position_0{k}") for k in (1, 2, 3)]),
]


# The edit material tool (D38-D41; profiles/kk.py says what each table holds). SVS's templates follow
# its LIF shaders (importer/tools/game_shaders/models.py); a shader none follows (the
# `_alpha` and `_low` copies, modded shaders) isn't editable. SVS's materials carry their textures by
# Raw Property, and their colours are the game's own, linear as its shaders see them.
EDIT = {
    "templates": {
        "eyebrow": "SVS lif_main_eyebrow",
        "eyelash": "SVS lif_main_eyelash_up",
        "eye_l": "SVS lif_main_eye", "eye_r": "SVS lif_main_eye", "eye_white": "SVS lif_main_eye",
        "hair": "SVS lif_main_hair",
        "body": "SVS lif_main_skin_body", "face": "SVS lif_main_skin_head",
    },
    # Shader (after its last `/`) -> edit template, before the Role's.
    "shader_templates": {"lif_main_acs": "SVS lif_main_acs", "lif_main_cloth": "SVS lif_main_cloth",
                         # The socks' shader is the clothes' without their parallax and liquid.
                         "lif_main_cloth_socks": "SVS lif_main_cloth",
                         # The nails have no Role.
                         "lif_main_nail": "SVS lif_main_nail"},
    "not_editable_blend_modes": ["glasses"],
    "textures": {
        "eyebrow": ["own:_eyebrow_texture"],
        "eyelash_up": ["own:_Eyelash_up_texture"],
        "eyelash_down": ["own:_Eyelash_dw_texture"],
        **_EYE_TEXTURES,
        "color_mask": ["own:_Hair_color_mask", "own:_Main_color_mask"],
        "detail1": ["own:_md_01"], "detail2": ["own:_md_02"],
        # The ramp, read at two places (lif_main_hair).
        "ramp": ["own:_Lamp"], "ramp2": ["own:_Lamp"],
        "main": ["own:_Main_texture"],
        "pattern_mask1": ["own:_PatternMask_01"], "pattern_mask2": ["own:_PatternMask_02"], "pattern_mask3": ["own:_PatternMask_03"],
        "detail_mask": ["own:_Detail_mask_01"], "detail_mask2": ["own:_Detail_mask_02"],
        "create": ["own:_Create_main_texture", "own:_Create_jm_main_skin_head"],
        # The matcap the nails and skin read at the bake's view normal; the ramp the body's highlight dims by.
        "matcap": ["own:_Mat_cap", "own:_shadematcap"], "ramp3": ["own:_Lamp"],
        **{f"paint{k}": [f"own:_Paint_texture_0{k}"] for k in (1, 2, 3)},
        # The skin's mesh-placed layers, and the body's highlight (its first detail mask, moved).
        "nip": ["own:_Nip"], "underhair": ["own:_Under_hair_texture"], "cheek": ["own:_Cheek_texture"],
        "lip": ["own:_Lip_texture"], "nose": ["own:_Nose_texture"], "detail_mask_highlight": ["own:_Detail_mask_01"],
        # The body's and face's create materials.
        "create_sunburn": ["create:_Sunburn_texture"], "create_skin_mask": ["create:_Skin_mask"],
        "create_facetype": ["create:_Facetype_texture"], "create_mole": ["create:_Hokuro_texture"],
        "create_eyeshadow": ["create:_Eyeshadow_texture"],
        # The clothes' create material (Schema Version 1.3).
        "create_main": ["create:_Main_texture"], "create_mask": ["create:_Main_color_mask"],
        "create_paint_mask": ["create:_Paint_mask"],
        **{f"create_pattern{k}": [f"create:_PatternMask_0{k}"] for k in (1, 2, 3, 4)},
        **{f"create_paint{k}": [f"create:_Paint_texture_0{k}"] for k in (1, 2, 3)},
    },
    "saturated": [],
    "saturated_roles": [],
    "plain_color_mask_shaders": [],
    "shadow": ["own:_ShadowColor"],
    "colors": {
        "SVS lif_main_eyebrow": [
            *_face_part_colors("_eyebrow_color0"),
            ["length", ["own:_BrowLength"], "float"], ["width", ["own:_BrowWidth"], "float"],
            ["light_influence", ["own:_Ligjht_influence"], "float"], ["shadow_power", ["own:_Shadow_power"], "float"],
        ],
        "SVS lif_main_eyelash_up": [*_face_part_colors("_Eyelash_color0"), ["shadow_power", ["own:_Shadow_power"], "float"]],
        "SVS lif_main_eye": _EYE_COLORS,
        "SVS lif_main_acs": [
            *[[f"main_color{k}", [f"own:_Main_color_0{k}"], "plain"] for k in (1, 2, 3, 4)],
            *[[f"main_color{k}_alpha", [f"own:_Main_color_0{k}"], "alpha"] for k in (1, 2, 3, 4)],
            *[[f"sub_color{k}", [f"own:_Sub_color_0{k}"], "plain"] for k in (1, 2, 3)],
            *[[f"sub_color{k}_alpha", [f"own:_Sub_color_0{k}"], "alpha"] for k in (1, 2, 3)],
            ["shadow_color", ["own:_ShadowColor"], "plain"], ["line_color", ["own:_Line_color"], "plain"],
            ["shadow_setting", ["own:_ShadowSetting"], "vector"], ["shadow_setting_w", ["own:_ShadowSetting"], "vector_w"],
            ["shadow_pull", ["own:_ShadowSetting"], "vector_z"], ["type_select", ["own:_TypeSelect"], "float"],
            *[[f"pattern{k}_{p}", [f"own:{raw.format(k=k)}"], "float"] for k in (1, 2, 3) for p, raw in (
                ("scale_u", "_PatternScale_0{k}u"), ("scale_v", "_PatternScale_0{k}v"), ("aspect_u", "_UVAspectRatioU"),
                ("aspect_v", "_UVAspectRatioV"), ("remap_min", "_PatternRemapMin"), ("remap_max", "_PatternRemapMax"),
                ("offset_u", "_PatternOffset_0{k}u"), ("offset_v", "_PatternOffset_0{k}v"), ("rotator", "_PatternRotator_0{k}"),
                ("clamp", "_patternclamp{k}"))],
            *[[name, [f"own:{raw}"], "float"] for name, raw in (
                ("shadow_power", "_Shadow_power"), ("shadow_extend", "_shadowextend"), ("shadow_color_on", "_ShadowColorON"),
                ("line_power", "_Line_power"), ("line_color_intensity1", "_LineColorIntensity1"),
                ("line_color_intensity2", "_LineColorIntensity2"), ("line_color_intensity3", "_LineColorIntensity3"),
                ("line_width_s", "_LineWidthS"), ("line_width", "_Line_width"), ("line_width_ss", "_LineWidthSS"),
                ("line_texture_on", "_Line_texture_onoff"), ("alpha_line", "_AlphaLine"), ("alpha", "_alpha"))],
        ],
        "SVS lif_main_cloth": [
            *[[f"main_color{k}", [f"own:_Main_color_0{k}"], "plain"] for k in (1, 2, 3, 4)],
            ["curvature_color", ["own:_Color_Cuvature"], "plain"], ["curvature_color_alpha", ["own:_Color_Cuvature"], "alpha"],
            ["shadow_color", ["own:_ShadowColor"], "plain"], ["line_color", ["own:_Line_color"], "plain"],
            ["shadow_setting", ["own:_ShadowSetting"], "vector"], ["shadow_setting_w", ["own:_ShadowSetting"], "vector_w"],
            ["shadow_pull", ["own:_ShadowSetting"], "vector_z"],
            *[[name, [f"own:{raw}"], "float"] for name, raw in (
                ("color_switch", "_Main_color_switchtest"), ("rim_scale", "_RimScale"), ("type_select", "_TypeSelect"),
                ("shadow_power", "_Shadow_power"), ("shadow_extend", "_shadowextend"), ("shadow_color_on", "_ShadowColorON"),
                ("line_power", "_Line_power"), ("alpha_line", "_AlphaLine"))],
            *[[f"create_{kind}{k}", [f"create:{raw}0{k}"], how] for k in (1, 2, 3, 4)
              for kind, raw in (("main_color", "_Main_color_"), ("sub_color", "_Sub_color_")) for how in ("plain",)],
            *[[f"create_{kind}{k}_alpha", [f"create:{raw}0{k}"], "alpha"] for k in (1, 2, 3, 4)
              for kind, raw in (("main_color", "_Main_color_"), ("sub_color", "_Sub_color_"))],
            *[[f"create_paint_color{k}", [f"create:_Paint_color_0{k}"], "plain"] for k in (1, 2, 3)],
            *[[f"create_paint_color{k}_alpha", [f"create:_Paint_color_0{k}"], "alpha"] for k in (1, 2, 3)],
            *[[f"create_pattern{k}_{p}", [f"create:{raw}0{k}{axis}"], "float"] for k in (1, 2, 3, 4) for p, raw, axis in (
                ("offset_u", "_PatternOffset_", "u"), ("offset_v", "_PatternOffset_", "v"), ("scale_u", "_PatternScale_", "u"),
                ("scale_v", "_PatternScale_", "v"), ("rotator", "_PatternRotator_", ""))],
            *[[f"create_paint{k}_position", [f"create:_Paint_position_0{k}"], "vector"] for k in (1, 2, 3)],
            *[[f"create_paint{k}_position_w", [f"create:_Paint_position_0{k}"], "vector_w"] for k in (1, 2, 3)],
        ],
        "SVS lif_main_nail": [
            *_plain(*[(f"nail_color{k}", f"_Nail_main_color_0{k}") for k in (1, 2, 3)], alpha=["nail_color1"]),
            *_plain(*[(f"paint_color{k}", f"_Paint_color_0{k}") for k in (1, 2, 3)], alpha=[f"paint_color{k}" for k in (1, 2, 3)]),
            *_vectors(*[(f"paint{k}_position", f"_Paint_position_offset_0{k}") for k in (1, 2, 3)]),
            *_floats(("gloss_power", "_Nail_gloss_power")), *_SKIN_LIGHT,
        ],
        "SVS lif_main_skin_body": [
            *_plain(("main_color", "_MainColor"), ("nip_color1", "_Nip_color_01"), ("nip_color2", "_Nip_color_02"),
                    ("under_hair_color", "_Under_hair_color"), ("detail_color2", "_Detail_color_02"),
                    ("shadow_color2", "_Shadow_color"), ("highlight_color", "_Highlight_color"),
                    alpha=["nip_color1", "under_hair_color", "detail_color2", "shadow_color2", "highlight_color"]),
            *_floats(("skin_red_power", "_Skin_red_power"), ("nip_size", "_Nip_size"), ("highlight_power", "_Highlight_power"),
                     ("high_light_power", "_High_light_power"), ("speclar_height", "_SpeclarHeight")),
            *_SKIN_LIGHT, *_SKIN_DETAIL,
            *_plain(("create_main_color", "create:_Main_color"), ("create_sunburn_color", "create:_Sunburn_color"),
                    alpha=["create_sunburn_color"]),
            *_CREATE_PAINTS,
        ],
        "SVS lif_main_skin_head": [
            *_plain(("main_color", "_MainColor"), ("cheek_color", "_Cheek_color"), ("cheek_highlight_color", "_Cheek_highlight_color"),
                    ("lip_color", "_Lip_color"), ("lip_highlight_color", "_Lip_highlight_color"),
                    ("nose_line_color", "_Nose_line_color"), ("shadow_color2", "_Shadow_color"),
                    alpha=["cheek_color", "cheek_highlight_color", "lip_color", "lip_highlight_color", "nose_line_color",
                           "shadow_color2"]),
            ["nose_color_alpha", ["own:_Nose_color"], "alpha"],
            *_vectors(("cheek_position", "_Cheek_position")),
            *_floats(("cheek_position_x", "_Cheek_position_x"), ("cheek_position_y", "_Cheek_position_y"),
                     ("cheek_rotation", "_Cheek_rotation"), ("cheek_size", "_Cheek_size")),
            *_SKIN_LIGHT, *_SKIN_DETAIL,
            *_plain(("create_main_color", "create:_Main_color"), ("create_mouth_color", "create:_Mouth_color"),
                    ("create_mole_color", "create:_Hokuro_color"), ("create_eyeshadow_color", "create:_Eyeshadow_color"),
                    alpha=["create_mole_color", "create_eyeshadow_color"]),
            *_vectors(("create_mole_position", "create:_Hokuro_position")),
            *_CREATE_PAINTS,
        ],
        "SVS lif_main_hair": [
            *[[name, [f"own:{raw}"], "plain"] for name, raw in _HAIR_COLORS],
            *[[f"{name}_alpha", [f"own:{raw}"], "alpha"] for name, raw in _HAIR_COLORS
              if name not in ("main_color", "shadow_color", "shadow_color2")],
            *[[name, [f"own:{raw}"], "float"] for name, raw in (
                ("ex_hair_color_on", "_Ex_hair_color_onoff"), ("ex_hair_color2_on", "_Ex_hair_color2_onoff"),
                ("shadow_power", "_Shadow_power"), ("shadow_color_on", "_ShadowColorON"))],
        ],
    },
    # SVS's masks keep data of their own in their alpha (the hair's colour mask its Ex hair colour 2).
    "channel_packed": ["main", "pattern_mask1", "pattern_mask2", "pattern_mask3", "detail_mask", "detail_mask2", "create", "create_main", "create_mask", "create_paint_mask",
                       "create_pattern1", "create_pattern2", "create_pattern3", "create_pattern4", "create_paint1", "create_paint2",
                       "create_paint3", "color_mask", "iris_mask", "pupil", "highlight1", "highlight2", "highlight3", "shadow_mask",
                       "eyebrow", "eyelash_up", "eyelash_down", "detail1", "detail2", "matcap", "paint1", "paint2", "paint3", "nip",
                       "underhair", "cheek", "lip", "nose", "detail_mask_highlight", "create_sunburn", "create_skin_mask",
                       "create_facetype", "create_mole", "create_eyeshadow"],
    "values": [
        # The eye white copies bake the eye white alone (ADR 0034).
        ["role:eye_white", {"eye_white_only": 1.0}],
        # An image node without an image reads black and opaque; the game's missing texture is
        # transparent.
        *[[f"missing:{slot}", {f"{slot}_present": 0.0}] for slot in _EYE_TEXTURES],
        *[[f"missing:{slot}", {f"{slot}_present": 0.0}] for slot in
          ("main", "color_mask", "pattern_mask1", "pattern_mask2", "pattern_mask3")],
        # The clothes composite their create material when the bundle carries one (Schema Version 1.3).
        ["has:create_mask", {"use_create": 1.0}],
        # The body and face composite theirs too; it lets Save bake the face without its eyeshadow.
        ["create:lif_create_main_skin_body", {"use_create": 1.0}],
        ["create:lif_create_main_skin_head", {"use_create": 1.0}],
        *[[f"missing:{slot}", {f"{slot}_present": 0.0}] for slot in
          ("paint1", "paint2", "paint3", "nip", "underhair", "create_facetype")],
        *[[f"missing:{slot}", {f"{slot}_present": 0.0}] for slot in
          ("create_main", "create_mask", "create_paint_mask", *[f"create_pattern{k}" for k in (1, 2, 3, 4)],
           *[f"create_paint{k}" for k in (1, 2, 3)])],
    ],
}


def _corrections():
    """`HumanIndirectCorrection.OnUpdate`, in the order it runs (profiles/corrections.py says how to
    read this, and docs/design/joint-corrections.md where it comes from). `m` is 1 on the left and -1
    on the right. The game sets one Euler angle at a time, so one bone's angles are separate outputs
    here, in the game's order. Its skirt corrections are left out."""
    sides = (("L", "1"), ("R", "(-1)"))
    inputs, values = {}, {}
    arms, legs, forearms, thighs = [], [], [], []
    for s, m in sides:
        left = s == "L"
        inputs.update({
            **{f"hand_{a}_{s}": ("euler", f"cf_j_hand_{s}", "yzx", a) for a in "xyz"},
            **{f"arm_{a}_{s}": ("euler", f"cf_j_arm00_{s}", "yzx", a) for a in "xyz"},
            f"elbow_{s}": ("euler", f"cf_j_forearm01_{s}", "yzx", "y"),
            **{f"thigh_{a}_{s}": ("euler", f"cf_j_thigh00_{s}", "yzx", a) for a in "xyz"},
            f"aim_{s}": ("euler", f"cf_d_thigh00_{s}", "yzx", "x"),
            f"knee_{s}": ("euler", f"cf_j_leg01_{s}", "yzx", "x"),
            **{f"ankle_{a}_{s}": ("euler", f"cf_j_leg03_{s}", "yzx", a) for a in "xyz"},
            f"hip_x_{s}": ("euler", f"cf_d_siri_{s}", "yzx", "x"),
        })
        # How far the elbow is past 50, 60 and 90 degrees in the direction it bends.
        past = "max(0, elbow_{s} - {n})" if left else "min(0, elbow_{s} + {n})"
        values.update({
            **{f"e{n}_{s}": past.format(s=s, n=n) for n in (50, 60, 90)},
            f"k90_{s}": f"max(0, knee_{s} - 90)",
            f"a80_{s}": f"min(0, aim_{s} + 80)",
            # cf_d_siri's position, which the centre of the hips reads back
            f"hip_py_{s}": f"-0.03 - {m} * thigh_z_{s} * 0.0001 - thigh_x_{s} * 0.0001",
            f"hip_pz_{s}": (f"-0.01 - thigh_x_{s} * 0.0001 - min(0, thigh_x_{s} + 80) * 0.0003"
                            f" + {m} * thigh_z_{s} * (-0.0001 if thigh_x_{s} < -80 else 0.0001)"),
        })
        arms += [
            ("rotation", f"cf_d_forearm_wrist_{s}", "yxz", {"z": f"hand_z_{s}"}),
            ("rotation", f"cf_d_forearm_wrist_{s}", "yxz", {"y": f"hand_y_{s}"}),
            ("rotation", f"cf_d_arm01_{s}", "yxz", {"x": f"arm_x_{s} * -0.8"}),
            ("rotation", f"cf_d_arm02_{s}", "yxz", {"x": f"arm_x_{s} * -0.5"}),
            ("rotation", f"cf_d_arm03_{s}", "yxz", {"x": f"arm_x_{s} * -0.2"}),
            ("rotation", f"cf_d_forearm01_{s}", "yxz", {"x": f"hand_x_{s} * 0.2"}),
            ("rotation", f"cf_d_forearm02_{s}", "yxz", {"x": f"hand_x_{s} * 0.5"}),
            ("rotation", f"cf_d_forearm03_{s}", "yxz", {"x": f"hand_x_{s} * 0.8"}),
            ("rotation", f"cf_j_shoulder02_{s}", "yxz", {"x": f"arm_x_{s} * 0.7"}),
            ("rotation", f"cf_j_shoulder02_{s}", "yxz", {"y": f"arm_y_{s} * 0.7"}),
            ("rotation", f"cf_j_shoulder02_{s}", "yxz", {"z": f"{'min' if left else 'max'}(0, arm_z_{s}) * 0.7"}),
        ]
        legs += [
            ("rotation", f"cf_d_leg00_{s}", "yxz", {"x": f"k90_{s} * 0.05"}),
            ("rotation", f"cf_d_leg01_{s}", "yxz", {"x": f"k90_{s} * -0.05"}),
            ("scale", f"cf_d_thigh03_{s}", {"x": f"1 + k90_{s} * 0.004"}),
            ("scale", f"cf_d_leg01_{s}", {"x": f"1 + k90_{s} * 0.002"}),
            ("position", f"cf_d_thigh03_{s}", {"z": f"max(0, knee_{s} - 60) * 0.00025"}),
            ("position", f"cf_d_thigh00_{s}", {"z": f"a80_{s} * 0.0008"}),
            ("position", f"cf_d_thigh00_{s}", {"y": f"a80_{s} * -0.0003"}),
            ("scale", f"cf_d_thigh00_{s}", {"y": f"1 - a80_{s} * 0.0017"}),
            ("position", f"cf_d_kneeB_{s}", {"z": f"-0.03 - knee_{s} * 0.0005 + k90_{s} * 0.001"}),
            ("position", f"cf_d_kneeB_{s}", {"y": f"knee_{s} * 0.0005 + k90_{s} * 0.0005"}),
            ("scale", f"cf_d_kneeB_{s}", {"x": f"1 - k90_{s} * 0.002"}),
            ("rotation", f"cf_d_kneeB_{s}", "yxz", {"x": f"knee_{s} * 0.25"}),
            ("position", f"cf_d_kneeF_{s}", {"z": f"0.0322 - knee_{s} * 0.0001 + k90_{s} * 0.0001"}),
            ("position", f"cf_d_kneeF_{s}", {"y": f"knee_{s} * -0.0003 + k90_{s} * 0.0001"}),
            ("rotation", f"cf_d_kneeF_{s}", "yxz", {"x": f"knee_{s} * 0.6"}),
            ("rotation", f"cf_d_leg03_{s}", "yxz", {"x": f"ankle_x_{s} * 0.1"}),
            ("rotation", f"cf_d_leg03_{s}", "yxz", {"z": f"ankle_z_{s} * 0.1"}),
            ("rotation", f"cf_d_leg02_{s}", "yxz", {"y": f"ankle_y_{s} * 0.4"}),
            ("rotation", f"cf_d_leg03_{s}", "yxz", {"y": f"ankle_y_{s} * 0.9"}),
            ("rotation", f"cf_d_thigh01_{s}", "yxz", {"y": f"thigh_y_{s} * -0.8"}),
            ("rotation", f"cf_d_thigh02_{s}", "yxz", {"y": f"thigh_y_{s} * -0.5"}),
            ("rotation", f"cf_d_thigh03_{s}", "yxz", {"y": f"thigh_y_{s} * -0.2"}),
        ]
        forearms += [
            ("position", f"cf_d_elboback_{s}", {"x": f"elbow_{s} * 0.0005 + e60_{s} * 0.0005"}),
            ("rotation", f"cf_d_elboback_{s}", "yxz", {"y": f"elbow_{s} * 0.25"}),
            ("position", f"cf_d_elboback_{s}", {"z": f"0.03 + {m} * (elbow_{s} * 0.0006 - e60_{s} * 0.0003)"}),
            ("rotation", f"cf_d_elbo_{s}", "yxz", {"y": f"elbow_{s} * 0.2 + e90_{s} * 0.6"}),
            ("position", f"cf_d_elbo_{s}", {"x": f"elbow_{s} * -0.0002 - e90_{s} * 0.0003"}),
            ("position", f"cf_d_forearm00_{s}", {"z": f"{m} * e90_{s} * -0.00033"}),
            ("rotation", f"cf_d_forearm00_{s}", "yxz", {"y": f"e90_{s} * 0.095"}),
            ("position", f"cf_d_elbo_{s}", {"z": f"-0.025 - {m} * (elbow_{s} * 0.00003 - e50_{s} * 0.0004)"}),
        ]
        thighs += [
            ("position", f"cf_d_hipleg1_{s}", {"x": f"thigh_z_{s} * 0.0003 - {m} * 0.0845"}),
            ("position", f"cf_d_hipleg1_{s}", {"y": f"(-thigh_x_{s} - {m} * thigh_z_{s}) * 0.0007 + 0.0315"}),
            ("position", f"cf_d_hipleg2_{s}", {"x": f"thigh_z_{s} * 0.001 - {m} * 0.041"}),
            ("position", f"cf_d_hipleg2_{s}", {"y": f"thigh_x_{s} * 0.0014 - 0.0773 - {m} * thigh_z_{s} * 0.0005"}),
            ("position", f"cf_d_hipleg2_{s}", {"z": f"0.0711 - thigh_x_{s} * 0.00148 + {m} * thigh_z_{s} * 0.0013"}),
            ("rotation", f"cf_d_hipleg1_{s}", "yxz", {"x": f"thigh_x_{s} * 0.66"}),
            ("rotation", f"cf_d_hipleg1_{s}", "yxz", {"z": f"thigh_z_{s} * 0.66"}),
            ("position", f"cf_d_siri_{s}", {"x": f"{m} * (thigh_z_{s} * 0.0002 - 0.053)"}),
            ("position", f"cf_d_siri_{s}", {"y": f"hip_py_{s}"}),
            ("rotation", f"cf_d_siri_{s}", "yxz", {"z": f"thigh_z_{s} * 0.25"}),
            ("rotation", f"cf_d_siri_{s}", "yxz", {"x": f"(thigh_x_{s} + 1) * 0.45"}),
            ("position", f"cf_d_siri_{s}", {"z": f"hip_pz_{s}"}),
        ]
    inputs.update({f"spine_{a}": ("euler", "cf_j_spine03", "yzx", a) for a in "xyz"})
    centre = [
        ("rotation", "cf_d_bust00", "yxz", {"x": "spine_x * -0.3"}),
        ("rotation", "cf_d_bust00", "yxz", {"y": "spine_y * -0.3"}),
        ("rotation", "cf_d_bust00", "yxz", {"z": "spine_z * -0.3"}),
        ("position", "cf_d_bust00", {"y": "0.01 - spine_x * 0.0003"}),
        ("position", "cf_d_bust00", {"z": "abs(spine_x) * (0.0005 if spine_x > 0 else 0.0003)"}),
        ("rotation", "cf_d_siri_C", "yxz", {"x": "(hip_x_L + hip_x_R) * 0.4"}),
        ("position", "cf_d_siri_C", {"y": "(hip_py_L + hip_py_R) * 0.5"}),
        ("position", "cf_d_siri_C", {"z": "(hip_pz_L + hip_pz_R + 0.0594) * 0.25 - 0.01"}),
        ("position", "cf_d_ana", {"y": "(hip_py_L + hip_py_R) * 0.1 - 0.0924"}),
        ("position", "cf_d_ana", {"z": "(hip_pz_L + hip_pz_R + 0.02) * 0.2 - 0.0296"}),
    ]
    return {"inputs": inputs, "values": values, "outputs": arms + legs + forearms + thighs + centre}


# The joint corrections (docs/design/joint-corrections.md).
CORRECTIONS = _corrections()

# The face rig's keys (Face Key Roles; KK's say more). SVS's open-mouth keys all carry the same jaw
# drop, and its lip-only (", Closed") keys move the lips clearly, so the lip moods use those.
FACE_KEYS = {
    "blink": "Eye Closed",
    "wink_l": "Eye Winking L", "wink_r": "Eye Winking R",
    "brows_up": "Eyebrow Excited", "brows_down": "Eyebrow Lonely", "brow_down_side": "Eyebrow Angry",
    "emote_sad_brows": "Eyebrow Worried", "emote_sad_eyes": "Eye Lonely",
    "emote_angry_brows": "Eyebrow Angry", "emote_angry_eyes": "Eye Angry",
    "corner_up": "Mouth Smiling, Closed", "corner_down": "Mouth Lonely, Closed", "corner_out": "Mouth Excited, Closed",
    "vowel_a": "Mouth A", "vowel_i": "Mouth I", "vowel_o": "Mouth O", "vowel_e": "Mouth E", "vowel_u": "Mouth U",
    "open_mood_up": "Mouth Hold In Mouth", "open_mood_down": "Mouth Lonely", "open_mood_left": "Mouth Displeased",
    "open_mood_right": "Mouth Impatient",
    "mood_up": "Mouth Smiling, Closed", "mood_down": "Mouth Lonely, Closed", "mood_left": "Mouth Displeased, Closed",
    "mood_right": "Mouth Smug, Closed",
    "mood2_up": "Mouth Catlike, Closed", "mood2_down": "Mouth Angry (Moderate), Closed",
    "mood2_left": "Mouth Hate, Closed", "mood2_right": "Mouth Impatient, Closed",
    "eyes_smiling": "Eye Smiling", "eyes_happy_closed": "Eye Happy, Closed", "eyes_half_lid": "Eye Displeased",
    "eyes_smug": "Eye Smug", "eyes_doubt": "Eye Doubt", "eyes_angry": "Eye Angry", "eyes_sad": "Eye Lonely",
    "brows_amazed": "Eyebrow Amazed", "brows_doubt": "Eyebrow Doubt", "brows_smiling": "Eyebrow Smiling",
    "brows_worried": "Eyebrow Worried", "brows_angry": "Eyebrow Angry",
    "open_smile": "Mouth Smiling", "open_cartoony": "Mouth Cartoony Smile", "open_excited": "Mouth Excited",
    "open_angry": "Mouth Angry", "open_hate": "Mouth Hate", "open_serious": "Mouth Serious",
    "open_triangle": "Mouth Triangle", "open_kiss": "Mouth Kiss", "open_catlike": "Mouth Catlike",
    "open_tongue": "Mouth Tongue Out", "open_playful": "Mouth Playful",
    "gag_eyes": "Gag eyes", "tears_small": "Tears small", "tears_med": "Tears med", "tears_big": "Tears big",
}
