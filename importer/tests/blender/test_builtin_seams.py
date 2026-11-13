"""Fix body seams on a hand-built Body (golden samples: run.py hooks --each)."""

import bmesh
import bpy
import numpy as np

from conftest import submodule
from hook_ctx import fake_ctx

character = submodule("character")
seams = submodule("builtin.seams")


def _body_with_a_seam(ch):
    """Two quads side by side whose touching edge is doubled: one face material, one body material,
    one hair material on a third quad with doubled vertices too."""
    mesh = bpy.data.meshes.new("Body")
    bm = bmesh.new()
    def quad(x0, mat):
        vs = [bm.verts.new(co) for co in ((x0, 0, 0), (x0 + 1, 0, 0), (x0 + 1, 0, 1), (x0, 0, 1))]
        bm.faces.new(vs).material_index = mat
    quad(0.0, 0)
    quad(1.0, 1)
    quad(2.0, 2)
    bm.to_mesh(mesh)
    bm.free()
    for i, role in enumerate(("face", "body", "hair")):
        mat = bpy.data.materials.new(role)
        ch.tag_material(mat, f"m_{role}", role)
        mesh.materials.append(mat)
    obj = bpy.data.objects.new("Body", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return ch.add_part(obj, "body")


def test_merges_only_the_face_and_body_materials():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    body = _body_with_a_seam(ch)
    assert len(body.data.vertices) == 12
    seams.fix_body_seams(fake_ctx(ch))
    # The face/body seam (2 vertices) merges; the hair quad's doubled edge with the body stays.
    assert len(body.data.vertices) == 10
    assert len(body.data.polygons) == 3


def test_no_body_is_a_warning():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    ctx = fake_ctx(ch)
    seams.fix_body_seams(ctx)
    assert ctx.log.warnings == ["The Character has no body, so no seams were fixed"]


def _corners(mesh):
    """Per face corner, in face order: its vertex's position and its normal."""
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    vi = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vi)
    n = np.empty(len(mesh.loops) * 3)
    mesh.corner_normals.foreach_get("vector", n)
    return co.reshape(-1, 3)[vi], n.reshape(-1, 3)


def test_it_does_what_merge_by_distance_with_centroid_merge_does(golden_import):
    """On the KK body: Merge by Distance at 0.00001, Centroid Merge, on the face and body faces only,
    and the custom normals the operator keeps."""
    ch = golden_import("kk")[1]  # for the operator
    body = ch.body
    slots = {i for i, s in enumerate(body.material_slots) if s.material.get("kkbp_role") in seams.ROLES}
    selected = {v for p in body.data.polygons if p.material_index in slots for v in p.vertices}
    for p in body.data.polygons:
        p.select = p.material_index in slots
    for v in body.data.vertices:
        v.select = v.index in selected
    for e in body.data.edges:
        e.select = all(v in selected for v in e.vertices)
    bpy.context.view_layer.objects.active = body
    with bpy.context.temp_override(active_object=body, object=body, selected_objects=[body]):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.remove_doubles(threshold=seams.MERGE_DISTANCE, use_centroid=True)
        bpy.ops.object.mode_set(mode="OBJECT")
    want_count, (want_co, want_n) = len(body.data.vertices), _corners(body.data)

    ch = golden_import("kk")[1]  # a fresh one, for the Hook
    eyes_before = len([p for p in ch.body.data.polygons
                       if ch.body.material_slots[p.material_index].material.get("kkbp_role") == "eye_l"])
    before_co, before_n = _corners(ch.body.data)
    seams.fix_body_seams(fake_ctx(ch))
    got_co, got_n = _corners(ch.body.data)
    assert len(ch.body.data.vertices) == want_count < len(before_co)
    assert np.abs(got_co - want_co).max() < 1e-6
    assert np.abs(got_n - want_n).max() < 0.02  # the operator itself moves a few corners by ~0.012
    assert np.abs(got_n - before_n).max() < 0.01  # every corner keeps its normal (stored compressed)
    assert eyes_before == len([p for p in ch.body.data.polygons
                               if ch.body.material_slots[p.material_index].material.get("kkbp_role") == "eye_l"])
