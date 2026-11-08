"""The Core Import's Steps on the golden samples and the builder's bundles, with no Hooks."""

import shutil

import bpy
import pytest

from bundle_builder import BundleBuilder
from conftest import golden, kkbp, submodule

character = submodule("character")
templates = submodule("templates")
settings = submodule("settings")


@pytest.fixture(autouse=True)
def no_preferences(monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})


def _import(path):
    result = kkbp.api.import_bundle(path, hooks=[])
    assert result.ok, f"{result.failed_step}: {result.error}"
    return result, character.Character(result.character_key)


def test_the_builder_bundle_imports(build):
    result, ch = _import(build())
    assert [s.status for s in result.steps if s.status != "ran"] == ["skipped"]  # SVS's eyelids
    assert ch.body.name == "Body Test Chara" and ch.armature.name == "Armature Test Chara"
    assert [o.name for o in ch.hairs] == ["Hair Outfit 00 Test Chara"]
    assert [o.name for o in ch.outfits] == ["Outfit 00 Test Chara"]
    assert len(ch.alt_outfits) == 1 and ch.tears is not None and ch.gag_eyes is not None
    assert ch.tears.parent == ch.body and ch.gag_eyes.parent == ch.body
    assert "cf_J_hairB_top" in ch.armature.data.bones  # an Outfit-owned bone, joined by Id
    for obj in ch.parts():
        if obj.type == "MESH":
            assert [m.type for m in obj.modifiers] == ["ARMATURE"]
            assert obj.modifiers[0].object == ch.armature
            assert all(s.material.get(templates.TEMPLATE) for s in obj.material_slots)
    assert len([o for o in bpy.data.objects if o.type == "ARMATURE"]) == 1


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_the_golden_samples_import(sample, tmp_path):
    copy = tmp_path / sample  # an import writes its log into the bundle's kkbp_cache/
    shutil.copytree(golden(sample), copy)
    result, ch = _import(copy)
    assert ch.body is not None and ch.armature is not None and ch.tongue is not None
    assert ch.tears is not None and ch.gag_eyes is not None
    assert len(ch.outfits) == 1 and len(ch.hairs) == 1
    tongue = ch.tongue
    assert tongue.data.shape_keys and len(tongue.data.shape_keys.key_blocks) > 30  # the mouth keys
    groups = {g.name for g in tongue.vertex_groups}
    weighted = {tongue.vertex_groups[g.group].name for v in tongue.data.vertices for g in v.groups if g.weight > 0}
    assert "cf_j_tang_01" in weighted and "cf_J_MouthCavity" not in weighted, groups
    assert len([o for o in ch.parts("tongue")]) == 1
    for mat in ch.materials():
        assert mat.get(templates.TEMPLATE) in kkbp.library.TEMPLATES
    for gag in ch.materials(roles="gag_eyes"):
        assert gag.name == gag[character.ID]
        paths = [fc.data_path for fc in gag.node_tree.animation_data.drivers]
        assert 'nodes["gag.choice"].outputs[0].default_value' in paths, paths  # an expression picks the pattern
    assert result.warnings == [], result.warnings


def test_expressions_drive_the_face(tmp_path):
    """A gag expression on Body shows its gag mesh, picks its pattern and hides the pupils; an eye
    expression picks the eye overlay; the tears follow Body's keys."""
    copy = tmp_path / "kk"
    shutil.copytree(golden("kk"), copy)
    _, ch = _import(copy)
    body_keys = ch.body.data.shape_keys.key_blocks
    gag_keys = ch.gag_eyes.data.shape_keys.key_blocks
    scene = bpy.context.scene

    def evaluate():
        scene.frame_set(scene.frame_current)

    evaluate()
    assert gag_keys["Gag eye 01"].value == 0
    body_keys["Gag Spiral Eyes"].value = 1.0  # shows cf_O_gag_eye_01 with pattern cf_t_gageye_01
    evaluate()
    assert gag_keys["Gag eye 01"].value == 1 and gag_keys["Gag eye 00"].value == 0
    gag = ch.material("cf_m_gageye_01")
    index = templates.patterns(gag).index("cf_t_gageye_01")
    assert templates.param(gag, "choice").default_value == templates.choice_value(gag, index)
    assert templates.pattern_param(gag, index, "angle_speed").default_value == pytest.approx(-0.5)
    assert templates.param(ch.material("cf_m_hitomi_00"), "hidden").default_value == 1
    body_keys["Gag Spiral Eyes"].value = 0.0
    body_keys["Eye Star Pupils"].value = 1.0  # the eyes' cf_t_expression_01 overlay
    evaluate()
    eye = ch.material("cf_m_hitomi_00")
    assert templates.param(eye, "hidden").default_value == 0
    assert templates.param(eye, "expression").default_value == \
        templates.choice_value(eye, templates.patterns(eye).index("cf_t_expression_01"))
    body_keys["Eye Crying"].value = 0.7
    evaluate()
    assert ch.tears.data.shape_keys.key_blocks["Eye Crying"].value == pytest.approx(0.7)


@pytest.mark.parametrize("sample, material, pattern", [
    ("kk", "cf_m_gageye_02", "cf_t_gageye_08"),
    ("kks", "cf_m_gageye_02", "cf_t_gageye_08"),
    ("svs", "cf_m_gageye_00", "cf_t_gageye_10"),
])
def test_fiery_eyes_step_through_their_sheet(sample, material, pattern, tmp_path):
    """The fiery eyes' texture is a 1 x 6 sheet of flames the game flips through (issue #15)."""
    copy = tmp_path / sample
    shutil.copytree(golden(sample), copy)
    _, ch = _import(copy)
    gag = ch.material(material)
    index = templates.patterns(gag).index(pattern)
    assert templates.pattern_param(gag, index, "tile_x").default_value == 1
    assert templates.pattern_param(gag, index, "tile_y").default_value == 6


def test_outfit_owned_bones_carry_their_outfit(build):
    b = BundleBuilder()
    b.add_bone("cf_J_hairB_top_2", "cf_j_head", group="hair", translation=(0.0, 0.15, -0.02), outfit=1)
    b.add_mesh("o_hair_b_2", ["c_m_hair_00"], outfit=1, bone="cf_J_hairB_top_2")
    _, ch = _import(build(b))
    bones = ch.armature.data.bones
    assert bones["cf_J_hairB_top"]["kkbp_outfit"] == 0 and bones["cf_J_hairB_top_2"]["kkbp_outfit"] == 1
    assert "kkbp_outfit" not in bones["cf_j_head"]
