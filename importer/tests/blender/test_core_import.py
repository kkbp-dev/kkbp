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
            prop, = templates.object_properties(gag)  # its choice, read from the object it is on (issue 70)
            users = [o for o in ch.parts("gag_eyes") if any(s.material == gag for s in o.material_slots)]
            assert users and all(f'["{prop}"]' in [fc.data_path for fc in o.animation_data.drivers] for o in users)
            assert gag.node_tree.animation_data is None or not gag.node_tree.animation_data.drivers
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
    assert templates.value_on(ch.gag_eyes, gag, "choice") == 3
    assert templates.pattern_param(gag, index, "angle_speed").default_value == pytest.approx(-0.5)
    assert templates.value_on(ch.body, ch.material("cf_m_hitomi_00"), "hidden") == 1
    body_keys["Gag eyes"].value = 0.0
    body_keys["Eye Star Pupils"].value = 1.0  # the eyes' cf_t_expression_01 overlay
    evaluate()
    eye = ch.material("cf_m_hitomi_00")
    assert templates.value_on(ch.body, eye, "hidden") == 0
    assert templates.value_on(ch.body, eye, "expression") == \
        templates.choice_value(eye, templates.patterns(eye).index("cf_t_expression_01"))
    body_keys["Eye Crying"].value = 0.7
    evaluate()
    assert ch.tears.data.shape_keys.key_blocks["Eye Crying"].value == pytest.approx(0.7)


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_the_tears_are_moved_from_bodys_shape_keys(sample, golden_import):
    """Issue 69: Body has the tear meshes' showing keys, which move nothing on Body and drive the Tears
    object's keys of the same name, so the tears are keyed with the rest of the face."""
    _, ch = golden_import(sample)
    body_keys, tear_keys = ch.body.data.shape_keys.key_blocks, ch.tears.data.shape_keys.key_blocks
    scene = bpy.context.scene
    names = [k.name for k in body_keys]
    tears = ["Tears big", "Tears med", "Tears small"]
    assert [n for n in names if n in tears] == tears
    last_expression = max(i for i, n in enumerate(names) if n.startswith(("Eye ", "Mouth ", "Eyebrow ")))
    assert names.index("Tears big") > last_expression  # with the driven keys, as on the Tears object
    basis = [tuple(v.co) for v in body_keys[0].data]
    assert [tuple(v.co) for v in body_keys["Tears big"].data] == basis

    def tear_mesh():
        return [tuple(v.co) for v in ch.tears.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]

    scene.frame_set(scene.frame_current)
    assert tear_keys["Tears big"].value == 0
    hidden = tear_mesh()
    body_keys["Tears big"].value = 1.0
    scene.frame_set(scene.frame_current)
    assert tear_keys["Tears big"].value == pytest.approx(1.0) and tear_keys["Tears med"].value == 0
    assert tear_mesh() != hidden
    body_keys["Tears big"].mute = True
    scene.frame_set(scene.frame_current)
    assert tear_keys["Tears big"].mute


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_the_tears_and_gag_eyes_rest_inside_the_head(sample, golden_import):
    """Issue 84: with their showing keys down, no vertex of the tears or the gag eyes is outside the
    face mesh, so nothing shows at the back of the head when the hair is hidden."""
    import bmesh
    from mathutils.bvhtree import BVHTree

    _, ch = golden_import(sample)
    body = ch.body
    slots = {i for i, s in enumerate(body.material_slots) if s.material in ch.materials(roles="face")}
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index not in slots], context="FACES")
    bm.transform(body.matrix_world)
    bm.normal_update()
    assert bm.faces
    skin = BVHTree.FromBMesh(bm)
    bm.free()
    parts = ch.parts(("tears", "gag_eyes"))
    assert parts
    for part in parts:
        outside = []
        for v in part.data.vertices:
            point = part.matrix_world @ v.co
            nearest, normal, _, _ = skin.find_nearest(point)
            if (point - nearest).dot(normal) > 0:
                outside.append(v.index)
        assert not outside, f"{part.name}: {len(outside)} of {len(part.data.vertices)} vertices are outside"


def test_svs_has_each_vowel_mouth_once(golden_import):
    """Issue 45: the game's own vowel and Cartoony Smile mouths carry the Expression Names, with no
    second copy under the game's numbered name."""
    _, ch = golden_import("svs")
    names = [k.name for k in ch.body.data.shape_keys.key_blocks]
    for name in ("Mouth A", "Mouth I", "Mouth U", "Mouth E", "Mouth O", "Mouth Cartoony Smile"):
        assert names.count(name) == 1, name
    assert not [n for n in names if n.startswith("mouth ")]


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
