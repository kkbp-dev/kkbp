using System;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using KKBP.Exporter.Core.Tests.Support;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    public class IdTests
    {
        [Theory]
        [InlineData("cf_m_body", "cf_m_body")]
        [InlineData("cf_m_hair_f_14_00_i 4060", "cf_m_hair_f_14_00_i_4060")]
        [InlineData("__a  b__", "a_b")]
        [InlineData("a/b\\c:d", "a_b_c_d")]
        [InlineData("cf_J_FaceRoot", "cf_J_FaceRoot")]
        [InlineData("o.tang-01", "o.tang-01")]
        [InlineData("髪_hair", "hair")]
        [InlineData("春野千佳", "")]
        [InlineData("_", "")]
        public void Simplify(string name, string expected)
        {
            Assert.Equal(expected, IdAllocator.Simplify(name));
        }

        [Fact]
        public void Empty_names_get_the_kind_prefix_and_a_counter()
        {
            var ids = new IdAllocator("mat");
            Assert.Equal("mat", ids.Get("a", "帽子"));
            Assert.Equal("mat_2", ids.Get("b", "_"));
            Assert.Equal("mat_3", ids.Get("c", null));
        }

        [Fact]
        public void Clashes_get_counters_in_arrival_order_and_keys_keep_their_Id()
        {
            var ids = new IdAllocator("bone");
            Assert.Equal("cf_s_dup", ids.Get("k1", "cf_s_dup"));
            Assert.Equal("cf_s_dup_2", ids.Get("k2", "cf_s_dup"));
            Assert.Equal("cf_s_dup", ids.Get("k1", "something else"));
            // A game name that clashes with a counted Id gets a counter on its own name.
            Assert.Equal("cf_s_dup_2_2", ids.Get("k3", "cf_s_dup_2"));
        }

        [Fact]
        public void Long_names_fit_63_bytes_with_their_counter()
        {
            var ids = new IdAllocator("mesh");
            string name = new string('a', 30) + "_" + new string('b', 40);
            string first = ids.Get("1", name);
            string second = ids.Get("2", name);
            Assert.Equal(63, first.Length);
            Assert.True(second.Length <= 63);
            Assert.EndsWith("_2", second);
            Assert.NotEqual(first, second);
        }

        [Fact]
        public void Truncation_never_leaves_a_doubled_underscore()
        {
            var ids = new IdAllocator("mesh");
            // Cutting at 61 characters for "_2" would end on the underscore at index 60.
            string name = new string('a', 60) + "_" + new string('b', 10);
            ids.Get("1", name);
            string second = ids.Get("2", name);
            Assert.DoesNotContain("__", second);
            Assert.Matches("^(?!.*__)[A-Za-z0-9.-](?:[A-Za-z0-9_.-]{0,61}[A-Za-z0-9.-])?$", second);
        }
    }

    public class JsonTests
    {
        [Fact]
        public void Numbers_are_written_the_same_in_every_locale()
        {
            var previous = CultureInfo.CurrentCulture;
            try
            {
                CultureInfo.CurrentCulture = new CultureInfo("de-DE");
                string json = JsonWriter.Write(new JsonArray { 0.5f, 1234.25, -3, 1e-7f, 100000000f }, false);
                Assert.Equal("[0.5,1234.25,-3,1E-07,100000000]", json);
            }
            finally
            {
                CultureInfo.CurrentCulture = previous;
            }
        }

        [Fact]
        public void Floats_round_trip()
        {
            foreach (float f in new[] { 0.1f, 1f / 3, 0.029999999329447748f, 3.4028235e38f, -0.0f })
            {
                Assert.Equal(f, float.Parse(JsonWriter.FormatFloat(f), CultureInfo.InvariantCulture));
            }
        }

        [Fact]
        public void NaN_and_infinity_are_rejected()
        {
            Assert.Throws<ExportException>(() => JsonWriter.Write(new JsonArray { float.NaN }, false));
            Assert.Throws<ExportException>(() => JsonWriter.Write(new JsonArray { double.PositiveInfinity }, false));
        }

        [Fact]
        public void Strings_are_escaped_and_keep_unicode()
        {
            string json = JsonWriter.Write(new JsonObject().Add("s", "a\"b\\c\n\t\u0001春"), false);
            Assert.Equal("{\"s\":\"a\\\"b\\\\c\\n\\t\\u0001春\"}", json);
        }

        [Fact]
        public void Indented_output_keeps_vectors_on_one_line()
        {
            string json = JsonWriter.Write(new JsonObject().Add("v", new JsonArray { 1f, 2f, 3f }).Add("e", new JsonArray()).Add("o", new JsonObject()), true);
            Assert.Equal("{\n  \"v\": [1, 2, 3],\n  \"e\": [],\n  \"o\": {}\n}\n", json);
        }

        [Fact]
        public void Duplicate_keys_are_rejected()
        {
            Assert.Throws<ArgumentException>(() => new JsonObject().Add("a", 1).Add("a", 2));
        }

        [Fact]
        public void Reader_reads_what_the_writer_writes()
        {
            var obj = new JsonObject().Add("name", "春野 \"千佳\"").Add("n", 0.25f).Add("list", new JsonArray { true, false, null, "x" });
            var back = (JsonObject)JsonReader.Parse(JsonWriter.Write(obj, true));
            Assert.Equal("春野 \"千佳\"", back["name"]);
            Assert.Equal(0.25, back["n"]);
            Assert.Equal(new object[] { true, false, null, "x" }, (JsonArray)back["list"]);
        }

        [Fact]
        public void Reader_handles_escapes_surrogates_and_a_bom()
        {
            var back = (JsonObject)JsonReader.Parse("﻿{\"a\": \"\\u6625\\ud83d\\ude00\\/\"}");
            Assert.Equal("春😀/", back["a"]);
        }

        [Theory]
        [InlineData("{\"a\": 1,}")]
        [InlineData("[1 2]")]
        [InlineData("{\"a\": tru}")]
        [InlineData("\"unterminated")]
        [InlineData("{} extra")]
        public void Reader_rejects_bad_json(string text)
        {
            Assert.Throws<FormatException>(() => JsonReader.Parse(text));
        }
    }

    public class UnitySpaceTests
    {
        [Fact]
        public void Positions_and_rotations_mirror_x()
        {
            var p = UnitySpace.Position(new Vec3(1, 2, 3));
            Assert.Equal((-1f, 2f, 3f), (p.X, p.Y, p.Z));
            var q = UnitySpace.Rotation(new Quat(0.1f, 0.2f, 0.3f, 0.9f));
            Assert.Equal((0.1f, -0.2f, -0.3f, 0.9f), (q.X, q.Y, q.Z, q.W));
            var uv = UnitySpace.Uv(new Vec2(0.25f, 0.75f));
            Assert.Equal((0.25f, 0.25f), (uv.X, uv.Y));
            Assert.Equal(new[] { 0, 2, 1, 3, 5, 4 }, UnitySpace.Triangles(new[] { 0, 1, 2, 3, 4, 5 }));
        }

        [Fact]
        public void Converting_then_rotating_equals_rotating_then_converting()
        {
            var rng = new Random(7);
            for (int i = 0; i < 100; i++)
            {
                var q = Normalize(new Quat(Next(rng), Next(rng), Next(rng), Next(rng)));
                var v = new Vec3(Next(rng), Next(rng), Next(rng));
                var a = UnitySpace.Position(Rotate(q, v));
                var b = Rotate(UnitySpace.Rotation(q), UnitySpace.Position(v));
                Assert.Equal(a.X, b.X, 4);
                Assert.Equal(a.Y, b.Y, 4);
                Assert.Equal(a.Z, b.Z, 4);
            }
        }

        private static float Next(Random rng) => (float)(rng.NextDouble() * 2 - 1);

        private static Quat Normalize(Quat q)
        {
            float l = (float)Math.Sqrt(q.X * q.X + q.Y * q.Y + q.Z * q.Z + q.W * q.W);
            return new Quat(q.X / l, q.Y / l, q.Z / l, q.W / l);
        }

        private static Vec3 Rotate(Quat q, Vec3 v)
        {
            var m = Matrix4.FromTrs(Vec3.Zero, q, Vec3.One);
            return new Vec3(
                m[0, 0] * v.X + m[0, 1] * v.Y + m[0, 2] * v.Z,
                m[1, 0] * v.X + m[1, 1] * v.Y + m[1, 2] * v.Z,
                m[2, 0] * v.X + m[2, 1] * v.Y + m[2, 2] * v.Z);
        }

        [Fact]
        public void Affine_inverse_undoes_the_matrix()
        {
            var m = Matrix4.FromTrs(new Vec3(1, -2, 3), Normalize(new Quat(0.2f, 0.4f, -0.1f, 0.9f)), new Vec3(1, 1.5f, 0.5f));
            var identity = m * m.InverseAffine();
            for (int r = 0; r < 4; r++)
            {
                for (int c = 0; c < 4; c++)
                {
                    Assert.Equal(r == c ? 1f : 0f, identity[r, c], 5);
                }
            }
        }
    }

    public class ContractSetTests
    {
        [Theory]
        [InlineData(typeof(BoneRole), "bone-role")]
        [InlineData(typeof(BoneGroup), "bone-group")]
        [InlineData(typeof(MaterialRole), "material-role")]
        [InlineData(typeof(BlendMode), "blend-mode")]
        [InlineData(typeof(TextureRole), "texture-role")]
        [InlineData(typeof(TextureVariant), "texture-variant")]
        [InlineData(typeof(ExpressionCategory), "expression-category")]
        public void Core_enums_match_the_closed_sets(Type type, string set)
        {
            Assert.Equal(ContractSchemas.SetMembers(set), ContractNames.All(type));
        }

        [Fact]
        public void Bone_Roles_has_HumanBodyBones_and_every_role_is_unique()
        {
            Assert.Equal(68, ContractSchemas.SetMembers("bone-role").Length);
            Assert.Equal(ContractSchemas.SetMembers("bone-role"), ContractSchemas.SetUnique("bone-role"));
        }

        [Fact]
        public void Core_uniqueness_matches_the_x_unique_lists()
        {
            var materialUnique = Enum.GetValues(typeof(MaterialRole)).Cast<MaterialRole>().Where(ContractNames.IsUnique).Select(r => ContractNames.Of(r));
            Assert.Equal(ContractSchemas.SetUnique("material-role"), materialUnique);
            var textureUnique = Enum.GetValues(typeof(TextureRole)).Cast<TextureRole>().Where(ContractNames.IsUnique).Select(r => ContractNames.Of(r));
            Assert.Equal(ContractSchemas.SetUnique("texture-role"), textureUnique);
        }

        [Fact]
        public void Liquid_mask_is_not_a_texture_role()
        {
            Assert.DoesNotContain("liquid_mask", ContractSchemas.SetMembers("texture-role"));
        }

        [Fact]
        public void Every_Expression_Name_has_a_category_prefix()
        {
            foreach (var name in ContractSchemas.SetMembers("expression-name"))
            {
                Assert.True(ContractNames.CategoryOf(name).HasValue, name);
            }
        }

        [Fact]
        public void Every_schema_is_strict()
        {
            foreach (var file in Directory.GetFiles(Repo.Path("contract/schema"), "*.schema.json"))
            {
                string text = File.ReadAllText(file);
                int objects = Regex.Matches(text, "\"type\": \"object\"").Count;
                int closed = Regex.Matches(text, "\"additionalProperties\": (false|\\{)").Count;
                int open = Regex.Matches(text, "\"(kk|kks|svs)\": \\{\\s*\"type\": \"object\"\\s*\\}").Count;
                Assert.True(objects - open <= closed, Path.GetFileName(file) + " has an object schema without additionalProperties");
            }
        }
    }

    public class ExpressionTableTests
    {
        [Theory]
        [InlineData("kk", "KK")]
        [InlineData("kks", "KKS")]
        [InlineData("svs", "SVS")]
        public void Table_passes_its_schema_and_parses(string file, string game)
        {
            string path = Repo.Path("contract/expressions/" + file + ".json");
            var errors = ContractSchemas.ValidateFile("expression-table.schema.json", path);
            Assert.True(errors.Count == 0, string.Join("\n", errors));

            var table = ExpressionTable.Parse(File.ReadAllText(path));
            Assert.Equal(game, table.Game);
            var names = table.Patterns.SelectMany(p => new[] { p.Name, p.ClosedName }).Where(n => n != null)
                .Concat(table.Recipes.Select(r => r.Name)).ToList();
            Assert.Equal(names.Count, names.Distinct().Count());
        }

        [Fact]
        public void KK_includes_the_chewing_and_eating_recipes()
        {
            var table = ExpressionTable.Parse(File.ReadAllText(Repo.Path("contract/expressions/kk.json")));
            Assert.Contains(table.Recipes, r => r.Name == "Mouth Chewing" && r.Shapes[0].Key == "kuti_face.f00_mogu_op");
            Assert.Contains(table.Recipes, r => r.Name == "Mouth Chewing, Closed");
            Assert.Contains(table.Recipes, r => r.Name == "Mouth Eating 2" && r.Shapes.Any(s => s.Key == "kuti_face.f00_tabe_op"));
        }

        [Fact]
        public void SVS_names_the_games_vowel_mouths_instead_of_baking_copies()
        {
            // Recipes for these made a second, identical key beside the game's own pattern.
            var table = ExpressionTable.Parse(File.ReadAllText(Repo.Path("contract/expressions/svs.json")));
            var named = new[] { "Mouth A", "Mouth I", "Mouth U", "Mouth E", "Mouth O" };
            for (int i = 0; i < named.Length; i++)
                Assert.Equal(named[i], table.Find(ExpressionList.Mouth, 19 + i).Name);
            Assert.Equal("Mouth Cartoony Smile", table.Find(ExpressionList.Mouth, 26).Name);
            Assert.Equal(new[] { "Mouth Hate", "Mouth Hate, Closed" }, table.Recipes.Select(r => r.Name).ToArray());
        }

        [Fact]
        public void Gag_eye_patterns_use_the_Gag_prefix()
        {
            var table = ExpressionTable.Parse(File.ReadAllText(Repo.Path("contract/expressions/kk.json")));
            Assert.Equal("Gag Heart Eyes", table.Find(ExpressionList.Eye, 26).Name);
            Assert.Equal("Eye Heart Pupils", table.Find(ExpressionList.Eye, 25).Name);
            Assert.Null(table.Find(ExpressionList.Eye, 999));
        }
    }

    public class CoreSourceTests
    {
        private static string[] Sources() => Directory.GetFiles(Repo.Path("exporters/core/src"), "*.cs");

        [Fact]
        public void Core_references_no_UnityEngine()
        {
            foreach (var file in Sources())
            {
                Assert.DoesNotContain("UnityEngine", File.ReadAllText(file));
            }
        }

        [Fact]
        public void Core_has_no_mutable_static_fields()
        {
            var field = new Regex(@"^\s*(public|internal|private|protected)?\s*static\s+(?!readonly\b|class\b|extern\b)[\w<>\[\],\s.?]+\s+\w+\s*(=|;)", RegexOptions.Multiline);
            foreach (var file in Sources())
            {
                var match = field.Match(File.ReadAllText(file));
                Assert.False(match.Success, Path.GetFileName(file) + ": " + match.Value.Trim());
            }
        }

        [Fact]
        public void Every_source_file_is_in_the_projitems()
        {
            string projitems = File.ReadAllText(Repo.Path("exporters/core/KKBP.Exporter.Core.projitems"));
            foreach (var file in Sources())
            {
                Assert.Contains("src\\" + Path.GetFileName(file), projitems);
            }
        }
    }

    public class MeshVectorTests
    {
        private static readonly int[][] Quad = { new[] { 0, 1, 2, 2, 1, 3 } };

        private static void AssertUnit(Vec3 v)
        {
            Assert.InRange(Math.Sqrt(v.X * v.X + v.Y * v.Y + v.Z * v.Z), 0.99999, 1.00001);
        }

        [Fact]
        public void Good_normals_are_made_unit_length()
        {
            var normals = MeshVectors.Normals(new[] { new Vec3(0, 0, 2), new Vec3(0, 3, 0), new Vec3(0, 0, 1), new Vec3(1, 1, 0) }, Quad);
            Assert.Equal(new Vec3(0, 0, 1), normals[0]);
            AssertUnit(normals[3]);
        }

        [Fact]
        public void A_zero_or_nan_normal_takes_its_neighbours_average()
        {
            var normals = MeshVectors.Normals(new[]
            {
                new Vec3(0, 0, 0), new Vec3(0, 0, 1), new Vec3(0, 0, 1), new Vec3(float.NaN, 0, 0),
            }, Quad);
            Assert.Equal(new Vec3(0, 0, 1), normals[0]);
            Assert.Equal(new Vec3(0, 0, 1), normals[3]);
        }

        [Fact]
        public void A_normal_with_no_good_neighbour_still_gets_a_unit_direction()
        {
            var normals = MeshVectors.Normals(new[] { Vec3.Zero, Vec3.Zero, Vec3.Zero, Vec3.Zero }, Quad);
            Assert.All(normals, AssertUnit);
        }

        [Fact]
        public void A_zero_tangent_is_rebuilt_perpendicular_to_its_normal_with_a_handedness()
        {
            var normals = new[] { new Vec3(0, 0, 1), new Vec3(0, 0, 1), new Vec3(0, 0, 1), new Vec3(1, 0, 0) };
            var tangents = MeshVectors.Tangents(new[]
            {
                new Vec4(0, 0, 0, 0), new Vec4(0, 2, 0.5f, -1), new Vec4(0, 1, 0, -1), new Vec4(0, 0, 0, 1),
            }, normals, Quad);
            var t0 = new Vec3(tangents[0].X, tangents[0].Y, tangents[0].Z);
            AssertUnit(t0);
            Assert.InRange(t0.Z, -1e-6f, 1e-6f);  // perpendicular to (0, 0, 1)
            Assert.Equal(-1, tangents[0].W);       // the neighbours' handedness
            var t3 = new Vec3(tangents[3].X, tangents[3].Y, tangents[3].Z);
            AssertUnit(t3);
            Assert.InRange(t3.X, -1e-6f, 1e-6f);  // perpendicular to (1, 0, 0)
            Assert.Equal(1, tangents[3].W);        // its own
            Assert.Equal(-1, tangents[1].W);
        }
    }
}
