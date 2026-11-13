"""The Core Import's Steps on the golden samples and the builder's bundles, with no Hooks."""

import bpy
import pytest

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

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
def test_the_golden_samples_import(sample, golden_import):
    result, ch = golden_import(sample)
    assert ch.body is not None and ch.armature is not None
    assert ch.tears is not None and ch.gag_eyes is not None
    assert len(ch.outfits) == 1 and len(ch.hairs) == 1
    # One tongue, inside Body (ADR 0039), weighted to the tongue bones and moved by Body's mouth keys.
    body = ch.body
    tongue_mats = set(ch.materials(roles="tongue"))
    holders = [o for o in ch.parts() if o.type == "MESH" and any(s.material in tongue_mats for s in o.material_slots)]
    assert len(tongue_mats) == 1 and holders == [body], (tongue_mats, holders)
    slots = {i for i, s in enumerate(body.material_slots) if s.material in tongue_mats}
    verts = {v for p in body.data.polygons if p.material_index in slots for v in p.vertices}
    names = {g.index: g.name for g in body.vertex_groups}
    weighted = {names[g.group] for v in verts for g in body.data.vertices[v].groups if g.weight > 0}
    assert "cf_j_tang_01" in weighted and "cf_J_MouthCavity" not in weighted, weighted
    basis = body.data.shape_keys.reference_key
    moved = [k.name for k in body.data.shape_keys.key_blocks[1:]
             if any((k.data[v].co - basis.data[v].co).length > 1e-5 for v in verts)]
    assert len(moved) >= 5, moved  # the mouth keys move the tongue (fewer in SVS, ADR 0035)
    for mat in ch.materials():
        assert mat.get(templates.TEMPLATE) in kkbp.library.TEMPLATES
    gags = ch.materials(roles="gag_eyes")
    assert len([g for g in gags if templates.picker(g) is not None]) == 1  # one dropdown (ADR 0042)
    for gag in gags:
        assert gag.name == gag[character.ID]
        if templates.picker(gag) is None:  # the others follow the dropdown
            paths = [fc.data_path for fc in gag.node_tree.animation_data.drivers]
            assert 'nodes["gag.choice"].outputs[0].default_value' in paths, paths
    assert result.warnings == [], result.warnings


def test_expressions_drive_the_face(golden_import):
    """Gag eyes, with Spiral Eyes picked on the dropdown, shows its gag mesh, picks its pattern and
    hides the pupils; an eye expression picks the eye overlay; the tears follow Body's keys."""
    _, ch = golden_import("kk")
    body_keys = ch.body.data.shape_keys.key_blocks
    gag_keys = ch.gag_eyes.data.shape_keys.key_blocks
    scene = bpy.context.scene

    def evaluate():
        scene.frame_set(scene.frame_current)

    evaluate()
    assert gag_keys["Gag eye 01"].value == 0
    menu = ch.material("cf_m_gageye_00")
    picker = templates.template_of(menu).patterns.picker
    templates.picker(menu).inputs[picker.menu].default_value = "Spiral Eyes"  # the 3rd gag expression
    menu.node_tree.update_tag()  # as kkbp.dropdowns does on the message bus, which tests don't run
    body_keys["Gag eyes"].value = 1.0  # shows cf_O_gag_eye_01 with pattern cf_t_gageye_01
    evaluate()
    assert gag_keys["Gag eye 01"].value == 1 and gag_keys["Gag eye 00"].value == 0
    gag = ch.material("cf_m_gageye_01")
    index = templates.patterns(gag).index("cf_t_gageye_01")
    assert templates.param(gag, "choice").default_value == 3
    assert templates.pattern_param(gag, index, "angle_speed").default_value == pytest.approx(-0.5)
    assert templates.param(ch.material("cf_m_hitomi_00"), "hidden").default_value == 1
    body_keys["Gag eyes"].value = 0.0
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
def test_fiery_eyes_step_through_their_sheet(sample, material, pattern, golden_import):
    """The fiery eyes' texture is a 1 x 6 sheet of flames the game flips through (issue #15)."""
    _, ch = golden_import(sample)
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
