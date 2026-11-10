#!/usr/bin/env python3
"""Writes the poses the exporters' correction probe runs (docs/design/joint-corrections.md): each
limb bone turned alone about each axis, then seeded random poses of all of them together.

Usage: correction_poses.py kk|kks|svs <poses.json>
"""

from __future__ import annotations

import json
import random
import sys

SIDED = ("cf_j_arm00", "cf_j_forearm01", "cf_j_hand", "cf_j_thigh00", "cf_j_leg01", "cf_j_leg03")
CENTRE = ("cf_j_spine03", "cf_j_head", "cf_j_waist02")
# How far each bone turns in the random poses, per axis, in degrees.
RANGE = {"cf_j_arm00": (60, 80, 80), "cf_j_forearm01": (20, 140, 20), "cf_j_hand": (60, 40, 60),
         "cf_j_thigh00": (110, 40, 60), "cf_j_leg01": (140, 10, 10), "cf_j_leg03": (40, 40, 20),
         "cf_j_spine03": (40, 40, 30), "cf_j_head": (40, 60, 30), "cf_j_waist02": (30, 30, 20)}
ANGLES = (-150, -120, -95, -85, -70, -55, -35, -15, 15, 35, 55, 70, 85, 95, 120, 150)


def poses(game: str) -> list[dict]:
    bones = [f"{b}_{s}" for b in SIDED for s in "LR"] + list(CENTRE)
    out: list[dict] = [{}]
    for bone in bones:
        for axis in range(3):
            for angle in ANGLES:
                e = [0.0, 0.0, 0.0]
                e[axis] = float(angle)
                out.append({bone: e})
    rng = random.Random(10)
    for _ in range(80):
        pose = {}
        for bone in bones:
            limit = RANGE[bone.rsplit("_", 1)[0] if bone[-2:] in ("_L", "_R") else bone]
            pose[bone] = [round(rng.uniform(-m, m), 2) for m in limit]
        out.append(pose)
    return out


if __name__ == "__main__":
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        json.dump(poses(sys.argv[1]), f)
