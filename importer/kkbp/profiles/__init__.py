"""Game Profiles: the importer's data about each Game that can't come from the bundle
(docs/design/game-profile.md).

Each Game has a data-only module here (`kk`, `kks`, `svs`): tables and settings, no behaviour. A
profile may extend another and set only what differs; `get` resolves the chain. Game lists on Steps
are separate and never widened by `EXTENDS`.

This package never imports bpy and uses relative imports only, so host tests import it directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from . import kk, kks, svs
from .corrections import CorrectionError, Corrections, parse as _parse_corrections

_MODULES = {m.GAME: m for m in (kk, kks, svs)}
# What a profile module may set. Each is optional in a module that EXTENDS another, and replaces
# the base profile's value when set.
_FIELDS = ("TEMPLATE_SET", "RAW_TEXTURES", "PATTERN_VALUES", "BONES", "EDIT", "CORRECTIONS")


class ProfileError(Exception):
    """A Game has no profile, or a profile is wrong."""


@dataclass(frozen=True)
class BoneRule:
    """Bones a tail rule applies to, and how long their bone is.

    A rule names Bone Roles, or Bone Groups. A group rule applies only to bones with no Bone Role,
    and can be limited to bones `under` the bone with a Bone Role, or `outside` its subtree.
    """

    length: float
    roles: frozenset[str] = frozenset()
    groups: frozenset[str] = frozenset()
    under: str | None = None
    outside: str | None = None


@dataclass(frozen=True)
class BoneRules:
    """How bone tails and roll are set (ADR 0017).

    - `upright`: the first matching rule makes a bone point straight up (world +Z), roll 0.
    - `chains`: bones of these Bone Groups point at their only child's head, connected; a chain's
      last bone points straight down, as long as the value says.
    - Every other bone is aimed: its Y axis is the game bone's local -Z and its Z axis the game's
      local +Y, `aim_length` long.
    """

    aim_length: float
    upright: tuple[BoneRule, ...]
    chains: Mapping[str, float]


@dataclass(frozen=True)
class Source:
    """Where an edit value comes from: `create` (the Create Material), `own` (the material) or
    `current` (the material being edited), and a Texture Role or Raw Property, with a pattern."""

    where: str
    key: str
    pattern: str | None = None

    @property
    def raw(self) -> bool:
        return self.key.startswith("_")


@dataclass(frozen=True)
class EditColor:
    param: str
    sources: tuple[Source, ...]
    how: str  # item, skin, light, dark, eyew_dark, plain, alpha, float, vector, vector_z or vector_w


@dataclass(frozen=True)
class EditRules:
    """The edit material tool's tables (D38-D41); `profiles/kk.py` says what each holds."""

    templates: Mapping[str | None, str]
    shader_templates: Mapping[str, str]  # a shader's name after its last `/` -> template, before the Role's
    not_editable_blend_modes: frozenset[str]
    textures: Mapping[str, tuple[Source, ...]]
    saturated: frozenset[str]
    saturated_roles: frozenset[str]
    plain_color_mask_shaders: frozenset[str]
    shadow: tuple[Source, ...]
    colors: Mapping[str, tuple[EditColor, ...]]
    values: tuple[tuple[tuple[str, ...], Mapping[str, object]], ...]
    # Edit slots whose image keeps independent data in its alpha, which Blender must not associate
    # with the colour (alpha mode Channel Packed), as the game samples them.
    channel_packed: frozenset[str] = frozenset()


_WHERE = ("create", "own", "current")
_HOW = ("item", "skin", "light", "dark", "eyew_dark", "plain", "alpha", "float", "vector", "vector_z", "vector_w")
_CONDITIONS = ("role", "raw", "shader", "missing", "has", "create")


@dataclass(frozen=True)
class Profile:
    game: str
    extends: str | None
    template_set: str
    raw_textures: Mapping[str, str]  # Raw Property -> template texture slot
    pattern_values: Mapping[str, str]  # Raw Property (`.x` for a vector component) -> template param
    bones: BoneRules
    edit: EditRules
    corrections: Corrections  # the game's joint corrections (profiles/corrections.py)


def games() -> tuple[str, ...]:
    """Every Game that has a profile."""
    return tuple(_MODULES)


def get(game: str) -> Profile:
    """The resolved profile for `game`, or ProfileError if it has none."""
    if game not in _MODULES:
        raise ProfileError(f"This importer doesn't support {game}. Update KKBP.")
    return _resolve(game, ())


def _resolve(game, seen):
    if game in seen:
        raise ProfileError(f"profile {game} extends itself through {' -> '.join(seen)}")
    module = _MODULES[game]
    extends = getattr(module, "EXTENDS", None)
    values = {}
    if extends is not None:
        if extends not in _MODULES:
            raise ProfileError(f"profile {game} extends {extends}, which has no profile")
        base = _resolve(extends, seen + (game,))
        values = {"TEMPLATE_SET": base.template_set, "RAW_TEXTURES": dict(base.raw_textures),
                  "PATTERN_VALUES": dict(base.pattern_values), "BONES": base.bones, "EDIT": base.edit,
                  "CORRECTIONS": base.corrections}
    for name in _FIELDS:
        if hasattr(module, name):
            value = getattr(module, name)
            values[name] = value
    missing = [name for name in _FIELDS if name not in values]
    if missing:
        raise ProfileError(f"profile {game} doesn't set {', '.join(missing)}")
    bones = values["BONES"]
    return Profile(game=game, extends=extends, template_set=values["TEMPLATE_SET"],
                   raw_textures=MappingProxyType(dict(values["RAW_TEXTURES"])),
                   pattern_values=MappingProxyType(dict(values["PATTERN_VALUES"])),
                   bones=bones if isinstance(bones, BoneRules) else _bone_rules(game, bones),
                   edit=values["EDIT"] if isinstance(values["EDIT"], EditRules) else _edit_rules(game, values["EDIT"]),
                   corrections=_corrections(game, values["CORRECTIONS"]))


def _corrections(game, data):
    if isinstance(data, Corrections):
        return data
    try:
        return _parse_corrections(game, data)
    except CorrectionError as ex:
        raise ProfileError(str(ex)) from None


def _source(game, text):
    where, _, key = text.partition(":")
    pattern = None
    if key.endswith("]") and "[" in key:
        key, _, pattern = key[:-1].partition("[")
    if where not in _WHERE or not key:
        raise ProfileError(f"profile {game}: EDIT source {text!r} should be create:, own: or current: and a key")
    return Source(where, key, pattern)


def _edit_rules(game, data):
    try:
        colors = {}
        for template, rows in data["colors"].items():
            out = []
            for param, sources, how in rows:
                if how not in _HOW:
                    raise ProfileError(f"profile {game}: EDIT colour {param} has unknown kind {how!r}")
                out.append(EditColor(param, tuple(_source(game, x) for x in sources), how))
            colors[template] = tuple(out)
        values = []
        for when, params in data["values"]:
            terms = tuple(when.split())
            if any(t.partition(":")[0] not in _CONDITIONS for t in terms):
                raise ProfileError(f"profile {game}: EDIT condition {when!r} isn't role:, raw:, shader:, missing:, has: or create:")
            values.append((terms, MappingProxyType(dict(params))))
        return EditRules(
            templates=MappingProxyType(dict(data["templates"])),
            shader_templates=MappingProxyType(dict(data.get("shader_templates", {}))),
            not_editable_blend_modes=frozenset(data["not_editable_blend_modes"]),
            textures=MappingProxyType({slot: tuple(_source(game, x) for x in sources)
                                       for slot, sources in data["textures"].items()}),
            saturated=frozenset(data["saturated"]),
            saturated_roles=frozenset(data["saturated_roles"]),
            plain_color_mask_shaders=frozenset(data["plain_color_mask_shaders"]),
            shadow=tuple(_source(game, x) for x in data["shadow"]),
            colors=MappingProxyType(colors),
            values=tuple(values),
            channel_packed=frozenset(data.get("channel_packed", ())),
        )
    except (KeyError, TypeError, ValueError) as ex:
        raise ProfileError(f"profile {game}: EDIT is malformed ({ex})") from None


def _bone_rules(game, data):
    try:
        upright = tuple(BoneRule(length=float(r["length"]), roles=frozenset(r.get("roles", ())),
                                 groups=frozenset(r.get("groups", ())), under=r.get("under"),
                                 outside=r.get("outside"))
                        for r in data["upright"])
        return BoneRules(aim_length=float(data["aim_length"]), upright=upright,
                         chains=MappingProxyType({g: float(v) for g, v in data["chains"].items()}))
    except (KeyError, TypeError, ValueError) as ex:
        raise ProfileError(f"profile {game}: BONES is malformed ({ex})") from None


__all__ = ["BoneRule", "BoneRules", "Corrections", "EditColor", "EditRules", "Profile", "Source", "ProfileError", "games", "get"]
