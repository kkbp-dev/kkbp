"""Where each material's texture goes in the atlas, and where its UVs go."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

MAX_TILES = 25  # UVs past this many repeats are clamped, as in the Material Combiner
SWATCH = 32  # the square a material without an image gets
UV_MARGIN = 2  # pixels kept clear round each piece so its colours don't bleed (the Combiner's default)


@dataclass
class Piece:
    """One material: its texture's size (None for a material with no image) and the largest UV
    coordinates its faces use."""

    key: str
    image_size: tuple[int, int] | None
    max_uv: tuple[float, float] = (1.0, 1.0)
    tiles: tuple[float, float] = field(init=False, default=(1.0, 1.0))
    size: tuple[float, float] = field(init=False, default=(0.0, 0.0))
    x: float = field(init=False, default=0.0)
    y: float = field(init=False, default=0.0)


@dataclass
class Layout:
    pieces: dict[str, Piece]
    size: tuple[int, int]  # the atlas, in pixels


def plan(pieces: list[Piece], gaps: int = 0) -> Layout:
    """Packs the pieces, largest first, into one square atlas."""
    ordered = _largest_first(pieces, gaps)
    _pack(ordered)
    width = max((p.x + p.size[0] for p in ordered), default=1)
    height = max((p.y + p.size[1] for p in ordered), default=1)
    side = int(max(width, height, 1))
    return Layout({p.key: p for p in ordered}, (side, side))


def plan_split(pieces: list[Piece], gaps: int = 0, max_side: int | None = None) -> list[Layout]:
    """Packs the pieces into as many square atlases as it takes for none to be wider than `max_side`
    pixels (issue 12); one atlas, as `plan` makes it, if they all fit or there is no limit. Nothing is
    scaled down: each piece, largest first, goes in the first atlas it fits in, or starts another. A
    piece wider than `max_side` on its own gets an atlas to itself, which is then over the limit."""
    if max_side is None:
        return [plan(pieces, gaps)]
    groups: list[list[Piece]] = []
    for p in _largest_first(pieces, gaps):
        for group in groups:
            if plan(group + [p], gaps).size[0] <= max_side:
                group.append(p)
                break
        else:
            groups.append([p])
    return [plan(group, gaps) for group in groups]  # packed once more: a failed try moved the pieces


def _largest_first(pieces, gaps):
    for p in pieces:
        p.tiles = tuple(min(max(v, 1.0), MAX_TILES) for v in p.max_uv)
        if p.image_size is None:
            p.size = (SWATCH + gaps, SWATCH + gaps)
        else:
            p.size = tuple(s * t + gaps for s, t in zip(p.image_size, p.tiles))
    return sorted(pieces, key=lambda p: (max(p.size), p.size[0] * p.size[1], p.size[0], p.key), reverse=True)


def remap(layout: Layout, key: str, u: float, v: float, gaps: int = 0) -> tuple[float, float]:
    """A UV of material `key` in the atlas. The atlas's image origin is top left, Blender's UV
    origin bottom left."""
    p = layout.pieces[key]
    width, height = layout.size
    margin = gaps + UV_MARGIN
    border = int(gaps / 2) + UV_MARGIN // 2
    gfx_width, gfx_height = p.size
    x = u / p.tiles[0] * (gfx_width - margin)
    y = v / p.tiles[1] * (gfx_height - margin) - gfx_height
    return (x + p.x + border) / width, (y - (p.y - border)) / height + 1


def pixel_size(p: Piece, gaps: int = 0) -> tuple[int, int]:
    """The pixels a piece's picture takes, without its gap."""
    return tuple(int(s - gaps) for s in p.size)


def tile_counts(p: Piece) -> tuple[int, int]:
    return tuple(math.ceil(t) for t in p.tiles)


# --- the bin packer -------------------------------------------------------------------------
# Jake Gordon's growing binary-tree packer (MIT), as the Material Combiner used it.

def _pack(pieces):
    if not pieces:
        return
    root = {"x": 0, "y": 0, "w": pieces[0].size[0], "h": pieces[0].size[1]}
    state = {"root": root}
    for p in pieces:
        w, h = p.size
        node = _find(state["root"], w, h)
        node = _split(node, w, h) if node else _grow(state, w, h)
        p.x, p.y = node["x"], node["y"]


def _find(node, w, h):
    if node.get("used"):
        return _find(node["right"], w, h) or _find(node["down"], w, h)
    if w <= node["w"] and h <= node["h"]:
        return node
    return None


def _split(node, w, h):
    node["used"] = True
    node["down"] = {"x": node["x"], "y": node["y"] + h, "w": node["w"], "h": node["h"] - h}
    node["right"] = {"x": node["x"] + w, "y": node["y"], "w": node["w"] - w, "h": h}
    return node


def _grow(state, w, h):
    root = state["root"]
    can_right, can_down = h <= root["h"], w <= root["w"]
    should_right = can_right and root["h"] >= root["w"] + w
    should_down = can_down and root["w"] >= root["h"] + h
    if should_right or (not should_down and can_right):
        state["root"] = {"used": True, "x": 0, "y": 0, "w": root["w"] + w, "h": root["h"], "down": root,
                         "right": {"x": root["w"], "y": 0, "w": w, "h": root["h"]}}
    elif should_down or can_down:
        state["root"] = {"used": True, "x": 0, "y": 0, "w": root["w"], "h": root["h"] + h,
                         "down": {"x": 0, "y": root["h"], "w": root["w"], "h": h}, "right": root}
    else:
        raise ValueError(f"no room for a {w} x {h} piece")
    return _split(_find(state["root"], w, h), w, h)
