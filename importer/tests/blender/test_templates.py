"""templates: apply, param, texture, swap, on the builder's bundles."""

import bpy
import pytest

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

templates = submodule("templates")
character = submodule("character")
library = submodule("library")


def _builder(game="KK"):
    """The default Character, with a baked face and left eye (the eye with expression overlays)."""
    b = BundleBuilder(game)
    materials = {m["id"]: m for m in b.materials}
    materials["cf_m_face_00"]["textures"] = [b.add_texture("_MainTex", role="main", variant="light"),
                                             b.add_texture("_MainTex", role="main", variant="dark")]
    materials["cf_m_hitomi_00"]["blend_mode"] = "alpha"
    materials["cf_m_hitomi_00"]["textures"] = [b.add_texture("_MainTex", role="main", variant="light"),
                                               b.add_texture("_expression", pattern="cf_t_expression_01"),
                                               b.add_texture("_expression", pattern="cf_t_expression_00")]
    b.add_material("cf_m_alpha_bot", role=None, textures=[
        b.add_texture("_MainTex", role="main", variant="light"),
        b.add_texture("_Cloth_alpha_bot")])
    return b


def _open(build, game="KK"):
    bundle = kkbp.bundle.open_bundle(build(_builder(game)))
    ch = character.Character.new("Test Chara", game, bundle.path)
    return bundle, ch


def _apply(ch, bundle, id):
    return templates.apply(ch, None, bundle.material(id))


def test_a_baked_material_gets_light_dark_with_its_textures(build):
    bundle, ch = _open(build)
    mat = _apply(ch, bundle, "cf_m_body")
    assert mat.name == "cf_m_body" and mat[templates.TEMPLATE] == "KK Light Dark"
    assert (mat[character.KEY], mat[character.ID], mat[character.ROLE]) == (ch.key, "cf_m_body", "body")
    assert ch.material("cf_m_body") == mat
    light = templates.texture(mat, "main", variant="light")
    assert light.image is not None and light.image.packed_file is not None
    assert light.image[character.ID] == "textures/0002.png" and light.image.name == "cf_m_body main.light"
    assert templates.texture(mat, "normal").image is not None
    assert character.KEY not in templates.texture(mat, "alpha_mask").image  # unset: the library placeholder
    assert templates.param(mat, "force_visibility").default_value == 2
    assert mat.surface_render_method == "DITHERED"


@pytest.mark.parametrize("game, template, visibility", [("KK", "KK Light Dark Face", 0),
                                                         ("SVS", "SVS Light Dark Face", 2)])
def test_a_face_with_bakes_without_eyeshadow_gets_the_eyeshadow_slider(build, game, template, visibility):
    """Issue 38: at 1 the face is the game's bake, at 0 the bake without eyeshadow."""
    b = _builder(game)
    face = next(m for m in b.materials if m["id"] == "cf_m_face_00")
    face["textures"] += [b.add_texture("_MainTex", role="main", variant="light_no_eyeshadow"),
                         b.add_texture("_MainTex", role="main", variant="dark_no_eyeshadow")]
    bundle = kkbp.bundle.open_bundle(build(b))
    ch = character.Character.new("Test Chara", game, bundle.path)
    mat = _apply(ch, bundle, "cf_m_face_00")
    assert mat[templates.TEMPLATE] == template
    slider = templates.param(mat, "eyeshadow")
    assert slider.default_value == 1 and templates.param(mat, "force_visibility").default_value == visibility
    for variant in ("light", "dark"):
        full = templates.texture(mat, "main", variant=variant)
        without = templates.texture(mat, "main", variant=f"{variant}_no_eyeshadow")
        assert character.KEY in full.image and character.KEY in without.image and full.image != without.image
        mix = slider.node.outputs[variant.capitalize()].links[0].to_socket
        assert mix.node.name == "shader" and mix.name == variant.capitalize()
    assert "cycles" in templates.template_of(mat).variants


def test_a_face_without_those_bakes_has_no_eyeshadow_slider(build):
    bundle, ch = _open(build)
    mat = _apply(ch, bundle, "cf_m_face_00")
    assert mat[templates.TEMPLATE] == "KK Light Dark" and "eyeshadow" not in templates.params(mat)
    assert templates.texture(mat, "main", variant="light_no_eyeshadow") is None


def test_parameters_and_render_method_come_from_the_set(build):
    bundle, ch = _open(build)
    face = _apply(ch, bundle, "cf_m_face_00")
    assert templates.param(face, "force_visibility").default_value == 0
    eye = _apply(ch, bundle, "cf_m_hitomi_00")
    assert eye[templates.TEMPLATE] == "KK Eye"
    assert eye.surface_render_method == "BLENDED" and eye.use_transparent_shadow


def test_a_material_without_its_baked_texture_is_transparent(build):
    bundle, ch = _open(build)
    assert _apply(ch, bundle, "cf_m_hitomi_00_2")[templates.TEMPLATE] == "Transparent"


def test_fixed_patterns_fill_their_nodes_in_bundle_order(build):
    bundle, ch = _open(build)
    eye = _apply(ch, bundle, "cf_m_hitomi_00")
    assert templates.patterns(eye) == ["cf_t_expression_01", "cf_t_expression_00"]
    assert templates.param(eye, "expression").default_value == 2  # no overlay
    assert templates.choice_value(eye, 1) == 1 and templates.choice_value(eye, None) == 2
    node = eye.node_tree.nodes["tex.expression.0"]
    assert node.image.name == "cf_m_hitomi_00 expression cf_t_expression_01"


def test_gag_patterns_build_a_chain(build):
    bundle, ch = _open(build)
    gag = _apply(ch, bundle, "cf_m_gageye_00")
    assert gag[templates.TEMPLATE] == "Gag" and gag.surface_render_method == "BLENDED"
    assert templates.patterns(gag) == ["cf_t_gageye_00", "cf_t_gageye_02"]
    assert templates.param(gag, "choice").default_value == 0
    assert templates.choice_value(gag, 0) == 1
    templates.pattern_param(gag, 1, "angle_speed").default_value = 0.5
    nodes = gag.node_tree.nodes
    assert nodes["main.pick.1"].inputs["Index"].default_value == 2
    out = nodes["gag.output"].inputs["Color"].links[0].from_node
    assert out == nodes["main.pick.1"]
    frame = nodes["main.uv.0"].inputs["Frame"].links[0].from_node
    assert (frame.type, frame.attribute_name) == ("ATTRIBUTE", "kkbp_gag_frame")  # no driver (ADR 0042)
    assert gag.node_tree.animation_data is None or not gag.node_tree.animation_data.drivers


def test_raw_slots_come_from_the_profile(build):
    bundle, ch = _open(build, "SVS")
    mat = _apply(ch, bundle, "cf_m_alpha_bot")
    assert mat[templates.TEMPLATE] == "SVS Light Dark"
    assert templates.texture(mat, "alpha_mask_bottom").image is not None
    bundle, ch = _open(build, "KK")
    mat = _apply(ch, bundle, "cf_m_alpha_bot")
    assert templates.texture(mat, "alpha_mask_bottom") is None  # KK's template has no such slot


def test_the_placeholder_is_replaced_everywhere(build):
    bundle, ch = _open(build)
    placeholder = bpy.data.materials.new("cf_m_body")
    mesh = bpy.data.meshes.new("m")
    mesh.materials.append(placeholder)
    mat = templates.apply(ch, placeholder, bundle.material("cf_m_body"))
    assert mesh.materials[0] == mat
    assert "cf_m_body" not in [m.name for m in bpy.data.materials if m != mat]


def test_templates_and_groups_are_appended_once_per_file(build):
    for _ in range(2):  # two Characters, with clashing material names
        bundle, ch = _open(build)
        for id in ("cf_m_body", "cf_m_face_00", "cf_m_gageye_00", "c_m_hair_00"):
            _apply(ch, bundle, id)
    groups = [g.name for g in bpy.data.node_groups]
    assert groups.count(".KK") == 1 and not [g for g in groups if g.startswith(".KK.")]
    assert len([m for m in bpy.data.materials if m.get(templates.TEMPLATE) == "KK Light Dark"
                and character.KEY not in m]) == 1
    assert len([m for m in bpy.data.materials if m.get(character.ID) == "cf_m_body"]) == 2
    images = [i.name for i in bpy.data.images]
    assert not [i for i in images if i.startswith("Template: Placeholder.")]


def test_swap_puts_a_variant_in_place_of_the_shader(build):
    bundle, ch = _open(build)
    mat = _apply(ch, bundle, "cf_m_body")
    assert templates.swap(mat, "cycles") == []
    assert mat.node_tree.nodes["shader"].node_tree.name == ".Cycles"
    assert templates.variant(mat) == "cycles"
    assert templates.param(mat, "force_visibility").default_value == 2  # the sockets carry over
    with pytest.raises(templates.TemplateError, match="has no parameter fresnel with the cycles variant"):
        templates.param(mat, "fresnel")
    templates.swap(mat, "eevee_mod")
    assert templates.param(mat, "fresnel").name == "Enable fresnel"
    with pytest.raises(templates.TemplateError, match="KK Light Dark template has no toon variant"):
        templates.swap(mat, "toon")


def test_swap_keeps_every_link_on_the_input_of_the_same_name(build):
    # Blender carries a group node's links over by socket identifier, which each variant numbers on its
    # own: the Principled variant's two extra bottom alpha mask inputs once put Hidden's link on
    # Light alpha, and the expression-driven eyes went transparent.
    bundle, ch = _open(build)
    for variant in ("principled", "eevee_mod", "cycles", "cycles_classic", "cycles_no_shadows"):
        mat = _apply(ch, bundle, "cf_m_body")
        tree = mat.node_tree
        held = tree.nodes.new("ShaderNodeValue")  # stands in for an expression's driven Hidden value
        tree.links.new(held.outputs[0], templates.param(mat, "hidden"))
        shader = tree.nodes[templates.template_of(mat).shader]

        def links():
            return sorted((l.from_node.name, l.from_socket.name, l.to_socket.name) for l in tree.links
                          if l.to_node == shader)

        before = links()
        dropped = templates.swap(mat, variant)
        kept = [link for link in before if link[2] not in dropped]
        assert links() == kept, variant
        assert templates.param(mat, "hidden").links[0].from_node == held, variant


def test_svs_gets_the_kk_variants_and_loses_its_bottom_alpha_mask(build):
    svs_bundle, svs = _open(build, "SVS")
    mat = _apply(svs, svs_bundle, "cf_m_body")
    assert templates.swap(mat, "cycles") == ["Alpha mask bottom", "Alpha mask bottom alpha"]
    assert templates.swap(mat, "principled") == []


def test_unknown_parameters_and_foreign_materials_are_errors(build):
    bundle, ch = _open(build)
    with pytest.raises(templates.TemplateError, match="has no parameter colour"):
        templates.param(_apply(ch, bundle, "cf_m_body"), "colour")
    with pytest.raises(templates.TemplateError, match="wasn't made from a KKBP Material Template"):
        templates.param(bpy.data.materials.new("mine"), "hidden")


def _floor_under_a_quad(material, path):
    """Renders the middle of a floor that has a quad with `material` between it and the sun, seen from
    under the quad. Returns the pixel's red value: 0 in the quad's shadow."""
    compat = submodule("compat")
    scene = bpy.context.scene
    scene.render.resolution_x = scene.render.resolution_y = 16
    scene.view_settings.view_transform = "Standard"

    def plane(name, size, z, material):
        mesh = bpy.data.meshes.new(name)
        h = size / 2
        mesh.from_pydata([(-h, -h, z), (h, -h, z), (h, h, z), (-h, h, z)], [], [(0, 1, 2, 3)])
        mesh.materials.append(material)
        obj = bpy.data.objects.new(name, mesh)
        scene.collection.objects.link(obj)

    plane("floor", 10, 0, bpy.data.materials.new("floor"))
    plane("quad", 2, 1, material)
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.location.z = 5
    camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    camera.location.z, camera.data.type, camera.data.ortho_scale = 0.5, "ORTHO", 1
    for obj in (sun, camera):
        scene.collection.objects.link(obj)
    scene.camera = camera
    compat.render_still(scene, path)
    image = bpy.data.images.load(str(path))
    middle = (8 * 16 + 8) * 4
    return image.pixels[middle]


def test_gag_eyes_cast_no_shadow(build, tmp_path):
    bundle, ch = _open(build)
    gag = _apply(ch, bundle, "cf_m_gageye_00")
    assert gag.use_transparent_shadow
    output = gag.node_tree.nodes["gag.output"]
    for name in ("Expression", "Alpha"):  # drawn in full, as when a gag expression shows
        for link in list(output.inputs[name].links):
            gag.node_tree.links.remove(link)
        output.inputs[name].default_value = 1.0
    assert _floor_under_a_quad(gag, tmp_path / "lit.png") > 0.5
    gag.use_transparent_shadow = False  # the same picture does shade the floor without it
    assert _floor_under_a_quad(gag, tmp_path / "shaded.png") < 0.1


def test_tears_cast_no_shadow(build, tmp_path):
    bundle, ch = _open(build)
    tears = _apply(ch, bundle, "c_m_namida")
    assert tears[templates.TEMPLATE] == "KK Tears" and tears.use_transparent_shadow
    assert _floor_under_a_quad(tears, tmp_path / "lit.png") > 0.5
    tears.use_transparent_shadow = False
    assert _floor_under_a_quad(tears, tmp_path / "shaded.png") < 0.1


def test_svs_tears_and_gag_eyes_cast_no_shadow_either(build):
    bundle, ch = _open(build, "SVS")
    gag = _apply(ch, bundle, "cf_m_gageye_00")
    assert gag.surface_render_method == "DITHERED" and gag.use_transparent_shadow
    assert _apply(ch, bundle, "c_m_namida").use_transparent_shadow
