"""The emotion presets, by Face Key Role, and how each poses the face rig: a preset moves the
controls that drive its roles (so it can be adjusted with them after), and sets the Face
Properties slider of a role no control drives."""

from __future__ import annotations

from . import board

# Each preset: Face Key Role -> how much of it.
PRESETS = {
    "Neutral": {},
    "Happy": {"eyes_smiling": 1.0, "open_smile": 1.0, "brows_smiling": 1.0},
    "Laugh": {"eyes_happy_closed": 1.0, "open_cartoony": 1.0, "brows_up": 0.5},
    "Gentle smile": {"eyes_smiling": 0.6, "mood_up": 1.0, "brows_smiling": 0.5},
    "Sad": {"eyes_sad": 1.0, "brows_worried": 1.0, "mood_down": 1.0},
    "Crying": {"eyes_sad": 1.0, "blink": 0.3, "brows_worried": 1.0, "open_mood_down": 1.0, "tears_med": 1.0},
    "Angry": {"eyes_angry": 1.0, "brows_angry": 1.0, "open_angry": 1.0},
    "Surprised": {"brows_up": 1.0, "vowel_o": 1.0},
    "Embarrassed": {"eyes_half_lid": 0.4, "brows_worried": 0.6, "mood_left": 1.0},
    "Smug": {"eyes_smug": 1.0, "brows_doubt": 0.5, "mood_right": 1.0},
    "Sleepy": {"blink": 0.55, "brows_down": 1.0, "vowel_a": 0.25},
    "Pained": {"eyes_happy_closed": 0.8, "brows_worried": 1.0, "mood2_down": 1.0},
}
GRID_BONES = tuple(board.bone_name(g) for g in board.JAW_GRIDS)  # placed, not scaled, by a preset


def resolve(keys, reach, raw) -> dict:
    """{preset: {"ops": [["loc", bone, index, value] or ["prop", key, value]], "expect": {key: value}}}.
    A role the Game has no key for is left out."""
    out = {}
    for preset, roles in PRESETS.items():
        ops, expect = [], {}
        for role, amount in roles.items():
            pairs = keys.get(role)
            if not pairs:
                continue
            if role in reach:
                for bone, index, full in reach[role]:
                    ops.append(["loc", bone, index, full if bone in GRID_BONES else full * amount])
            elif all(name in raw for name, _ in pairs):
                ops.extend(["prop", name, amount * weight] for name, weight in pairs)
            else:
                continue
            for name, weight in pairs:
                expect[name] = expect.get(name, 0.0) + amount * weight
        out[preset] = {"ops": ops, "expect": expect}
    return out
