"""Reads each bundle file into its section, collecting every problem instead of stopping at one.

Unknown fields are ignored, as the Schema Version rules require. A value outside a closed set is
an error in a bundle whose minor version this importer knows, and a warning in a newer one: the
value is kept as a plain string, which the importer's own code never matches.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from types import MappingProxyType

from . import _contract as contract
from . import model

_BAD = object()
_ID = re.compile(contract.ID_PATTERN)
_TEXTURE_FILE = re.compile(r"^textures/[0-9]{4,}\.png$")
_OUTFIT_MESH = re.compile(r"^outfits/([0-9]{2})/outfit\.glb$")
_OUTFIT_DATA = re.compile(r"^outfits/([0-9]{2})/outfit\.json$")
_RFC3339_UTC = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z$")

# The Game Extensions each Game writes (export-bundle.md, "Shared core and Game Extensions").
GAME_EXTENSIONS = {"KK": ("kk",), "KKS": ("kk", "kks"), "SVS": ("svs",)}


class Reader:
    """Reads JSON files of one bundle. `errors` and `warnings` collect what it finds."""

    def __init__(self, root: Path):
        self.root = root
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.newer_minor = False
        self.game_extensions: tuple[str, ...] = ()
        self._warned: set[tuple[str, str]] = set()

    # --- files ------------------------------------------------------------------------

    def load(self, relative: str):
        """The parsed JSON of a bundle file, or _BAD (with an error) if it is missing or unreadable."""
        path = self.root / relative
        if not path.is_file():
            self.errors.append(f"{relative} is missing")
            return _BAD
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            self.errors.append(f"{relative} starts with a byte order mark; bundle JSON is UTF-8 without one")
            return _BAD
        try:
            return json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
        except UnicodeDecodeError as ex:
            self.errors.append(f"{relative} isn't UTF-8 ({ex.reason} at byte {ex.start})")
        except ValueError as ex:
            self.errors.append(f"{relative} isn't valid JSON ({ex})")
        return _BAD

    # --- values -----------------------------------------------------------------------

    def error(self, where: str, message: str):
        self.errors.append(f"{where}: {message}")
        return _BAD

    def field(self, obj: dict, key: str, where: str, check, optional=False):
        """obj[key] checked by `check`. A missing optional field is None."""
        if key not in obj:
            return None if optional else self.error(where, f"'{key}' is missing")
        return check(self, obj[key], f"{where}.{key}")

    def fields(self, obj, where: str, spec: dict):
        """{key: value} for every key in spec ({key: check or (check, optional)}), or _BAD."""
        if not isinstance(obj, dict):
            return self.error(where, "should be an object")
        out = {}
        for key, check in spec.items():
            optional = False
            if isinstance(check, tuple):
                check, optional = check
            out[key] = self.field(obj, key, where, check, optional)
        return _BAD if any(v is _BAD for v in out.values()) else out

    def closed(self, set_name: str, value: str, where: str, members) -> str:
        if value in members:
            return value
        if self.newer_minor:
            if (set_name, value) not in self._warned:
                self._warned.add((set_name, value))
                self.warnings.append(f"{where}: '{value}' isn't a {set_name} this importer knows; it is ignored")
            return value
        return self.error(where, f"'{value}' isn't a {set_name}")

    def extensions(self, value, where: str):
        """The Game Extensions of one section: {key: frozen mapping} for the keys the Game writes."""
        if value is None:
            value = {}
        elif not isinstance(value, dict):
            return self.error(where, "should be an object")
        out = {}
        for key in self.game_extensions:
            ext = value.get(key, {})
            if not isinstance(ext, dict):
                return self.error(f"{where}.{key}", "should be an object")
            out[key] = _freeze(ext)
        return MappingProxyType(out)


def _reject_constant(name):
    raise ValueError(f"{name} isn't a JSON number")


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


# --- checks: (reader, value, where) -> value or _BAD ------------------------------------

def string(r, v, where):
    return v if isinstance(v, str) else r.error(where, "should be a string")


def nonempty(r, v, where):
    if not isinstance(v, str) or not v:
        return r.error(where, "should be a non-empty string")
    return v


def nullable_string(r, v, where):
    return v if v is None or isinstance(v, str) else r.error(where, "should be a string or null")


def boolean(r, v, where):
    return v if isinstance(v, bool) else r.error(where, "should be true or false")


def number(r, v, where):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return r.error(where, "should be a number")
    return float(v)


def ident(r, v, where):
    if not isinstance(v, str) or not _ID.match(v):
        return r.error(where, f"{v!r} isn't a valid Id")
    return v


def nullable_ident(r, v, where):
    return None if v is None else ident(r, v, where)


def outfit_index(r, v, where):
    if isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 99:
        return r.error(where, "should be an Outfit index from 0 to 99")
    return v


def nullable_outfit(r, v, where):
    return None if v is None else outfit_index(r, v, where)


def vec(n):
    def check(r, v, where):
        if not isinstance(v, list) or len(v) != n:
            return r.error(where, f"should be a list of {n} numbers")
        items = [number(r, x, f"{where}[{i}]") for i, x in enumerate(v)]
        return _BAD if _BAD in items else tuple(items)
    return check


def one_of(set_name, members):
    def check(r, v, where):
        if not isinstance(v, str):
            return r.error(where, f"should be a {set_name}")
        return r.closed(set_name, v, where, members)
    return check


def nullable(check):
    def wrapped(r, v, where):
        return None if v is None else check(r, v, where)
    return wrapped


def list_of(check, min_items=0, unique=False):
    def wrapped(r, v, where):
        if not isinstance(v, list):
            return r.error(where, "should be a list")
        if len(v) < min_items:
            return r.error(where, f"should have at least {min_items} item{'s' if min_items > 1 else ''}")
        items = [check(r, x, f"{where}[{i}]") for i, x in enumerate(v)]
        if _BAD in items:
            return _BAD
        if unique and len(set(items)) != len(items):
            return r.error(where, "repeats an item")
        return tuple(items)
    return wrapped


def map_of(check):
    def wrapped(r, v, where):
        if not isinstance(v, dict):
            return r.error(where, "should be an object")
        items = {k: check(r, x, f"{where}.{k}") for k, x in v.items()}
        return _BAD if _BAD in items.values() else MappingProxyType(items)
    return wrapped


def extensions(r, v, where):
    return r.extensions(v, where)


def enum(*values):
    def check(r, v, where):
        if v not in values:
            return r.error(where, f"should be one of {', '.join(repr(x) for x in values)}")
        return v
    return check


VEC2, VEC3, VEC4 = vec(2), vec(3), vec(4)
OPTIONAL_EXTENSIONS = (extensions, True)


# --- sections ---------------------------------------------------------------------------

def schema_version(r, v, where):
    if not isinstance(v, str) or not re.match(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$", v):
        return r.error(where, f"{v!r} isn't a major.minor version")
    return v


def manifest_head(r: Reader, data) -> tuple | None:
    """The Manifest's Game and Schema Version, checked first because everything else depends on
    them. Sets r.newer_minor and r.game_extensions. Returns None (with errors) if the bundle can't
    be read at all."""
    head = r.fields(data, "manifest.json", {"game": string, "schema_version": schema_version})
    if head is _BAD:
        return None
    major, minor = (int(x) for x in head["schema_version"].split("."))
    if major != contract.SCHEMA_MAJOR:
        r.errors.append(f"manifest.json: Schema Version {head['schema_version']} isn't supported; "
                        f"this importer reads {contract.SCHEMA_MAJOR}.x. Update KKBP.")
        return None
    if minor > contract.SCHEMA_MINOR:
        r.newer_minor = True
        r.warnings.append(f"The bundle's Schema Version {head['schema_version']} is newer than this importer's "
                          f"{contract.SCHEMA_MAJOR}.{contract.SCHEMA_MINOR}; anything new in it is ignored.")
    if head["game"] not in contract.GAMES:
        r.errors.append(f"This importer doesn't support {head['game']}. Update KKBP.")
        return None
    r.game_extensions = GAME_EXTENSIONS[head["game"]]
    return head["game"], head["schema_version"]


def manifest(r: Reader, data, game: str, version: str) -> model.Manifest | None:
    where = "manifest.json"
    f = r.fields(data, where, {
        "exporter": lambda r, v, w: r.fields(v, w, {"name": nonempty, "version": nonempty}),
        "exported_at": _exported_at,
        "character_name": string,
        "card": lambda r, v, w: v if v is None or v == "card.png" else r.error(w, "should be 'card.png' or null"),
        "options": lambda r, v, w: r.fields(v, w, {
            "all_outfits": boolean, "all_variations": boolean, "physics": boolean,
            "enabled_shape_keys": boolean, "current_pose": boolean, "extensions": OPTIONAL_EXTENSIONS}),
        "passes": list_of(_pass_entry, min_items=1),
    })
    if f is _BAD:
        return None
    options = f["options"]
    if options["extensions"] is None:
        options["extensions"] = r.extensions({}, f"{where}.options.extensions")
    return model.Manifest(
        game=game,
        schema_version=version,
        exporter=model.Exporter(**f["exporter"]),
        exported_at=f["exported_at"],
        character_name=f["character_name"],
        card=None if f["card"] is None else r.root / f["card"],
        options=model.ExportOptions(**options),
        passes=f["passes"],
    )


def _exported_at(r, v, where):
    if not isinstance(v, str) or not _RFC3339_UTC.match(v):
        return r.error(where, "should be an RFC 3339 time in UTC")
    return v


def _pass_entry(r, v, where):
    f = r.fields(v, where, {"kind": enum("body", "outfit"), "outfit": nullable_outfit,
                            "mesh": string, "data": string})
    if f is _BAD:
        return _BAD
    if f["kind"] == "body":
        if f["outfit"] is not None or f["mesh"] != "body.glb" or f["data"] != "body.json":
            return r.error(where, "a body Pass has outfit null, mesh 'body.glb' and data 'body.json'")
    else:
        mesh, data = _OUTFIT_MESH.match(f["mesh"]), _OUTFIT_DATA.match(f["data"])
        if f["outfit"] is None or not mesh or not data:
            return r.error(where, "an Outfit Pass has an Outfit index, mesh 'outfits/NN/outfit.glb' "
                                  "and data 'outfits/NN/outfit.json'")
    return model.PassEntry(**f)


def character(r: Reader, data) -> model.Character | None:
    f = r.fields(data, "character.json", {"name": string, "extensions": OPTIONAL_EXTENSIONS})
    if f is _BAD:
        return None
    return model.Character(name=f["name"], extensions=f["extensions"] or r.extensions({}, ""))


def skeleton(r: Reader, data) -> model.Skeleton | None:
    f = r.fields(data, "skeleton.json", {"bones": list_of(_bone, min_items=1)})
    return None if f is _BAD else model.Skeleton(bones=f["bones"])


def _bone(r, v, where):
    f = r.fields(v, where, {
        "id": ident, "name": string, "parent": nullable_ident,
        "role": (one_of("Bone Role", contract.BONE_ROLES), True),
        "group": one_of("Bone Group", contract.BONE_GROUPS),
        "translation": VEC3, "rotation": VEC4, "scale": VEC3, "game_scale": (VEC3, True),
    })
    if f is _BAD:
        return _BAD
    if f["game_scale"] is None:
        del f["game_scale"]
    elif not all(c > 0 for c in f["game_scale"]):
        return r.error(f"{where}.game_scale", "should be above 0 on every axis")
    return model.Bone(**f)


def texture(r, v, where):
    f = r.fields(v, where, {
        "role": (one_of("Texture Role", contract.TEXTURE_ROLES), True),
        "raw": nonempty,
        "variant": (one_of("Texture Variant", contract.TEXTURE_VARIANTS), True),
        "pattern": (nonempty, True),
        "file": lambda r, v, w: v if isinstance(v, str) and _TEXTURE_FILE.match(v)
        else r.error(w, "should be a path like 'textures/0001.png'"),
        "offset": VEC2, "scale": VEC2,
    })
    if f is _BAD:
        return _BAD
    f["file"] = r.root / f["file"]
    return model.Texture(**f)


def materials(r: Reader, data) -> tuple[model.Material, ...] | None:
    f = r.fields(data, "materials.json", {"materials": list_of(_material)})
    return None if f is _BAD else f["materials"]


def _material(r, v, where):
    f = r.fields(v, where, {
        "id": ident, "name": string, "shader": string,
        "role": (one_of("Material Role", contract.MATERIAL_ROLES), True),
        "blend_mode": one_of("Blend Mode", contract.BLEND_MODES),
        "colors": map_of(VEC4), "floats": map_of(number), "vectors": map_of(VEC4),
        "textures": list_of(texture),
        "extensions": OPTIONAL_EXTENSIONS,
    })
    if f is _BAD:
        return _BAD
    f["extensions"] = f["extensions"] or r.extensions({}, where)
    # The Create Material: KK's and KKS's in `kk`, SVS's in `svs` (Schema Version 1.3).
    for game in ("kk", "svs"):
        section = f["extensions"].get(game)
        if section and "create" in section:
            f["create"] = _create(r, v["extensions"][game]["create"], f"{where}.extensions.{game}.create")
            if f["create"] is _BAD:
                return _BAD
            f["extensions"] = MappingProxyType({**f["extensions"],
                                                game: MappingProxyType({k: x for k, x in section.items() if k != "create"})})
    return model.Material(**f)


def _create(r, v, where):
    f = r.fields(v, where, {
        "shader": string,
        "colors": map_of(VEC4), "floats": map_of(number), "vectors": map_of(VEC4),
        "textures": list_of(texture),
    })
    return _BAD if f is _BAD else model.CreateMaterial(**f)


def pass_data(r: Reader, data, entry: model.PassEntry) -> model.Pass | None:
    where = entry.data
    f = r.fields(data, where, {
        "kind": enum("body", "outfit"), "outfit": nullable_outfit,
        "meshes": list_of(_mesh),
        "body_textures": (list_of(_body_texture, min_items=1), True),
        "extensions": OPTIONAL_EXTENSIONS,
    })
    if f is _BAD:
        return None
    if f["kind"] != entry.kind or f["outfit"] != entry.outfit:
        r.errors.append(f"{where} doesn't match its Manifest entry (kind {f['kind']}, outfit {f['outfit']})")
        return None
    if f["kind"] == "body" and f["body_textures"] is not None:
        r.errors.append(f"{where}: the Body Pass has no body_textures")
        return None
    return model.Pass(
        kind=f["kind"], outfit=f["outfit"],
        mesh_path=r.root / entry.mesh, data_path=r.root / entry.data,
        meshes=f["meshes"], body_textures=f["body_textures"] or (),
        extensions=f["extensions"] or r.extensions({}, where),
    )


def _mesh(r, v, where):
    f = r.fields(v, where, {"id": ident, "name": string, "materials": list_of(ident, min_items=1),
                            "alternate": boolean})
    return _BAD if f is _BAD else model.Mesh(**f)


def _body_texture(r, v, where):
    f = r.fields(v, where, {"material": ident, "texture": texture})
    return _BAD if f is _BAD else model.BodyTexture(**f)


def expressions(r: Reader, data) -> model.Expressions | None:
    f = r.fields(data, "expressions.json", {"expressions": list_of(_expression), "effects": list_of(_effect)})
    return None if f is _BAD else model.Expressions(records=f["expressions"], effects=f["effects"])


def _expression(r, v, where):
    f = r.fields(v, where, {
        "mesh": ident, "target": nonempty,
        "category": one_of("expression category", contract.EXPRESSION_CATEGORIES),
        "name": nullable(one_of("Expression Name", contract.EXPRESSION_NAMES)),
        "game_name": nullable_string,
        "extensions": OPTIONAL_EXTENSIONS,
    })
    if f is _BAD:
        return _BAD
    f["extensions"] = f["extensions"] or r.extensions({}, where)
    return model.Expression(**f)


def _effect(r, v, where):
    f = r.fields(v, where, {
        "target": nonempty,
        "shows": (list_of(ident, min_items=1, unique=True), True),
        "hides": (list_of(ident, min_items=1, unique=True), True),
        "material_changes": (list_of(_material_change, min_items=1), True),
    })
    if f is _BAD:
        return _BAD
    if not any(f[k] for k in ("shows", "hides", "material_changes")):
        return r.error(where, "names no shows, hides or material_changes")
    return model.Effect(target=f["target"], shows=f["shows"] or (), hides=f["hides"] or (),
                        material_changes=f["material_changes"] or ())


def _material_change(r, v, where):
    f = r.fields(v, where, {
        "material": ident,
        "textures": list_of(_texture_change),
        "floats": map_of(number), "vectors": map_of(VEC4),
    })
    return _BAD if f is _BAD else model.MaterialChange(**f)


def _texture_change(r, v, where):
    f = r.fields(v, where, {"raw": nonempty, "pattern": nonempty})
    return _BAD if f is _BAD else model.TextureChange(**f)


def physics(r: Reader, data) -> model.Physics | None:
    f = r.fields(data, "physics.json", {"chains": list_of(_chain), "colliders": list_of(_collider)})
    return None if f is _BAD else model.Physics(**f)


def _chain(r, v, where):
    f = r.fields(v, where, {
        "root": ident, "outfit": nullable_outfit, "gravity": VEC3, "force": VEC3,
        "end_length": number, "end_offset": VEC3, "weight": number,
        "colliders": list_of(string), "exclusions": list_of(ident),
        "particles": list_of(_particle, min_items=1),
    })
    return _BAD if f is _BAD else model.Chain(**f)


def _particle(r, v, where):
    f = r.fields(v, where, {"bone": ident, "damping": number, "elasticity": number,
                            "stiffness": number, "inert": number, "radius": number})
    return _BAD if f is _BAD else model.Particle(**f)


def _collider(r, v, where):
    f = r.fields(v, where, {
        "name": nonempty, "outfit": nullable_outfit, "bone": ident, "center": VEC3, "rotation": VEC4,
        "radius": number, "height": number, "direction": enum("x", "y", "z"), "bound": enum("outside", "inside"),
    })
    return _BAD if f is _BAD else model.Collider(**f)
