"""The contract rules the schemas can't express (contract/README.md), checked across files.

The rules that need the .glb files (the glTF Validator, `extras.id`, rest poses, morph targets) are
left to the contract tests: the importer hands .glb files out as paths and never reads them here.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from . import _contract as contract
from . import model

# Expression Name prefix -> category (contract/README.md, "Expression categories").
CATEGORY_BY_PREFIX = {"Eye": "eye", "Mouth": "mouth", "Eyebrow": "eyebrow", "Gag": "gag", "Tears": "tears"}
NO_EYESHADOW = ("light_no_eyeshadow", "dark_no_eyeshadow")  # they come as a pair, beside light and dark


def check(root: Path, manifest: model.Manifest, skeleton: model.Skeleton, materials: tuple[model.Material, ...],
          passes: tuple[model.Pass, ...], expressions: model.Expressions, physics: model.Physics) -> list[str]:
    problems: list[str] = []
    if manifest.card is not None and not manifest.card.is_file():
        problems.append("the Manifest names card.png but it is missing")
    bones = _bones(problems, skeleton)
    rel = lambda path: path.relative_to(root).as_posix()  # noqa: E731
    slots = _materials(problems, materials, rel)
    mesh_pass = _meshes(problems, passes, slots, rel)
    _creates(problems, materials, passes)
    _expressions(problems, expressions, mesh_pass, slots)
    _physics(problems, physics, bones)
    return problems


def pass_problems(manifest: model.Manifest) -> list[str]:
    """The Manifest's Pass list: one body Pass, each Outfit once, each in its own outfits/NN/.
    Checked before the Pass data files are read, since repeated Passes would repeat every mesh."""
    problems: list[str] = []
    bodies = [p for p in manifest.passes if p.kind == "body"]
    if len(bodies) != 1:
        problems.append(f"the Manifest lists {len(bodies)} body Passes; a bundle has exactly one")
    for outfit, count in Counter(p.outfit for p in manifest.passes if p.kind == "outfit").items():
        if count > 1:
            problems.append(f"the Manifest lists Outfit {outfit:02d} {count} times")
    for p in manifest.passes:
        if p.kind == "outfit" and not (p.mesh.startswith(f"outfits/{p.outfit:02d}/")
                                       and p.data.startswith(f"outfits/{p.outfit:02d}/")):
            problems.append(f"Outfit {p.outfit:02d}'s files {p.mesh} and {p.data} aren't in outfits/{p.outfit:02d}/")
    return problems


def _bones(problems, skeleton):
    ids = Counter(b.id for b in skeleton.bones)
    problems.extend(f"bone Id {i} appears twice" for i, n in ids.items() if n > 1)
    for b in skeleton.bones:
        if b.parent is not None and b.parent not in ids:
            problems.append(f"bone {b.id} has unknown parent {b.parent}")
    _unique(problems, "Bone Role", (b.role for b in skeleton.bones), contract.BONE_ROLES_UNIQUE)
    return set(ids)


def _materials(problems, materials, rel):
    """Checks materials and returns {material Id: set of (raw, variant, pattern) slots}."""
    ids = Counter(m.id for m in materials)
    problems.extend(f"material Id {i} appears twice" for i, n in ids.items() if n > 1)
    _unique(problems, "Material Role", (m.role for m in materials), contract.MATERIAL_ROLES_UNIQUE)
    slots = {}
    for m in materials:
        slots[m.id] = _textures(problems, f"material {m.id}", m.textures, rel)
        if m.create is not None:
            _textures(problems, f"material {m.id}'s create", m.create.textures, rel)
    return slots


def _textures(problems, what, textures, rel):
    """Checks one texture list and returns its set of (raw, variant, pattern) slots."""
    own = set()
    roles = set()
    for t in textures:
        slot = (t.raw, t.variant, t.pattern)
        if slot in own:
            problems.append(f"{what} repeats texture slot {_slot(slot)}")
        own.add(slot)
        if t.role in contract.TEXTURE_ROLES_UNIQUE:
            key = (t.role, t.variant, t.pattern)
            if key in roles:
                problems.append(f"{what} repeats Texture Role {_slot(key)}")
            roles.add(key)
        if not t.file.is_file():
            problems.append(f"{what} texture file {rel(t.file)} is missing")
    for raw, variant, pattern in sorted(own, key=str):
        if variant in NO_EYESHADOW:
            for needed in ("light", "dark", *NO_EYESHADOW):
                if (raw, needed, pattern) not in own:
                    problems.append(f"{what} has {raw} without eyeshadow but no {needed} Variant of it")
    return own


def _meshes(problems, passes, slots, rel):
    """Checks each Pass's meshes and body textures and returns {mesh Id: its Pass}."""
    mesh_pass = {}
    body_materials = set()
    for p in passes:
        for path in (p.mesh_path, p.data_path):
            if not path.is_file():
                problems.append(f"Pass file {rel(path)} is missing")
        for mesh in p.meshes:
            if mesh.id in mesh_pass:
                problems.append(f"mesh Id {mesh.id} appears twice")
            mesh_pass[mesh.id] = p
            for material in mesh.materials:
                if material not in slots:
                    problems.append(f"mesh {mesh.id} uses unknown material {material}")
                elif p.kind == "body":
                    body_materials.add(material)
    for p in passes:
        filled = set()
        for b in p.body_textures:
            t = b.texture
            slot = (t.raw, t.variant, t.pattern)
            if b.material not in body_materials:
                problems.append(f"{rel(p.data_path)} has a body texture on {b.material}, which no Body Pass mesh uses")
            elif slot in slots[b.material] or (b.material, slot) in filled:
                problems.append(f"{rel(p.data_path)} body texture {_slot(slot)} on {b.material} fills a slot "
                                "that is already filled")
            filled.add((b.material, slot))
            if not t.file.is_file():
                problems.append(f"{rel(p.data_path)} body texture file {rel(t.file)} is missing")
    return mesh_pass


def _creates(problems, materials, passes):
    """A material with a create is used by exactly one Pass: the Body Pass if it has a Material Role,
    an Outfit Pass if it has none."""
    for m in materials:
        if m.create is None:
            continue
        users = [p for p in passes if m.id in p.materials]
        want = "the Body Pass" if m.role else "an Outfit Pass"
        if len(users) != 1 or (users[0].kind == "body") != bool(m.role):
            problems.append(f"material {m.id} has a create but is used by {_passes(users)}, not only by {want}")


def _passes(passes):
    if not passes:
        return "no Pass"
    return ", ".join("the Body Pass" if p.kind == "body" else f"Outfit {p.outfit:02d}" for p in passes)


def _expressions(problems, expressions, mesh_pass, slots):
    seen = set()
    names = set()
    target_passes: dict[str, set[int]] = {}
    showing_keys = {e.mesh for e in expressions.records
                    if e.game_name is None and e.category in ("tears", "gag")}
    for e in expressions.records:
        if e.mesh not in mesh_pass:
            problems.append(f"expression {e.target} is on unknown mesh {e.mesh}")
        else:
            target_passes.setdefault(e.target, set()).add(id(mesh_pass[e.mesh]))
        if (e.mesh, e.target) in seen:
            problems.append(f"expression {e.target} appears twice on mesh {e.mesh}")
        seen.add((e.mesh, e.target))
        if e.name is not None:
            if (e.mesh, e.name) in names:
                problems.append(f"Expression Name {e.name} appears twice on mesh {e.mesh}")
            names.add((e.mesh, e.name))
            if e.target != e.name:
                problems.append(f"expression {e.name} has target name {e.target}")
            if CATEGORY_BY_PREFIX.get(e.name.split(" ")[0]) != e.category:
                problems.append(f"expression {e.name} has category {e.category}")
        target_passes.setdefault(e.target, set())

    effect_targets = set()
    for effect in expressions.effects:
        target = effect.target
        if target in effect_targets:
            problems.append(f"expression {target} has two effects entries")
        effect_targets.add(target)
        if target not in target_passes:
            problems.append(f"effects name expression {target}, which no record has")
            continue
        own = target_passes[target]
        for kind, meshes in (("shows", effect.shows), ("hides", effect.hides)):
            for mesh in meshes:
                if mesh not in mesh_pass or id(mesh_pass[mesh]) not in own:
                    problems.append(f"expression {target} {kind} mesh {mesh}, which isn't in its Pass")
                elif kind == "shows" and mesh not in showing_keys:
                    problems.append(f"expression {target} shows mesh {mesh}, which has no showing key")
        for change in effect.material_changes:
            if change.material not in slots:
                problems.append(f"expression {target} changes unknown material {change.material}")
                continue
            for t in change.textures:
                if not any(raw == t.raw and pattern == t.pattern for raw, _, pattern in slots[change.material]):
                    problems.append(f"expression {target} sets pattern {t.pattern} on {t.raw}, "
                                    f"which material {change.material} doesn't have")


def _physics(problems, physics, bones):
    names = Counter(c.name for c in physics.colliders)
    problems.extend(f"collider {n} appears twice" for n, k in names.items() if k > 1)
    for c in physics.colliders:
        _bone(problems, bones, c.bone, f"collider {c.name}")
    for chain in physics.chains:
        _bone(problems, bones, chain.root, "chain root")
        for c in chain.colliders:
            if c not in names:
                problems.append(f"chain {chain.root} uses unknown collider {c}")
        for b in chain.exclusions:
            _bone(problems, bones, b, f"chain {chain.root} exclusion")
        for p in chain.particles:
            _bone(problems, bones, p.bone, f"chain {chain.root} particle")


def _bone(problems, bones, bone, what):
    if bone not in bones:
        problems.append(f"{what} refers to unknown bone {bone}")


def _unique(problems, set_name, values, unique):
    for value, n in Counter(v for v in values if v in unique).items():
        if n > 1:
            problems.append(f"{set_name} {value} appears {n} times")


def _slot(slot):
    first, variant, pattern = slot
    return first + (f" ({variant})" if variant else "") + (f" [{pattern}]" if pattern else "")

