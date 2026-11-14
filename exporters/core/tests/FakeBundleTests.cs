using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using KKBP.Exporter.Core.Tests.Fake;
using KKBP.Exporter.Core.Tests.Support;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    /// <summary>Exports the fake Character once and checks the bundle against the contract.</summary>
    public sealed class FakeBundleFixture : IDisposable
    {
        public static readonly DateTime ExportTime = new DateTime(2026, 11, 1, 6, 26, 5, DateTimeKind.Utc);

        public FakeBundleFixture()
        {
            Temp = new TempDir();
            Files = new RecordingFiles(Temp.Path);
            Export = new BundleExport(new FakeAdapter(), Files, () => ExportTime);
            var run = Export.Run();
            while (run.MoveNext())
            {
                Yielded.Add(run.Current);
            }
        }

        public TempDir Temp { get; }
        public RecordingFiles Files { get; }
        public BundleExport Export { get; }
        public List<object> Yielded { get; } = new List<object>();

        public string Bundle => Export.BundlePath;

        public string FilePath(string relative) => Path.Combine(Bundle, relative.Replace('/', Path.DirectorySeparatorChar));

        public JsonDocument Json(string relative) => JsonDocument.Parse(File.ReadAllText(FilePath(relative)));

        public void Dispose() => Temp.Dispose();
    }

    public sealed class FakeBundleTests : IClassFixture<FakeBundleFixture>
    {
        private readonly FakeBundleFixture f;

        public FakeBundleTests(FakeBundleFixture fixture)
        {
            f = fixture;
        }

        [Fact]
        public void Export_succeeds()
        {
            Assert.Null(f.Export.Error);
            Assert.Equal(ExportState.Succeeded, f.Export.State);
        }

        [Fact]
        public void Bundle_passes_the_contract()
        {
            var problems = ContractChecker.Check(f.Bundle);
            Assert.True(problems.Count == 0, string.Join("\n", problems));
        }

        [Fact]
        public void Every_glb_passes_the_Khronos_validator()
        {
            var glbs = Directory.GetFiles(f.Bundle, "*.glb", SearchOption.AllDirectories).OrderBy(p => p, StringComparer.Ordinal).ToList();
            Assert.Equal(3, glbs.Count);
            var result = GltfValidator.Run(glbs);
            Assert.True(result.ExitCode == 0, result.Report);
        }

        [Fact]
        public void Bundle_has_the_agreed_layout()
        {
            Assert.Equal("20261101062605_春野 テスト_Chika", Path.GetFileName(f.Bundle));
            foreach (var file in new[]
            {
                "manifest.json", "character.json", "skeleton.json", "materials.json", "expressions.json", "physics.json",
                "body.glb", "body.json", "outfits/00/outfit.glb", "outfits/00/outfit.json", "outfits/01/outfit.glb", "outfits/01/outfit.json",
                "card.png", "textures/0001.png",
            })
            {
                Assert.True(File.Exists(f.FilePath(file)), file + " is missing");
            }
            Assert.False(Directory.Exists(f.FilePath("kkbp_cache")));
        }

        [Fact]
        public void Manifest_is_written_last()
        {
            Assert.Equal("manifest.json", f.Files.Written.Last());
            Assert.Single(f.Files.Written, "manifest.json");
        }

        [Fact]
        public void Manifest_records_game_options_and_passes()
        {
            using var manifest = f.Json("manifest.json");
            var root = manifest.RootElement;
            Assert.Equal("KK", root.GetProperty("game").GetString());
            Assert.Equal("1.2", root.GetProperty("schema_version").GetString());
            Assert.Equal("2026-11-01T06:26:05Z", root.GetProperty("exported_at").GetString());
            Assert.Equal("card.png", root.GetProperty("card").GetString());
            Assert.True(root.GetProperty("options").GetProperty("all_outfits").GetBoolean());
            var passes = root.GetProperty("passes").EnumerateArray().Select(p => p.GetProperty("mesh").GetString()).ToArray();
            Assert.Equal(new[] { "body.glb", "outfits/00/outfit.glb", "outfits/01/outfit.glb" }, passes);
        }

        [Fact]
        public void Yields_are_passed_on_in_order_with_nested_waits_flattened()
        {
            Assert.Equal(FakeAdapter.ExpectedYields(), f.Yielded);
        }

        [Fact]
        public void Ids_follow_the_naming_rules()
        {
            using var skeleton = f.Json("skeleton.json");
            var bones = skeleton.RootElement.GetProperty("bones").EnumerateArray().Select(b => b.GetProperty("id").GetString()).ToList();
            Assert.Contains("cf_j_hips", bones);
            Assert.Contains("cf_s_dup", bones);
            Assert.Contains("cf_s_dup_2", bones);
            Assert.Contains("bone", bones);
            Assert.Contains("bone_2", bones);
            Assert.Contains("bone_3", bones);

            using var materials = f.Json("materials.json");
            var mats = materials.RootElement.GetProperty("materials").EnumerateArray().Select(m => m.GetProperty("id").GetString()).ToList();
            Assert.Equal(new[] { "cf_m_body", "cf_m_tooth", "cf_m_face_00", "cf_m_gageye_00", "cf_m_hitomi_00", "cf_m_bot_skirt01", "cf_m_acs_ribbon", "mat", "mat_2" }, mats);

            using var outfit0 = f.Json("outfits/00/outfit.json");
            using var outfit1 = f.Json("outfits/01/outfit.json");
            var meshes = outfit0.RootElement.GetProperty("meshes").EnumerateArray()
                .Concat(outfit1.RootElement.GetProperty("meshes").EnumerateArray())
                .Select(m => m.GetProperty("id").GetString()).ToList();
            Assert.Equal(new[] { "o_bot_skirt", "o_bot_skirt_2", "acs_ribbon", "mesh", "mesh_2", "acs_ribbon_2", "pin" }, meshes);
        }

        [Fact]
        public void Only_a_bone_the_game_scales_has_a_game_scale()
        {
            using var skeleton = f.Json("skeleton.json");
            var bones = skeleton.RootElement.GetProperty("bones").EnumerateArray().ToDictionary(b => b.GetProperty("id").GetString());
            var scale = bones["cf_j_thigh00_L"].GetProperty("game_scale").EnumerateArray().Select(c => c.GetSingle()).ToArray();
            Assert.Equal(new[] { 0.9f, 1.1f, 0.9f }, scale);
            Assert.False(bones["cf_j_head"].TryGetProperty("game_scale", out _));
        }

        [Fact]
        public void A_helper_is_never_above_a_weighted_bone()
        {
            // The adapter makes BodyTop and both cf_s_dup helpers, but every weighted bone is below BodyTop and
            // the face mesh weights both cf_s_dup.
            using var skeleton = f.Json("skeleton.json");
            var groups = skeleton.RootElement.GetProperty("bones").EnumerateArray()
                .ToDictionary(b => b.GetProperty("id").GetString(), b => b.GetProperty("group").GetString());
            Assert.Equal("deform", groups["BodyTop"]);
            Assert.Equal("deform", groups["cf_s_dup"]);
            Assert.Equal("deform", groups["cf_s_dup_2"]);
        }

        [Fact]
        public void Parents_are_listed_before_children_in_the_skeleton()
        {
            using var skeleton = f.Json("skeleton.json");
            var seen = new HashSet<string>();
            foreach (var bone in skeleton.RootElement.GetProperty("bones").EnumerateArray())
            {
                var parent = bone.GetProperty("parent");
                if (parent.ValueKind == JsonValueKind.String)
                {
                    Assert.Contains(parent.GetString(), seen);
                }
                seen.Add(bone.GetProperty("id").GetString());
            }
        }

        [Fact]
        public void Alternate_meshes_are_flagged()
        {
            using var outfit0 = f.Json("outfits/00/outfit.json");
            var alternate = outfit0.RootElement.GetProperty("meshes").EnumerateArray()
                .Where(m => m.GetProperty("alternate").GetBoolean()).Select(m => m.GetProperty("id").GetString());
            Assert.Equal(new[] { "o_bot_skirt_2" }, alternate);
        }

        [Fact]
        public void Textures_keep_roles_variants_and_patterns()
        {
            using var materials = f.Json("materials.json");
            var all = materials.RootElement.GetProperty("materials").EnumerateArray().ToList();
            var body = all.Single(m => m.GetProperty("id").GetString() == "cf_m_body");
            var textures = body.GetProperty("textures").EnumerateArray().ToList();
            Assert.Equal(new[] { "light", "dark" }, textures.Where(t => t.GetProperty("raw").GetString() == "_MainTex").Select(t => t.GetProperty("variant").GetString()));
            Assert.Equal(2, textures.Count(t => t.TryGetProperty("role", out var r) && r.GetString() == "overlay"));
            Assert.False(textures.Single(t => t.GetProperty("raw").GetString() == "_liquidmask").TryGetProperty("role", out _));

            var gag = all.Single(m => m.GetProperty("id").GetString() == "cf_m_gageye_00");
            Assert.Equal(new[] { "cf_t_gageye_00", "cf_t_gageye_01" }, gag.GetProperty("textures").EnumerateArray().Select(t => t.GetProperty("pattern").GetString()));

            // Numbered in write order, which puts each Outfit's body textures among its materials' textures and their creates.
            using var outfit0 = f.Json("outfits/00/outfit.json");
            using var outfit1 = f.Json("outfits/01/outfit.json");
            var files = all.SelectMany(m => m.GetProperty("textures").EnumerateArray().Concat(CreateTextures(m)))
                .Concat(new[] { outfit0, outfit1 }.SelectMany(o => o.RootElement.GetProperty("body_textures").EnumerateArray()).Select(b => b.GetProperty("texture")))
                .Select(t => t.GetProperty("file").GetString()).OrderBy(x => x, StringComparer.Ordinal).ToList();
            Assert.Equal(Enumerable.Range(1, files.Count).Select(i => "textures/" + i.ToString("0000") + ".png"), files);
        }

        private static IEnumerable<JsonElement> CreateTextures(JsonElement material)
        {
            return material.TryGetProperty("extensions", out var e) && e.TryGetProperty("kk", out var kk) && kk.TryGetProperty("create", out var create)
                ? create.GetProperty("textures").EnumerateArray()
                : Enumerable.Empty<JsonElement>();
        }

        [Fact]
        public void Material_sections_are_written_under_their_extension_and_field()
        {
            using var materials = f.Json("materials.json");
            var all = materials.RootElement.GetProperty("materials").EnumerateArray().ToList();
            var withExtensions = all.Where(m => m.TryGetProperty("extensions", out _)).Select(m => m.GetProperty("id").GetString());
            Assert.Equal(new[] { "cf_m_body", "cf_m_bot_skirt01" }, withExtensions);

            var create = all[0].GetProperty("extensions").GetProperty("kk").GetProperty("create");
            Assert.Equal(new[] { "shader", "colors", "floats", "vectors", "textures" }, create.EnumerateObject().Select(p => p.Name));
            Assert.Equal("Custom/CreateTexture/BodySkin", create.GetProperty("shader").GetString());
            Assert.Equal(new[] { "_Color", "_Color2" }, create.GetProperty("colors").EnumerateObject().Select(p => p.Name));
            Assert.Equal(0.5, create.GetProperty("floats").GetProperty("_PatternScale").GetDouble());
            var textures = create.GetProperty("textures").EnumerateArray().ToList();
            Assert.Equal(new[] { "_MainTex", "_ColorMask", "_Texture3" }, textures.Select(t => t.GetProperty("raw").GetString()));
            Assert.Equal("main", textures[0].GetProperty("role").GetString());
            Assert.False(textures[2].TryGetProperty("role", out _));
        }

        [Fact]
        public void Material_section_textures_follow_the_materials_own()
        {
            using var materials = f.Json("materials.json");
            foreach (var material in materials.RootElement.GetProperty("materials").EnumerateArray().Where(m => CreateTextures(m).Any()))
            {
                var own = material.GetProperty("textures").EnumerateArray().Select(Number).ToList();
                var create = CreateTextures(material).Select(Number).ToList();
                var both = own.Concat(create).ToList();
                Assert.Equal(Enumerable.Range(both[0], both.Count), both);
            }
        }

        private static int Number(JsonElement texture)
        {
            string file = texture.GetProperty("file").GetString();
            return int.Parse(file.Substring("textures/".Length, file.Length - "textures/".Length - ".png".Length));
        }

        [Fact]
        public void Shader_values_are_sorted_by_raw_property()
        {
            using var materials = f.Json("materials.json");
            var body = materials.RootElement.GetProperty("materials")[0];
            Assert.Equal(new[] { "_Color", "_ShadowColor" }, body.GetProperty("colors").EnumerateObject().Select(p => p.Name));
        }

        [Fact]
        public void Expressions_are_named_from_the_table()
        {
            using var expressions = f.Json("expressions.json");
            var face = expressions.RootElement.GetProperty("expressions").EnumerateArray()
                .Where(e => e.GetProperty("mesh").GetString() == "cf_O_face")
                .Select(e => e.GetProperty("target").GetString()).ToList();
            Assert.Equal(new[] { "Eye Default", "Mouth Default", "Mouth Default, Closed", "Gag Heart Eyes", "Eye Star Pupils", "Mouth Chewing", "Tears small", "kuti_face.f00_untranslated" }, face);
        }

        [Fact]
        public void Expressions_record_what_they_show_hide_and_change()
        {
            using var expressions = f.Json("expressions.json");
            var all = expressions.RootElement.GetProperty("expressions").EnumerateArray().ToList();
            Assert.All(all, e => Assert.False(e.TryGetProperty("shows", out _) || e.TryGetProperty("hides", out _) || e.TryGetProperty("material_changes", out _)));
            var effects = expressions.RootElement.GetProperty("effects").EnumerateArray().ToList();
            Assert.Equal(new[] { "Gag Heart Eyes", "Eye Star Pupils" }, effects.Select(e => e.GetProperty("target").GetString()));
            var gag = effects[0];
            Assert.Equal(new[] { "cf_O_gag_eye_00" }, gag.GetProperty("shows").EnumerateArray().Select(x => x.GetString()));
            Assert.Equal(new[] { "cf_Ohitomi_L" }, gag.GetProperty("hides").EnumerateArray().Select(x => x.GetString()));
            var change = gag.GetProperty("material_changes").EnumerateArray().Single();
            Assert.Equal("cf_m_gageye_00", change.GetProperty("material").GetString());
            Assert.Equal("cf_t_gageye_01", change.GetProperty("textures")[0].GetProperty("pattern").GetString());
            Assert.Equal(new[] { "_SizeSpeed", "_angleSpeed" }, change.GetProperty("floats").EnumerateObject().Select(p => p.Name));
            Assert.Equal(4, change.GetProperty("vectors").GetProperty("_TileAnimation").GetArrayLength());

            var stars = effects[1];
            Assert.False(stars.TryGetProperty("shows", out _));
            Assert.Equal("_expression", stars.GetProperty("material_changes")[0].GetProperty("textures")[0].GetProperty("raw").GetString());

            var showing = all.Single(e => e.GetProperty("target").GetString() == "Gag eye 00");
            Assert.Equal(JsonValueKind.Null, showing.GetProperty("game_name").ValueKind);
        }

        [Fact]
        public void Outfit_passes_carry_their_body_textures()
        {
            using var body = f.Json("body.json");
            Assert.False(body.RootElement.TryGetProperty("body_textures", out _));
            foreach (var outfit in new[] { "outfits/00/outfit.json", "outfits/01/outfit.json" })
            {
                using var data = f.Json(outfit);
                var texture = data.RootElement.GetProperty("body_textures").EnumerateArray().Single();
                Assert.Equal("cf_m_body", texture.GetProperty("material").GetString());
                Assert.Equal("alpha_mask", texture.GetProperty("texture").GetProperty("role").GetString());
                Assert.True(File.Exists(f.FilePath(texture.GetProperty("texture").GetProperty("file").GetString())));
            }
            using var materials = f.Json("materials.json");
            var bodyMaterial = materials.RootElement.GetProperty("materials").EnumerateArray().Single(m => m.GetProperty("id").GetString() == "cf_m_body");
            Assert.DoesNotContain(bodyMaterial.GetProperty("textures").EnumerateArray(), t => t.GetProperty("raw").GetString() == "_AlphaMask");
        }

        [Fact]
        public void Physics_chain_can_use_a_collider_from_another_pass()
        {
            using var physics = f.Json("physics.json");
            var chain = physics.RootElement.GetProperty("chains")[0];
            Assert.Equal(0, chain.GetProperty("outfit").GetInt32());
            Assert.Equal(new[] { "cf_hit_spine01", "cf_hit_thigh_L" }, chain.GetProperty("colliders").EnumerateArray().Select(c => c.GetString()));
            var collider = physics.RootElement.GetProperty("colliders")[0];
            Assert.Equal(JsonValueKind.Null, collider.GetProperty("outfit").ValueKind);
            Assert.Equal(-0.01, collider.GetProperty("center")[0].GetDouble(), 6);
        }

        [Fact]
        public void Glb_holds_one_skin_and_meshes_at_the_scene_root()
        {
            using var doc = Glb.ReadJson(f.FilePath("body.glb"));
            var root = doc.RootElement;
            Assert.Equal(1, root.GetProperty("skins").GetArrayLength());
            var nodes = root.GetProperty("nodes").EnumerateArray().ToList();
            var sceneNodes = root.GetProperty("scenes")[0].GetProperty("nodes").EnumerateArray().Select(n => n.GetInt32()).ToList();
            var meshNodes = Enumerable.Range(0, nodes.Count).Where(i => nodes[i].TryGetProperty("mesh", out _)).ToList();
            Assert.Equal(4, meshNodes.Count);
            Assert.All(meshNodes, i => Assert.Contains(i, sceneNodes));
            Assert.All(meshNodes, i => Assert.False(nodes[i].TryGetProperty("translation", out _)));
            Assert.Equal(nodes.Count - meshNodes.Count, root.GetProperty("skins")[0].GetProperty("joints").GetArrayLength());

            // The face mesh has six weights per vertex, so it needs a second joint set.
            var face = root.GetProperty("meshes").EnumerateArray().Single(m => m.GetProperty("name").GetString() == "cf_O_face");
            var attributes = face.GetProperty("primitives")[0].GetProperty("attributes");
            Assert.True(attributes.TryGetProperty("JOINTS_1", out _));
            Assert.True(attributes.TryGetProperty("TEXCOORD_1", out _));
            Assert.Equal(8, face.GetProperty("extras").GetProperty("targetNames").GetArrayLength());
        }

        [Fact]
        public void Exporting_again_gives_identical_files()
        {
            using var temp = new TempDir();
            var again = new BundleExport(new FakeAdapter(), new DiskBundleFiles(temp.Path), () => FakeBundleFixture.ExportTime);
            again.RunToEnd();
            Assert.Equal(ExportState.Succeeded, again.State);

            var first = Directory.GetFiles(f.Bundle, "*", SearchOption.AllDirectories).Select(p => Path.GetRelativePath(f.Bundle, p)).OrderBy(p => p, StringComparer.Ordinal).ToList();
            var second = Directory.GetFiles(again.BundlePath, "*", SearchOption.AllDirectories).Select(p => Path.GetRelativePath(again.BundlePath, p)).OrderBy(p => p, StringComparer.Ordinal).ToList();
            Assert.Equal(first, second);
            foreach (var file in first)
            {
                Assert.True(File.ReadAllBytes(Path.Combine(f.Bundle, file)).SequenceEqual(File.ReadAllBytes(Path.Combine(again.BundlePath, file))), file + " differs");
            }
        }
    }
}
