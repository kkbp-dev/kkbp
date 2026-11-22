"""Convert shaders on the builder's Character (golden samples: run.py hooks --each)."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

templates = submodule("templates")
character = submodule("character")


def _baked(game="KK"):
    """The default Character with a baked face and left eye, so they get Light Dark templates."""
    b = BundleBuilder(game)
    materials = {m["id"]: m for m in b.materials}
    for id in ("cf_m_face_00", "cf_m_hitomi_00"):
        materials[id]["textures"] = [b.add_texture("_MainTex", role="main", variant="light"),
                                     b.add_texture("_MainTex", role="main", variant="dark")]
    return b


def _import(build, variant):
    result = kkbp.api.import_bundle(build(_baked()), options={"convert_shaders": variant}, hooks=["Convert shaders"])
    assert result.ok and [(h.name, h.status) for h in result.hooks] == [("Convert shaders", "ran")], result.hooks
    return character.Character.for_tool(bpy.context), result


def _shader(mat):
    return mat.node_tree.nodes[templates.template_of(mat).shader].node_tree.name


def test_cycles(build):
    ch, _ = _import(build, "cycles")
    body = ch.material("cf_m_body")
    assert _shader(body) == ".Cycles" and templates.variant(body) == "cycles"
    assert all(templates.texture_node(body, slot).image is not None for slot in templates.template_of(body).textures)
    assert bpy.context.scene.render.engine == "CYCLES"
    assert ch.material("c_m_namida").get(templates.VARIANT) is None  # the tears keep their own template


def test_eevee_mod(build):
    ch, _ = _import(build, "eevee_mod")
    face, body, eye = ch.material("cf_m_face_00"), ch.material("cf_m_body"), ch.material("cf_m_hitomi_00")
    assert _shader(face) == _shader(body) == ".Eevee Mod"
    assert templates.param(body, "fresnel").default_value == "Disable fresnel"
    assert templates.texture_node(body, "permalight_mask").image.name == "Template: Body neck shadow"
    assert templates.param(body, "disable_permalight_mask").default_value is True
    sdf = templates.param(face, "permalight_mask").links[0].from_node
    assert sdf.node_tree.name == ".SDF_Cel_Shader"
    assert sdf.node_tree.nodes["SDF Texture"].image.name == "Face SDF KK"
    assert ch.body.modifiers["Light Rotation Catcher"].node_group.name == ".Light Rotation Catcher"
    # The eyes keep the Eevee shader and are always lit.
    assert _shader(eye) == ".KK" and not templates.param(eye, "permalight_mask").is_linked
    assert tuple(templates.param(eye, "permalight_mask").default_value) == (1.0, 0.0, 0.0, 1.0)


def test_svs_faces_share_a_copy_of_the_sdf_group_with_svs_images(build):
    """The SDF and its hair contact shadows mask are drawn in a face UV layout, which SVS's face
    doesn't share with KK's: SVS faces get a copy of the group with SVS's images, one per file."""
    path = build(_baked("SVS"))
    for _ in range(2):
        kkbp.api.import_bundle(path, options={"convert_shaders": "eevee_mod"}, hooks=["Convert shaders"])
    faces = [m for m in bpy.data.materials if m.get(character.ROLE) == "face" and character.KEY in m]
    assert len(faces) == 2
    groups = [templates.param(f, "permalight_mask").links[0].from_node.node_tree for f in faces]
    assert groups[0] == groups[1] and groups[0].name == ".SDF_Cel_Shader SVS"
    assert groups[0].nodes["SDF Texture"].image.name == "Face SDF SVS"
    assert groups[0].nodes["Hair contact shadows mask"].image.name == "SVS hair contact shadows mask"
    kk = bpy.data.node_groups[".SDF_Cel_Shader"]  # the library's own, which KK faces get, keeps KK's
    assert kk.nodes["SDF Texture"].image.name == "Face SDF KK"


def test_principled(build):
    ch, _ = _import(build, "principled")
    mat = ch.material("cf_m_body")
    assert _shader(mat) == ".Principled"
    # The group still feeds the material output, and still gets the light texture.
    shader = mat.node_tree.nodes[templates.template_of(mat).shader]
    output = next(n for n in mat.node_tree.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
    assert any(l.from_node == shader for l in output.inputs["Surface"].links)
    assert templates.param(mat, "light").is_linked
    # The eye's alpha is its light texture's, not the value its expressions drive Hidden with.
    eye = ch.material("cf_m_hitomi_00")
    light_alpha = templates.param(eye, "light_alpha").links[0].from_socket
    assert light_alpha.node == templates.texture(eye, "main", "light") and light_alpha.name == "Alpha"


def test_svs_keeps_its_bottom_alpha_mask_without_a_warning(build):
    """The KK variants get SVS's two masks merged into one (ADR 0057), so nothing is lost."""
    path = build(BundleBuilder("SVS"))
    result = kkbp.api.import_bundle(path, options={"convert_shaders": "cycles"}, hooks=["Convert shaders"])
    assert not any("Alpha mask bottom" in w for w in result.warnings), result.warnings
