"""The symmetry Step and the upper-eyeline offset, on hand-built meshes and the Golden Samples (ADR 0049)."""

from types import SimpleNamespace

import bmesh
import bpy
import pytest
from mathutils import kdtree

from conftest import submodule
from hook_ctx import fake_ctx

character = submodule("character")
mesh_steps = submodule("steps.mesh")
symmetry = submodule("steps.symmetry")

NOISE = symmetry.SNAP_DISTANCE / 4  # what the glTF importer leaves between mirror partners


def _bundle(roles):
    return SimpleNamespace(material=lambda i: SimpleNamespace(role=roles[i]) if i in roles else None)


def _object(ch, triangles, roles=("body",), part="body", outfit=None, keys=False):
    """One triangle per (corners, material index), each with its own vertices."""
    mesh = bpy.data.meshes.new("m")
    bm = bmesh.new()
    for corners, mat in triangles:
        bm.faces.new([bm.verts.new(c) for c in corners]).material_index = mat
    bm.to_mesh(mesh)
    bm.free()
    for role in roles:
        mat = bpy.data.materials.new(role)
        mat["id"] = role
        mesh.materials.append(mat)
    obj = bpy.data.objects.new("m", mesh)
    bpy.context.scene.collection.objects.link(obj)
    if keys:
        obj.shape_key_add(name="Basis")
        smile = obj.shape_key_add(name="smile")
        for d in smile.data:
            d.co.z += 0.01
    return ch.add_part(obj, part, outfit=outfit)


def _mirror_gap(points, p):
    return min((q - type(q)((-p[0], p[1], p[2]))).length for q in points)


def test_partners_within_a_mesh_become_exact_mirrors():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    obj = _object(ch, [(((0.1, 0, 1.4), (0.12, 0, 1.4), (0.1, 0, 1.42)), 0),
                       (((-0.1 - NOISE, 0, 1.4), (-0.12, 0, 1.4 + NOISE), (-0.1, 0, 1.42)), 0),
                       (((NOISE / 2, 0.01, 1.5), (0.01, 0.01, 1.6), (-0.01, 0.01, 1.6)), 0)], keys=True)
    mesh = obj.data
    symmetry.snap_to_symmetry(fake_ctx(ch, _bundle({})))
    co = [v.co.copy() for v in mesh.vertices]
    for v in range(3):
        assert (co[v].x, co[v].y, co[v].z) == (-co[v + 3].x, co[v + 3].y, co[v + 3].z)
    assert co[6].x == 0.0
    smile = mesh.shape_keys.key_blocks["smile"]
    assert smile.data[3].co.x == co[3].x and abs(smile.data[3].co.z - co[3].z - 0.01) < 1e-6


def test_partners_farther_apart_stay():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    far = symmetry.SNAP_DISTANCE * 5
    obj = _object(ch, [(((0.1, 0, 1.4), (0.12, 0, 1.4), (0.1, 0, 1.42)), 0),
                       (((-0.1 - far, 0, 1.4), (-0.12, 0, 1.4), (-0.1, 0, 1.42)), 0)])
    symmetry.snap_to_symmetry(fake_ctx(ch, _bundle({})))
    assert abs(obj.data.vertices[3].co.x - (-0.1 - far)) < 1e-9


def test_the_eyes_pair_across_meshes_but_an_overlay_keeps_its_own_partner():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    left = _object(ch, [(((0.03, -0.06, 1.45), (0.035, -0.06, 1.45), (0.03, -0.06, 1.455)), 0)])
    right = _object(ch, [(((-0.03 - NOISE, -0.06, 1.45), (-0.035, -0.06, 1.45 + NOISE), (-0.03, -0.06, 1.455)), 0)])
    # A face and an eyeline lying within NOISE of it, each symmetrical in its own mesh.
    tri = ((0.02, -0.07, 1.44), (0.025, -0.07, 1.44), (0.02, -0.07, 1.445))
    mirror = tuple((-x, y, z) for x, y, z in tri)
    face = _object(ch, [(tri, 0), (tuple((x + NOISE, y, z) for x, y, z in mirror), 0)])
    eyeline = _object(ch, [(tuple((x + NOISE, y, z) for x, y, z in tri), 0), (tuple((x - NOISE / 3, y, z) for x, y, z in mirror), 0)])
    symmetry.snap_to_symmetry(fake_ctx(ch, _bundle({})))
    for a, b in ((left, right),):
        for v in range(3):
            pa, pb = a.data.vertices[v].co, b.data.vertices[v].co
            assert (pa.x, pa.y, pa.z) == (-pb.x, pb.y, pb.z)
    for obj in (face, eyeline):
        for v in range(3):
            pa, pb = obj.data.vertices[v].co, obj.data.vertices[v + 3].co
            assert (pa.x, pa.y, pa.z) == (-pb.x, pb.y, pb.z)
    # Each overlay vertex stays its own, a little off the face's.
    assert (face.data.vertices[0].co - eyeline.data.vertices[0].co).length > 0


def test_outfits_are_not_paired_across_meshes():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    a = _object(ch, [(((0.2, 0, 1.0), (0.21, 0, 1.0), (0.2, 0, 1.01)), 0)], part="outfit", outfit=0)
    _object(ch, [(((-0.2 - NOISE, 0, 1.0), (-0.21, 0, 1.0), (-0.2, 0, 1.01)), 0)], part="outfit", outfit=0)
    symmetry.snap_to_symmetry(fake_ctx(ch, _bundle({})))
    assert a.data.vertices[0].co.x == pytest.approx(0.2, abs=1e-7)


def test_the_upper_eyeline_moves_forward_off_its_shadow():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    tri = ((0.02, -0.07, 1.44), (0.025, -0.07, 1.44), (0.02, -0.07, 1.445))
    obj = _object(ch, [(tri, 0), (tri, 1)], roles=("eyeline_upper", "eyeline_shadow"), keys=True)
    alone = _object(ch, [(tri, 0)], roles=("eyeline_upper",))
    mesh_steps.move_upper_eyeline_forward(
        fake_ctx(ch, _bundle({"eyeline_upper": "eyeline_upper", "eyeline_shadow": "eyeline_shadow"})))
    offset = mesh_steps.UPPER_EYELINE_OFFSET
    assert obj.data.vertices[0].co.y == pytest.approx(-0.07 - offset)
    assert obj.data.vertices[3].co.y == pytest.approx(-0.07)  # the shadow stays
    assert obj.data.shape_keys.key_blocks["smile"].data[0].co.y == pytest.approx(-0.07 - offset)
    assert alone.data.vertices[0].co.y == pytest.approx(-0.07)  # no shadow, nothing to clear


@pytest.mark.parametrize("sample", ["kk", "kks", "svs"])
def test_the_golden_body_is_an_exact_mirror_image(golden_import, sample):
    """Every Body vertex has a partner at exactly (-x, y, z), nearer than any other vertex, but for the
    few the game's own mesh has none for (the tongue; on KKS, 13 on the crotch's middle line)."""
    body = golden_import(sample)[1].body
    mesh = body.data
    tree = kdtree.KDTree(len(mesh.vertices))
    for v in mesh.vertices:
        tree.insert(v.co, v.index)
    tree.balance()
    unpaired = [v.index for v in mesh.vertices if tree.find((-v.co.x, v.co.y, v.co.z))[2] > 0]
    assert len(unpaired) <= 20, len(unpaired)
