using System.Collections.Generic;
using System.Linq;
using KKBP.Exporter.Core.AdapterKit;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    public class NormalMapTests
    {
        [Fact]
        public void Dxt5nm_pixels_take_x_from_alpha()
        {
            // DXT5nm stores X in A and Y in G, with R at 1. A flat normal is (128, 128) there.
            var pixels = new byte[] { 255, 128, 255, 128 };
            NormalMaps.UnpackUnity(pixels);
            Assert.Equal(new byte[] { 128, 128, 255, 255 }, pixels);
        }

        [Fact]
        public void Plain_maps_with_opaque_alpha_keep_x_in_red()
        {
            var pixels = new byte[] { 255, 128, 0, 255 };
            NormalMaps.UnpackUnity(pixels);
            Assert.Equal(255, pixels[0]);
            Assert.Equal(128, pixels[1]);
            Assert.InRange(pixels[2], 127, 129); // X is 1, so Z is 0.
            Assert.Equal(255, pixels[3]);
        }

        [Fact]
        public void Z_is_rebuilt_and_never_negative()
        {
            var pixels = new byte[] { 255, 255, 0, 255 };
            NormalMaps.UnpackUnity(pixels);
            Assert.Equal(128, pixels[2]);
        }
    }

    public class DeltaTests
    {
        [Fact]
        public void Subtract_and_compare()
        {
            var basis = new[] { new Vec3(0, 1, 0), new Vec3(1, 1, 1) };
            var posed = new[] { new Vec3(0, 1.5f, 0), new Vec3(1, 1, 1) };
            var d = Deltas.Subtract(posed, basis);
            Assert.Equal(0.5f, d[0].Y, 6);
            Assert.False(Deltas.IsEmpty(d));
            Assert.True(Deltas.IsEmpty(Deltas.Subtract(basis, basis)));
            Assert.True(Deltas.Same(d, new[] { new Vec3(0, 0.5f, 0), new Vec3(0, 0, 0.0000001f) }));
            Assert.False(Deltas.Same(d, new[] { new Vec3(0, 0.5f, 0), new Vec3(0, 0.001f, 0) }));
        }
    }

    public class HiddenBasisTests
    {
        [Fact]
        public void Offset_is_half_the_face_depth_backwards()
        {
            var face = new[] { new Vec3(0, 1.5f, 0.05f), new Vec3(0, 1.6f, -0.08f), new Vec3(0.1f, 1.55f, 0.1f) };
            var offset = HiddenBasis.Offset(face);
            Assert.Equal(0, offset.X);
            Assert.Equal(-0.09f, offset.Z, 5);
        }

        [Fact]
        public void Apply_hides_the_mesh_and_adds_a_showing_key()
        {
            var mesh = new MeshData { Positions = new[] { new Vec3(0, 1.5f, 0.1f), new Vec3(0.01f, 1.5f, 0.1f) } };
            var existing = new MorphData { Category = ExpressionCategory.Eye, ExpressionName = "Eye Default", PositionDeltas = new[] { new Vec3(0, 0.01f, 0), new Vec3(0, 0.01f, 0) } };
            mesh.Morphs.Add(existing);
            HiddenBasis.Apply(mesh, new Vec3(0, 0, -0.2f), ExpressionCategory.Tears, "Tears big");

            Assert.Equal(-0.1f, mesh.Positions[0].Z, 5);
            Assert.Equal(0.01f, existing.PositionDeltas[0].Y, 6);
            var show = mesh.Morphs.Last();
            Assert.Equal("Tears big", show.ExpressionName);
            Assert.Null(show.GameName);
            Assert.Equal(0.2f, show.PositionDeltas[1].Z, 5);
        }

        [Fact]
        public void Only_tears_and_gag_eyes_get_one()
        {
            var mesh = new MeshData { Positions = new[] { Vec3.Zero } };
            Assert.Throws<System.ArgumentException>(() => HiddenBasis.Apply(mesh, Vec3.Zero, ExpressionCategory.Eye, "Eye Default"));
        }
    }

    public class EyeWhiteTests
    {
        private static MeshData Eye()
        {
            var eye = new MeshData
            {
                Key = "body:cf_O_hitomi_L",
                Name = "cf_O_hitomi_L",
                Positions = new[] { new Vec3(0, 1.4f, 0.02f), new Vec3(0.01f, 1.4f, 0.02f), new Vec3(0, 1.41f, 0.02f) },
                Normals = new[] { new Vec3(0, 0, 1), new Vec3(0, 0, 2), new Vec3(0, 0.6f, 0.8f) },
                BoneKeys = new[] { "body:cf_J_Eye_tx_L" },
                InfluencesPerVertex = 1,
                Joints = new[] { 0, 0, 0 },
                Weights = new[] { 1f, 1f, 1f },
            };
            eye.UvSets.Add(new[] { new Vec2(0, 0), new Vec2(1, 0), new Vec2(0, 1) });
            eye.SubMeshes.Add(new SubMesh { Indices = new[] { 0, 1, 2 }, MaterialKey = "body:cf_O_hitomi_L#0" });
            return eye;
        }

        [Fact]
        public void The_copy_rests_behind_the_eye_along_its_normals()
        {
            var eye = Eye();
            var copy = EyeWhites.Copy(eye, k => k + "_white");

            Assert.Equal("body:cf_O_hitomi_L_white", copy.Key);
            Assert.Equal("cf_O_hitomi_L_white", copy.Name);
            Assert.Equal(0.019f, copy.Positions[0].Z, 6);
            Assert.Equal(0.019f, copy.Positions[1].Z, 6); // the normal's length doesn't matter
            Assert.Equal(1.4094f, copy.Positions[2].Y, 6);
            Assert.Equal(0.0192f, copy.Positions[2].Z, 6);
            Assert.Equal(0.02f, eye.Positions[0].Z, 6); // the eye stays where the game has it
            Assert.Equal("body:cf_O_hitomi_L#0_white", copy.SubMeshes[0].MaterialKey);
            Assert.Equal(new[] { 0, 1, 2 }, copy.SubMeshes[0].Indices);
            Assert.Equal(eye.BoneKeys, copy.BoneKeys);
            Assert.Equal(eye.Weights, copy.Weights);
            Assert.Equal(eye.UvSets[0], copy.UvSets[0]);
            Assert.NotSame(eye.UvSets[0], copy.UvSets[0]);
        }

        [Fact]
        public void Shape_keys_are_copied_without_their_effects()
        {
            var eye = Eye();
            var morph = new MorphData { Category = ExpressionCategory.Eye, ExpressionName = "Eye Wink", GameName = "eye_wink", PositionDeltas = new[] { Vec3.Zero, Vec3.Zero, new Vec3(0, -0.001f, 0) } };
            morph.HidesMeshKeys.Add("body:something");
            eye.Morphs.Add(morph);
            var copy = EyeWhites.Copy(eye, k => k);

            Assert.Equal("Eye Wink", copy.Morphs[0].ExpressionName);
            Assert.Equal(-0.001f, copy.Morphs[0].PositionDeltas[2].Y, 6);
            Assert.Empty(copy.Morphs[0].HidesMeshKeys);
        }

        [Fact]
        public void Whatever_hides_the_eye_hides_the_copy()
        {
            var face = new MeshData { Key = "body:cf_O_face" };
            var hides = new MorphData { ExpressionName = "Eye Closed" };
            hides.HidesMeshKeys.Add("body:cf_O_hitomi_L");
            var other = new MorphData { ExpressionName = "Eye Default" };
            face.Morphs.Add(hides);
            face.Morphs.Add(other);

            EyeWhites.HideWith(new[] { face }, "body:cf_O_hitomi_L", "body:cf_O_hitomi_L_white");
            EyeWhites.HideWith(new[] { face }, "body:cf_O_hitomi_L", "body:cf_O_hitomi_L_white");

            Assert.Equal(new[] { "body:cf_O_hitomi_L", "body:cf_O_hitomi_L_white" }, hides.HidesMeshKeys);
            Assert.Empty(other.HidesMeshKeys);
        }

        [Fact]
        public void An_eye_without_normals_is_refused()
        {
            var eye = Eye();
            eye.Normals = null;
            Assert.Throws<System.ArgumentException>(() => EyeWhites.Copy(eye, k => k));
        }
    }

    public class SeamClosingTests
    {
        // A rim triangle at z 0 and a disc triangle 3 mm behind it, its corners 0.4 mm off the rim's
        // sideways, as in SVS's eye sockets. Every edge of each is open.
        private static MeshData Socket(Vec3 discDelta, ExpressionCategory category = ExpressionCategory.Gag)
        {
            var mesh = new MeshData
            {
                Positions = new[]
                {
                    new Vec3(0, 0, 0), new Vec3(0.01f, 0, 0), new Vec3(0, 0.01f, 0),
                    new Vec3(0.0004f, 0, -0.003f), new Vec3(0.0104f, 0, -0.003f), new Vec3(0.0004f, 0.01f, -0.003f),
                },
            };
            mesh.SubMeshes.Add(new SubMesh { Indices = new[] { 0, 1, 2, 3, 4, 5 } });
            var deltas = new Vec3[6];
            for (int v = 3; v < 6; v++)
            {
                deltas[v] = discDelta;
            }
            mesh.Morphs.Add(new MorphData { Category = category, ExpressionName = "Gag Heart Eyes", PositionDeltas = deltas });
            return mesh;
        }

        [Fact]
        public void A_key_that_nearly_closes_the_seam_closes_it()
        {
            var mesh = Socket(new Vec3(0, 0, 0.003f));
            var closed = SeamClosing.Close(mesh, ExpressionCategory.Gag);

            Assert.Single(closed);
            for (int v = 0; v < 3; v++)
            {
                var end = mesh.Positions[v + 3] + mesh.Morphs[0].PositionDeltas[v + 3];
                Assert.Equal(0, (end - mesh.Positions[v]).Length, 6);
            }
            Assert.Equal(0, mesh.Morphs[0].PositionDeltas[0].Length, 6);
        }

        [Fact]
        public void A_key_that_stops_too_far_off_is_left_as_it_is()
        {
            var mesh = Socket(new Vec3(0, 0, 0.0015f));
            Assert.Empty(SeamClosing.Close(mesh, ExpressionCategory.Gag));
            Assert.Equal(0.0015f, mesh.Morphs[0].PositionDeltas[3].Z, 6);
        }

        [Fact]
        public void Keys_of_other_categories_are_left_as_they_are()
        {
            var mesh = Socket(new Vec3(0, 0, 0.003f), ExpressionCategory.Eye);
            Assert.Empty(SeamClosing.Close(mesh, ExpressionCategory.Gag));
            Assert.Equal(0.003f, mesh.Morphs[0].PositionDeltas[3].Z, 6);
        }

        [Fact]
        public void A_uv_seam_is_not_an_open_edge()
        {
            // A quad of two triangles whose shared edge has its own vertices on each side (a UV seam).
            var mesh = new MeshData
            {
                Positions = new[]
                {
                    new Vec3(0, 0, 0), new Vec3(1, 0, 0), new Vec3(1, 1, 0),
                    new Vec3(0, 0, 0), new Vec3(1, 1, 0), new Vec3(0, 1, 0),
                },
            };
            mesh.SubMeshes.Add(new SubMesh { Indices = new[] { 0, 1, 2, 3, 4, 5 } });
            // Every corner is on the quad's outline, so all six are open-edge vertices; welding is what
            // keeps the diagonal from counting twice as open.
            Assert.Equal(6, SeamClosing.OpenEdgeVertices(mesh).Count);

            var inner = new MeshData { Positions = new Vec3[9] };
            for (int i = 0; i < 9; i++)
            {
                inner.Positions[i] = new Vec3(i % 3, i / 3, 0);
            }
            // A 2x2 grid with the centre vertex duplicated (index 4 and a copy at 9) on one triangle.
            inner.Positions = inner.Positions.Concat(new[] { new Vec3(1, 1, 0) }).ToArray();
            inner.SubMeshes.Add(new SubMesh
            {
                Indices = new[] { 0, 1, 4, 0, 4, 3, 1, 2, 5, 1, 5, 9, 3, 4, 7, 3, 7, 6, 4, 5, 8, 4, 8, 7 },
            });
            var open = SeamClosing.OpenEdgeVertices(inner);
            Assert.DoesNotContain(4, open);
            Assert.DoesNotContain(9, open);
            Assert.Equal(8, open.Count);
        }
    }

    public class BoneRuleTests
    {
        [Theory]
        [InlineData("cf_j_sk_00_01", false, BoneGroup.Skirt)]
        [InlineData("cf_d_sk_03_00", false, BoneGroup.Skirt)]
        [InlineData("cf_d_bust01_L", false, BoneGroup.Breast)]
        [InlineData("cf_s_bnip01_bustsize_R", false, BoneGroup.Breast)]
        [InlineData("cf_J_Vagina_L.003", false, BoneGroup.Nsfw)]
        [InlineData("cf_j_kokan", false, BoneGroup.Nsfw)]
        [InlineData("cf_s_ana", false, BoneGroup.Nsfw)]
        [InlineData("cm_J_dan101_00", false, BoneGroup.Nsfw)]
        [InlineData("cf_j_tang_03", false, BoneGroup.Mouth)]
        [InlineData("cf_J_Eye03_s_L", true, BoneGroup.Eye)]
        [InlineData("cf_J_hitomi_tx_R", true, BoneGroup.Eye)]
        [InlineData("cf_J_MayuTip_s_L", true, BoneGroup.Eyebrow)]
        [InlineData("cf_J_MouthLow", true, BoneGroup.Mouth)]
        [InlineData("cf_J_CheekUp_s_L", true, BoneGroup.Face)]
        [InlineData("cf_J_FaceRoot", true, BoneGroup.Face)]
        [InlineData("cf_j_hips", false, BoneGroup.Deform)]
        [InlineData("cf_s_thigh01_L", false, BoneGroup.Deform)]
        [InlineData("cf_d_arm01_R", false, BoneGroup.Deform)]
        [InlineData("cf_pv_hand_L", false, BoneGroup.Helper)]
        [InlineData("a_n_hair_pin", false, BoneGroup.Helper)]
        [InlineData("k_f_kokan_00", false, BoneGroup.Helper)]
        public void Body_groups_come_from_names(string name, bool underFace, BoneGroup expected)
        {
            Assert.Equal(expected, BoneRules.BodyGroup(name, underFace));
        }

        [Fact]
        public void A_needed_helper_is_face_above_the_face_root_only_and_deform_otherwise()
        {
            Assert.Equal(BoneGroup.Face, BoneRules.NeededHelperGroup(new[] { true, true }));
            Assert.Equal(BoneGroup.Deform, BoneRules.NeededHelperGroup(new[] { true, false }));
        }

        [Fact]
        public void Unweighted_outfit_bones_become_helpers_but_keep_the_tree_and_physics()
        {
            BoneData B(string key, string parent) => new BoneData { Key = key, ParentKey = parent, Group = BoneGroup.Hair };
            var bones = new List<BoneData>
            {
                B("hair", "head"),            // Above a weighted bone: kept.
                B("hair/a", "hair"),          // Weighted.
                B("hair/a/tip", "hair/a"),    // Unweighted leaf, but a physics particle: kept.
                B("hair/b", "hair"),          // Unweighted, nothing below: helper.
                B("hair/b/c", "hair/b"),      // Unweighted leaf: helper.
            };
            var mesh = new MeshData { BoneKeys = new[] { "hair/a", "hair/b" }, Joints = new[] { 0, 1 }, Weights = new[] { 1f, 0f } };
            var chain = new PhysicsChain { RootKey = "hair/a" };
            chain.Particles.Add(new PhysicsParticle { BoneKey = "hair/a/tip" });

            BoneRules.MarkUnweightedHelpers(bones, BoneRules.WeightedBones(new[] { mesh }), BoneRules.PhysicsBones(new[] { chain }, new PhysicsCollider[0]));

            Assert.Equal(new[] { BoneGroup.Hair, BoneGroup.Hair, BoneGroup.Hair, BoneGroup.Helper, BoneGroup.Helper }, bones.Select(b => b.Group));
        }
    }

    public class BlendModeTests
    {
        private static readonly HashSet<string> Glasses = new HashSet<string> { "Shader Forge/toon_glasses_lod0" };
        private static readonly HashSet<string> Alpha = new HashSet<string> { "Shader Forge/main_alpha" };

        [Theory]
        [InlineData("Shader Forge/toon_glasses_lod0", 3000, false, BlendMode.Glasses)]
        [InlineData("Shader Forge/main_alpha", 2000, false, BlendMode.Alpha)]
        [InlineData("Shader Forge/main_item", 3100, false, BlendMode.Alpha)]
        [InlineData("Shader Forge/main_item", 2450, false, BlendMode.Cutout)]
        [InlineData("Shader Forge/main_item", 2000, true, BlendMode.Cutout)]
        [InlineData("Shader Forge/main_item", 2000, false, BlendMode.Opaque)]
        [InlineData(null, 2000, false, BlendMode.Opaque)]
        public void Tables_first_then_render_queue(string shader, int queue, bool clip, BlendMode expected)
        {
            Assert.Equal(expected, BlendModes.From(shader, queue, clip, Glasses, Alpha));
        }
    }
}

namespace KKBP.Exporter.Core.Tests
{
    public class TextureRoleTests
    {
        [Theory]
        [InlineData("_MainTex", TextureRole.Main)]
        [InlineData("_Hair_color_mask", TextureRole.ColorMask)]
        [InlineData("_Cloth_alpha", TextureRole.AlphaMask)]
        [InlineData("_overtex3", TextureRole.Overlay)]
        public void Raw_properties_map_to_roles(string raw, TextureRole role)
        {
            Assert.Equal(role, KKBP.Exporter.Core.AdapterKit.TextureRoles.For(raw));
        }

        [Fact]
        public void Others_have_no_role_and_normal_maps_are_known()
        {
            Assert.Null(KKBP.Exporter.Core.AdapterKit.TextureRoles.For("_liquidmask"));
            Assert.True(KKBP.Exporter.Core.AdapterKit.TextureRoles.IsNormalMap("_NormalMapDetail"));
            Assert.True(KKBP.Exporter.Core.AdapterKit.TextureRoles.IsNormalMap("_BumpMap"));
            Assert.False(KKBP.Exporter.Core.AdapterKit.TextureRoles.IsNormalMap("_MainTex"));
        }
    }
}

namespace KKBP.Exporter.Core.Tests
{
    public class BoneRoleTests
    {
        [Theory]
        [InlineData("cf_j_hips", BoneRole.Hips)]
        [InlineData("cf_n_height", BoneRole.BodyRoot)]
        [InlineData("cf_j_forearm01_R", BoneRole.RightLowerArm)]
        [InlineData("cf_j_thumb01_L", BoneRole.LeftThumbProximal)]
        [InlineData("cf_j_little03_R", BoneRole.RightLittleDistal)]
        [InlineData("cf_J_hitomi_tx_L", BoneRole.LeftEye)]
        [InlineData("cf_pv_knee_R", BoneRole.RightKneePole)]
        [InlineData("cf_j_bust01_L", BoneRole.LeftBreast)]
        public void Body_bone_names_map_to_roles(string name, BoneRole role)
        {
            Assert.Equal(role, KKBP.Exporter.Core.AdapterKit.BoneRules.Role(name));
        }

        [Fact]
        public void Other_bones_have_no_role()
        {
            Assert.Null(KKBP.Exporter.Core.AdapterKit.BoneRules.Role("cf_s_spine01"));
        }
    }
}

namespace KKBP.Exporter.Core.Tests
{
    public class LightBakeTests
    {
        private static Vec2 V(float x, float y) => new Vec2(x, y);

        [Fact]
        public void Overlapping_islands_go_to_separate_layers()
        {
            // Two triangles over the same UV area, not sharing vertices, and a third elsewhere.
            var uvs = new[] { V(0, 0), V(0.5f, 0), V(0, 0.5f), V(0.1f, 0.1f), V(0.6f, 0.1f), V(0.1f, 0.6f), V(0.8f, 0.8f), V(0.9f, 0.8f), V(0.8f, 0.9f) };
            var depths = KKBP.Exporter.Core.AdapterKit.LightBake.IslandDepths(new[] { 0, 1, 2, 3, 4, 5, 6, 7, 8 }, uvs);
            Assert.Equal(new[] { 0f, 0f, 0f, -0.0001f, -0.0001f, -0.0001f, 0f, 0f, 0f }, depths);
        }

        [Fact]
        public void Fold_keeps_the_most_opaque_pixel_of_each_tile()
        {
            // Two 1x1 tiles side by side: the second is opaque.
            var pixels = new byte[] { 10, 10, 10, 100, 20, 20, 20, 255 };
            Assert.Equal(new byte[] { 20, 20, 20, 255 }, KKBP.Exporter.Core.AdapterKit.LightBake.Fold(pixels, 1, 2, 1));
        }

        private static double Lin(byte b) { double c = b / 255.0; return c <= 0.04045 ? c / 12.92 : System.Math.Pow((c + 0.055) / 1.055, 2.4); }
        private static byte Srgb(double l) { double c = l <= 0.0031308 ? l * 12.92 : 1.055 * System.Math.Pow(l, 1 / 2.4) - 0.055; return (byte)System.Math.Round(c * 255); }

        [Fact]
        public void Pupil_coverage_and_colour_give_back_the_whole_eye()
        {
            // In linear light: the lit white, the eye white's own colour, the iris, and the iris's coverage of
            // three pixels: none, half, all.
            double[] lit = { 0.9, 0.92, 0.98 };
            double[] eyeWhite = { 0.8, 0.85, 0.95 };
            double[] iris = { 0.3, 0.05, 0.2 };
            double[] coverage = { 0, 0.5, 1 };
            byte[] full = new byte[12], white = new byte[12], onBlack = new byte[12], onWhite = new byte[12];
            for (int p = 0; p < 3; p++)
            {
                double a = coverage[p];
                for (int c = 0; c < 3; c++)
                {
                    full[p * 4 + c] = Srgb(a * iris[c] + (1 - a) * eyeWhite[c]);
                    white[p * 4 + c] = Srgb(eyeWhite[c]);
                    onBlack[p * 4 + c] = Srgb(a * iris[c]);
                    onWhite[p * 4 + c] = Srgb(a * iris[c] + (1 - a) * lit[c]);
                }
                full[p * 4 + 3] = white[p * 4 + 3] = onBlack[p * 4 + 3] = onWhite[p * 4 + 3] = 255;
            }

            var pupil = KKBP.Exporter.Core.AdapterKit.LightBake.Pupil(full, white, onBlack, onWhite);

            Assert.Equal(0, pupil[3]);
            Assert.InRange(pupil[7], 126, 129);
            Assert.Equal(255, pupil[11]);
            Assert.Equal(white[0], pupil[0]); // uncovered: the eye white's colour, so filtering adds no fringe
            for (int p = 1; p < 3; p++)
            {
                double a = pupil[p * 4 + 3] / 255.0;
                for (int c = 0; c < 3; c++)
                {
                    byte back = Srgb(a * Lin(pupil[p * 4 + c]) + (1 - a) * Lin(white[p * 4 + c]));
                    Assert.InRange(back, full[p * 4 + c] - 1, full[p * 4 + c] + 1);
                }
            }
        }

        [Fact]
        public void Pupil_needs_some_uncovered_eye_white()
        {
            var covered = new byte[] { 10, 10, 10, 255 };
            Assert.Throws<System.ArgumentException>(() => KKBP.Exporter.Core.AdapterKit.LightBake.Pupil(covered, covered, covered, new byte[] { 200, 200, 200, 255 }));
        }

        [Fact]
        public void Overlay_takes_only_fully_opaque_pixels()
        {
            var quad = new byte[] { 1, 1, 1, 255, 2, 2, 2, 255 };
            KKBP.Exporter.Core.AdapterKit.LightBake.Overlay(quad, new byte[] { 9, 9, 9, 255, 8, 8, 8, 254 });
            Assert.Equal(new byte[] { 9, 9, 9, 255, 2, 2, 2, 255 }, quad);
        }

        [Fact]
        public void Pad_grows_islands_into_empty_pixels()
        {
            // 3x1: one opaque pixel in the middle.
            var pixels = new byte[] { 0, 0, 0, 0, 50, 60, 70, 255, 0, 0, 0, 0 };
            var padded = KKBP.Exporter.Core.AdapterKit.LightBake.Pad(pixels, 3, 1, 1);
            Assert.Equal(new byte[] { 50, 60, 70, 255, 50, 60, 70, 255, 50, 60, 70, 255 }, padded);
        }
    }

    public class CardBatchTests : System.IDisposable
    {
        private readonly string folder = System.IO.Path.Combine(System.IO.Path.GetTempPath(), "kkbp-cards-" + System.Guid.NewGuid().ToString("N"));

        public CardBatchTests()
        {
            System.IO.Directory.CreateDirectory(System.IO.Path.Combine(folder, "sub"));
            foreach (string name in new[] { "b.png", "A.PNG", "notes.txt", "c.pngx" })
            {
                System.IO.File.WriteAllText(System.IO.Path.Combine(folder, name), "");
            }
            System.IO.File.WriteAllText(System.IO.Path.Combine(folder, "sub", "d.png"), "");
        }

        public void Dispose()
        {
            System.IO.Directory.Delete(folder, true);
        }

        [Fact]
        public void Cards_are_the_pngs_directly_in_the_folder_by_name()
        {
            var names = CardBatch.Cards(folder).Select(System.IO.Path.GetFileName).ToList();
            Assert.Equal(new[] { "A.PNG", "b.png" }, names);
        }

        [Fact]
        public void A_batch_goes_through_every_card_and_counts_the_results()
        {
            var batch = new CardBatch(folder);
            Assert.True(batch.Next());
            Assert.Equal("Card 1 of 2: A.PNG", batch.Progress);
            batch.Succeeded("/out/a");
            Assert.True(batch.Next());
            batch.Failed("the game rejected it");
            Assert.False(batch.Next());
            Assert.Null(batch.Card);
            Assert.Equal("1 exported, 1 failed", batch.Summary);
            Assert.EndsWith("b.png", batch.Failures[0].Key);
        }

        [Fact]
        public void The_report_lists_bundles_and_failures()
        {
            var batch = new CardBatch(folder);
            batch.Next();
            batch.Succeeded("/out/a");
            batch.Next();
            batch.Failed("rejected");
            batch.Next();
            var result = new JsonObject();
            Assert.Equal("1 exported, 1 failed", batch.Report(result));
            string json = JsonWriter.Write(result, false);
            Assert.Contains("\"bundles\":[\"/out/a\"]", json.Replace(" ", ""));
            Assert.Contains("\"error\":\"rejected\"", json.Replace(" ", ""));
        }

        [Fact]
        public void Stopping_ends_the_batch_after_the_current_card()
        {
            var batch = new CardBatch(folder);
            batch.Next();
            batch.Stop();
            batch.Succeeded("/out/a");
            Assert.False(batch.Next());
            Assert.True(batch.Stopped);
            Assert.Equal("1 exported, 0 failed, stopped with 1 left", batch.Summary);
        }

        [Fact]
        public void Stopping_at_the_last_card_is_just_the_end()
        {
            var batch = new CardBatch(folder);
            batch.Next();
            batch.Next();
            batch.Stop();
            Assert.False(batch.Next());
            Assert.False(batch.Stopped);
        }

        [Fact]
        public void The_browser_lists_subfolders_and_counts_cards()
        {
            var browser = new FolderBrowser(System.IO.Path.Combine(folder, "missing", "deeper"));
            Assert.Equal(System.IO.Path.GetFullPath(folder), browser.Current);
            Assert.Equal(new[] { "sub" }, browser.Subfolders);
            Assert.Equal(2, browser.CardCount);
            browser.Enter("sub");
            Assert.Equal(1, browser.CardCount);
            browser.Up();
            Assert.Equal(System.IO.Path.GetFullPath(folder), browser.Current);
        }
    }

    public class CardFileTests
    {
        /// <summary>A PNG with one empty chunk and IEND, then card data that starts with <paramref name="mark"/>.</summary>
        private static byte[] Card(string mark)
        {
            var bytes = new List<byte> { 0x89, (byte)'P', (byte)'N', (byte)'G', 13, 10, 26, 10 };
            foreach (string type in new[] { "tEXt", "IEND" })
            {
                bytes.AddRange(new byte[] { 0, 0, 0, 0 });
                bytes.AddRange(System.Text.Encoding.ASCII.GetBytes(type));
                bytes.AddRange(new byte[] { 1, 2, 3, 4 });  // the CRC, which nothing checks
            }
            if (mark != null)
            {
                byte[] text = System.Text.Encoding.UTF8.GetBytes(mark);
                bytes.AddRange(new byte[] { 100, 0, 0, 0, (byte)text.Length });
                bytes.AddRange(text);
                bytes.AddRange(new byte[] { 5, 0x30, 0x2E, 0x30, 0x2E, 0x30 });
            }
            return bytes.ToArray();
        }

        [Theory]
        [InlineData("【KoiKatuChara】")]
        [InlineData("【SVChara】")]
        [InlineData("【SVClothes】")]
        public void A_card_carries_its_games_mark_after_the_picture(string mark)
        {
            byte[] card = Card(mark);
            Assert.Equal(mark, CardFile.Mark(card));
            Assert.Equal(Card(null), CardFile.PngPart(card));
        }

        [Fact]
        public void A_plain_picture_has_no_mark_and_text_has_no_picture()
        {
            Assert.Null(CardFile.Mark(Card(null)));
            var text = System.Text.Encoding.ASCII.GetBytes("just some text, not a picture at all");
            Assert.Null(CardFile.PngPart(text));
            Assert.Null(CardFile.Mark(text));
        }
    }
}
