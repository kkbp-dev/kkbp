"""Every name in the Hook asset descriptions against its file (library/hook_assets.py, D15)."""

import bpy
import pytest

from conftest import submodule

hook_assets = submodule("library.hook_assets")
appending = submodule("appending")


def _contents(path):
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        names = {k: list(getattr(source, k)) for k in ("collections", "objects", "materials", "images",
                                                      "node_groups", "meshes", "armatures")}
    return names


@pytest.mark.parametrize("asset", hook_assets.FILES, ids=lambda a: a.path.name)
def test_every_file_exists_and_every_datablock_carries_the_asset_version(asset):
    assert asset.path.is_file(), f"run scripts/build-library.sh: {asset.path.name} is missing"
    with bpy.data.libraries.load(str(asset.path), link=False) as (source, target):
        for kind in ("collections", "objects", "materials", "images", "node_groups"):
            setattr(target, kind, list(getattr(source, kind)))
    for kind in ("collections", "objects", "materials", "images", "node_groups"):
        for datablock in getattr(target, kind):
            assert datablock.get(hook_assets.VERSION_PROP) == hook_assets.ASSET_VERSION, f"{kind} {datablock.name}"


def test_rigify_widgets():
    names = _contents(hook_assets.RIGIFY.path)
    assert hook_assets.RIGIFY.collection in names["collections"]
    assert sorted(hook_assets.RIGIFY.widgets) == sorted(names["objects"])


def test_face_cards():
    cards = hook_assets.FACE_CARDS
    names = _contents(cards.path)
    assert {cards.collection, cards.bone_shapes} <= set(names["collections"])
    assert {cards.rig, *cards.meshes} <= set(names["objects"])
    assert cards.atlas in names["images"]
    assert set(cards.eye_white_masks.values()) <= set(names["images"])
    added = appending.append(cards.path, "collections", cards.collection, hook_assets.VERSION_PROP)
    collection = next(c for c in added if appending.base_name(c.name) == cards.collection)
    materials = {appending.base_name(s.material.name): s.material for o in collection.all_objects
                 for s in o.material_slots if s.material}
    for (material, node), roles in [*cards.textures.items(), (cards.eye_white_mask, "the eye white mask")]:
        assert material in materials, material
        found = materials[material].node_tree.nodes.get(node)
        assert found is not None and found.type == "TEX_IMAGE", f"{material}: no image node {node} for {roles}"
    mask = materials[cards.eye_white_mask[0]].node_tree.nodes[cards.eye_white_mask[1]].image
    assert mask is not None and mask.name == cards.eye_white_masks["KK Light Dark"]
    atlas = bpy.data.images[cards.atlas]
    assert atlas.file_format == "WEBP" and tuple(atlas.size) == (8192, 4480) and atlas.packed_file


def test_outline_images():
    outlines = hook_assets.OUTLINES
    names = _contents(outlines.path)
    assert {outlines.black, outlines.placeholder, *outlines.face_masks.values()} <= set(names["images"])


def test_shared_images_are_appended_once():
    cards = hook_assets.FACE_CARDS
    for _ in range(2):
        appending.append(cards.path, "collections", cards.collection, hook_assets.VERSION_PROP)
    assert len([i for i in bpy.data.images if appending.base_name(i.name) == cards.atlas]) == 1
