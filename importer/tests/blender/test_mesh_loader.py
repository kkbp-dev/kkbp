"""The Mesh Loader on the builder's .glb files and the golden samples."""

import json

import bpy
import pytest

from conftest import golden, submodule

mesh_loader = submodule("mesh_loader")


@pytest.fixture
def collection():
    c = bpy.data.collections.new("Chara")
    bpy.context.scene.collection.children.link(c)
    return c


@pytest.fixture(autouse=True)
def fresh_check(monkeypatch):
    monkeypatch.setattr(mesh_loader, "_checked_ok", False)


def test_every_option_it_sets_exists():
    assert mesh_loader.problems() == []


def test_it_sets_every_option_the_importer_has():
    assert mesh_loader.unset_options() == []


def test_a_missing_option_is_reported(monkeypatch):
    monkeypatch.setitem(mesh_loader.GLTF_OPTIONS, "import_vertex_ghosts", True)
    (message,) = mesh_loader.problems()
    assert message == f"glTF importer option import_vertex_ghosts no longer exists in Blender {bpy.app.version_string}"


def test_load_refuses_when_an_option_is_missing(monkeypatch, build, collection):
    monkeypatch.setitem(mesh_loader.GLTF_OPTIONS, "import_vertex_ghosts", True)
    with pytest.raises(mesh_loader.MeshLoaderError, match="import_vertex_ghosts no longer exists"):
        mesh_loader.load(build() / "body.glb", collection)


def test_loads_a_builder_pass(build, collection):
    path = build()
    loaded = mesh_loader.load(path / "body.glb", collection)
    data = json.loads((path / "body.json").read_text(encoding="utf-8"))
    assert sorted(loaded.meshes) == sorted(m["id"] for m in data["meshes"])
    assert {b.name for b in loaded.armature.data.bones} >= {"cf_n_height", "cf_j_hips", "cf_j_head", "cf_J_FaceRoot"}
    assert "cf_J_hairB_top" not in loaded.armature.data.bones  # Outfit-owned, only in the Outfit's .glb
    for m in data["meshes"]:
        obj = loaded.meshes[m["id"]]
        assert [s.material.get("id") for s in obj.material_slots] == m["materials"]
        assert obj.parent == loaded.armature or any(md.type == "ARMATURE" for md in obj.modifiers)


def test_everything_lands_in_the_given_collection(build, collection):
    loaded = mesh_loader.load(build() / "body.glb", collection)
    made = [loaded.armature, *loaded.meshes.values()]
    assert all(o.users_collection == (collection,) for o in made)
    assert set(collection.objects) == set(made)
    assert not [o for o in bpy.data.objects if o.name.startswith("Icosphere")]


def test_expressions_become_shape_keys(build, collection):
    loaded = mesh_loader.load(build() / "body.glb", collection)
    face = loaded.meshes["cf_O_face"]
    names = [k.name for k in face.data.shape_keys.key_blocks][1:]
    assert names == ["Eye Happy", "Eye Happy, Closed", "Mouth Default", "eye_face.f00_custom", "Gag Heart Eyes"]


def test_rest_pose_matches_the_skeleton(build, collection):
    loaded = mesh_loader.load(build() / "body.glb", collection)
    # glTF +Y up becomes Blender +Z up; the builder's head is 1.45 m above the root.
    head = loaded.armature.data.bones["cf_j_head"].head_local
    assert head.z == pytest.approx(1.45, abs=1e-5) and abs(head.x) < 1e-5


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_loads_the_golden_samples(sample, collection):
    bundle = golden(sample)
    for relative in ("body.glb", "outfits/00/outfit.glb"):
        data = json.loads((bundle / relative.replace(".glb", ".json")).read_text(encoding="utf-8"))
        loaded = mesh_loader.load(bundle / relative, collection)
        assert sorted(loaded.meshes) == sorted(m["id"] for m in data["meshes"])
        for m in data["meshes"]:
            assert [s.material.get("id") for s in loaded.meshes[m["id"]].material_slots] == m["materials"]
