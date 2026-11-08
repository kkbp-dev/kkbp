"""The sections of an opened Export Bundle.

Every section is a frozen dataclass built when the bundle opens. Field names are the JSON field
names. Lists are tuples, maps are read-only mappings, vectors are tuples, and file paths are
absolute. All matching between sections uses Ids.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

EMPTY: Mapping = MappingProxyType({})


class _Extensible:
    """A section that can carry Game Extensions (`extensions.kk`, `extensions.svs`, …)."""

    extensions: Mapping[str, Mapping]

    def extension(self, key: str) -> Mapping | None:
        """This section's Game Extension `key`, or None if the bundle's Game doesn't write it.

        KK writes `kk`, KKS writes `kk` and `kks`, SVS writes `svs`. An extension the Game writes
        but left out is an empty mapping.
        """
        return self.extensions.get(key)


# --- manifest.json ----------------------------------------------------------------------

@dataclass(frozen=True)
class Exporter:
    name: str
    version: str


@dataclass(frozen=True)
class ExportOptions(_Extensible):
    all_outfits: bool
    all_variations: bool
    physics: bool
    enabled_shape_keys: bool
    current_pose: bool
    extensions: Mapping[str, Mapping]


@dataclass(frozen=True)
class PassEntry:
    """One Pass as the Manifest lists it. `mesh` and `data` are relative to the bundle."""

    kind: str
    outfit: int | None
    mesh: str
    data: str


@dataclass(frozen=True)
class Manifest:
    game: str
    schema_version: str
    exporter: Exporter
    exported_at: str
    character_name: str
    card: Path | None
    options: ExportOptions
    passes: tuple[PassEntry, ...]


# --- character.json ---------------------------------------------------------------------

@dataclass(frozen=True)
class Character(_Extensible):
    name: str
    extensions: Mapping[str, Mapping]


# --- skeleton.json ----------------------------------------------------------------------

@dataclass(frozen=True)
class Bone:
    id: str
    name: str
    parent: str | None
    role: str | None
    group: str
    translation: tuple[float, float, float]
    rotation: tuple[float, float, float, float]
    scale: tuple[float, float, float]


@dataclass(frozen=True)
class Skeleton:
    bones: tuple[Bone, ...]
    _by_id: Mapping[str, Bone] = field(init=False, repr=False, compare=False)
    _by_role: Mapping[str, Bone] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "_by_id", MappingProxyType({b.id: b for b in self.bones}))
        object.__setattr__(self, "_by_role", MappingProxyType(
            {b.role: b for b in reversed(self.bones) if b.role is not None}))

    def bone(self, id: str) -> Bone | None:
        return self._by_id.get(id)

    def by_role(self, role: str) -> Bone | None:
        """The bone with this Bone Role, or None. Every Bone Role is unique."""
        return self._by_role.get(role)

    def in_group(self, group: str) -> tuple[Bone, ...]:
        return tuple(b for b in self.bones if b.group == group)


# --- materials.json ---------------------------------------------------------------------

@dataclass(frozen=True)
class Texture:
    role: str | None
    raw: str
    variant: str | None
    pattern: str | None
    file: Path
    offset: tuple[float, float]
    scale: tuple[float, float]


class _Textured:
    """Shader data with textures: a material, or the Create Material that makes its main texture."""

    textures: tuple[Texture, ...]

    def texture(self, role: str, variant: str | None = None, pattern: str | None = None) -> Texture | None:
        """The texture with this Texture Role, Variant and pattern, or None.

        `variant=None` and `pattern=None` mean "no variant" and "no pattern", not "any".
        `overlay` may repeat, so it raises ValueError here; use `textures_with_role`.
        """
        if role == "overlay":
            raise ValueError("overlay textures may repeat; use textures_with_role('overlay')")
        for t in self.textures:
            if t.role == role and t.variant == variant and t.pattern == pattern:
                return t
        return None

    def textures_with_role(self, role: str) -> tuple[Texture, ...]:
        """Every texture with this Texture Role, in the game's order."""
        return tuple(t for t in self.textures if t.role == role)

    def textures_for(self, raw: str) -> tuple[Texture, ...]:
        """Every texture in the slot with this Raw Property: all its Variants and patterns."""
        return tuple(t for t in self.textures if t.raw == raw)


@dataclass(frozen=True)
class CreateMaterial(_Textured):
    """The KK or KKS game material that composites a material's main texture (`extensions.kk.create`).

    Its `main` texture is the uncoloured base the game colours; its colours, masks and layers are what
    the game composites onto it.
    """

    shader: str
    colors: Mapping[str, tuple[float, float, float, float]]
    floats: Mapping[str, float]
    vectors: Mapping[str, tuple[float, float, float, float]]
    textures: tuple[Texture, ...]


@dataclass(frozen=True)
class Material(_Extensible, _Textured):
    id: str
    name: str
    shader: str
    role: str | None
    blend_mode: str
    colors: Mapping[str, tuple[float, float, float, float]]
    floats: Mapping[str, float]
    vectors: Mapping[str, tuple[float, float, float, float]]
    textures: tuple[Texture, ...]
    extensions: Mapping[str, Mapping]
    # Read from `extensions.kk.create`, which then no longer holds it. None if the material has none.
    create: CreateMaterial | None = None


# --- body.json and outfits/NN/outfit.json -----------------------------------------------

@dataclass(frozen=True)
class Mesh:
    id: str
    name: str
    materials: tuple[str, ...]
    alternate: bool


@dataclass(frozen=True)
class BodyTexture:
    """A texture an Outfit puts on a body material."""

    material: str
    texture: Texture


@dataclass(frozen=True)
class Pass(_Extensible):
    kind: str
    outfit: int | None
    mesh_path: Path
    data_path: Path
    meshes: tuple[Mesh, ...]
    body_textures: tuple[BodyTexture, ...]
    extensions: Mapping[str, Mapping]

    @property
    def materials(self) -> tuple[str, ...]:
        """The Ids of the materials this Pass's meshes use, in first-use order."""
        return tuple(dict.fromkeys(m for mesh in self.meshes for m in mesh.materials))


# --- expressions.json -------------------------------------------------------------------

@dataclass(frozen=True)
class Expression(_Extensible):
    mesh: str
    target: str
    category: str
    name: str | None
    game_name: str | None
    extensions: Mapping[str, Mapping]


@dataclass(frozen=True)
class TextureChange:
    raw: str
    pattern: str


@dataclass(frozen=True)
class MaterialChange:
    material: str
    textures: tuple[TextureChange, ...]
    floats: Mapping[str, float]
    vectors: Mapping[str, tuple[float, float, float, float]]


@dataclass(frozen=True)
class Effect:
    """What the game does besides moving vertices while the expression `target` is on."""

    target: str
    shows: tuple[str, ...]
    hides: tuple[str, ...]
    material_changes: tuple[MaterialChange, ...]


@dataclass(frozen=True)
class Expressions:
    records: tuple[Expression, ...]
    effects: tuple[Effect, ...]
    _effects: Mapping[str, Effect] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "_effects", MappingProxyType({e.target: e for e in self.effects}))

    def effect(self, target: str) -> Effect | None:
        return self._effects.get(target)

    def on_mesh(self, mesh: str) -> tuple[Expression, ...]:
        return tuple(e for e in self.records if e.mesh == mesh)


# --- physics.json -----------------------------------------------------------------------

@dataclass(frozen=True)
class Particle:
    bone: str
    damping: float
    elasticity: float
    stiffness: float
    inert: float
    radius: float


@dataclass(frozen=True)
class Chain:
    root: str
    outfit: int | None
    gravity: tuple[float, float, float]
    force: tuple[float, float, float]
    end_length: float
    end_offset: tuple[float, float, float]
    weight: float
    colliders: tuple[str, ...]
    exclusions: tuple[str, ...]
    particles: tuple[Particle, ...]


@dataclass(frozen=True)
class Collider:
    name: str
    outfit: int | None
    bone: str
    center: tuple[float, float, float]
    rotation: tuple[float, float, float, float]
    radius: float
    height: float
    direction: str
    bound: str


@dataclass(frozen=True)
class Physics:
    chains: tuple[Chain, ...]
    colliders: tuple[Collider, ...]
