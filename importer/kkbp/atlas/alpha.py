"""Folding an alpha mask into a texture's alpha, so an atlased material keeps its transparency
without an alpha-mask atlas (the legacy export prep's apply_alpha)."""

from __future__ import annotations

from PIL import Image, ImageChops


def apply_alpha_mask(texture: Image.Image, mask: Image.Image, inverted: bool = False) -> Image.Image:
    """`texture` with its alpha multiplied by the mask's red times the mask's alpha. An `inverted`
    mask (SVS's) shows where its red is black, so its red counts inverted (ADR 0057)."""
    texture = texture.convert("RGBA")
    mask = mask.convert("RGBA").resize(texture.size, Image.LANCZOS)
    red, _, _, mask_alpha = mask.split()
    if inverted:
        red = ImageChops.invert(red)
    r, g, b, alpha = texture.split()
    alpha = ImageChops.multiply(alpha, ImageChops.multiply(red, mask_alpha))
    return Image.merge("RGBA", (r, g, b, alpha))
