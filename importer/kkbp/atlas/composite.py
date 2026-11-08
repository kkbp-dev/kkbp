"""Painting the atlas with Pillow."""

from __future__ import annotations

from PIL import Image

from .layout import Layout, pixel_size, tile_counts


def compose(layout: Layout, pictures: dict, gaps: int = 0) -> Image.Image:
    """The atlas. `pictures` maps each piece's key to a Pillow image, or to an RGBA colour (0-255) for
    a material without one."""
    atlas = Image.new("RGBA", layout.size)
    half = int(gaps / 2)
    for key, p in layout.pieces.items():
        size = pixel_size(p, gaps)
        picture = pictures.get(key)
        if picture is None or isinstance(picture, tuple):
            tile = Image.new("RGBA", size, tuple(picture) if picture else (1, 1, 1, 1))
        else:
            tile = picture.convert("RGBA")
            if max(p.tiles) > 1:
                tile = _tiled(tile, p, size)
        atlas.paste(tile, (int(p.x + half), int(p.y + half)))
    return atlas


def _tiled(image, p, size):
    """The image repeated as often as the piece's UVs go past 1, from the bottom up."""
    out = Image.new("RGBA", size)
    width, height = image.size
    across, up = tile_counts(p)
    for row in range(up):
        y = size[1] - height - row * height
        for column in range(across):
            out.paste(image, (column * width, y))
    return out
