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


def test_a_smaller_picture_is_scaled_up_to_fill_its_place():
    # The KK body: a 4096 px light texture sets the place, its normal map is 1024 px (scaled down here).
    layout = atlas.plan([atlas.Piece("body", (64, 64))])
    normal = Image.new("RGBA", (16, 16), (62, 125, 237, 255))
    out = atlas.compose(layout, {"body": normal})
    for xy in ((2, 2), (40, 10), (10, 60), (63, 63)):  # far from the 16 px a corner paste would cover
        assert out.getpixel(xy) == (62, 125, 237, 255), xy


def test_a_larger_picture_is_scaled_down_to_its_place():
    layout = atlas.plan([atlas.Piece("small", (32, 32)), atlas.Piece("big", (64, 64))])
    picture = Image.new("RGBA", (128, 128), (10, 200, 30, 255))
    out = atlas.compose(layout, {"small": picture, "big": (0, 0, 0, 255)})
    small, big = layout.pieces["small"], layout.pieces["big"]
    assert out.getpixel((int(small.x) + 16, int(small.y) + 16)) == (10, 200, 30, 255)
    assert out.getpixel((int(big.x) + 5, int(big.y) + 5)) == (0, 0, 0, 255)
    below = (int(small.x) + 5, int(small.y + small.size[1]) + 5)  # the atlas's unused space under it
    assert below[1] < out.size[1] and out.getpixel(below) == (0, 0, 0, 0)  # the picture didn't spill out


def test_a_tiled_piece_repeats_its_picture_at_the_place_s_tile_size():
    layout = atlas.plan([atlas.Piece("tiled", (32, 32), max_uv=(2.0, 1.0))])
    picture = Image.new("RGBA", (8, 8), (0, 0, 255, 255))
    picture.putpixel((0, 0), (255, 255, 0, 255))  # marks each repeat's top left corner
    out = atlas.compose(layout, {"tiled": picture})
    assert out.getpixel((0, 0))[:3] == out.getpixel((32, 0))[:3]  # two repeats, 32 px apart
    assert out.getpixel((20, 20)) == (0, 0, 255, 255) and out.getpixel((52, 20)) == (0, 0, 255, 255)


def test_a_picture_for_a_piece_without_an_image_fills_its_swatch():
    layout = atlas.plan([atlas.Piece("plain", None)])
    out = atlas.compose(layout, {"plain": Image.new("RGBA", (4, 4), (9, 8, 7, 255))})
    assert out.getpixel((SWATCH - 1, SWATCH - 1)) == (9, 8, 7, 255)


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


def _big():
    return [atlas.Piece("body", (4096, 4096)), atlas.Piece("face", (4096, 4096)),
            atlas.Piece("top", (4096, 4096)), atlas.Piece("skirt", (4096, 4096)),
            atlas.Piece("shoes", (512, 1024)), atlas.Piece("plain", None)]


def test_an_atlas_over_the_cap_is_split_into_several():
    """Issue 12: four 4096 px materials don't fit one 4096 px atlas, so each gets its own, and the
    small ones share another. Nothing is scaled down."""
    assert atlas.plan(_big()).size[0] > 8192
    layouts = atlas.plan_split(_big(), max_side=4096)
    assert len(layouts) == 5 and all(l.size[0] <= 4096 for l in layouts)
    keys = [sorted(l.pieces) for l in layouts]
    assert sorted(k for group in keys for k in group) == ["body", "face", "plain", "shoes", "skirt", "top"]
    assert ["plain", "shoes"] in keys
    for layout in layouts:
        for p in layout.pieces.values():
            if p.image_size is not None:
                assert p.size == p.image_size  # never scaled down


def test_pieces_share_an_atlas_while_they_fit():
    layouts = atlas.plan_split(_big(), max_side=8192)
    assert len(layouts) == 2 and all(l.size[0] <= 8192 for l in layouts)
    assert len(layouts[0].pieces) == 4  # the four big ones fill the first


def test_an_atlas_under_the_cap_is_one_atlas_as_before():
    def pieces():
        return [atlas.Piece("a", (100, 100)), atlas.Piece("b", (50, 50)), atlas.Piece("c", (64, 32))]

    one, = atlas.plan_split(pieces(), max_side=8192)
    whole = atlas.plan(pieces())
    assert one.size == whole.size
    assert {k: (p.x, p.y) for k, p in one.pieces.items()} == {k: (p.x, p.y) for k, p in whole.pieces.items()}
    free, = atlas.plan_split(pieces())  # no cap
    assert free.size == whole.size


def test_a_piece_larger_than_the_cap_gets_an_atlas_of_its_own():
    """It isn't scaled down, so its atlas is over the cap; nothing else goes in with it."""
    layouts = atlas.plan_split([atlas.Piece("tiled", (1024, 1024), max_uv=(3.0, 1.0)), atlas.Piece("small", (256, 256))],
                               max_side=2048)
    assert [sorted(l.pieces) for l in layouts] == [["tiled"], ["small"]]
    assert layouts[0].size[0] == 3072 and layouts[1].size[0] <= 2048


def test_uvs_land_inside_their_piece_in_a_split_atlas():
    for layout in atlas.plan_split(_big(), max_side=4096):
        for key, p in layout.pieces.items():
            for u, v in ((0.0, 0.0), (1.0, 1.0)):
                x, y = atlas.remap(layout, key, u, v)
                assert p.x <= x * layout.size[0] <= p.x + p.size[0], key
                assert p.y <= (1 - y) * layout.size[1] <= p.y + p.size[1], key
