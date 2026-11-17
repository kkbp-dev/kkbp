using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace KKBP.Exporter.Core.Tests.Support
{
    /// <summary>
    /// Checks a bundle against the contract: every JSON file against its schema, then the rules
    /// contract/README.md lists as checked in code. Returns every problem found.
    /// </summary>
    public static class ContractChecker
    {
        private static readonly Dictionary<string, string> CategoryByPrefix = new Dictionary<string, string>
        {
            { "Eye", "eye" }, { "Mouth", "mouth" }, { "Eyebrow", "eyebrow" }, { "Gag", "gag" }, { "Tears", "tears" },
        };

        public static List<string> Check(string bundle)
        {
            var problems = new List<string>();
            string P(string relative) => Path.Combine(bundle, relative.Replace('/', Path.DirectorySeparatorChar));

            var schemaFiles = new Dictionary<string, string>
            {
                { "manifest.json", "manifest.schema.json" },
                { "character.json", "character.schema.json" },
                { "skeleton.json", "skeleton.schema.json" },
                { "materials.json", "materials.schema.json" },
                { "expressions.json", "expressions.schema.json" },
                { "physics.json", "physics.schema.json" },
            };
            foreach (var pair in schemaFiles)
            {
                if (!File.Exists(P(pair.Key)))
                {
                    problems.Add("missing " + pair.Key);
                    continue;
                }
                problems.AddRange(ContractSchemas.ValidateFile(pair.Value, P(pair.Key)));
            }
            if (problems.Count > 0)
            {
                return problems;
            }

            using var manifest = Read(P("manifest.json"));
            using var skeleton = Read(P("skeleton.json"));
            using var materials = Read(P("materials.json"));
            using var expressions = Read(P("expressions.json"));
            using var physics = Read(P("physics.json"));

            if (manifest.RootElement.GetProperty("card").ValueKind == JsonValueKind.String && !File.Exists(P("card.png")))
            {
                problems.Add("the Manifest names card.png but it is missing");
            }

            // Bones.
            var bones = new Dictionary<string, JsonElement>();
            foreach (var bone in skeleton.RootElement.GetProperty("bones").EnumerateArray())
            {
                string id = bone.GetProperty("id").GetString();
                if (!bones.TryAdd(id, bone))
                {
                    problems.Add("bone Id " + id + " appears twice");
                }
            }
            foreach (var bone in bones.Values)
            {
                var parent = bone.GetProperty("parent");
                if (parent.ValueKind == JsonValueKind.String && !bones.ContainsKey(parent.GetString()))
                {
                    problems.Add("bone " + bone.GetProperty("id").GetString() + " has unknown parent " + parent.GetString());
                }
                if (bone.TryGetProperty("game_scale", out var gameScale) && gameScale.EnumerateArray().All(c => Math.Abs(c.GetDouble() - 1) < 1e-6))
                {
                    problems.Add("bone " + bone.GetProperty("id").GetString() + " has a game_scale of 1");
                }
            }
            CheckUnique(problems, "Bone Role", bones.Values.Select(b => Optional(b, "role")), ContractSchemas.SetUnique("bone-role"));

            // Materials and textures.
            var materialIds = new HashSet<string>();
            var materialSlots = new Dictionary<string, HashSet<string>>();
            var creates = new Dictionary<string, string>(); // material Id -> its Material Role, or null
            var textureUnique = new HashSet<string>(ContractSchemas.SetUnique("texture-role"));
            foreach (var material in materials.RootElement.GetProperty("materials").EnumerateArray())
            {
                string id = material.GetProperty("id").GetString();
                if (!materialIds.Add(id))
                {
                    problems.Add("material Id " + id + " appears twice");
                }
                materialSlots[id] = CheckTextures(problems, "material " + id, material.GetProperty("textures"), textureUnique, P);
                if (material.TryGetProperty("extensions", out var extensions))
                {
                    foreach (string game in new[] { "kk", "svs" })
                    {
                        if (extensions.TryGetProperty(game, out var section) && section.TryGetProperty("create", out var create))
                        {
                            CheckTextures(problems, "material " + id + " create", create.GetProperty("textures"), textureUnique, P);
                            creates[id] = Optional(material, "role");
                        }
                    }
                }
            }
            CheckUnique(problems, "Material Role", materials.RootElement.GetProperty("materials").EnumerateArray().Select(m => Optional(m, "role")), ContractSchemas.SetUnique("material-role"));

            // Passes: data files and glTF.
            var meshIds = new HashSet<string>();
            var meshPass = new Dictionary<string, string>();
            var bodyMaterials = new HashSet<string>();
            var materialPasses = new Dictionary<string, HashSet<string>>(); // material Id -> "kind\ndata file" of each Pass using it
            var targetsByMesh = new Dictionary<string, HashSet<string>>();
            foreach (var pass in manifest.RootElement.GetProperty("passes").EnumerateArray())
            {
                string data = pass.GetProperty("data").GetString();
                string mesh = pass.GetProperty("mesh").GetString();
                if (!File.Exists(P(data)) || !File.Exists(P(mesh)))
                {
                    problems.Add("Pass files " + mesh + " or " + data + " are missing");
                    continue;
                }
                problems.AddRange(ContractSchemas.ValidateFile("pass.schema.json", P(data)));
                using var passData = Read(P(data));
                if (passData.RootElement.GetProperty("kind").GetString() != pass.GetProperty("kind").GetString()
                    || passData.RootElement.GetProperty("outfit").ToString() != pass.GetProperty("outfit").ToString())
                {
                    problems.Add(data + " doesn't match its Manifest entry");
                }
                var passMeshes = new HashSet<string>();
                foreach (var m in passData.RootElement.GetProperty("meshes").EnumerateArray())
                {
                    string id = m.GetProperty("id").GetString();
                    if (!meshIds.Add(id))
                    {
                        problems.Add("mesh Id " + id + " appears twice");
                    }
                    passMeshes.Add(id);
                    meshPass[id] = data;
                    foreach (var mat in m.GetProperty("materials").EnumerateArray())
                    {
                        if (!materialIds.Contains(mat.GetString()))
                        {
                            problems.Add("mesh " + id + " uses unknown material " + mat.GetString());
                        }
                        if (pass.GetProperty("kind").GetString() == "body")
                        {
                            bodyMaterials.Add(mat.GetString());
                        }
                        if (!materialPasses.TryGetValue(mat.GetString(), out var passes))
                        {
                            materialPasses[mat.GetString()] = passes = new HashSet<string>();
                        }
                        passes.Add(pass.GetProperty("kind").GetString() + "\n" + data);
                    }
                }
                if (passData.RootElement.TryGetProperty("body_textures", out var bodyTextures))
                {
                    var used = new HashSet<string>();
                    foreach (var b in bodyTextures.EnumerateArray())
                    {
                        string material = b.GetProperty("material").GetString();
                        var texture = b.GetProperty("texture");
                        string slot = texture.GetProperty("raw").GetString() + "\n" + Optional(texture, "variant") + "\n" + Optional(texture, "pattern");
                        if (!bodyMaterials.Contains(material))
                        {
                            problems.Add(data + " has a body texture on " + material + ", which no Body Pass mesh uses");
                        }
                        else if (materialSlots[material].Contains(slot) || !used.Add(material + "\n" + slot))
                        {
                            problems.Add(data + " body texture " + texture.GetProperty("raw").GetString() + " on " + material + " fills a slot that is already filled");
                        }
                        if (!File.Exists(P(texture.GetProperty("file").GetString())))
                        {
                            problems.Add(data + " body texture file " + texture.GetProperty("file").GetString() + " is missing");
                        }
                    }
                }
                CheckGlb(problems, P(mesh), mesh, bones, materialIds, passMeshes, targetsByMesh);
            }

            // A create sits only on a material of the Pass whose objects it colours.
            foreach (var entry in creates)
            {
                materialPasses.TryGetValue(entry.Key, out var users);
                string expected = entry.Value != null ? "body" : "outfit";
                if (users == null || users.Count != 1 || !users.Single().StartsWith(expected + "\n", StringComparison.Ordinal))
                {
                    problems.Add("material " + entry.Key + " has a create but isn't used by meshes of exactly one " + (entry.Value != null ? "Body" : "Outfit") + " Pass");
                }
            }

            // Expressions.
            var showingKeys = new HashSet<string>(expressions.RootElement.GetProperty("expressions").EnumerateArray()
                .Where(e => Optional(e, "game_name") == null && (e.GetProperty("category").GetString() == "tears" || e.GetProperty("category").GetString() == "gag"))
                .Select(e => e.GetProperty("mesh").GetString()));
            var seen = new HashSet<string>();
            var namesPerMesh = new HashSet<string>();
            foreach (var e in expressions.RootElement.GetProperty("expressions").EnumerateArray())
            {
                string mesh = e.GetProperty("mesh").GetString();
                string target = e.GetProperty("target").GetString();
                string name = Optional(e, "name");
                if (!meshIds.Contains(mesh))
                {
                    problems.Add("expression " + target + " is on unknown mesh " + mesh);
                }
                if (!seen.Add(mesh + "\n" + target))
                {
                    problems.Add("expression " + target + " appears twice on mesh " + mesh);
                }
                if (name != null)
                {
                    if (!namesPerMesh.Add(mesh + "\n" + name))
                    {
                        problems.Add("Expression Name " + name + " appears twice on mesh " + mesh);
                    }
                    if (target != name)
                    {
                        problems.Add("expression " + name + " has target name " + target);
                    }
                    string prefix = name.Split(' ')[0];
                    if (!CategoryByPrefix.TryGetValue(prefix, out var category) || category != e.GetProperty("category").GetString())
                    {
                        problems.Add("expression " + name + " has category " + e.GetProperty("category").GetString());
                    }
                }
                if (!targetsByMesh.TryGetValue(mesh, out var targets) || !targets.Remove(target))
                {
                    problems.Add("expression " + target + " isn't a morph target of mesh " + mesh);
                }
            }
            var targetPasses = new Dictionary<string, HashSet<string>>();
            foreach (var e in expressions.RootElement.GetProperty("expressions").EnumerateArray())
            {
                string target = e.GetProperty("target").GetString();
                if (!targetPasses.TryGetValue(target, out var passes))
                {
                    targetPasses[target] = passes = new HashSet<string>();
                }
                if (meshPass.TryGetValue(e.GetProperty("mesh").GetString(), out var pass))
                {
                    passes.Add(pass);
                }
            }
            var effectTargets = new HashSet<string>();
            foreach (var e in expressions.RootElement.GetProperty("effects").EnumerateArray())
            {
                string target = e.GetProperty("target").GetString();
                if (!effectTargets.Add(target))
                {
                    problems.Add("expression " + target + " has two effects entries");
                }
                if (!targetPasses.TryGetValue(target, out var ownPasses))
                {
                    problems.Add("effects name expression " + target + ", which no record has");
                    continue;
                }
                foreach (var list in new[] { "shows", "hides" })
                {
                    if (!e.TryGetProperty(list, out var linked))
                    {
                        continue;
                    }
                    foreach (var other in linked.EnumerateArray().Select(x => x.GetString()))
                    {
                        if (!meshPass.TryGetValue(other, out var otherPass) || !ownPasses.Contains(otherPass))
                        {
                            problems.Add("expression " + target + " " + list + " mesh " + other + ", which isn't in its Pass");
                        }
                        else if (list == "shows" && !showingKeys.Contains(other))
                        {
                            problems.Add("expression " + target + " shows mesh " + other + ", which has no showing key");
                        }
                    }
                }
                if (e.TryGetProperty("material_changes", out var changes))
                {
                    foreach (var change in changes.EnumerateArray())
                    {
                        string material = change.GetProperty("material").GetString();
                        if (!materialSlots.TryGetValue(material, out var slots))
                        {
                            problems.Add("expression " + target + " changes unknown material " + material);
                            continue;
                        }
                        foreach (var t in change.GetProperty("textures").EnumerateArray())
                        {
                            string prefix = t.GetProperty("raw").GetString() + "\n";
                            string suffix = "\n" + t.GetProperty("pattern").GetString();
                            if (!slots.Any(slot => slot.StartsWith(prefix, StringComparison.Ordinal) && slot.EndsWith(suffix, StringComparison.Ordinal)))
                            {
                                problems.Add("expression " + target + " sets a pattern material " + material + " doesn't have");
                            }
                        }
                    }
                }
            }
            foreach (var pair in targetsByMesh)
            {
                foreach (var target in pair.Value)
                {
                    problems.Add("morph target " + target + " on mesh " + pair.Key + " isn't in expressions.json");
                }
            }

            // Physics.
            var colliders = new HashSet<string>();
            foreach (var c in physics.RootElement.GetProperty("colliders").EnumerateArray())
            {
                if (!colliders.Add(c.GetProperty("name").GetString()))
                {
                    problems.Add("collider " + c.GetProperty("name").GetString() + " appears twice");
                }
                RequireBone(problems, bones, c.GetProperty("bone").GetString(), "collider");
            }
            foreach (var chain in physics.RootElement.GetProperty("chains").EnumerateArray())
            {
                RequireBone(problems, bones, chain.GetProperty("root").GetString(), "chain root");
                foreach (var c in chain.GetProperty("colliders").EnumerateArray())
                {
                    if (!colliders.Contains(c.GetString()))
                    {
                        problems.Add("chain uses unknown collider " + c.GetString());
                    }
                }
                foreach (var b in chain.GetProperty("exclusions").EnumerateArray())
                {
                    RequireBone(problems, bones, b.GetString(), "chain exclusion");
                }
                foreach (var p in chain.GetProperty("particles").EnumerateArray())
                {
                    RequireBone(problems, bones, p.GetProperty("bone").GetString(), "chain particle");
                }
            }
            return problems;
        }

        /// <summary>
        /// Checks one texture list (a material's own, or its create's): unique slots, unique Roles except the
        /// repeatable ones, and files that exist. Returns the slots it found.
        /// </summary>
        private static HashSet<string> CheckTextures(List<string> problems, string label, JsonElement textures, HashSet<string> textureUnique, Func<string, string> path)
        {
            var slots = new HashSet<string>();
            var roles = new HashSet<string>();
            foreach (var texture in textures.EnumerateArray())
            {
                string variantPattern = Optional(texture, "variant") + "\n" + Optional(texture, "pattern");
                if (!slots.Add(texture.GetProperty("raw").GetString() + "\n" + variantPattern))
                {
                    problems.Add(label + " repeats texture slot " + texture.GetProperty("raw").GetString());
                }
                string role = Optional(texture, "role");
                if (role != null && textureUnique.Contains(role) && !roles.Add(role + "\n" + variantPattern))
                {
                    problems.Add(label + " repeats Texture Role " + role);
                }
                if (!File.Exists(path(texture.GetProperty("file").GetString())))
                {
                    problems.Add(label + " texture file " + texture.GetProperty("file").GetString() + " is missing");
                }
            }
            foreach (var texture in textures.EnumerateArray())
            {
                string variant = Optional(texture, "variant");
                if (variant == null || !variant.EndsWith("_no_eyeshadow", StringComparison.Ordinal))
                {
                    continue;
                }
                string raw = texture.GetProperty("raw").GetString();
                foreach (string needed in new[] { "light", "dark", "light_no_eyeshadow", "dark_no_eyeshadow" })
                {
                    if (!slots.Contains(raw + "\n" + needed + "\n" + Optional(texture, "pattern")))
                    {
                        problems.Add(label + " has " + raw + " without eyeshadow but no " + needed + " Variant of it");
                    }
                }
            }
            return slots;
        }

        private static void CheckGlb(List<string> problems, string path, string label, Dictionary<string, JsonElement> bones,
            HashSet<string> materialIds, HashSet<string> passMeshes, Dictionary<string, HashSet<string>> targetsByMesh)
        {
            using var doc = Glb.ReadJson(path);
            var root = doc.RootElement;
            var meshes = root.TryGetProperty("meshes", out var m) ? m.EnumerateArray().ToList() : new List<JsonElement>();
            var meshNodes = new HashSet<string>();
            foreach (var node in root.GetProperty("nodes").EnumerateArray())
            {
                string id = ExtrasId(problems, node, label + " node");
                if (node.TryGetProperty("mesh", out var meshIndex))
                {
                    meshNodes.Add(id);
                    var mesh = meshes[meshIndex.GetInt32()];
                    ExtrasId(problems, mesh, label + " mesh");
                    var targets = new HashSet<string>();
                    if (mesh.GetProperty("extras").TryGetProperty("targetNames", out var names))
                    {
                        foreach (var n in names.EnumerateArray())
                        {
                            targets.Add(n.GetString());
                        }
                    }
                    targetsByMesh[id] = targets;
                    continue;
                }
                if (!bones.TryGetValue(id, out var bone))
                {
                    problems.Add(label + " bone " + id + " isn't in skeleton.json");
                    continue;
                }
                foreach (var property in new[] { "translation", "rotation", "scale" })
                {
                    var a = node.GetProperty(property).EnumerateArray().Select(x => x.GetDouble()).ToArray();
                    var b = bone.GetProperty(property).EnumerateArray().Select(x => x.GetDouble()).ToArray();
                    if (a.Length != b.Length || a.Zip(b, (x, y) => Math.Abs(x - y)).Any(d => d > 1e-6))
                    {
                        problems.Add(label + " bone " + id + " " + property + " differs from skeleton.json");
                    }
                }
            }
            if (!meshNodes.SetEquals(passMeshes))
            {
                problems.Add(label + " meshes don't match its data file");
            }
            if (root.TryGetProperty("materials", out var materials))
            {
                foreach (var material in materials.EnumerateArray())
                {
                    string id = ExtrasId(problems, material, label + " material");
                    if (!materialIds.Contains(id))
                    {
                        problems.Add(label + " material " + id + " isn't in materials.json");
                    }
                }
            }
        }

        private static string ExtrasId(List<string> problems, JsonElement element, string label)
        {
            string name = element.TryGetProperty("name", out var n) ? n.GetString() : null;
            string id = element.TryGetProperty("extras", out var extras) && extras.TryGetProperty("id", out var i) ? i.GetString() : null;
            if (id == null || id != name)
            {
                problems.Add(label + " '" + name + "' has extras.id '" + id + "'");
            }
            return id;
        }

        private static void CheckUnique(List<string> problems, string set, IEnumerable<string> values, string[] unique)
        {
            var seen = new HashSet<string>();
            foreach (var value in values.Where(v => v != null))
            {
                if (unique.Contains(value) && !seen.Add(value))
                {
                    problems.Add(set + " " + value + " appears more than once");
                }
            }
        }

        private static void RequireBone(List<string> problems, Dictionary<string, JsonElement> bones, string id, string what)
        {
            if (!bones.ContainsKey(id))
            {
                problems.Add(what + " refers to unknown bone " + id);
            }
        }

        private static string Optional(JsonElement element, string property)
        {
            return element.TryGetProperty(property, out var value) && value.ValueKind == JsonValueKind.String ? value.GetString() : null;
        }

        private static JsonDocument Read(string path)
        {
            return JsonDocument.Parse(File.ReadAllText(path));
        }
    }
}
