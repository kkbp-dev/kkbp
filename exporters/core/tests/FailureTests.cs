using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using KKBP.Exporter.Core.Tests.Fake;
using KKBP.Exporter.Core.Tests.Support;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    public class FailureTests
    {
        [Fact]
        public void A_failing_pass_stops_the_export_without_a_manifest()
        {
            using var temp = new TempDir();
            var export = new BundleExport(new FakeAdapter { FailInOutfit = 1 }, temp.Path);
            export.RunToEnd();

            Assert.Equal(ExportState.Failed, export.State);
            Assert.Equal(1, export.FailedPass.Outfit);
            Assert.IsType<InvalidOperationException>(export.Error);
            Assert.True(File.Exists(Path.Combine(export.BundlePath, "body.glb")));
            Assert.True(File.Exists(Path.Combine(export.BundlePath, "outfits", "00", "outfit.glb")));
            Assert.False(File.Exists(Path.Combine(export.BundlePath, "manifest.json")));
        }

        [Fact]
        public void An_export_runs_only_once()
        {
            using var temp = new TempDir();
            var export = new BundleExport(new FakeAdapter(), temp.Path);
            export.RunToEnd();
            Assert.Throws<InvalidOperationException>(() => export.Run().MoveNext());
        }

        [Fact]
        public void A_second_export_of_the_same_moment_gets_its_own_folder()
        {
            using var temp = new TempDir();
            var time = new DateTime(2026, 1, 2, 3, 4, 5, DateTimeKind.Utc);
            var a = new BundleExport(new FakeAdapter(), new DiskBundleFiles(temp.Path), () => time);
            var b = new BundleExport(new FakeAdapter(), new DiskBundleFiles(temp.Path), () => time);
            a.RunToEnd();
            b.RunToEnd();
            Assert.Equal(Path.GetFileName(a.BundlePath) + "_2", Path.GetFileName(b.BundlePath));
        }

        [Fact]
        public void Folder_names_are_the_same_on_every_platform()
        {
            var time = new DateTime(2026, 7, 5, 16, 15, 55, DateTimeKind.Utc);
            Assert.Equal("20260705161555_a_b_c_d_e_f_g_h_i", BundleExport.FolderName(time, "a<b>c:d\"e/f\\g|h?i"));
            Assert.Equal("20260705161555_春野千佳", BundleExport.FolderName(time, "春野千佳"));
            Assert.Equal("20260705161555_Character", BundleExport.FolderName(time, " ... "));
        }

        public static IEnumerable<object[]> BadPasses()
        {
            yield return new object[] { "a bone whose rest pose changes between Passes", (Action<PassSink>)(s => s.Bones[0].Position = new Vec3(1, 0, 0)), 1 };
            yield return new object[] { "a bone with no game scale on one axis", (Action<PassSink>)(s => s.Bones[1].GameScale = new Vec3(1, 0, 1)), 0 };
            yield return new object[] { "a mesh using a material nobody captured", (Action<PassSink>)(s => s.Meshes[0].SubMeshes[0].MaterialKey = "mat:missing"), 0 };
            yield return new object[] { "two bones with the same unique role", (Action<PassSink>)(s => s.Bones[2].Role = BoneRole.Hips), 0 };
            yield return new object[] { "two textures in one slot", (Action<PassSink>)(s => s.Materials[0].Textures.Add(new TextureData { Raw = "_NormalMap", Png = FakeAdapter.Png })), 0 };
            yield return new object[] { "an expression in the wrong category", (Action<PassSink>)(s => s.Meshes[1].Morphs[0].Category = ExpressionCategory.Mouth), 0 };
            yield return new object[] { "a texture that isn't a PNG", (Action<PassSink>)(s => s.Materials[0].Textures[0].Png = new byte[] { 1, 2, 3, 4, 5, 6, 7, 8 }), 0 };
            yield return new object[] { "a vertex with no weight", (Action<PassSink>)(s => Array.Clear(s.Meshes[0].Weights, 0, s.Meshes[0].InfluencesPerVertex)), 0 };
            yield return new object[] { "a second root bone", (Action<PassSink>)(s => s.Bones[2].ParentKey = null), 0 };
            yield return new object[] { "showing a mesh that has no showing key", (Action<PassSink>)(s => s.Meshes[1].Morphs[3].ShowsMeshKeys[0] = s.Meshes[0].Key), 0 };
            yield return new object[] { "showing a mesh from another Pass", (Action<PassSink>)(s => s.Meshes[1].Morphs[3].ShowsMeshKeys[0] = "/outfit0/o_bot_skirt"), 0 };
            yield return new object[] { "switching to a pattern the material lacks", (Action<PassSink>)(s => s.Meshes[1].Morphs[3].MaterialChanges[0].Textures["_MainTex"] = "cf_t_gageye_99"), 0 };
            yield return new object[] { "an expression's effects given on two shape keys", (Action<PassSink>)(s =>
            {
                var gag = s.Meshes[1].Morphs[3];
                s.Meshes[0].Morphs.Add(new MorphData
                {
                    Category = gag.Category,
                    ExpressionName = gag.ExpressionName,
                    GameName = gag.GameName,
                    PositionDeltas = new Vec3[s.Meshes[0].Positions.Length],
                    HidesMeshKeys = { gag.HidesMeshKeys[0] },
                });
            }), 0 };
            yield return new object[] { "a material change that sets nothing", (Action<PassSink>)(s => s.Meshes[1].Morphs[4].MaterialChanges[0] = new MaterialChange { MaterialKey = "mat:eye_l" }), 0 };
            yield return new object[] { "a body texture in the Body Pass", (Action<PassSink>)(s => s.BodyTextures.Add(new BodyTexture { MaterialKey = "mat:body", Texture = new TextureData { Raw = "_AlphaMask", Png = FakeAdapter.Png } })), 0 };
            yield return new object[] { "a body texture on an Outfit material", (Action<PassSink>)(s => s.BodyTextures[0].MaterialKey = "mat:skirt"), 1 };
            yield return new object[] { "a body texture in a slot the material fills", (Action<PassSink>)(s => s.BodyTextures[0].Texture.Raw = "_NormalMap"), 1 };
            yield return new object[] { "two textures in one slot of a material section", (Action<PassSink>)(s => s.Materials[0].Sections[0].Textures.Add(new TextureData { Raw = "_Texture3", Png = FakeAdapter.Png })), 0 };
            yield return new object[] { "two textures with one Role in a material section", (Action<PassSink>)(s => s.Materials[0].Sections[0].Textures[2].Role = TextureRole.ColorMask), 0 };
            yield return new object[] { "a material section texture that isn't a PNG", (Action<PassSink>)(s => s.Materials[0].Sections[0].Textures[0].Png = new byte[] { 1, 2, 3, 4, 5, 6, 7, 8 }), 0 };
            yield return new object[] { "two material sections with one field", (Action<PassSink>)(s => s.Materials[0].Sections.Add(FakeAdapter.Create("Custom/CreateTexture/Other"))), 0 };
            yield return new object[] { "a material section over a plain extension field", (Action<PassSink>)(s => s.Materials[0].Extensions = new JsonObject().Add("kk", new JsonObject().Add("create", 1))), 0 };
            yield return new object[] { "a material section with no field name", (Action<PassSink>)(s => s.Materials[0].Sections[0].Field = null), 0 };
            yield return new object[] { "a material section no mesh of its Pass uses", (Action<PassSink>)(s => s.Materials.Add(new MaterialData { Key = "mat:unused", Name = "cf_m_unused", Shader = "s", Sections = { FakeAdapter.Create("Custom/CreateTexture/Clothes") } })), 0 };
            yield return new object[] { "a mesh using another Pass's material with a section", (Action<PassSink>)(s => s.Meshes[0].SubMeshes[0].MaterialKey = "mat:body"), 1 };
        }

        [Theory]
        [MemberData(nameof(BadPasses))]
        public void Bad_captures_fail_the_export(string what, Action<PassSink> spoil, int pass)
        {
            using var temp = new TempDir();
            var export = new BundleExport(new SpoilingAdapter(spoil, pass), temp.Path);
            export.RunToEnd();
            Assert.True(export.State == ExportState.Failed, what + " was accepted");
            Assert.IsType<ExportException>(export.Error);
            Assert.False(File.Exists(Path.Combine(export.BundlePath, "manifest.json")));
        }

        /// <summary>The fake adapter, with one Pass's captured data changed after capture.</summary>
        private sealed class SpoilingAdapter : IGameAdapter
        {
            private readonly FakeAdapter fake = new FakeAdapter();
            private readonly Action<PassSink> spoil;
            private readonly int pass;

            public SpoilingAdapter(Action<PassSink> spoil, int pass)
            {
                this.spoil = spoil;
                this.pass = pass;
            }

            public string Game => fake.Game;
            public string ExporterName => fake.ExporterName;
            public string ExporterVersion => fake.ExporterVersion;
            public ExportOptions Options => fake.Options;
            public CharacterInfo Character => fake.Character;

            public IList<PassInfo> Passes() => fake.Passes();

            public IEnumerator Capture(PassInfo info, PassSink sink)
            {
                yield return fake.Capture(info, sink);
                if ((info.Outfit ?? -1) + 1 == pass)
                {
                    spoil(sink);
                }
            }
        }
    }
}
