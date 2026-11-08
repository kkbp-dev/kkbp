"""The export atlas's layout, UV remapping and compositing (kkbp/atlas/, D28)."""

from PIL import Image

import atlas
from atlas.layout import SWATCH


def test_pieces_are_packed_largest_first_into_a_square():
    layout = atlas.plan([atlas.Piece("small", (64, 64)), atlas.Piece("big", (128, 128)),
                         atlas.Piece("plain", None)])
    big, small, plain = (layout.pieces[k] for k in ("big", "small", "plain"))
    assert (big.x, big.y) == (0, 0)
    assert layout.size[0] == layout.size[1] >= 128
    for a, b in ((big, small), (big, plain), (small, plain)):
        assert a.x + a.size[0] <= b.x or b.x + b.size[0] <= a.x or a.y + a.size[1] <= b.y or b.y + b.size[1] <= a.y
    assert plain.size == (SWATCH, SWATCH)


def test_uvs_past_one_tile_the_image():
    layout = atlas.plan([atlas.Piece("tiled", (32, 32), max_uv=(2.0, 1.0))])
    assert layout.pieces["tiled"].size == (64.0, 32.0)
    picture = Image.new("RGBA", (32, 32), (255, 0, 0, 255))
    out = atlas.compose(layout, {"tiled": picture})
    assert out.size == (64, 64)
    assert out.getpixel((10, 10)) == (255, 0, 0, 255) and out.getpixel((40, 10)) == (255, 0, 0, 255)
    assert out.getpixel((10, 40)) == (0, 0, 0, 0)  # the square atlas's unused lower half


def test_uvs_land_inside_their_piece():
    layout = atlas.plan([atlas.Piece("a", (100, 100)), atlas.Piece("b", (50, 50))])
    width, height = layout.size
    for key in ("a", "b"):
        p = layout.pieces[key]
        for u, v in ((0, 0), (1, 1), (0.5, 0.25)):
            x, y = atlas.remap(layout, key, u, v)
            px, py = x * width, (1 - y) * height  # back to pixels, origin top left
            assert p.x <= px <= p.x + p.size[0] and p.y <= py <= p.y + p.size[1], (key, u, v, px, py)


def test_a_material_without_an_image_gets_its_colour():
    layout = atlas.plan([atlas.Piece("plain", None)])
    out = atlas.compose(layout, {"plain": (10, 20, 30, 255)})
    assert out.getpixel((5, 5)) == (10, 20, 30, 255)


def test_the_alpha_mask_folds_into_the_texture():
    texture = Image.new("RGBA", (4, 4), (200, 100, 50, 255))
    mask = Image.new("RGBA", (2, 2), (0, 0, 0, 255))
    mask.putpixel((0, 0), (255, 0, 0, 255))
    out = atlas.apply_alpha_mask(texture, mask)
    assert out.getpixel((0, 0)) == (200, 100, 50, 255)  # red mask keeps it
    assert out.getpixel((3, 3))[3] == 0  # black mask hides it
