"""The Character's Collection as an asset: it shows in the Asset Browser, tagged with its
Game, with the Card's picture as its preview.

The Card is a PNG with the game's data after the picture. Pillow reads only the picture, and the
preview holds pixels, so none of the Card's data goes into the .blend.
"""

from __future__ import annotations

PREVIEW_SIZE = 256  # pixels on each side: the Card is scaled into this square, centred, the rest clear
ICON_SIZE = 32  # the small icon list views draw


def mark_asset(ctx):
    """Marks the Character's Collection as an asset, tagged with its Game, with the Card as preview."""
    ch = ctx.character
    collection = ch.collection
    if collection is None:
        ctx.log.warning("The Character has no Collection, so it isn't marked as an asset")
        return
    collection.asset_mark()
    collection.asset_data.description = f"{ch.name} ({ch.game}), imported by KKBP"
    if ch.game:
        collection.asset_data.tags.new(ch.game, skip_if_exists=True)
    card = ctx.bundle.manifest.card
    if card is None:
        ctx.log.info("The bundle has no Card, so the asset has no preview")
        return
    try:
        preview = collection.preview_ensure()
        preview.image_size = (PREVIEW_SIZE, PREVIEW_SIZE)
        preview.image_pixels_float.foreach_set(square_pixels(card, PREVIEW_SIZE))
        preview.icon_size = (ICON_SIZE, ICON_SIZE)
        preview.icon_pixels_float.foreach_set(square_pixels(card, ICON_SIZE))
    except OSError as ex:
        ctx.log.warning(f"The Card couldn't be read, so the asset has no preview: {ex}")


def square_pixels(path, size: int) -> list[float]:
    """The picture in the PNG at `path`, scaled to fit a `size` square and centred on a clear one, as
    RGBA floats from the bottom row up, the order Blender's previews take. Pillow is required to
    import (`settings.require_pillow`), so it is there; it is imported here, not when the add-on
    loads, because the add-on must load without it to offer installing it."""
    from PIL import Image

    with Image.open(path) as card:
        picture = card.convert("RGBA")
    scale = size / max(picture.size)
    fitted = (max(1, round(picture.width * scale)), max(1, round(picture.height * scale)))
    picture = picture.resize(fitted, Image.Resampling.LANCZOS)
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.paste(picture, ((size - picture.width) // 2, (size - picture.height) // 2))
    data = square.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
    return [b / 255.0 for b in data]
