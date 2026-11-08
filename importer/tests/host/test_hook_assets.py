"""The Hook asset descriptions against the contract and the Template Descriptions.
tests/blender/test_hook_assets.py checks them against the files themselves."""

import library
from bundle import _contract
from library import hook_assets


def test_face_cards_name_material_roles():
    assert set(hook_assets.FACE_CARDS.textures.values()) <= set(_contract.MATERIAL_ROLES)


def test_outline_face_masks_are_keyed_by_template():
    assert set(hook_assets.OUTLINES.face_masks) <= set(library.TEMPLATES)


def test_each_file_is_next_to_the_template_library():
    for asset in hook_assets.FILES:
        assert asset.path.parent == library.LIBRARY.parent
