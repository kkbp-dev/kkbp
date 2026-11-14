"""Checks bundle files against the contract's JSON Schemas with jsonschema (a dev dependency)."""

import json

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from conftest import SCHEMAS

SCHEMA_FOR = {
    "manifest.json": "manifest.schema.json",
    "character.json": "character.schema.json",
    "skeleton.json": "skeleton.schema.json",
    "materials.json": "materials.schema.json",
    "expressions.json": "expressions.schema.json",
    "physics.json": "physics.schema.json",
}


def _registry():
    resources = []
    for path in sorted(SCHEMAS.rglob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources), dict(resources)


_REGISTRY, _BY_ID = _registry()
_BASE = "https://schemas.kkbp.invalid/1.2/"


def problems(bundle_dir):
    """Every schema problem in a bundle folder, as 'file: path: message' strings."""
    out = []
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    files = dict(SCHEMA_FOR)
    files.update({p["data"]: "pass.schema.json" for p in manifest["passes"]})
    for file, schema in files.items():
        validator = Draft202012Validator(_BY_ID[_BASE + schema].contents, registry=_REGISTRY)
        data = json.loads((bundle_dir / file).read_text(encoding="utf-8"))
        for error in validator.iter_errors(data):
            out.append(f"{file}: {'/'.join(str(p) for p in error.absolute_path)}: {error.message}")
    return out
