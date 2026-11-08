"""Export prep with no target: the readable bone names only, as the legacy armature had them."""

from __future__ import annotations

from . import common


def prepare(ch, skeleton, log):
    common.rename(ch.armature, common.readable_names(ch.armature, skeleton))
