"""The Low poly Hook on a copy of the KK golden sample, after Outlines and Rigify."""

import bpy
import pytest

from conftest import submodule

low_poly = submodule("builtin.low_poly")
outlines = submodule("builtin.outlines")
colors = submodule("collection_colors")
steps = submodule("pipeline.steps")
character = submodule("character")

HOOKS = ["Outlines", "Rigify", "Low poly"]
OPTIONS = {"use_outlines": True, "use_rigify": True, "low_poly": "medium"}


@pytest.fixture
def ch(golden_import):
    """The import, made once and opened afresh for each test."""
    result, ch = golden_import("kk", hooks=HOOKS, options=OPTIONS)
    assert [h.status for h in result.hooks] == ["ran"] * len(HOOKS), result.hooks
    return ch


def _original(ch, copy):
    return next(o for o in ch.parts(low_poly.COPIED) if copy.name == f"{o.name}{low_poly.SUFFIX}")


def test_the_hook_is_off_by_default_and_runs_after_every_hook_that_changes_meshes():
    assert low_poly.SWITCH.default == "off"
    order = steps.BUILTIN_HOOKS
    assert order.index("Low poly") > max(order.index(h) for h in ("Separate meshes", "Outlines", "SFW", "Rigify"))
    assert order[-1] == "Delete default scene"


def test_each_outfit_part_and_hair_gets_one_low_poly_copy(ch):
    copies = ch.parts("low_poly")
    originals = ch.parts(low_poly.COPIED)
    assert len(copies) == len(originals) > 0
    for copy in copies:
        original = _original(ch, copy)
        assert copy.get(character.OUTFIT) == original.get(character.OUTFIT)
        assert copy.data is not original.data
    assert ch.outfits and all(o.get(character.ROLE) == "outfit" for o in ch.outfits)  # the originals keep their role


def test_the_copies_have_about_the_presets_share_of_faces(ch):
    ratio = low_poly.RATIOS["medium"]
    for copy in ch.parts("low_poly"):
        original = _original(ch, copy)
        share = len(copy.data.polygons) / len(original.data.polygons)
        assert ratio * 0.6 < share < ratio * 1.4, (copy.name, share)


def test_the_copies_have_no_outline_but_keep_the_materials_and_weights(ch):
    for copy in ch.parts("low_poly"):
        original = _original(ch, copy)
        assert not [m for m in copy.modifiers if m.type == "SOLIDIFY"]
        assert [m for m in original.modifiers if m.type == "SOLIDIFY"]  # the original keeps its outline
        own = [m for m in original.data.materials if m is not None and not m.get(outlines.OUTLINE)]
        assert list(copy.data.materials) == own
        assert {g.name for g in copy.vertex_groups} == {g.name for g in original.vertex_groups}
        weighted = sum(1 for v in copy.data.vertices if v.groups)
        assert weighted == len(copy.data.vertices)
        armature = [m for m in copy.modifiers if m.type == "ARMATURE"]
        assert len(armature) == 1 and armature[0].object == ch.rig
        assert not [m for m in copy.modifiers if m.type == "DECIMATE"]  # applied, not left on


def test_the_copies_are_in_a_hidden_yellow_collection_per_outfit_that_shows_the_outfit(ch):
    for copy in ch.parts("low_poly"):
        index = copy.get(character.OUTFIT)
        collection = bpy.data.collections[low_poly.COLLECTION.format(index=index, name=ch.name)]
        assert list(copy.users_collection) == [collection]
        assert collection.name in ch.collection.children
        assert collection.get(character.OUTFIT) == index
        assert collection.color_tag == colors.COLORS["low_poly"]
        assert collection.hide_render


def test_off_makes_no_copies(golden_import):
    _, ch = golden_import("kk", hooks=["Low poly"], options={"low_poly": "off"})
    assert not ch.parts("low_poly")


def test_running_the_hook_again_replaces_the_copies(ch):
    first = len(ch.parts("low_poly"))
    submodule("tools.run_hook").run_hook(ch, "Low poly", {"low_poly": "strong"})
    copies = ch.parts("low_poly")
    assert len(copies) == first
    assert not [o for o in bpy.data.objects if low_poly.SUFFIX in o.name and o.name.endswith(".001")]
    for copy in copies:
        share = len(copy.data.polygons) / len(_original(ch, copy).data.polygons)
        assert share < low_poly.RATIOS["medium"] * 0.75
