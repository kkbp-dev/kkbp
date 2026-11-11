#!/usr/bin/env python3
"""Writes the poses the exporters' correction probe runs (docs/design/joint-corrections.md): each
limb bone turned alone about each axis, then seeded random poses of all of them together.

Usage: correction_poses.py kk|kks|svs <poses.json>
       correction_poses.py --trim kk|kks|svs <probe output> <test data.json.gz>

--trim keeps what the importer's tests need from a probe's output: the bones the Game Profile's
CORRECTIONS name and their ancestors, and in each pose the moves of those bones only.
"""

from __future__ import annotations

import gzip
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "kkbp"))
from profiles import corrections, kk, kks, svs  # noqa: E402  (the add-on's bpy-free profiles)

_MODULES = {"kk": kk, "kks": kks, "svs": svs}

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


def _rules(game):
    module = _MODULES[game]
    data = getattr(module, "CORRECTIONS", None) or getattr(_MODULES[module.EXTENDS.lower()], "CORRECTIONS")
    return corrections.parse(module.GAME, data)


def _round(v):
    return [float(f"{c:.7g}") for c in v]


def trim(game: str, raw: dict) -> dict:
    parents = {b["name"]: b["parent"] for b in raw["bones"]}
    keep = set()
    for name in _rules(game).bones():
        while name is not None and name in parents and name not in keep:
            keep.add(name)
            name = parents[name]
    bones = [{**b, "position": _round(b["position"]), "rotation": _round(b["rotation"]),
              "scale": _round(b["scale"]), "lossy_scale": _round(b["lossy_scale"])}
             for b in raw["bones"] if b["name"] in keep]
    out = []
    for p in raw["poses"]:
        moved = [{"name": m["name"], "position": _round(m["position"]), "rotation": _round(m["rotation"]),
                  "scale": _round(m["scale"])} for m in p["moved"] if m["name"] in keep]
        out.append({"set": {k: _round(v) for k, v in p["set"].items()}, "moved": moved})
    return {"bones": bones, "poses": out}


if __name__ == "__main__":
    if sys.argv[1] == "--trim":
        with open(sys.argv[3], encoding="utf-8") as f:
            raw = json.load(f)
        with gzip.open(sys.argv[4], "wt", encoding="utf-8") as f:
            json.dump(trim(sys.argv[2], raw), f, separators=(",", ":"))
    else:
        with open(sys.argv[2], "w", encoding="utf-8") as f:
            json.dump(poses(sys.argv[1]), f)
