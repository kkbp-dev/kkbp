"""Export prep for VRChat: as VRM, with the upper chest merged too, since it breaks VRChat's eye
tracking."""

from __future__ import annotations

from . import vrm


def prepare(ch, skeleton, log):
    upper_chest = skeleton.by_role("upper_chest")
    vrm.prepare(ch, skeleton, log, extra_merged=("Upper Chest",) if upper_chest else ())
