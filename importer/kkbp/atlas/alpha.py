"""Folding an alpha mask into a texture's alpha, so an atlased material keeps its transparency
without an alpha-mask atlas (the legacy export prep's apply_alpha)."""

from __future__ import annotations

from PIL import Image, ImageChops


def apply_alpha_mask(texture: Image.Image, mask: Image.Image) -> Image.Image:
    """`texture` with its alpha multiplied by the mask's red times the mask's alpha."""
    texture = texture.convert("RGBA")
    mask = mask.convert("RGBA").resize(texture.size, Image.LANCZOS)
    red, _, _, mask_alpha = mask.split()
    r, g, b, alpha = texture.split()
    alpha = ImageChops.multiply(alpha, ImageChops.multiply(red, mask_alpha))
    return Image.merge("RGBA", (r, g, b, alpha))
