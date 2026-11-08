"""Outlines on the builder's Character (golden samples: run.py hooks --each)."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp, submodule

templates = submodule("templates")
character = submodule("character")
outlines = submodule("builtin.outlines")


def _baked(game="KK"):
    """The default Character with a baked face, hair and shirt, so they get Light Dark templates."""
    b = BundleBuilder(game)
    materials = {m["id"]: m for m in b.materials}
    for id in ("cf_m_face_00", "c_m_hair_00", "ct_top_shirt"):
        materials[id]["textures"] += [b.add_texture("_MainTex", role="main", variant="light"),
                                      b.add_texture("_MainTex", role="main", variant="dark")]
    materials["ct_top_shirt"]["blend_mode"] = "glasses"
    return b


def _import(build, game="KK", **options):
    result = kkbp.api.import_bundle(build(_baked(game)), options=options, hooks=["Outlines"])
    assert result.ok and result.hooks[0].status == "ran", result.hooks
    return character.Character.for_tool(bpy.context)


def _slots(obj):
    return [s.material.name for s in obj.material_slots]


def test_body_gets_a_face_and_a_body_outline(build):
    ch = _import(build)
    body = ch.body
    modifier = body.modifiers["Outline Modifier"]
    assert modifier.type == "SOLIDIFY" and modifier.use_flip_normals and modifier.material_offset == 4
    assert _slots(body)[-2:] == ["Outline cf_m_face_00", "Outline cf_m_body"]
    face = bpy.data.materials["Outline cf_m_face_00"]
    assert templates.texture(face, "main", "light").image.name == "Template: BlackWithAlpha"
    assert templates.texture(face, "alpha_mask").image.name == "KK OutlineMask.png"
    assert templates.param(face, "force_visibility").default_value == 2
    assert face.use_backface_culling and face[outlines.OUTLINE] == "cf_m_face_00"
    assert ch.material("cf_m_face_00").name == "cf_m_face_00"  # the outline doesn't take the Id


def test_textured_materials_get_their_own_outline(build):
    ch = _import(build)
    shirt = ch.outfits[0]
    assert _slots(shirt) == ["ct_top_shirt", "Outline ct_top_shirt", f"Outline {shirt.name}"]
    own = bpy.data.materials["Outline ct_top_shirt"]
    assert not templates.param(own, "light").is_linked
    assert tuple(templates.param(own, "light").default_value) == (0.0, 0.0, 0.0, 1.0)
    assert not templates.param(own, "light_alpha").is_linked  # glasses: no alpha on the outline
    assert shirt.modifiers["Outline Modifier"].material_offset == 1
    assert "Outline Modifier" in ch.hairs[0].modifiers


def test_svs_face_gets_the_svs_mask(build):
    _import(build, "SVS")
    face = next(m for m in bpy.data.materials if m.name.startswith("Outline cf_m_face_00"))
    assert templates.texture(face, "alpha_mask").image.name == "SVS OutlineMask.png"


def test_no_outlines_with_cycles(build):
    result = kkbp.api.import_bundle(build(_baked()), options={"convert_shaders": "cycles"}, hooks=["Outlines"])
    assert result.hooks[0].status == "ran"
    assert "Outline Modifier" not in character.Character.for_tool(bpy.context).body.modifiers


def test_a_body_without_uvs_keeps_the_whole_thickness(build):
    # The builder's meshes have no UV maps, so there is nothing to read the face mask through.
    ch = _import(build, "SVS")
    assert ch.body.modifiers["Outline Modifier"].vertex_group == ""
    assert outlines.THICKNESS_GROUP not in ch.body.vertex_groups


def test_thinning_follows_the_mask_on_face_vertices_only():
    # Two quads side by side: the left uses the face material, the right another. The mask is white
    # (no outline) on its left half, black on its right half.
    mesh = bpy.data.meshes.new("thin")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (2, 0, 0), (2, 1, 0)], [],
                     [(0, 1, 2, 3), (1, 4, 5, 2)])
    face, other = bpy.data.materials.new("thin face"), bpy.data.materials.new("thin other")
    mesh.materials.append(face)
    mesh.materials.append(other)
    mesh.polygons[1].material_index = 1
    uv = mesh.uv_layers.new(name=outlines.UV_MAP)
    # Face quad: corners 0 and 3 in the white half, 1 and 2 in the black half. The other quad's UVs
    # are all in the white half, which must not matter.
    for loop, at in zip(mesh.polygons[0].loop_indices, [(0.1, 0.1), (0.9, 0.1), (0.9, 0.9), (0.1, 0.9)]):
        uv.data[loop].uv = at
    for loop in mesh.polygons[1].loop_indices:
        uv.data[loop].uv = (0.1, 0.5)
    obj = bpy.data.objects.new("thin", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mask = bpy.data.images.new("thin mask", 2, 1)
    mask.pixels[:] = [1, 1, 1, 1, 0, 0, 0, 1]
    modifier = obj.modifiers.new("Outline Modifier", "SOLIDIFY")

    outlines._thin_where_masked(obj, face, mask, modifier)

    group = obj.vertex_groups[outlines.THICKNESS_GROUP]
    weights = [group.weight(i) for i in range(6)]
    assert weights == [0.0, 1.0, 1.0, 0.0, 1.0, 1.0]
    assert modifier.vertex_group == group.name and modifier.thickness_vertex_group == 0.0
