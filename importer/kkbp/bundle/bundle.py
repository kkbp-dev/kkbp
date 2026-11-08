"""Opening an Export Bundle."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from . import model, reader, rules
from .reader import _BAD

CACHE_FOLDER = "kkbp_cache"
_CACHE_KIND = re.compile(r"^[a-z0-9_]+$")


class BundleError(Exception):
    """An Export Bundle can't be opened. `problems` lists everything found wrong with it."""

    def __init__(self, path: Path, problems: list[str]):
        self.path = path
        self.problems = list(problems)
        super().__init__(str(self))

    def __str__(self):
        if len(self.problems) == 1:
            return f"Can't open the Export Bundle at {self.path}: {self.problems[0]}"
        lines = "".join(f"\n  - {p}" for p in self.problems)
        return f"Can't open the Export Bundle at {self.path} ({len(self.problems)} problems):{lines}"


@dataclass(frozen=True)
class Bundle:
    """An opened, checked Export Bundle. Read-only; .glb files and textures are handed out as paths."""

    path: Path
    manifest: model.Manifest
    character: model.Character
    skeleton: model.Skeleton
    materials: tuple[model.Material, ...]
    passes: tuple[model.Pass, ...]
    expressions: model.Expressions
    physics: model.Physics
    warnings: tuple[str, ...]
    _materials: Mapping[str, model.Material] = field(init=False, repr=False, compare=False)
    _meshes: Mapping[str, tuple[model.Mesh, model.Pass]] = field(init=False, repr=False, compare=False)

    def __post_init__(self):
        object.__setattr__(self, "_materials", MappingProxyType({m.id: m for m in self.materials}))
        object.__setattr__(self, "_meshes", MappingProxyType(
            {mesh.id: (mesh, p) for p in self.passes for mesh in p.meshes}))

    @property
    def game(self) -> str:
        return self.manifest.game

    def material(self, id: str) -> model.Material | None:
        return self._materials.get(id)

    def materials_with_role(self, role: str) -> tuple[model.Material, ...]:
        return tuple(m for m in self.materials if m.role == role)

    def mesh(self, id: str) -> model.Mesh | None:
        found = self._meshes.get(id)
        return found[0] if found else None

    def pass_of(self, mesh_id: str) -> model.Pass | None:
        """The Pass whose .glb holds this mesh."""
        found = self._meshes.get(mesh_id)
        return found[1] if found else None

    def extension(self, key: str) -> Mapping | None:
        """The Character's Game Extension `key` from character.json, or None for other Games."""
        return self.character.extension(key)

    def cache_dir(self, kind: str) -> Path:
        """The folder `kkbp_cache/<kind>/` inside the bundle, created if needed. Only the importer
        writes there, and deleting it is always safe."""
        if not _CACHE_KIND.match(kind):
            raise ValueError(f"cache kind {kind!r} should be lower-case letters, digits and underscores")
        path = self.path / CACHE_FOLDER / kind
        path.mkdir(parents=True, exist_ok=True)
        return path


def open_bundle(path) -> Bundle:
    """Opens and checks the Export Bundle in folder `path` (or the folder of its manifest.json).

    Raises BundleError listing every problem found. Problems that don't stop the import are in
    the returned bundle's `warnings`.
    """
    root = Path(path).expanduser().resolve()
    if root.is_file() and root.name == "manifest.json":
        root = root.parent
    if not root.is_dir():
        raise BundleError(root, ["the folder doesn't exist"])
    if not (root / "manifest.json").is_file():
        raise BundleError(root, ["there is no manifest.json, so this is an unfinished export or not an Export Bundle"])

    r = reader.Reader(root)
    data = r.load("manifest.json")
    head = None if data is _BAD else reader.manifest_head(r, data)
    if head is None:
        raise BundleError(root, r.errors)
    manifest = reader.manifest(r, data, *head)

    sections = {}
    for name, read in (("character", reader.character), ("skeleton", reader.skeleton),
                       ("materials", reader.materials), ("expressions", reader.expressions),
                       ("physics", reader.physics)):
        data = r.load(f"{name}.json")
        sections[name] = None if data is _BAD else read(r, data)

    passes = []
    pass_problems = rules.pass_problems(manifest) if manifest else []
    r.errors.extend(pass_problems)
    for entry in manifest.passes if manifest and not pass_problems else ():
        data = r.load(entry.data)
        passes.append(None if data is _BAD else reader.pass_data(r, data, entry))

    if r.errors:
        raise BundleError(root, r.errors)
    passes = tuple(passes)
    problems = rules.check(root, manifest, sections["skeleton"], sections["materials"], passes,
                           sections["expressions"], sections["physics"])
    if problems:
        raise BundleError(root, problems)
    return Bundle(path=root, manifest=manifest, passes=passes, warnings=tuple(r.warnings), **sections)
