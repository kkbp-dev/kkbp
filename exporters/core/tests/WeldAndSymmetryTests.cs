using System.Collections.Generic;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    internal static class TestMeshes
    {
        /// <summary>A mesh of the given triangles, one bone per vertex from `bones`, with one material.</summary>
        public static MeshData Make(string key, Vec3[] positions, int[] triangles, string[] bones, int[] boneOfVertex, string material)
        {
            var mesh = new MeshData
            {
                Key = key,
                Name = key,
                Positions = positions,
                Normals = new Vec3[positions.Length],
                BoneKeys = bones,
                InfluencesPerVertex = 4,
                Joints = new int[positions.Length * 4],
                Weights = new float[positions.Length * 4],
            };
            for (int v = 0; v < positions.Length; v++)
            {
                mesh.Normals[v] = new Vec3(0, 0, v % 2 == 0 ? 1 : -1);
                mesh.Joints[v * 4] = boneOfVertex[v];
                mesh.Weights[v * 4] = 1;
            }
            mesh.SubMeshes.Add(new SubMesh { Indices = triangles, MaterialKey = material });
            return mesh;
        }

        public static string[] BonesOf(MeshData mesh, int v)
        {
            var result = new List<string>();
            for (int s = 0; s < mesh.InfluencesPerVertex; s++)
            {
                if (mesh.Weights[v * mesh.InfluencesPerVertex + s] > 0)
                {
                    result.Add(mesh.BoneKeys[mesh.Joints[v * mesh.InfluencesPerVertex + s]]);
                }
            }
            return result.ToArray();
        }
    }

    public class WeldTests
    {
        private static readonly Dictionary<string, MaterialRole> NoRoles = new Dictionary<string, MaterialRole>();

        // Two triangles side by side whose shared edge is written twice, as at a UV seam:
        // vertices 1 and 3, and 2 and 4, are copies a few micrometres apart.
        private static MeshData Seam(float gap)
        {
            var p = new[]
            {
                new Vec3(0, 0, 0), new Vec3(0.01f, 0, 0), new Vec3(0, 0.01f, 0),
                new Vec3(0.01f + gap, 0, 0), new Vec3(0, 0.01f, gap), new Vec3(0.01f, 0.01f, 0),
            };
            return TestMeshes.Make("m", p, new[] { 0, 1, 2, 3, 5, 4 }, new[] { "a", "b" }, new[] { 0, 0, 0, 1, 1, 1 }, "mat");
        }

        [Fact]
        public void Copies_get_one_position_weights_and_shape_keys()
        {
            var mesh = Seam(5e-6f);
            var deltas = new Vec3[6];
            deltas[1] = new Vec3(0, 0.002f, 0);
            deltas[3] = new Vec3(0, 0.004f, 0);
            mesh.Morphs.Add(new MorphData { Category = ExpressionCategory.Mouth, GameName = "k", PositionDeltas = deltas });
            var normals = (Vec3[])mesh.Normals.Clone();

            var result = Welds.Weld(new[] { mesh }, NoRoles);

            Assert.Equal(2, result.Groups);
            Assert.Equal(mesh.Positions[1], mesh.Positions[3]);
            Assert.Equal(mesh.Positions[2], mesh.Positions[4]);
            Assert.Equal(0.01f + 2.5e-6f, mesh.Positions[1].X, 7);
            Assert.Equal(0.003f, deltas[1].Y, 6);
            Assert.Equal(deltas[1], deltas[3]);
            Assert.Equal(new[] { "a", "b" }, TestMeshes.BonesOf(mesh, 1));
            Assert.Equal(new[] { "a", "b" }, TestMeshes.BonesOf(mesh, 3));
            Assert.Equal(0.5f, mesh.Weights[1 * 4], 6);
            Assert.Equal(normals, mesh.Normals); // each copy keeps its own normal
            Assert.Equal(new Vec3(0, 0, 0), mesh.Positions[0]);
        }

        [Fact]
        public void Copies_farther_apart_than_the_distance_stay()
        {
            var mesh = Seam(2e-5f);
            var before = (Vec3[])mesh.Positions.Clone();
            Assert.Equal(0, Welds.Weld(new[] { mesh }, NoRoles).Groups);
            Assert.Equal(before, mesh.Positions);
        }

        [Fact]
        public void A_triangle_is_never_collapsed()
        {
            // Vertices 0 and 1 are 1 µm apart but share a triangle: a short edge, not copies.
            var p = new[] { new Vec3(0, 0, 0), new Vec3(1e-6f, 0, 0), new Vec3(0, 0.01f, 0) };
            var mesh = TestMeshes.Make("m", p, new[] { 0, 1, 2 }, new[] { "a" }, new[] { 0, 0, 0 }, "mat");
            Assert.Equal(0, Welds.Weld(new[] { mesh }, NoRoles).Groups);
            Assert.NotEqual(mesh.Positions[0], mesh.Positions[1]);
        }

        [Fact]
        public void A_double_sided_triangle_keeps_its_back()
        {
            // The back is the same triangle with its own vertices and the other winding.
            var p = new[]
            {
                new Vec3(0, 0, 0), new Vec3(0.01f, 0, 0), new Vec3(0, 0.01f, 0),
                new Vec3(0, 0, 1e-6f), new Vec3(0.01f, 0, 0), new Vec3(0, 0.01f, 0),
            };
            var mesh = TestMeshes.Make("m", p, new[] { 0, 1, 2, 3, 5, 4 }, new[] { "a" }, new int[6], "mat");
            var result = Welds.Weld(new[] { mesh }, NoRoles);
            Assert.Equal(0, result.Groups);
            Assert.Equal(6, result.KeptApart);
            Assert.Equal(1e-6f, mesh.Positions[3].Z);
        }

        [Fact]
        public void The_neck_joins_the_face_to_the_body_with_the_bodys_weights()
        {
            var face = TestMeshes.Make("face", new[] { new Vec3(0, 1.4f, 0), new Vec3(0.01f, 1.4f, 0), new Vec3(0, 1.41f, 0) },
                new[] { 0, 1, 2 }, new[] { "faceroot" }, new int[3], "face_mat");
            var faceKey = new Vec3[3];
            faceKey[0] = new Vec3(0, 0.001f, 0);
            face.Morphs.Add(new MorphData { Category = ExpressionCategory.Mouth, GameName = "k", PositionDeltas = faceKey });
            var body = TestMeshes.Make("body", new[] { new Vec3(5e-5f, 1.4f, 0), new Vec3(0.01f, 1.39f, 0), new Vec3(0, 1.39f, 0) },
                new[] { 0, 1, 2 }, new[] { "head" }, new int[3], "body_mat");
            // The eyeline sits on the face, but isn't welded to it.
            var eyeline = TestMeshes.Make("eyeline", new[] { new Vec3(0.01f, 1.4f, 2e-6f), new Vec3(0.02f, 1.4f, 0), new Vec3(0.01f, 1.41f, 0) },
                new[] { 0, 1, 2 }, new[] { "faceroot" }, new int[3], "eyeline_mat");
            var roles = new Dictionary<string, MaterialRole>
            {
                { "face_mat", MaterialRole.Face }, { "body_mat", MaterialRole.Body }, { "eyeline_mat", MaterialRole.EyelineUpper },
            };

            var result = Welds.Weld(new[] { face, body, eyeline }, roles);

            Assert.Equal(1, result.SeamCopies);
            Assert.Equal(body.Positions[0], face.Positions[0]);
            Assert.Equal(2.5e-5f, face.Positions[0].X, 7);
            Assert.Equal(new[] { "head" }, TestMeshes.BonesOf(face, 0));
            Assert.Equal(new[] { "faceroot", "head" }, face.BoneKeys);
            Assert.Equal(new[] { "head" }, TestMeshes.BonesOf(body, 0));
            Assert.Equal(Vec3.Zero, faceKey[0]); // the body has no such key, so the neck doesn't move with it
            Assert.Equal(2e-6f, eyeline.Positions[0].Z);
        }

        [Fact]
        public void A_mesh_with_mismatched_arrays_is_left_for_the_checks()
        {
            var mesh = Seam(5e-6f);
            mesh.Weights = new float[1];
            Assert.Equal(0, Welds.Weld(new[] { mesh }, NoRoles).Groups);
        }
    }

    public class SymmetryTests
    {
        private static MeshData Points(string key, params Vec3[] p)
        {
            var triangles = new List<int>();
            for (int i = 0; i + 2 < p.Length; i += 3)
            {
                triangles.AddRange(new[] { i, i + 1, i + 2 });
            }
            return TestMeshes.Make(key, p, triangles.ToArray(), new[] { "a" }, new int[p.Length], "mat");
        }

        [Fact]
        public void Near_mirror_pairs_become_exact_mirrors()
        {
            var mesh = Points("m", new Vec3(0.1f, 1, 0.02f), new Vec3(-0.10003f, 1.00001f, 0.02f), new Vec3(0.3f, 1, 0));
            var result = Symmetry.Mirror(new[] { mesh });
            var a = mesh.Positions[0];
            var b = mesh.Positions[1];
            Assert.Equal(-a.X, b.X);
            Assert.Equal(a.Y, b.Y);
            Assert.Equal(a.Z, b.Z);
            Assert.Equal(0.100015f, a.X, 6);
            Assert.Equal(2, result.Paired);
            Assert.Equal(new Vec3(0.3f, 1, 0), mesh.Positions[2]); // nothing near its mirror
            Assert.Equal(1, result.Unpaired);
        }

        [Fact]
        public void Vertices_near_the_middle_go_onto_it()
        {
            var mesh = Points("m", new Vec3(2e-5f, 1, 0), new Vec3(-6e-5f, 1.1f, 0), new Vec3(0.2f, 1, 0));
            var result = Symmetry.Mirror(new[] { mesh });
            Assert.Equal(0f, mesh.Positions[0].X);
            Assert.Equal(-6e-5f, mesh.Positions[1].X); // its mirror is 0.12 mm away
            Assert.Equal(1, result.Centred);
        }

        [Fact]
        public void Positions_shared_by_welded_copies_move_together()
        {
            var mesh = Points("m", new Vec3(0.1f, 1, 0), new Vec3(-0.10002f, 1, 0), new Vec3(0.3f, 1, 0),
                new Vec3(0.1f, 1, 0), new Vec3(0.2f, 1.2f, 0), new Vec3(0.2f, 1.3f, 0));
            Symmetry.Mirror(new[] { mesh });
            Assert.Equal(mesh.Positions[0], mesh.Positions[3]);
            Assert.Equal(-mesh.Positions[0].X, mesh.Positions[1].X);
        }

        [Fact]
        public void The_left_eye_pairs_with_the_right_in_another_mesh()
        {
            var left = Points("l", new Vec3(0.03f, 1.5f, 0.05f), new Vec3(0.031f, 1.5f, 0.05f), new Vec3(0.03f, 1.501f, 0.05f));
            var right = Points("r", new Vec3(-0.03001f, 1.5f, 0.05f), new Vec3(-0.031f, 1.5f, 0.05f), new Vec3(-0.03f, 1.50101f, 0.05f));
            var result = Symmetry.Mirror(new[] { left, right });
            Assert.Equal(6, result.Paired);
            for (int v = 0; v < 3; v++)
            {
                Assert.Equal(-left.Positions[v].X, right.Positions[v].X);
                Assert.Equal(left.Positions[v].Y, right.Positions[v].Y);
            }
        }
    }
}
