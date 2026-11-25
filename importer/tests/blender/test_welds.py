"""The weld Steps on hand-built meshes, and on the Golden Samples (ADR 0047)."""

from types import SimpleNamespace

import bmesh
import bpy
import numpy as np
import pytest

from conftest import submodule
from hook_ctx import fake_ctx

character = submodule("character")
welds = submodule("steps.welds")

NEAR = welds.WELD_DISTANCE / 10  # how far apart the glTF importer leaves the exporter's copies


def _bundle(roles):
    """A bundle that knows only the Material Roles of materials by Id."""
    return SimpleNamespace(material=lambda i: SimpleNamespace(role=roles[i]) if i in roles else None)


def _object(ch, quads, roles=("body",), part="body"):
    """One quad per (x, z, material index), each with its own four vertices, so touching quads have
    doubled edges; a material per role, with the role's name as its Id."""
    mesh = bpy.data.meshes.new("m")
    bm = bmesh.new()
    for x, z, mat in quads:
        vs = [bm.verts.new(co) for co in ((x, 0, z), (x + 1, 0, z), (x + 1, 0, z + 1), (x, 0, z + 1))]
        bm.faces.new(vs).material_index = mat
    bm.to_mesh(mesh)
    bm.free()
    for role in roles:
        mat = bpy.data.materials.new(role)
        mat["id"] = role
        mesh.materials.append(mat)
    obj = bpy.data.objects.new("m", mesh)
    bpy.context.scene.collection.objects.link(obj)
    return ch.add_part(obj, part)


def _corner_normals(mesh):
    co = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get("co", co)
    vi = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get("vertex_index", vi)
    n = np.empty(len(mesh.loops) * 3)
    mesh.corner_normals.foreach_get("vector", n)
    return {tuple(np.round(c, 4)) + (i % 4,): tuple(v) for i, (c, v) in
            enumerate(zip(co.reshape(-1, 3)[vi], n.reshape(-1, 3)))}


def test_copies_in_one_mesh_weld_and_keep_their_normals():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    obj = _object(ch, [(0, 0, 0), (1, 0, 0)])
    mesh = obj.data
    mesh.vertices[4].co.x += NEAR  # the exporter's copies, as the glTF importer leaves them
    # A hard edge: each quad's corners point their own way.
    mesh.normals_split_custom_set([(0, -1, 0)] * 4 + [(0.6, -0.8, 0)] * 4)
    before = _corner_normals(mesh)
    welds.weld_copies(fake_ctx(ch, _bundle({"body": "body"})))
    assert len(mesh.vertices) == 6 and len(mesh.polygons) == 2
    after = _corner_normals(mesh)
    for k in before:
        assert np.allclose(before[k], after[k], atol=0.01), k


def test_copies_in_two_meshes_stay_apart():
    """An eyeline sits on the face, and a nail on the body: they are their own surfaces."""
    ch = character.Character.new("Chika", "KK", "/nowhere")
    a = _object(ch, [(0, 0, 0)])
    b = _object(ch, [(1, 0, 0)])
    welds.weld_copies(fake_ctx(ch, _bundle({"body": "body"})))
    assert len(a.data.vertices) == len(b.data.vertices) == 4


def test_copies_farther_apart_stay():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    obj = _object(ch, [(0, 0, 0), (1, 0, 0)])
    obj.data.vertices[4].co.x += welds.WELD_DISTANCE * 3
    obj.data.vertices[7].co.x += welds.WELD_DISTANCE * 3
    welds.weld_copies(fake_ctx(ch, _bundle({"body": "body"})))
    assert len(obj.data.vertices) == 8


def test_a_face_is_never_collapsed():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    obj = _object(ch, [(0, 0, 0)])
    obj.data.vertices[1].co = obj.data.vertices[0].co  # a degenerate edge the game wrote
    welds.weld_copies(fake_ctx(ch, _bundle({"body": "body"})))
    assert len(obj.data.vertices) == 4 and len(obj.data.polygons) == 1


def test_a_cluster_welds_by_index_not_by_distance():
    """Vertex 0 is within the distance of 1 and of 2, which share a face, so it can weld onto only one:
    always 1, the lower index, though 2 is nearer. The nearer one changes with physics between exports."""
    ch = character.Character.new("Chika", "KK", "/nowhere")
    mesh = bpy.data.meshes.new("m")
    bm = bmesh.new()
    d = welds.WELD_DISTANCE
    vs = [bm.verts.new(co) for co in ((0, 0, 0), (0.6 * d, 0, 0), (-0.3 * d, 0, 0),
                                      (0, 0, 1), (1, 0, 0), (1, 0, 1))]
    bm.faces.new((vs[1], vs[2], vs[3]))
    bm.faces.new((vs[0], vs[4], vs[5]))
    bm.to_mesh(mesh)
    bm.free()
    mat = bpy.data.materials.new("body")
    mat["id"] = "body"
    mesh.materials.append(mat)
    obj = bpy.data.objects.new("m", mesh)
    bpy.context.scene.collection.objects.link(obj)
    ch.add_part(obj, "body")
    welds.weld_copies(fake_ctx(ch, _bundle({"body": "body"})))
    assert len(mesh.vertices) == 5 and len(mesh.polygons) == 2
    xs = sorted(v.co.x for v in mesh.vertices if abs(v.co.x) < 0.5 and v.co.z == 0)
    assert xs == pytest.approx([-0.3 * d, 0], abs=d / 100)  # 2 kept its place; 1 went onto 0


def test_the_back_of_a_double_sided_card_stays():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    obj = _object(ch, [(0, 0, 0), (0, 0, 0)])
    mesh = obj.data
    mesh.polygons[1].flip()
    welds.weld_copies(fake_ctx(ch, _bundle({"body": "body"})))
    assert len(mesh.vertices) == 8 and len(mesh.polygons) == 2


def test_a_doubled_layer_of_several_faces_stays_apart():
    """An eyeline and its shadow: two quads side by side, then the same two again with their own
    vertices. Once the first shadow quad is kept apart, the second must still be found."""
    ch = character.Character.new("Chika", "KK", "/nowhere")
    mesh = bpy.data.meshes.new("m")
    bm = bmesh.new()
    for _ in range(2):
        vs = [bm.verts.new(co) for co in ((0, 0, 0), (1, 0, 0), (2, 0, 0), (2, 0, 1), (1, 0, 1), (0, 0, 1))]
        bm.faces.new((vs[0], vs[1], vs[4], vs[5]))
        bm.faces.new((vs[1], vs[2], vs[3], vs[4]))
    bm.to_mesh(mesh)
    bm.free()
    mat = bpy.data.materials.new("body")
    mat["id"] = "body"
    mesh.materials.append(mat)
    obj = bpy.data.objects.new("m", mesh)
    bpy.context.scene.collection.objects.link(obj)
    ch.add_part(obj, "body")
    welds.weld_copies(fake_ctx(ch, _bundle({"body": "body"})))
    assert len(mesh.vertices) == 12 and len(mesh.polygons) == 4


def test_the_neck_welds_the_face_to_the_body_only():
    """On Body: the face/body doubled edge welds; the doubled edge of two body quads (two meshes joined
    into Body) and the eyeline's doubled edge with the face stay."""
    ch = character.Character.new("Chika", "KK", "/nowhere")
    body = _object(ch, [(0, 0, 0), (1, 0, 1), (2, 0, 1), (-1, 0, 2)], roles=("face", "body", "eyeline_upper"))
    for v in (4, 7):  # the body quad's edge on the face's side, as the importer leaves the copies
        body.data.vertices[v].co.x += NEAR
    ctx = fake_ctx(ch, _bundle({"face": "face", "body": "body", "eyeline_upper": "eyeline_upper"}))
    welds.weld_neck(ctx)
    assert len(body.data.vertices) == 14
    assert len(body.data.polygons) == 4
    assert ctx.log.lines[-1].endswith("Welded 2 face vertices onto the body at the neck")


def test_a_character_with_no_body_has_no_neck():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    welds.weld_neck(fake_ctx(ch, _bundle({})))


def _neck(body):
    role = {i: s.material.get("kkbp_role") for i, s in enumerate(body.material_slots)}
    used = {}
    for p in body.data.polygons:
        if role[p.material_index] in welds.NECK:
            for v in p.vertices:
                used.setdefault(v, set()).add(role[p.material_index])
    return used


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_the_golden_neck_is_one_surface(golden_import, sample):
    """No face vertex is left beside a body vertex."""
    body = golden_import(sample)[1].body
    used = _neck(body)
    assert sum(1 for roles in used.values() if len(roles) == 2) >= 20
    face = [body.data.vertices[v].co for v, roles in used.items() if roles == {"face"}]
    others = [body.data.vertices[v].co for v, roles in used.items() if roles == {"body"}]
    assert not [a for a in face if any((a - b).length < 1e-4 for b in others if abs(a.z - b.z) < 1e-4)]
