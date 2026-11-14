"""The built-in Hooks' asset files and what each Hook takes from its file (D15).

Each Hook that needs assets owns one file next to library.blend, built with it by
scripts/build-library.sh (importer/tools/library/build.py, ADR 0040). These descriptions are the only place the Hooks find the files'
datablock and node names; a harness test checks every name against its file. Every datablock in
the files carries `kkbp_asset_version`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

HERE = Path(__file__).resolve().parent
ASSET_VERSION = 1
VERSION_PROP = "kkbp_asset_version"


@dataclass(frozen=True)
class RigifyAssets:
    """The fixed widget meshes the Rigify Hook gives its bones. Widgets it makes itself, such as the
    eye widgets, aren't in the file."""

    path: Path
    collection: str
    widgets: tuple[str, ...]


@dataclass(frozen=True)
class FaceCardAssets:
    """The face cards: two card meshes and the armature that poses them, in one collection.

    `textures` maps each card image node, as (material, node), to the Material Roles whose light
    texture goes into it, tried in order: SVS has no eyelines, so its eyelash takes the upper
    eyeline's place. A node none of them fills draws nothing.

    `eye_white_masks` maps the eye white material's template to the mask image that cuts the eye
    white out of its texture, which is laid out by the Game's eye UVs (ADR 0037).
    """

    path: Path
    collection: str
    bone_shapes: str  # the child collection with the card rig's bone shapes, kept out of the view layer
    rig: str
    meshes: tuple[str, ...]
    textures: Mapping[tuple[str, str], tuple[str, ...]]
    eye_white_mask: tuple[str, str]  # the mask's image node, as (material, node)
    eye_white_masks: Mapping[str, str]
    atlas: str  # the mouth atlas image, stored as WebP


@dataclass(frozen=True)
class OutlineAssets:
    """The images the Outlines Hook puts into outline materials."""

    path: Path
    black: str  # replaces the main texture: the outline is black and keeps the material's alpha
    placeholder: str  # an empty alpha mask
    face_masks: Mapping[str, str]  # face material's template -> the mask that hides the outline around the eyes
    # The face masks around which Body's outline also gets no thickness (ADR 0033). Each is white where
    # it hides the outline. Only SVS's: KK's eyelines sit on the face and need the outline's push.
    thinning_masks: frozenset[str]


RIGIFY = RigifyAssets(
    path=HERE / "rigify.blend",
    collection="Bone Widgets",
    widgets=("Custom1 Grid", "Custom2 Grid", "Eye Grid", "Mouth Grid", "WidgetBP", "WidgetBreastL", "WidgetBreastR",
             "WidgetBust", "WidgetChest", "WidgetEye", "WidgetFace", "WidgetFinger", "WidgetFingerThumb", "WidgetFoot",
             "WidgetHandL", "WidgetHandR", "WidgetHead", "WidgetHeel", "WidgetHips", "WidgetKnee", "WidgetNeck",
             "WidgetPelvis", "WidgetRoot", "WidgetShoulderL", "WidgetShoulderR", "WidgetSkirt", "WidgetSpine",
             "WidgetToe"),
)

FACE_CARDS = FaceCardAssets(
    path=HERE / "face_cards.blend",
    collection="Face cards",
    bone_shapes="Facecard bone shapes",
    rig="Face card rig",
    meshes=("Face card eyes", "Face card mouth"),
    textures=MappingProxyType({
        ("Eyeline card", "tex.eyeline_upper"): ("eyeline_upper", "eyelash"),
        ("Eyeline card", "tex.eyeline_shadow"): ("eyeline_shadow",),
        ("Eyeline card", "tex.eyeline_lower"): ("eyeline_lower",),
        ("Eyewhite card", "tex.eye_white"): ("eye_white",),
        ("Pupil L card", "tex.eye_l"): ("eye_l",),
        ("Pupil R card", "tex.eye_r"): ("eye_r",),
    }),
    eye_white_mask=("Eyewhite card", "tex.eye_white_mask"),
    eye_white_masks=MappingProxyType({"KK Light Dark": "Eye_White_Alpha", "SVS Light Dark": "SVS Eye_White_Alpha"}),
    atlas="MouthAtlas.webp",
)

# The face masks are drawn in each face mesh's UV layout, which follows the face's template.
OUTLINES = OutlineAssets(
    path=HERE / "outlines.blend",
    black="Template: BlackWithAlpha",
    placeholder="Template: Placeholder",
    face_masks=MappingProxyType({"KK Light Dark": "KK OutlineMask.png", "KK Light Dark Face": "KK OutlineMask.png",
                                 "SVS Light Dark": "SVS OutlineMask.png"}),
    thinning_masks=frozenset({"SVS OutlineMask.png"}),
)

FILES = (RIGIFY, FACE_CARDS, OUTLINES)
