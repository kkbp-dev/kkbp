"""The export atlas's layout, UV remapping and compositing (D28). This package never imports bpy:
export prep (tools/export_prep/) gives it sizes and UV bounds and Pillow images, and applies what it
returns. It reproduces shotariya's Material Combiner as the legacy export prep used it (credited in
NOTICE): a square atlas with no gaps, images tiled where UVs go past 1, and a 32-pixel swatch for a
material with no image. Unlike the Combiner, which refused an atlas over 20000 px, the materials
of an atlas over the size the user picked are split over several atlases.
"""

from .alpha import apply_alpha_mask
from .composite import compose
from .layout import Layout, Piece, plan, plan_split, remap

__all__ = ["Layout", "Piece", "apply_alpha_mask", "compose", "plan", "plan_split", "remap"]
