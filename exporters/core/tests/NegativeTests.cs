using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using KKBP.Exporter.Core.Tests.Support;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    /// <summary>Shows that the contract checks can fail: each one is given something broken.</summary>
    public sealed class NegativeTests : IClassFixture<FakeBundleFixture>
    {
        private readonly FakeBundleFixture f;

        public NegativeTests(FakeBundleFixture fixture)
        {
            f = fixture;
        }

        [Theory]
        [InlineData("manifest.json", "manifest.schema.json", "$.game", "\"AC\"")]
        [InlineData("manifest.json", "manifest.schema.json", "$.schema_version", "\"1\"")]
        [InlineData("manifest.json", "manifest.schema.json", "$.passes[1].outfit", "null")]
        [InlineData("manifest.json", "manifest.schema.json", "$.extra", "1")]
        [InlineData("skeleton.json", "skeleton.schema.json", "$.bones[1].role", "\"left_wing\"")]
        [InlineData("skeleton.json", "skeleton.schema.json", "$.bones[0].id", "\"cf__j\"")]
        [InlineData("skeleton.json", "skeleton.schema.json", "$.bones[0].group", "\"hitbox\"")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].textures[0].role", "\"liquid_mask\"")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].textures[0].variant", "\"pre_light\"")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].blend_mode", "\"transparent\"")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].extensions.kk.other", "1")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].extensions.kk.create.id", "\"cf_m_body\"")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].extensions.kk.create.colors._Color", "[1, 1, 1]")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].extensions.kk.create.textures[0].variant", "\"pre_light\"")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].extensions.kks.create", "{}")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].extensions.svs.create", "{}")]
        [InlineData("character.json", "character.schema.json", "$.extensions.kk.create", "{}")]
        [InlineData("materials.json", "materials.schema.json", "$.materials[0].colors._Color", "[1, 1, 1]")]
        [InlineData("expressions.json", "expressions.schema.json", "$.expressions[0].name", "\"Eye Happy Face\"")]
        [InlineData("expressions.json", "expressions.schema.json", "$.expressions[0].category", "\"hitbox\"")]
        [InlineData("physics.json", "physics.schema.json", "$.colliders[0].direction", "\"w\"")]
        [InlineData("character.json", "character.schema.json", "$.extensions.ac", "{}")]
        [InlineData("character.json", "character.schema.json", "$.extensions.kk", "{\"personality\": 8}")]
        [InlineData("expressions.json", "expressions.schema.json", "$.effects[0].material_changes", "[]")]
        [InlineData("expressions.json", "expressions.schema.json", "$.effects[0].shows", "[\"a\", \"a\"]")]
        [InlineData("expressions.json", "expressions.schema.json", "$.expressions[5].shows", "[\"cf_O_gag_eye_00\"]")]
        [InlineData("outfits/00/outfit.json", "pass.schema.json", "$.body_textures[0].texture.role", "\"skin\"")]
        public void Schemas_reject_broken_files(string file, string schema, string path, string value)
        {
            var doc = JsonNode.Parse(File.ReadAllText(f.FilePath(file)));
            Set(doc, path, JsonNode.Parse(value));
            Assert.NotEmpty(ContractSchemas.Validate(schema, doc.ToJsonString()));
        }

        [Fact]
        public void Pass_schema_rejects_a_body_with_an_outfit_index()
        {
            var doc = JsonNode.Parse(File.ReadAllText(f.FilePath("body.json")));
            doc["outfit"] = 0;
            Assert.NotEmpty(ContractSchemas.Validate("pass.schema.json", doc.ToJsonString()));
        }

        [Theory]
        [InlineData("materials.json", "$.materials[1].role", "\"body\"", "Material Role body")]
        [InlineData("materials.json", "$.materials[0].textures[1].variant", "\"light\"", "repeats texture slot")]
        [InlineData("skeleton.json", "$.bones[2].parent", "\"nowhere\"", "unknown parent")]
        [InlineData("expressions.json", "$.expressions[0].category", "\"mouth\"", "has category")]
        [InlineData("expressions.json", "$.expressions[0].mesh", "\"no_such_mesh\"", "unknown mesh")]
        [InlineData("physics.json", "$.chains[0].colliders[0]", "\"cf_hit_missing\"", "unknown collider")]
        [InlineData("body.json", "$.meshes[0].materials[0]", "\"no_such_material\"", "unknown material")]
        [InlineData("expressions.json", "$.effects[0].shows[0]", "\"o_bot_skirt\"", "isn't in its Pass")]
        [InlineData("expressions.json", "$.effects[0].shows[0]", "\"o_body_a\"", "has no showing key")]
        [InlineData("expressions.json", "$.effects[0].material_changes[0].textures[0].pattern", "\"cf_t_gageye_99\"", "doesn't have")]
        [InlineData("expressions.json", "$.effects[1].target", "\"Gag Heart Eyes\"", "two effects entries")]
        [InlineData("expressions.json", "$.effects[0].target", "\"no_such_expression\"", "which no record has")]
        [InlineData("outfits/00/outfit.json", "$.body_textures[0].material", "\"cf_m_bot_skirt01\"", "no Body Pass mesh uses")]
        [InlineData("outfits/00/outfit.json", "$.body_textures[0].texture.raw", "\"_NormalMap\"", "already filled")]
        public void Checker_reports_broken_bundles(string file, string path, string value, string expected)
        {
            using var copy = new TempDir();
            CopyBundle(f.Bundle, copy.Path);
            string target = Path.Combine(copy.Path, file);
            var doc = JsonNode.Parse(File.ReadAllText(target));
            Set(doc, path, JsonNode.Parse(value));
            File.WriteAllText(target, doc.ToJsonString());

            var problems = ContractChecker.Check(copy.Path);
            Assert.Contains(problems, p => p.Contains(expected));
        }

        [Theory]
        [InlineData("cf_m_body", "textures[1].raw", "\"_MainTex\"", "create repeats texture slot _MainTex")]
        [InlineData("cf_m_body", "textures[2].role", "\"main\"", "create repeats Texture Role main")]
        [InlineData("cf_m_body", "textures[0].file", "\"textures/9999.png\"", "create texture file textures/9999.png is missing")]
        public void Checker_reports_broken_creates(string material, string path, string value, string expected)
        {
            Assert.Contains(CheckWithMaterial(material, m => Set(m, "$.extensions.kk.create." + path, JsonNode.Parse(value))), p => p.Contains(expected));
        }

        [Fact]
        public void Checker_reports_a_create_on_a_role_material_outside_the_Body_Pass()
        {
            // The skirt is an Outfit material; with a Role it would have to belong to the Body Pass.
            Assert.Contains(CheckWithMaterial("cf_m_bot_skirt01", m => m["role"] = "hair"), p => p.Contains("cf_m_bot_skirt01 has a create but isn't used by meshes of exactly one Body Pass"));
        }

        [Fact]
        public void Checker_reports_a_create_on_a_role_less_material_of_the_Body_Pass()
        {
            Assert.Contains(CheckWithMaterial("cf_m_body", m => m.AsObject().Remove("role")), p => p.Contains("cf_m_body has a create but isn't used by meshes of exactly one Outfit Pass"));
        }

        [Fact]
        public void Checker_reports_a_create_on_a_material_two_Passes_use()
        {
            // The ribbon's material is used by both Outfits.
            string create = "{\"shader\": \"s\", \"colors\": {}, \"floats\": {}, \"vectors\": {}, \"textures\": []}";
            Assert.Contains(CheckWithMaterial("cf_m_acs_ribbon", m => m["extensions"] = JsonNode.Parse("{\"kk\": {\"create\": " + create + "}}")),
                p => p.Contains("cf_m_acs_ribbon has a create but isn't used by meshes of exactly one Outfit Pass"));
        }

        /// <summary>Checks a copy of the fake bundle with one material in materials.json changed.</summary>
        private List<string> CheckWithMaterial(string id, Action<JsonNode> change)
        {
            using var copy = new TempDir();
            CopyBundle(f.Bundle, copy.Path);
            string target = Path.Combine(copy.Path, "materials.json");
            var doc = JsonNode.Parse(File.ReadAllText(target));
            change(doc["materials"].AsArray().Single(m => (string)m["id"] == id));
            File.WriteAllText(target, doc.ToJsonString());
            return ContractChecker.Check(copy.Path);
        }

        [Fact]
        public void Checker_reports_a_missing_texture()
        {
            using var copy = new TempDir();
            CopyBundle(f.Bundle, copy.Path);
            File.Delete(Path.Combine(copy.Path, "textures", "0003.png"));
            Assert.Contains(ContractChecker.Check(copy.Path), p => p.Contains("0003.png is missing"));
        }

        [Fact]
        public void Validator_fails_a_broken_glb()
        {
            using var temp = new TempDir();
            string truncated = Path.Combine(temp.Path, "truncated.glb");
            byte[] bytes = File.ReadAllBytes(f.FilePath("body.glb"));
            File.WriteAllBytes(truncated, bytes[..(bytes.Length / 2)]);
            string garbage = Path.Combine(temp.Path, "garbage.glb");
            File.WriteAllBytes(garbage, new byte[] { 1, 2, 3 });

            Assert.NotEqual(0, GltfValidator.Run(new[] { truncated }).ExitCode);
            Assert.NotEqual(0, GltfValidator.Run(new[] { garbage }).ExitCode);
        }

        /// <summary>Sets a value at a simple JSONPath such as $.a.b[1].c, creating the last member if needed.</summary>
        private static void Set(JsonNode root, string path, JsonNode value)
        {
            var parts = path.Substring(2).Replace("[", ".[").Split('.');
            JsonNode node = root;
            for (int i = 0; i < parts.Length; i++)
            {
                bool last = i == parts.Length - 1;
                string part = parts[i];
                if (part.StartsWith("["))
                {
                    int index = int.Parse(part.Trim('[', ']'));
                    if (last)
                    {
                        node[index] = value;
                    }
                    else
                    {
                        node = node[index];
                    }
                }
                else if (last)
                {
                    node[part] = value;
                }
                else
                {
                    node = node[part] ?? (node[part] = new System.Text.Json.Nodes.JsonObject());
                }
            }
        }

        private static void CopyBundle(string from, string to)
        {
            foreach (var file in Directory.GetFiles(from, "*", SearchOption.AllDirectories))
            {
                string target = Path.Combine(to, Path.GetRelativePath(from, file));
                Directory.CreateDirectory(Path.GetDirectoryName(target));
                File.Copy(file, target);
            }
        }
    }
}
