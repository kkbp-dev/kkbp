"""The Character's Collection as an asset with the Card as its preview, and the colours
of the Collections the import makes."""

import struct
import zlib

import pytest

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

character = submodule("character")
asset = submodule("steps.asset")
colors = submodule("collection_colors")
settings = submodule("settings")


def _import(build, monkeypatch, builder=None):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})
    result = kkbp.api.import_bundle(build(builder or BundleBuilder()), hooks=[])
    assert result.ok, f"{result.failed_step}: {result.error}"
    return character.Character(result.character_key)


def test_the_characters_collection_is_an_asset_tagged_with_its_game(build, monkeypatch):
    ch = _import(build, monkeypatch)
    data = ch.collection.asset_data
    assert data is not None
    assert [t.name for t in data.tags] == ["KK"]
    assert ch.name in data.description


def test_the_card_is_the_assets_preview(build, monkeypatch):
    ch = _import(build, monkeypatch)
    preview = ch.collection.preview
    assert tuple(preview.image_size) == (asset.PREVIEW_SIZE, asset.PREVIEW_SIZE)
    pixels = list(preview.image_pixels_float)
    # the builder's card is one pixel of (200, 120, 160): the whole square is that colour
    middle = (asset.PREVIEW_SIZE * asset.PREVIEW_SIZE // 2 + asset.PREVIEW_SIZE // 2) * 4
    assert pixels[middle:middle + 4] == pytest.approx([200 / 255, 120 / 255, 160 / 255, 1.0], abs=0.01)
    assert tuple(preview.icon_size) == (asset.ICON_SIZE, asset.ICON_SIZE)


def test_a_bundle_with_no_card_gives_an_asset_with_no_preview(build, monkeypatch):
    b = BundleBuilder()
    b.card = False
    ch = _import(build, monkeypatch, b)
    assert ch.collection.asset_data is not None
    preview = ch.collection.preview
    assert preview is None or tuple(preview.image_size) == (0, 0)


def _card(path, width, height, trailing=b""):
    """A `width` x `height` opaque red PNG with `trailing` after its end, as a game Card has its data."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    rows = b"".join(b"\x00" + b"\xff\x00\x00\xff" * width for _ in range(height))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
                     + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"") + trailing)
    return path


def test_a_tall_card_is_fitted_and_centred_and_its_data_left_out(tmp_path):
    card = _card(tmp_path / "card.png", 252, 352, trailing=b"KoiKatuChara" + bytes(5000))
    size = 64
    pixels = asset.square_pixels(card, size)
    assert len(pixels) == size * size * 4

    def alpha(x, y):  # y from the bottom, as Blender's previews go
        return pixels[(y * size + x) * 4 + 3]
    width = round(252 * size / 352)
    left = (size - width) // 2
    assert alpha(0, size // 2) == 0.0 and alpha(size - 1, size // 2) == 0.0  # clear beside the card
    assert alpha(left + 1, 0) == 1.0 and alpha(left + 1, size - 1) == 1.0  # the card fills the height
    assert alpha(left + width - 2, size // 2) == 1.0


def test_the_collections_take_their_colours(build, monkeypatch):
    b = BundleBuilder()
    ch = _import(build, monkeypatch, b)
    assert ch.collection.color_tag == colors.COLORS["character"]
    kinds = {c.name.split(" ")[0]: c.color_tag for c in ch.collection.children}
    assert kinds["Outfit"] == colors.COLORS["outfit"]
    assert kinds["Tears"] == colors.COLORS["face"]


def test_every_colour_is_one_of_blenders():
    import bpy

    tags = {item.identifier for item in bpy.types.Collection.bl_rna.properties["color_tag"].enum_items}
    assert set(colors.COLORS.values()) <= tags
