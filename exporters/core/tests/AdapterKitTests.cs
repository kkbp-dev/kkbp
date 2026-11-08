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
