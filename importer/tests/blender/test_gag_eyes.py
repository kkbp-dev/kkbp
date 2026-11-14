"""Gag eyes: one shape key, and a dropdown on the gag eyes' first material that picks the gag
expression (issue 35, ADR 0042)."""

import bpy
import pytest

from bundle_builder import BundleBuilder
from conftest import golden, kkbp, submodule

character = submodule("character")
templates = submodule("templates")
settings = submodule("settings")
gag = submodule("steps.gag")
dropdowns = submodule("dropdowns")

FIERY = "Gag eyes (Fiery Eyes)"


@pytest.fixture(autouse=True)
def no_preferences(monkeypatch):
    monkeypatch.setattr(settings, "option_defaults", lambda: {})


def _import(path):
    result = kkbp.api.import_bundle(path, hooks=[])
    assert result.ok, f"{result.failed_step}: {result.error}"
    return result, character.Character(result.character_key)


def _evaluate():
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    scene.frame_set(scene.frame_current)


def _picker(ch):
    mat = next(m for m in ch.materials(roles="gag_eyes") if templates.picker(m) is not None)
    return mat, templates.picker(mat), templates.template_of(mat).patterns.picker


def _pick(ch, label=None, number=None):
    _, node, names = _picker(ch)
    if label is not None:
        node.inputs[names.menu].default_value = label
    if number is not None:
        node.inputs[names.number].default_value = number
    dropdowns.refresh()  # what the message bus does in Blender's event loop, which tests don't run
    _evaluate()


def _two_gags():
    """The builder's Character with a second gag expression, of a shape of its own, on a second
    gag mesh and material."""
    b = BundleBuilder()
    b.add_material("cf_m_gageye_01", role="gag_eyes", blend_mode="alpha", textures=[
        b.add_texture("_MainTex", role="main", pattern="cf_t_gageye_01")])
    b.add_mesh("cf_O_gag_eye_01", ["cf_m_gageye_01"], bone="cf_j_head")
    b.add_expression("cf_O_face", "Gag Fiery Eyes", "gag", game_name="炎")
    b.add_expression("cf_O_gag_eye_01", "Gag eye 01", "gag")
    b.add_effect("Gag Fiery Eyes", shows=["cf_O_gag_eye_01"],
                 material_changes=[{"material": "cf_m_gageye_01",
                                    "textures": [{"raw": "_MainTex", "pattern": "cf_t_gageye_01"}],
                                    "floats": {}, "vectors": {}}])
    return b


def _moved(key):
    basis = key.relative_key
    return max((k.co - b.co).length for k, b in zip(key.data, basis.data))


def test_the_gag_keys_become_one_key_and_a_correction(build):
    _, ch = _import(build(_two_gags()))
    keys = ch.body.data.shape_keys.key_blocks
    names = [k.name for k in keys]
    assert "Gag Heart Eyes" not in names and "Gag Fiery Eyes" not in names
    assert names[1] == gag.GAG_KEY and names[-1] == FIERY, names
    assert gag.corrections(ch.body) == {FIERY: ["Gag Fiery Eyes"]}
    # The builder moves the face 1 mm more for each expression on it: Heart Eyes is its 5th, Fiery Eyes its 6th.
    assert _moved(keys[gag.GAG_KEY]) == pytest.approx(0.005, abs=1e-6)
    assert _moved(keys[FIERY]) == pytest.approx(0.001, abs=1e-6)


def test_the_dropdown_picks_the_gag_expression(build):
    _, ch = _import(build(_two_gags()))
    body = ch.body.data.shape_keys.key_blocks
    shows = ch.gag_eyes.data.shape_keys.key_blocks
    fiery = body[FIERY]
    mat, node, _ = _picker(ch)
    assert mat == ch.material("cf_m_gageye_00")
    assert [i.name for i in node.node_tree.nodes if i.type == "MENU_SWITCH"]  # the dropdown's own group
    _pick(ch, "Heart Eyes")
    assert shows["Gag eye 00"].value == 0  # Gag eyes is down
    body[gag.GAG_KEY].value = 1.0
    _evaluate()
    assert shows["Gag eye 00"].value == 1 and shows["Gag eye 01"].value == 0
    assert fiery.value == 0
    _pick(ch, "Fiery Eyes")
    assert shows["Gag eye 00"].value == 0 and shows["Gag eye 01"].value == 1
    assert fiery.value == 1
    assert templates.value_on(ch.gag_eyes, ch.material("cf_m_gageye_01"), "choice") == 2
    _pick(ch, "Fiery Eyes", number=1)  # the number wins over the dropdown
    assert shows["Gag eye 00"].value == 1 and fiery.value == 0
    body[gag.GAG_KEY].value = 0.4
    _pick(ch, number=2)
    assert fiery.value == pytest.approx(0.4)
    body[gag.GAG_KEY].mute = True
    _evaluate()
    assert fiery.mute


def test_each_gag_expression_gets_a_pick_node(build):
    """The first gag material shows the patterns by expression, so two expressions can share one."""
    b = BundleBuilder()
    b.add_expression("cf_O_face", "Gag Spiral Eyes", "gag", game_name="ぐるぐる")
    b.add_effect("Gag Spiral Eyes", shows=["cf_O_gag_eye_00"],
                 material_changes=[{"material": "cf_m_gageye_00",
                                    "textures": [{"raw": "_MainTex", "pattern": "cf_t_gageye_02"}],
                                    "floats": {}, "vectors": {}}])
    _, ch = _import(build(b))
    mat, node, names = _picker(ch)
    picks = sorted((n for n in mat.node_tree.nodes if n.name.startswith("main.pick.")), key=lambda n: n.name)
    assert [p.inputs["Index"].default_value for p in picks] == [1, 2]
    assert all(p.inputs["Choice"].links[0].from_node == node for p in picks)
    tex = {p.inputs["Color"].links[0].from_node.image.name for p in picks}
    assert len(tex) == 1  # both show cf_t_gageye_02


def test_drivers_read_the_dropdown_by_its_place(build):
    """Drivers read a dropdown as its item's number in the order the items were made (ADR 0042)."""
    b = BundleBuilder()
    extra = ["Gag Spiral Eyes", "Gag Dazed", "Gag Staring", "Gag Oval Eyes"]
    for i, name in enumerate(extra):
        b.add_expression("cf_O_face", name, "gag", game_name=f"extra {i}")
    _, ch = _import(build(b))
    mat, _, _ = _picker(ch)
    menu, _ = templates.picker_paths(mat)
    holder = bpy.data.objects.new("probe", None)
    bpy.context.scene.collection.objects.link(holder)
    holder["place"] = -1.0
    fcurve = holder.driver_add('["place"]')
    var = fcurve.driver.variables.new()
    var.name, var.type = "m", "SINGLE_PROP"
    var.targets[0].id_type = "MATERIAL"
    var.targets[0].id = mat
    var.targets[0].data_path = menu
    fcurve.driver.expression = "m"
    for place, name in enumerate(["Heart Eyes", "Spiral Eyes", "Dazed", "Staring", "Oval Eyes"]):
        _pick(ch, name)
        assert holder["place"] == place, name


def test_driver_expressions_stay_simple(build):
    """Blender runs simple driver expressions without Python, so they work in untrusted files."""
    _, ch = _import(build(_two_gags()))
    owners = [o.data.shape_keys for o in ch.parts() if o.type == "MESH" and o.data.shape_keys]
    owners += [m.node_tree for m in ch.materials()] + [o for o in ch.parts() if o.type == "MESH"]
    drivers = [(o.name, fc) for o in owners if o.animation_data for fc in o.animation_data.drivers]
    assert any("gag.expression" in v.targets[0].data_path for _, fc in drivers for v in fc.driver.variables)
    for name, fcurve in drivers:
        if fcurve.driver.type == "SCRIPTED":
            assert fcurve.driver.is_simple_expression, (name, fcurve.data_path, fcurve.driver.expression)


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_the_golden_samples_have_one_gag_key(sample, golden_import):
    result, ch = golden_import(sample)
    names = [k.name for k in ch.body.data.shape_keys.key_blocks]
    assert [n for n in names if n.startswith("Gag")] == [gag.GAG_KEY, FIERY], names
    assert [n for n in ch.tears.data.shape_keys.key_blocks.keys() if n.startswith("Gag eyes")] == [gag.GAG_KEY, FIERY]
    mat, node, names = _picker(ch)
    items = len(gag.gag_expressions(kkbp.api.open_bundle(golden(sample))))
    assert node.node_tree.interface.items_tree[names.number].max_value == items
    assert result.warnings == [], result.warnings


def test_fiery_eyes_leave_the_pupils_showing(golden_import):
    """Every KK gag expression hides the pupils but Fiery Eyes, which burns in front of them."""
    _, ch = golden_import("kk")
    body = ch.body.data.shape_keys.key_blocks

    def pupil():
        return templates.value_on(ch.body, ch.material("cf_m_hitomi_00"), "hidden")

    _pick(ch, "Heart Eyes")
    assert pupil() == 0  # Gag eyes is down
    body[gag.GAG_KEY].value = 1.0
    _evaluate()
    assert pupil() == 1 and body[FIERY].value == 0
    _pick(ch, "Fiery Eyes")
    assert pupil() == 0 and body[FIERY].value == 1
    _pick(ch, number=1)  # Circle Eyes 1, the first
    assert pupil() == 1 and body[FIERY].value == 0


def test_the_gag_patterns_read_the_frame_from_their_object(build):
    """The animated patterns turn with the frame, read from a property on each object with a Gag
    material; a driver in the material would update it, and every driver reading its dropdown, on
    every frame (ADR 0042)."""
    _, ch = _import(build(_two_gags()))
    scene = bpy.context.scene
    scene.frame_set(12)
    gags = [m for m in ch.materials(roles="gag_eyes") if templates.template_of(m).patterns.chain is not None]
    assert gags
    for mat in gags:
        chain = templates.template_of(mat).patterns.chain
        node = templates.param(mat, chain.frame).node
        assert (node.type, node.attribute_type, node.attribute_name) == ("ATTRIBUTE", "OBJECT", chain.frame_property)
        assert not (mat.node_tree.animation_data and any("gag.frame" in fc.data_path
                                                         for fc in mat.node_tree.animation_data.drivers))
        users = [o for o in ch.parts("gag_eyes") if any(s.material == mat for s in o.material_slots)]
        assert users
        for obj in users:
            assert obj[chain.frame_property] == 12


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
@pytest.mark.parametrize("keyed", [None, "Gag eyes", "Eye Star Pupils"])
def test_a_frame_change_updates_no_material(sample, keyed, golden_import):
    """Playing an animation doesn't re-evaluate the materials, with nothing keyed or with the gag eyes
    or an expression that picks an eye overlay keyed (issue 70): what the expressions change on a
    material is driven on the objects, which the material reads as it is drawn. A driver on the
    material would re-evaluate it on every frame, even while the key stays still."""
    _, ch = golden_import(sample)
    scene = bpy.context.scene
    blocks = ch.body.data.shape_keys.key_blocks
    if keyed is not None:
        if keyed not in blocks:
            pytest.skip(f"{sample} has no {keyed}")
        for frame, value in ((1, 0.0), (4, 1.0), (8, 0.0)):
            blocks[keyed].value = value
            blocks[keyed].keyframe_insert("value", frame=frame)
    seen = []

    def note(scene, depsgraph):
        seen.append({type(u.id).__name__ + " " + u.id.name for u in depsgraph.updates})

    bpy.app.handlers.frame_change_post.append(note)
    try:
        for frame in range(1, 9):
            scene.frame_set(frame)
    finally:
        bpy.app.handlers.frame_change_post.remove(note)
    for updated in seen[2:]:
        assert not {u for u in updated if u.startswith("Material")}, sorted(updated)
        if keyed is None:
            assert not {u for u in updated if u.startswith("Key")}, sorted(updated)


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_the_gag_eyes_take_the_eyeshadow_away(sample, golden_import):
    """Issue 38: the face's eyeshadow fades out as Gag eyes rises, whatever its own slider says, and
    can still be hidden by hand while Gag eyes is down."""
    _, ch = golden_import(sample)
    face = next(m for m in ch.materials(roles="face"))
    assert templates.param(face, "eyeshadow").default_value == 1
    key = ch.body.data.shape_keys.key_blocks[gag.GAG_KEY]

    def hidden():
        return templates.value_on(ch.body, face, "eyeshadow_hidden")

    _evaluate()
    assert hidden() == 0
    key.value = 1.0
    _evaluate()
    assert hidden() == 1
    key.value = 0.25
    _evaluate()
    assert hidden() == pytest.approx(0.25)
    key.value = 0.0
    templates.param(face, "eyeshadow_hidden").default_value = 1.0  # by hand
    _evaluate()
    assert hidden() == 1
    drivers = [fc for o in ch.parts() if o.animation_data for fc in o.animation_data.drivers
               if "eyeshadow_hidden" in fc.data_path]
    assert drivers and all(fc.driver.is_simple_expression for fc in drivers)
