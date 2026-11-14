"""Writes small, valid Export Bundles for tests, so they go through the real open-and-check path.

    b = BundleBuilder("KK")          # the default Character: body, face, tears, gag eyes, one Outfit
    b.add_bone("cf_J_hair_2", parent="cf_j_head", group="hair", outfit=0)
    path = b.build(tmp_path)         # writes <tmp_path>/<yyyyMMddHHmmss>_<name>/ and returns it
    edit_json(path, "materials.json", lambda d: d["materials"].pop())   # break it for a negative test

The .glb files are real glTF 2.0 files: every mesh is one skinned triangle per material, at the
scene root, with a morph target per expression on it (ADR 0006), so Blender can import them too.
No bpy and nothing outside the standard library.
"""

from __future__ import annotations

import copy
import json
import math
import struct
import zlib
from pathlib import Path

GENERATOR = "KKBP test bundle builder"


class BundleBuilder:
    def __init__(self, game: str = "KK", name: str = "Test Chara", *, empty: bool = False):
        """The default Character, or with `empty=True` only a body root bone and nothing else."""
        self.game = game
        self.name = name
        self.schema_version = "1.2"
        self.card = True
        self.exported_at = "2026-11-01T12:00:00Z"
        self.bones: list[dict] = []
        self.materials: list[dict] = []
        self.passes: dict[object, dict] = {"body": {"kind": "body", "outfit": None, "meshes": []}}
        self.expressions: list[dict] = []
        self.effects: list[dict] = []
        self.chains: list[dict] = []
        self.colliders: list[dict] = []
        self._textures: list[tuple[str, tuple]] = []
        self._owner: dict[str, object] = {}
        self._skin_bone: dict[str, str] = {}
        self.add_bone("cf_n_height", parent=None, role="body_root")
        if not empty:
            self._default_character()

    # --- building blocks ----------------------------------------------------------------

    def add_bone(self, id, parent, *, group="deform", role=None, name=None, translation=(0.0, 0.0, 0.0),
                 rotation=(0.0, 0.0, 0.0, 1.0), outfit=None, game_scale=None):
        """A bone. Outfit-owned bones (`outfit=N`) are only in that Outfit's .glb (ADR 0009)."""
        bone = {"id": id, "name": name or id, "parent": parent, "group": group,
                "translation": list(translation), "rotation": list(rotation), "scale": [1.0, 1.0, 1.0]}
        if role:
            bone["role"] = role
        if game_scale is not None:
            bone["game_scale"] = list(game_scale)
        self.bones.append(bone)
        self._owner[id] = "body" if outfit is None else outfit
        return bone

    def add_texture(self, raw, *, role=None, variant=None, pattern=None, color=(255, 255, 255, 255)):
        """A texture entry with its own PNG file, for add_material or a body texture."""
        file = f"textures/{len(self._textures) + 1:04d}.png"
        self._textures.append((file, color))
        t = {"raw": raw, "file": file, "offset": [0.0, 0.0], "scale": [1.0, 1.0]}
        for key, value in (("role", role), ("variant", variant), ("pattern", pattern)):
            if value is not None:
                t[key] = value
        return t

    def add_material(self, id, *, role=None, blend_mode="opaque", shader="Shader Forge/main_skin",
                     textures=(), name=None, colors=None, floats=None, vectors=None, create=None):
        m = {"id": id, "name": name or id, "shader": shader, "blend_mode": blend_mode,
             "colors": colors or {"_Color": [1.0, 1.0, 1.0, 1.0]}, "floats": floats or {"_Cutoff": 0.5},
             "vectors": vectors or {}, "textures": list(textures)}
        if role:
            m["role"] = role
        if create:
            m["extensions"] = {"kk": {"create": create}}
        self.materials.append(m)
        return m

    def add_create(self, shader, *, colors=None, floats=None, textures=None):
        """A KK or KKS Create Material for add_material(create=…): a main texture and a colour mask
        unless `textures` is given."""
        if textures is None:
            textures = [self.add_texture("_MainTex", role="main"), self.add_texture("_ColorMask", role="color_mask")]
        return {"shader": shader, "colors": colors or {"_Color": [1.0, 0.5, 0.5, 1.0]},
                "floats": floats or {}, "vectors": {}, "textures": list(textures)}

    def add_outfit(self, index):
        self.passes.setdefault(index, {"kind": "outfit", "outfit": index, "meshes": []})
        return self.passes[index]

    def add_mesh(self, id, materials, *, outfit=None, bone="cf_n_height", alternate=False, name=None):
        """A mesh in the Body Pass, or in Outfit `outfit`'s Pass, skinned to `bone`."""
        p = self.passes["body"] if outfit is None else self.add_outfit(outfit)
        mesh = {"id": id, "name": name or id, "materials": list(materials), "alternate": alternate}
        p["meshes"].append(mesh)
        self._skin_bone[id] = bone
        return mesh

    def add_body_texture(self, outfit, material, texture):
        self.add_outfit(outfit).setdefault("body_textures", []).append({"material": material, "texture": texture})

    def add_expression(self, mesh, target, category, *, name=None, game_name=None):
        """An expression record. `name` defaults to `target` for categories other than `other`."""
        if name is None and category != "other":
            name = target
        e = {"mesh": mesh, "target": target, "category": category, "name": name, "game_name": game_name}
        self.expressions.append(e)
        return e

    def add_effect(self, target, *, shows=(), hides=(), material_changes=()):
        e = {"target": target}
        for key, value in (("shows", shows), ("hides", hides), ("material_changes", material_changes)):
            if value:
                e[key] = list(value)
        self.effects.append(e)
        return e

    def add_chain(self, root, particles, *, outfit=None, colliders=()):
        chain = {"root": root, "outfit": outfit, "gravity": [0.0, -0.01, 0.0], "force": [0.0, 0.0, 0.0],
                 "end_length": 0.0, "end_offset": [0.0, 0.0, 0.0], "weight": 1.0, "colliders": list(colliders),
                 "exclusions": [],
                 "particles": [{"bone": b, "damping": 0.1, "elasticity": 0.1, "stiffness": 0.1, "inert": 0.0,
                                "radius": 0.01} for b in particles]}
        self.chains.append(chain)
        return chain

    def add_collider(self, name, bone, *, outfit=None):
        c = {"name": name, "outfit": outfit, "bone": bone, "center": [0.0, 0.0, 0.0],
             "rotation": [0.0, 0.0, 0.0, 1.0], "radius": 0.05, "height": 0.1, "direction": "y", "bound": "outside"}
        self.colliders.append(c)
        return c

    # --- the default Character ----------------------------------------------------------

    def _default_character(self):
        self.add_bone("cf_j_hips", "cf_n_height", role="hips", translation=(0.0, 0.9, 0.0))
        self.add_bone("cf_j_spine01", "cf_j_hips", role="spine", translation=(0.0, 0.1, 0.0))
        self.add_bone("cf_j_neck", "cf_j_spine01", role="neck", translation=(0.0, 0.35, 0.0))
        self.add_bone("cf_j_head", "cf_j_neck", role="head", translation=(0.0, 0.1, 0.0))
        self.add_bone("cf_J_FaceRoot", "cf_j_head", role="face_root", group="face", translation=(0.0, 0.05, 0.0))
        self.add_bone("cf_J_hitomi_tx_L", "cf_J_FaceRoot", role="left_eye", group="eye",
                      translation=(0.03, 0.05, 0.08))
        self.add_bone("cf_J_hitomi_tx_R", "cf_J_FaceRoot", role="right_eye", group="eye",
                      translation=(-0.03, 0.05, 0.08))
        self.add_bone("cf_J_hairB_top", "cf_j_head", group="hair", translation=(0.0, 0.15, -0.02), outfit=0)
        self.add_bone("cf_J_hairB_00", "cf_J_hairB_top", group="hair", translation=(0.0, -0.1, -0.05), outfit=0)
        self.add_bone("N_Hair_pony", "cf_J_hairB_top", group="helper", outfit=0)

        self.add_material("cf_m_body", role="body", textures=[
            self.add_texture("_MainTex", role="main"),
            self.add_texture("_MainTex", role="main", variant="light"),
            self.add_texture("_MainTex", role="main", variant="dark"),
            self.add_texture("_NormalMap", role="normal"),
            self.add_texture("_liquidmask"),
        ])
        self.add_material("cf_m_face_00", role="face", shader="Shader Forge/main_skin",
                          textures=[self.add_texture("_MainTex", role="main")])
        self.add_material("cf_m_hitomi_00", role="eye_l", shader="Shader Forge/main_item",
                          textures=[self.add_texture("_MainTex", role="main"),
                                    self.add_texture("_overtex1", role="overlay"),
                                    self.add_texture("_overtex2", role="overlay")])
        self.add_material("cf_m_hitomi_00_2", role="eye_r", shader="Shader Forge/main_item",
                          textures=[self.add_texture("_MainTex", role="main")])
        self.add_material("c_m_namida", role="tears", blend_mode="alpha", shader="Shader Forge/main_alpha")
        self.add_material("cf_m_gageye_00", role="gag_eyes", blend_mode="alpha", textures=[
            self.add_texture("_MainTex", role="main", pattern="cf_t_gageye_00"),
            self.add_texture("_MainTex", role="main", pattern="cf_t_gageye_02"),
        ])
        self.add_material("c_m_hair_00", role="hair", shader="Shader Forge/main_hair",
                          textures=[self.add_texture("_MainTex", role="main"),
                                    self.add_texture("_ColorMask", role="color_mask")])
        self.add_material("ct_top_shirt", blend_mode="cutout", shader="Shader Forge/main_opaque",
                          textures=[self.add_texture("_MainTex", role="main"),
                                    self.add_texture("_AlphaMask", role="alpha_mask")])
        if self.game != "SVS":  # KK and KKS colour the body and clothes through Create Materials
            for m, shader in ((self.materials[0], "Shader Forge/create_body"),
                              (self.materials[-1], "Shader Forge/create_topN")):
                m["extensions"] = {"kk": {"create": self.add_create(shader)}}

        self.add_mesh("o_body_a", ["cf_m_body"], bone="cf_j_hips")
        self.add_mesh("cf_O_face", ["cf_m_face_00"], bone="cf_j_head")
        self.add_mesh("cf_Ohitomi_L", ["cf_m_hitomi_00"], bone="cf_J_hitomi_tx_L")
        self.add_mesh("cf_Ohitomi_R", ["cf_m_hitomi_00_2"], bone="cf_J_hitomi_tx_R")
        self.add_mesh("cf_O_namida_L", ["c_m_namida"], bone="cf_j_head")
        self.add_mesh("cf_O_gag_eye_00", ["cf_m_gageye_00"], bone="cf_j_head")
        self.add_mesh("o_hair_b", ["c_m_hair_00"], outfit=0, bone="cf_J_hairB_00")
        self.add_mesh("o_top_shirt", ["ct_top_shirt"], outfit=0, bone="cf_j_spine01")
        self.add_mesh("o_top_shirt_alt", ["ct_top_shirt"], outfit=0, bone="cf_j_spine01", alternate=True)
        self.add_body_texture(0, "cf_m_body", self.add_texture("_AlphaMask", role="alpha_mask"))

        self.add_expression("cf_O_face", "Eye Happy", "eye", game_name="笑い")
        self.add_expression("cf_O_face", "Eye Happy, Closed", "eye", game_name="笑い")
        self.add_expression("cf_O_face", "Mouth Default", "mouth", game_name="デフォルト")
        self.add_expression("cf_O_face", "eye_face.f00_custom", "other", game_name="eye_face.f00_custom")
        self.add_expression("cf_O_face", "Gag Heart Eyes", "gag", game_name="ハート目")
        self.add_expression("cf_O_namida_L", "Tears big", "tears")
        self.add_expression("cf_O_gag_eye_00", "Gag eye 00", "gag")
        self.add_effect("Gag Heart Eyes", shows=["cf_O_gag_eye_00"], hides=["cf_Ohitomi_L", "cf_Ohitomi_R"],
                        material_changes=[{"material": "cf_m_gageye_00",
                                           "textures": [{"raw": "_MainTex", "pattern": "cf_t_gageye_02"}],
                                           "floats": {"_AngleSpeed": 0.5}, "vectors": {"_TileAnimation": [1, 1, 1, 0]}}])

        self.add_collider("Col_Head", "cf_j_head")
        self.add_chain("cf_J_hairB_top", ["cf_J_hairB_top", "cf_J_hairB_00"], outfit=0, colliders=["Col_Head"])

    # --- output -------------------------------------------------------------------------

    def files(self) -> dict[str, dict]:
        """Every JSON file of the bundle, by relative path. Edit them before write() to break a rule."""
        passes = [self.passes["body"]] + [self.passes[k] for k in sorted(k for k in self.passes if k != "body")]
        out = {
            "manifest.json": {
                "game": self.game,
                "schema_version": self.schema_version,
                "exporter": {"name": GENERATOR, "version": "0.0.0"},
                "exported_at": self.exported_at,
                "character_name": self.name,
                "card": "card.png" if self.card else None,
                "options": {"all_outfits": False, "all_variations": False, "physics": True,
                            "enabled_shape_keys": False, "current_pose": False},
                "passes": [{"kind": p["kind"], "outfit": p["outfit"], "mesh": _mesh_file(p), "data": _data_file(p)}
                           for p in passes],
            },
            "character.json": {"name": self.name},
            "skeleton.json": {"bones": self.bones},
            "materials.json": {"materials": self.materials},
            "expressions.json": {"expressions": self.expressions, "effects": self.effects},
            "physics.json": {"chains": self.chains, "colliders": self.colliders},
        }
        for p in passes:
            out[_data_file(p)] = p
        return copy.deepcopy(out)

    def build(self, parent: Path, files: dict[str, dict] | None = None) -> Path:
        """Writes the bundle into a new folder under `parent` and returns that folder."""
        files = self.files() if files is None else files
        root = Path(parent) / f"{self.exported_at[:19].replace('-', '').replace(':', '').replace('T', '')}_{self.name}"
        root.mkdir(parents=True)
        for relative, data in files.items():
            if relative != "manifest.json":
                _write_json(root / relative, data)
        for file, color in self._textures:
            _write(root / file, png(color))
        if self.card:
            _write(root / "card.png", png((200, 120, 160, 255)))
        for p in self.passes.values():
            _write(root / _mesh_file(p), self.glb(p))
        if "manifest.json" in files:
            _write_json(root / "manifest.json", files["manifest.json"])  # written last, as the exporters do
        return root

    def glb(self, p: dict) -> bytes:
        """The .glb of one Pass: its bones as the node tree, and its meshes skinned at the scene root."""
        owner = p["outfit"] if p["kind"] == "outfit" else "body"
        bones = [b for b in self.bones if self._owner[b["id"]] in ("body", owner)]
        index = {b["id"]: i for i, b in enumerate(bones)}
        world = _world_matrices(bones)
        buf = _Buffer()
        nodes = []
        for b in bones:
            node = {"name": b["id"], "extras": {"id": b["id"]}, "translation": b["translation"],
                    "rotation": b["rotation"]}
            children = [index[c["id"]] for c in bones if c["parent"] == b["id"]]
            if children:
                node["children"] = children
            nodes.append(node)
        roots = [index[b["id"]] for b in bones if b["parent"] is None or b["parent"] not in index]
        ibm = buf.accessor(b"".join(struct.pack("<16f", *_column_major(_inverse_rigid(world[b["id"]])))
                                    for b in bones), "MAT4", len(bones))

        materials = []
        material_index = {}
        meshes = []
        for mesh_number, mesh in enumerate(p["meshes"]):
            targets = [e["target"] for e in self.expressions if e["mesh"] == mesh["id"]]
            bone = self._skin_bone.get(mesh["id"], bones[0]["id"])
            origin = [world[bone][r][3] for r in range(3)]
            primitives = []
            for k, material in enumerate(mesh["materials"]):
                if material not in material_index:
                    material_index[material] = len(materials)
                    materials.append({"name": material, "extras": {"id": material}})
                base = [origin[0] + 0.01 * mesh_number, origin[1] + 0.02 * k, origin[2]]
                positions = [base, [base[0] + 0.01, base[1], base[2]], [base[0], base[1] + 0.01, base[2]]]
                primitives.append({
                    "attributes": {
                        "POSITION": buf.vec3(positions),
                        "NORMAL": buf.vec3([[0.0, 0.0, 1.0]] * 3),
                        "JOINTS_0": buf.accessor(struct.pack("<4H", index[bone], 0, 0, 0) * 3, "VEC4", 3, 5123),
                        "WEIGHTS_0": buf.accessor(struct.pack("<4f", 1.0, 0.0, 0.0, 0.0) * 3, "VEC4", 3),
                    },
                    "material": material_index[material],
                    "targets": [{"POSITION": buf.vec3([[0.0, 0.0, 0.001 * (t + 1)]] * 3)} for t in range(len(targets))],
                })
                if not targets:
                    del primitives[-1]["targets"]
            gltf_mesh = {"name": mesh["id"], "extras": {"id": mesh["id"]}, "primitives": primitives}
            if targets:
                gltf_mesh["extras"]["targetNames"] = targets
            meshes.append(gltf_mesh)
            nodes.append({"name": mesh["id"], "extras": {"id": mesh["id"]}, "mesh": mesh_number, "skin": 0})

        gltf = {
            "asset": {"version": "2.0", "generator": GENERATOR},
            "scene": 0,
            "scenes": [{"nodes": roots + list(range(len(bones), len(nodes)))}],
            "nodes": nodes,
            "skins": [{"joints": list(range(len(bones))), "inverseBindMatrices": ibm, "skeleton": roots[0]}],
            "meshes": meshes,
            "materials": materials,
        }
        return buf.glb(gltf)


def edit_json(bundle: Path, relative: str, change):
    """Loads a bundle file, calls `change(data)` on it and writes it back."""
    path = Path(bundle) / relative
    data = json.loads(path.read_text(encoding="utf-8"))
    result = change(data)
    _write_json(path, data if result is None else result)


def png(rgba=(255, 255, 255, 255)) -> bytes:
    """A 1x1 RGBA PNG."""
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"\x00" + bytes(rgba))) + chunk(b"IEND", b""))


# --- helpers ----------------------------------------------------------------------------

def _mesh_file(p):
    return "body.glb" if p["kind"] == "body" else f"outfits/{p['outfit']:02d}/outfit.glb"


def _data_file(p):
    return "body.json" if p["kind"] == "body" else f"outfits/{p['outfit']:02d}/outfit.json"


def _write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _write_json(path: Path, data):
    _write(path, json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))


class _Buffer:
    def __init__(self):
        self.data = bytearray()
        self.views = []
        self.accessors = []

    def accessor(self, data: bytes, kind: str, count: int, component=5126, minmax=None):
        while len(self.data) % 4:
            self.data.append(0)
        self.views.append({"buffer": 0, "byteOffset": len(self.data), "byteLength": len(data)})
        self.data += data
        a = {"bufferView": len(self.views) - 1, "componentType": component, "count": count, "type": kind}
        if minmax:
            a["min"], a["max"] = minmax
        self.accessors.append(a)
        return len(self.accessors) - 1

    def vec3(self, rows):
        flat = b"".join(struct.pack("<3f", *r) for r in rows)
        packed = [struct.unpack("<3f", struct.pack("<3f", *r)) for r in rows]
        lo = [min(r[i] for r in packed) for i in range(3)]
        hi = [max(r[i] for r in packed) for i in range(3)]
        return self.accessor(flat, "VEC3", len(rows), minmax=(lo, hi))

    def glb(self, gltf: dict) -> bytes:
        gltf = dict(gltf, buffers=[{"byteLength": len(self.data)}], bufferViews=self.views, accessors=self.accessors)
        text = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
        text += b" " * (-len(text) % 4)
        binary = bytes(self.data) + b"\x00" * (-len(self.data) % 4)
        length = 12 + 8 + len(text) + 8 + len(binary)
        return (struct.pack("<4sII", b"glTF", 2, length) + struct.pack("<I4s", len(text), b"JSON") + text
                + struct.pack("<I4s", len(binary), b"BIN\x00") + binary)


def _world_matrices(bones):
    by_id = {b["id"]: b for b in bones}
    out = {}

    def world(bid):
        if bid not in out:
            b = by_id[bid]
            local = _trs(b["translation"], b["rotation"])
            parent = b["parent"]
            out[bid] = _matmul(world(parent), local) if parent in by_id else local
        return out[bid]

    for b in bones:
        world(b["id"])
    return out


def _trs(t, q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), t[0]],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), t[1]],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), t[2]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def _matmul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _inverse_rigid(m):
    r = [[m[j][i] for j in range(3)] for i in range(3)]  # transpose of the rotation
    t = [-sum(r[i][k] * m[k][3] for k in range(3)) for i in range(3)]
    return [r[0] + [t[0]], r[1] + [t[1]], r[2] + [t[2]], [0.0, 0.0, 0.0, 1.0]]


def _column_major(m):
    return [m[r][c] for c in range(4) for r in range(4)]
