"""Bone helpers for the Rigify Hook."""

from __future__ import annotations

from ...character import OUTFIT


def outfit_of(idblock):
    """The Outfit index of a Part or bone (D29), or None."""
    value = idblock.get(OUTFIT)
    return value if isinstance(value, int) else None


def copy_tags(source, target):
    """The bundle Id and Outfit a generated rig bone takes from its ORG- bone."""
    for prop in ("id", OUTFIT):
        if prop in source:
            target[prop] = source[prop]
