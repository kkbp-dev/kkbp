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
