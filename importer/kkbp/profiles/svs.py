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


# The edit material tool (D38-D41; profiles/kk.py says what each table holds). SVS's templates follow
# its LIF shaders (issue 62, importer/tools/game_shaders/models.py); a shader none follows (the
# `_alpha` and `_low` copies, modded shaders) isn't editable. SVS's materials carry their textures by
# Raw Property, and their colours are the game's own, linear as its shaders see them.
EDIT = {
    "templates": {
        "eyebrow": "SVS lif_main_eyebrow",
        "eyelash": "SVS lif_main_eyelash_up",
        "eye_l": "SVS lif_main_eye", "eye_r": "SVS lif_main_eye", "eye_white": "SVS lif_main_eye",
        "hair": "SVS lif_main_hair",
    },
    "shader_templates": {},
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
    "channel_packed": ["color_mask", "iris_mask", "pupil", "highlight1", "highlight2", "highlight3", "shadow_mask",
                       "eyebrow", "eyelash_up", "eyelash_down", "detail1", "detail2"],
    "values": [
        # The eye white copies bake the eye white alone (ADR 0034).
        ["role:eye_white", {"eye_white_only": 1.0}],
        # An image node without an image reads black and opaque; the game's missing texture is
        # transparent.
        *[[f"missing:{slot}", {f"{slot}_present": 0.0}] for slot in _EYE_TEXTURES],
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
