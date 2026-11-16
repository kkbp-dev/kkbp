using System;
using System.Collections.Generic;
using System.Globalization;

namespace KKBP.Exporter.Core
{
    /// <summary>
    /// Turns captured Passes into Export Bundle files. Each Pass's .glb, data file and textures are
    /// written as soon as it is captured; the shared JSON files and the Manifest are written by Finish.
    /// </summary>
    internal sealed class BundleWriter
    {
        public const string SchemaVersion = "1.2";

        private static readonly byte[] PngSignature = { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A };

        private readonly IBundleFiles files;
        private readonly string generator;

        private readonly IdAllocator meshIds = new IdAllocator("mesh");
        private readonly IdAllocator materialIds = new IdAllocator("mat");
        private readonly IdAllocator boneIds = new IdAllocator("bone");

        private readonly Dictionary<string, BoneRecord> bonesByKey = new Dictionary<string, BoneRecord>();
        private readonly List<BoneRecord> skeletonBones = new List<BoneRecord>();
        // Bones a mesh of any Pass weights, or physics uses: no helper may be at or above one.
        private readonly HashSet<string> neededBones = new HashSet<string>();
        private readonly HashSet<BoneRole> boneRoles = new HashSet<BoneRole>();

        private readonly HashSet<string> materialKeys = new HashSet<string>();
        private readonly HashSet<string> bodyMaterialKeys = new HashSet<string>();
        private readonly Dictionary<string, HashSet<string>> textureSlots = new Dictionary<string, HashSet<string>>();
        private readonly Dictionary<string, HashSet<string>> textureRoleSlots = new Dictionary<string, HashSet<string>>();
        private readonly JsonArray materials = new JsonArray();
        private readonly HashSet<MaterialRole> materialRoles = new HashSet<MaterialRole>();

        // Materials that carry a section: key -> the number of the Pass that captured them.
        private readonly Dictionary<string, int> sectionMaterialPass = new Dictionary<string, int>();
        private readonly HashSet<string> usedSectionMaterials = new HashSet<string>();
        private int currentPass;

        private readonly HashSet<string> meshKeys = new HashSet<string>();
        private readonly JsonArray expressions = new JsonArray();
        private readonly JsonArray effects = new JsonArray();
        private readonly HashSet<string> effectTargets = new HashSet<string>();
        private readonly JsonArray chains = new JsonArray();
        private readonly JsonArray colliders = new JsonArray();
        private readonly HashSet<string> colliderNames = new HashSet<string>();
        private readonly List<KeyValuePair<string, string>> colliderUses = new List<KeyValuePair<string, string>>();
        private readonly JsonArray passes = new JsonArray();
        private int textureCount;

        private sealed class BoneRecord
        {
            public string Key;
            public string Id;
            public string Name;
            public string ParentKey;
            public BoneRole? Role;
            public BoneGroup Group;
            public Vec3 Translation;
            public Quat Rotation;
            public Vec3 Scale;
            public Vec3 GameScale;
        }

        public BundleWriter(IBundleFiles files, string generator)
        {
            this.files = files;
            this.generator = generator;
        }

        public void WritePass(PassSink sink)
        {
            PassInfo pass = sink.Pass;
            string folder = pass.Kind == PassKind.Body ? "" : "outfits/" + pass.Outfit.Value.ToString("00", CultureInfo.InvariantCulture) + "/";
            string meshPath = folder + (pass.Kind == PassKind.Body ? "body.glb" : "outfit.glb");
            string dataPath = folder + (pass.Kind == PassKind.Body ? "body.json" : "outfit.json");
            object outfit = pass.Outfit.HasValue ? (object)pass.Outfit.Value : null;

            currentPass = passes.Count;
            var passBoneIndex = new Dictionary<string, int>();
            var glbBones = AddBones(sink.Bones, passBoneIndex);
            foreach (var material in sink.Materials)
            {
                AddMaterial(material, pass.Kind == PassKind.Body);
            }

            // Copies of one vertex become one, then the Body is mirrored; both before the meshes are converted (ADR 0047).
            var roles = new Dictionary<string, MaterialRole>();
            foreach (var material in sink.Materials)
            {
                if (material.Key != null && material.Role.HasValue)
                {
                    roles[material.Key] = material.Role.Value;
                }
            }
            Welds.Weld(sink.Meshes, roles);
            if (pass.Kind == PassKind.Body)
            {
                Symmetry.Mirror(sink.Meshes);
            }

            var glbMeshes = new List<GlbMesh>();
            var meshRecords = new JsonArray();
            var passMeshes = new Dictionary<string, MeshData>();
            var linked = new List<MorphData>();
            foreach (var mesh in sink.Meshes)
            {
                glbMeshes.Add(ConvertMesh(mesh, passBoneIndex, meshRecords, linked));
                passMeshes[mesh.Key] = mesh;
            }
            foreach (var morph in linked)
            {
                AddEffect(morph, passMeshes);
            }
            foreach (var section in sectionMaterialPass)
            {
                if (section.Value == currentPass && !usedSectionMaterials.Contains(section.Key))
                {
                    throw new ExportException("Material '" + section.Key + "' carries a material section but no mesh of its Pass uses it.");
                }
            }
            neededBones.UnionWith(AdapterKit.BoneRules.WeightedBones(sink.Meshes));
            neededBones.UnionWith(AdapterKit.BoneRules.PhysicsBones(sink.Chains, sink.Colliders));
            var bodyTextures = BodyTextures(sink);
            AddPhysics(sink, outfit);

            files.Write(meshPath, GlbWriter.Write(generator, glbBones, glbMeshes));
            var data = new JsonObject()
                .Add("kind", pass.Kind == PassKind.Body ? "body" : "outfit")
                .Add("outfit", outfit)
                .Add("meshes", meshRecords);
            if (bodyTextures.Count > 0)
            {
                data.Add("body_textures", bodyTextures);
            }
            AddExtensions(data, sink.Extensions);
            files.Write(dataPath, JsonWriter.ToUtf8(data, true));

            passes.Add(new JsonObject()
                .Add("kind", pass.Kind == PassKind.Body ? "body" : "outfit")
                .Add("outfit", outfit)
                .Add("mesh", meshPath)
                .Add("data", dataPath));
        }

        /// <summary>Writes the shared files, then the Manifest last.</summary>
        public void Finish(IGameAdapter adapter, CharacterInfo character, DateTime exportedAtUtc)
        {
            foreach (var use in colliderUses)
            {
                if (!colliderNames.Contains(use.Value))
                {
                    throw new ExportException(use.Key + " uses collider '" + use.Value + "', which no Pass captured.");
                }
            }
            var characterJson = new JsonObject().Add("name", character.Name);
            AddExtensions(characterJson, character.Extensions);
            files.Write("character.json", JsonWriter.ToUtf8(characterJson, true));
            files.Write("skeleton.json", JsonWriter.ToUtf8(new JsonObject().Add("bones", Skeleton()), true));
            files.Write("materials.json", JsonWriter.ToUtf8(new JsonObject().Add("materials", materials), true));
            files.Write("expressions.json", JsonWriter.ToUtf8(new JsonObject().Add("expressions", expressions).Add("effects", effects), true));
            files.Write("physics.json", JsonWriter.ToUtf8(new JsonObject().Add("chains", chains).Add("colliders", colliders), true));
            if (character.CardPng != null)
            {
                CheckPng(character.CardPng, "The Card");
                files.Write("card.png", character.CardPng);
            }

            ExportOptions o = adapter.Options;
            var options = new JsonObject()
                .Add("all_outfits", o.AllOutfits)
                .Add("all_variations", o.AllVariations)
                .Add("physics", o.Physics)
                .Add("enabled_shape_keys", o.EnabledShapeKeys)
                .Add("current_pose", o.CurrentPose);
            AddExtensions(options, o.Extensions);

            var manifest = new JsonObject()
                .Add("game", adapter.Game)
                .Add("schema_version", SchemaVersion)
                .Add("exporter", new JsonObject().Add("name", adapter.ExporterName).Add("version", adapter.ExporterVersion))
                .Add("exported_at", exportedAtUtc.ToString("yyyy-MM-dd'T'HH:mm:ss'Z'", CultureInfo.InvariantCulture))
                .Add("character_name", character.Name)
                .Add("card", character.CardPng != null ? "card.png" : null)
                .Add("options", options)
                .Add("passes", passes);
            files.Write("manifest.json", JsonWriter.ToUtf8(manifest, true));
        }

        private List<GlbBone> AddBones(List<BoneData> bones, Dictionary<string, int> passBoneIndex)
        {
            for (int i = 0; i < bones.Count; i++)
            {
                if (bones[i].Key == null || passBoneIndex.ContainsKey(bones[i].Key))
                {
                    throw new ExportException("Bone '" + bones[i].Name + "' has no key, or its key appears twice in one Pass.");
                }
                passBoneIndex.Add(bones[i].Key, i);
            }
            var result = new List<GlbBone>();
            foreach (var bone in bones)
            {
                int parent = -1;
                if (bone.ParentKey != null && !passBoneIndex.TryGetValue(bone.ParentKey, out parent))
                {
                    throw new ExportException("Bone '" + bone.Name + "' has a parent that isn't in the same Pass.");
                }
                var record = Record(bone, bones, passBoneIndex, 0);
                result.Add(new GlbBone { Id = record.Id, Parent = parent, Translation = record.Translation, Rotation = record.Rotation, Scale = record.Scale });
            }
            return result;
        }

        /// <summary>Records a bone, recording its parents first so that Ids follow the hierarchy.</summary>
        private BoneRecord Record(BoneData bone, List<BoneData> passBones, Dictionary<string, int> passBoneIndex, int depth)
        {
            if (depth > passBones.Count)
            {
                throw new ExportException("Bone '" + bone.Name + "' is in a parent cycle.");
            }
            if (bone.ParentKey != null && !bonesByKey.ContainsKey(bone.ParentKey))
            {
                Record(passBones[passBoneIndex[bone.ParentKey]], passBones, passBoneIndex, depth + 1);
            }
            var t = UnitySpace.Position(bone.Position);
            var r = Normalize(UnitySpace.Rotation(bone.Rotation));
            var s = UnitySpace.Scale(bone.Scale);
            var gameScale = UnitySpace.Scale(bone.GameScale);
            if (!(gameScale.X > 0 && gameScale.Y > 0 && gameScale.Z > 0) || float.IsInfinity(gameScale.X + gameScale.Y + gameScale.Z))
            {
                throw new ExportException("Bone '" + bone.Name + "' has a game scale that isn't above 0 on every axis.");
            }
            BoneRecord record;
            if (bonesByKey.TryGetValue(bone.Key, out record))
            {
                // All Passes share bone Ids, so a bone seen again must have the same rest pose.
                if (record.ParentKey != bone.ParentKey || !Near(record.Translation, t) || !Near(record.Rotation, r) || !Near(record.Scale, s))
                {
                    throw new ExportException("Bone '" + bone.Name + "' has a different parent or rest pose in two Passes.");
                }
                return record;
            }
            if (bone.Role.HasValue && !boneRoles.Add(bone.Role.Value))
            {
                throw new ExportException("Bone Role " + ContractNames.Of(bone.Role.Value) + " is on two bones.");
            }
            record = new BoneRecord
            {
                Key = bone.Key, Id = boneIds.Get(bone.Key, bone.Name), Name = bone.Name ?? "", ParentKey = bone.ParentKey,
                Role = bone.Role, Group = bone.Group, Translation = t, Rotation = r, Scale = s, GameScale = gameScale,
            };
            bonesByKey.Add(bone.Key, record);
            skeletonBones.Add(record);
            return record;
        }

        private BoneRecord Parent(BoneRecord bone)
        {
            return bone.ParentKey != null ? bonesByKey[bone.ParentKey] : null;
        }

        /// <summary>
        /// skeleton.json's bones, in the order they were first seen. A helper is safe to delete, so a bone
        /// that a mesh of any Pass weights or physics uses, or that has one below it, isn't a helper,
        /// whatever rule made it one (BoneRules.NeededHelperGroup).
        /// </summary>
        private JsonArray Skeleton()
        {
            // For each bone, whether each needed bone at or below it is at or below the face root.
            var below = new Dictionary<string, List<bool>>();
            foreach (var bone in skeletonBones)
            {
                if (!neededBones.Contains(bone.Key))
                {
                    continue;
                }
                bool underFace = false;
                for (BoneRecord b = bone; b != null && !underFace; b = Parent(b))
                {
                    underFace = b.Role == BoneRole.FaceRoot;
                }
                for (BoneRecord b = bone; b != null; b = Parent(b))
                {
                    List<bool> found;
                    if (!below.TryGetValue(b.Key, out found))
                    {
                        below[b.Key] = found = new List<bool>();
                    }
                    found.Add(underFace);
                }
            }
            var result = new JsonArray();
            foreach (var bone in skeletonBones)
            {
                BoneGroup group = bone.Group;
                List<bool> needed;
                if (group == BoneGroup.Helper && below.TryGetValue(bone.Key, out needed))
                {
                    group = AdapterKit.BoneRules.NeededHelperGroup(needed);
                }
                var json = new JsonObject()
                    .Add("id", bone.Id)
                    .Add("name", bone.Name)
                    .Add("parent", bone.ParentKey != null ? bonesByKey[bone.ParentKey].Id : null);
                if (bone.Role.HasValue)
                {
                    json.Add("role", ContractNames.Of(bone.Role.Value));
                }
                json.Add("group", ContractNames.Of(group))
                    .Add("translation", Vec(bone.Translation))
                    .Add("rotation", Vec(bone.Rotation))
                    .Add("scale", Vec(bone.Scale));
                if (!Near(bone.GameScale, Vec3.One))
                {
                    json.Add("game_scale", Vec(bone.GameScale));
                }
                result.Add(json);
            }
            return result;
        }


        private void AddMaterial(MaterialData material, bool bodyPass)
        {
            if (material.Key == null)
            {
                throw new ExportException("Material '" + material.Name + "' has no key.");
            }
            if (!materialKeys.Add(material.Key))
            {
                return; // Already written by an earlier Pass.
            }
            if (bodyPass)
            {
                bodyMaterialKeys.Add(material.Key);
            }
            string id = materialIds.Get(material.Key, material.Name);
            var json = new JsonObject()
                .Add("id", id)
                .Add("name", material.Name ?? "")
                .Add("shader", material.Shader ?? "");
            if (material.Role.HasValue)
            {
                if (ContractNames.IsUnique(material.Role.Value) && !materialRoles.Add(material.Role.Value))
                {
                    throw new ExportException("Material Role " + ContractNames.Of(material.Role.Value) + " is on two materials.");
                }
                json.Add("role", ContractNames.Of(material.Role.Value));
            }
            json.Add("blend_mode", ContractNames.Of(material.BlendMode));
            AddShaderValues(json, material.Colors, material.Floats, material.Vectors);
            string owner = "material '" + material.Name + "'";
            json.Add("textures", Textures(material.Textures, owner, textureSlots[id] = new HashSet<string>(), textureRoleSlots[id] = new HashSet<string>()));
            // Sections come after the material's own textures, so their files follow in write order.
            AddExtensions(json, Extensions(material, owner));
            materials.Add(json);
        }

        /// <summary>Adds colors, floats and vectors, each keyed by Raw Property in ordinal order.</summary>
        private static void AddShaderValues(JsonObject json, Dictionary<string, Color> colorValues, Dictionary<string, float> floatValues, Dictionary<string, Vec4> vectorValues)
        {
            var colors = new JsonObject();
            foreach (string key in SortedKeys(colorValues.Keys))
            {
                var c = colorValues[key];
                colors.Add(key, new JsonArray { c.R, c.G, c.B, c.A });
            }
            var floats = new JsonObject();
            foreach (string key in SortedKeys(floatValues.Keys))
            {
                floats.Add(key, floatValues[key]);
            }
            var vectors = new JsonObject();
            foreach (string key in SortedKeys(vectorValues.Keys))
            {
                var v = vectorValues[key];
                vectors.Add(key, new JsonArray { v.X, v.Y, v.Z, v.W });
            }
            json.Add("colors", colors).Add("floats", floats).Add("vectors", vectors);
        }

        /// <summary>Writes a texture list, checking that its slots, and its unique Roles, appear once each.</summary>
        private JsonArray Textures(List<TextureData> textures, string owner, HashSet<string> slots, HashSet<string> roles)
        {
            var result = new JsonArray();
            foreach (var texture in textures)
            {
                if (texture == null)
                {
                    throw new ExportException("A texture on " + owner + " is missing.");
                }
                string label = "Texture " + texture.Raw + " on " + owner;
                if (!slots.Add(Slot(texture, label)))
                {
                    throw new ExportException(Capitalise(owner) + " has two textures for " + texture.Raw + " with the same Variant and pattern.");
                }
                string role = RoleSlot(texture);
                if (role != null && !roles.Add(role))
                {
                    throw new ExportException(Capitalise(owner) + " has two textures with Role " + ContractNames.Of(texture.Role.Value) + ".");
                }
                result.Add(WriteTexture(texture, label));
            }
            CheckBakesWithoutEyeshadow(textures, owner);
            return result;
        }

        /// <summary>A bake without eyeshadow comes as a light and dark pair, beside the light and dark bakes of the same texture.</summary>
        private static void CheckBakesWithoutEyeshadow(List<TextureData> textures, string owner)
        {
            var all = new[] { TextureVariant.Light, TextureVariant.Dark, TextureVariant.LightNoEyeshadow, TextureVariant.DarkNoEyeshadow };
            foreach (var texture in textures)
            {
                if (texture.Variant != TextureVariant.LightNoEyeshadow && texture.Variant != TextureVariant.DarkNoEyeshadow)
                {
                    continue;
                }
                foreach (var variant in all)
                {
                    if (!textures.Exists(t => t.Raw == texture.Raw && t.Pattern == texture.Pattern && t.Variant == variant))
                    {
                        throw new ExportException(Capitalise(owner) + " has a bake of " + texture.Raw + " without eyeshadow but no " + ContractNames.Of(variant) + " Variant of it.");
                    }
                }
            }
        }

        /// <summary>
        /// The material's Game Extensions with its sections merged in: the adapter's own members first,
        /// then each section in order, as extensions.&lt;Extension&gt;.&lt;Field&gt;. The adapter's objects aren't changed.
        /// </summary>
        private JsonObject Extensions(MaterialData material, string owner)
        {
            if (material.Sections == null || material.Sections.Count == 0)
            {
                return material.Extensions;
            }
            var result = new JsonObject();
            var byKey = new Dictionary<string, JsonObject>();
            if (material.Extensions != null)
            {
                foreach (var member in material.Extensions.Members)
                {
                    var inner = member.Value as JsonObject;
                    if (inner == null)
                    {
                        result.Add(member.Key, member.Value);
                        continue;
                    }
                    var copy = new JsonObject();
                    foreach (var m in inner.Members)
                    {
                        copy.Add(m.Key, m.Value);
                    }
                    byKey.Add(member.Key, copy);
                    result.Add(member.Key, copy);
                }
            }
            foreach (var section in material.Sections)
            {
                if (section == null || string.IsNullOrEmpty(section.Extension) || string.IsNullOrEmpty(section.Field))
                {
                    throw new ExportException("A material section on " + owner + " has no extension key or field name.");
                }
                string path = section.Extension + "." + section.Field;
                JsonObject target;
                if (!byKey.TryGetValue(section.Extension, out target))
                {
                    object existing;
                    if (result.TryGet(section.Extension, out existing))
                    {
                        throw new ExportException("Material section " + path + " on " + owner + " goes in an extension that isn't an object.");
                    }
                    target = new JsonObject();
                    byKey.Add(section.Extension, target);
                    result.Add(section.Extension, target);
                }
                object clash;
                if (target.TryGet(section.Field, out clash))
                {
                    throw new ExportException(Capitalise(owner) + " has " + path + " twice.");
                }
                var json = new JsonObject().Add("shader", section.Shader ?? "");
                AddShaderValues(json, section.Colors, section.Floats, section.Vectors);
                json.Add("textures", Textures(section.Textures, path + " on " + owner, new HashSet<string>(), new HashSet<string>()));
                target.Add(section.Field, json);
            }
            sectionMaterialPass[material.Key] = currentPass;
            return result;
        }

        private static string Capitalise(string s)
        {
            return s.Length == 0 ? s : char.ToUpperInvariant(s[0]) + s.Substring(1);
        }

        /// <summary>The textures an Outfit Pass puts on body materials. Their slots must be free on the material.</summary>
        private JsonArray BodyTextures(PassSink sink)
        {
            var result = new JsonArray();
            if (sink.BodyTextures.Count == 0)
            {
                return result;
            }
            if (sink.Pass.Kind == PassKind.Body)
            {
                throw new ExportException("The Body Pass has body textures; its materials hold their own textures.");
            }
            var slots = new HashSet<string>();
            var roles = new HashSet<string>();
            foreach (var body in sink.BodyTextures)
            {
                string id;
                if (body == null || body.Texture == null || body.MaterialKey == null
                    || !bodyMaterialKeys.Contains(body.MaterialKey) || !materialIds.TryFind(body.MaterialKey, out id))
                {
                    throw new ExportException("A body texture is missing, or names a material the Body Pass didn't capture.");
                }
                string label = "Body texture " + body.Texture.Raw + " on material " + id;
                string slot = Slot(body.Texture, label);
                if (textureSlots[id].Contains(slot) || !slots.Add(id + "\n" + slot))
                {
                    throw new ExportException(label + " fills a slot the material already has, or appears twice.");
                }
                string role = RoleSlot(body.Texture);
                if (role != null && (textureRoleSlots[id].Contains(role) || !roles.Add(id + "\n" + role)))
                {
                    throw new ExportException(label + " repeats Role " + ContractNames.Of(body.Texture.Role.Value) + " on its material.");
                }
                result.Add(new JsonObject().Add("material", id).Add("texture", WriteTexture(body.Texture, label)));
            }
            return result;
        }

        /// <summary>The texture's (Raw Property, Variant, pattern), which is unique within a material.</summary>
        private static string Slot(TextureData texture, string label)
        {
            if (string.IsNullOrEmpty(texture.Raw))
            {
                throw new ExportException(label + " has no Raw Property.");
            }
            string variant = texture.Variant.HasValue ? ContractNames.Of(texture.Variant.Value) : "";
            return texture.Raw + "\n" + variant + "\n" + (texture.Pattern ?? "");
        }

        /// <summary>The texture's (Role, Variant, pattern) if its Role is unique, otherwise null.</summary>
        private static string RoleSlot(TextureData texture)
        {
            if (!texture.Role.HasValue || !ContractNames.IsUnique(texture.Role.Value))
            {
                return null;
            }
            string variant = texture.Variant.HasValue ? ContractNames.Of(texture.Variant.Value) : "";
            return texture.Role.Value + "\n" + variant + "\n" + (texture.Pattern ?? "");
        }

        private JsonObject WriteTexture(TextureData texture, string label)
        {
            CheckPng(texture.Png, label);
            textureCount++;
            string file = "textures/" + textureCount.ToString("0000", CultureInfo.InvariantCulture) + ".png";
            files.Write(file, texture.Png);

            var json = new JsonObject();
            if (texture.Role.HasValue)
            {
                json.Add("role", ContractNames.Of(texture.Role.Value));
            }
            json.Add("raw", texture.Raw);
            if (texture.Variant.HasValue)
            {
                json.Add("variant", ContractNames.Of(texture.Variant.Value));
            }
            if (texture.Pattern != null)
            {
                json.Add("pattern", texture.Pattern);
            }
            return json.Add("file", file)
                .Add("offset", new JsonArray { texture.Offset.X, texture.Offset.Y })
                .Add("scale", new JsonArray { texture.Scale.X, texture.Scale.Y });
        }

        /// <summary>
        /// Writes what an expression shows, hides and changes as its one entry in "effects", once its Pass's
        /// meshes have Ids. Only one of the expression's shape keys may carry them.
        /// </summary>
        private void AddEffect(MorphData morph, Dictionary<string, MeshData> passMeshes)
        {
            string label = "Expression '" + morph.TargetName + "'";
            if (!effectTargets.Add(morph.TargetName))
            {
                throw new ExportException(label + " has what it shows, hides or changes given on more than one shape key.");
            }
            var record = new JsonObject().Add("target", morph.TargetName);
            if (morph.ShowsMeshKeys.Count > 0)
            {
                var shows = PassMeshIds(morph.ShowsMeshKeys, passMeshes, label);
                foreach (string key in morph.ShowsMeshKeys)
                {
                    if (!passMeshes[key].Morphs.Exists(m => m.GameName == null && (m.Category == ExpressionCategory.Tears || m.Category == ExpressionCategory.Gag)))
                    {
                        throw new ExportException(label + " shows mesh '" + passMeshes[key].Name + "', which has no showing key.");
                    }
                }
                record.Add("shows", shows);
            }
            if (morph.HidesMeshKeys.Count > 0)
            {
                record.Add("hides", PassMeshIds(morph.HidesMeshKeys, passMeshes, label));
            }
            if (morph.MaterialChanges.Count > 0)
            {
                var changes = new JsonArray();
                var changed = new HashSet<string>();
                foreach (var change in morph.MaterialChanges)
                {
                    string id;
                    if (change == null || change.MaterialKey == null || !materialIds.TryFind(change.MaterialKey, out id) || !changed.Add(id))
                    {
                        throw new ExportException(label + " changes a material that wasn't captured, or one material twice.");
                    }
                    if (change.Textures.Count + change.Floats.Count + change.Vectors.Count == 0)
                    {
                        throw new ExportException(label + " has a change to material " + id + " that sets nothing.");
                    }
                    var textures = new JsonArray();
                    foreach (string raw in SortedKeys(change.Textures.Keys))
                    {
                        string pattern = change.Textures[raw];
                        if (pattern == null || !HasPattern(id, raw, pattern))
                        {
                            throw new ExportException(label + " sets " + raw + " on material " + id + " to a pattern the material doesn't have.");
                        }
                        textures.Add(new JsonObject().Add("raw", raw).Add("pattern", pattern));
                    }
                    var floats = new JsonObject();
                    foreach (string key in SortedKeys(change.Floats.Keys))
                    {
                        floats.Add(key, change.Floats[key]);
                    }
                    var vectors = new JsonObject();
                    foreach (string key in SortedKeys(change.Vectors.Keys))
                    {
                        var v = change.Vectors[key];
                        vectors.Add(key, new JsonArray { v.X, v.Y, v.Z, v.W });
                    }
                    changes.Add(new JsonObject().Add("material", id).Add("textures", textures).Add("floats", floats).Add("vectors", vectors));
                }
                record.Add("material_changes", changes);
            }
            effects.Add(record);
        }

        private JsonArray PassMeshIds(List<string> keys, Dictionary<string, MeshData> passMeshes, string label)
        {
            var ids = new JsonArray();
            var seen = new HashSet<string>();
            foreach (string key in keys)
            {
                string id;
                if (key == null || !passMeshes.ContainsKey(key) || !seen.Add(key) || !meshIds.TryFind(key, out id))
                {
                    throw new ExportException(label + " names a mesh that isn't in its Pass, or names one twice.");
                }
                ids.Add(id);
            }
            return ids;
        }

        private bool HasPattern(string materialId, string raw, string pattern)
        {
            foreach (string slot in textureSlots[materialId])
            {
                string[] parts = slot.Split('\n');
                if (parts[0] == raw && parts[2] == pattern)
                {
                    return true;
                }
            }
            return false;
        }

        private GlbMesh ConvertMesh(MeshData mesh, Dictionary<string, int> passBoneIndex, JsonArray meshRecords,
            List<MorphData> linked)
        {
            string label = "Mesh '" + mesh.Name + "'";
            if (mesh.Key == null || !meshKeys.Add(mesh.Key))
            {
                throw new ExportException(label + " has no key, or its key was already used.");
            }
            if (mesh.Positions == null || mesh.Positions.Length == 0)
            {
                throw new ExportException(label + " has no vertices.");
            }
            int count = mesh.Positions.Length;
            CheckLength(label, "normals", mesh.Normals, count);
            CheckLength(label, "tangents", mesh.Tangents, count);
            CheckLength(label, "colours", mesh.Colors, count);
            foreach (var uvs in mesh.UvSets)
            {
                CheckLength(label, "UVs", uvs, count);
            }
            if (mesh.SubMeshes.Count == 0)
            {
                throw new ExportException(label + " has no sub-meshes.");
            }

            string id = meshIds.Get(mesh.Key, mesh.Name);
            // glTF needs unit normals and tangents; a zero-length one from the game is rebuilt (MeshVectors).
            var triangles = mesh.SubMeshes.ConvertAll(sub => sub.Indices);
            var normals = mesh.Normals == null ? null : MeshVectors.Normals(mesh.Normals, triangles);
            var tangents = mesh.Tangents == null ? null : MeshVectors.Tangents(mesh.Tangents, normals, triangles);
            var glb = new GlbMesh
            {
                Id = id,
                Positions = Map(mesh.Positions, UnitySpace.Position),
                Normals = normals == null ? null : Map(normals, UnitySpace.Direction),
                Tangents = tangents == null ? null : Map(tangents, UnitySpace.Tangent),
                Colors = mesh.Colors,
                UvSets = new List<Vec2[]>(),
                Primitives = new List<int[]>(),
                PrimitiveMaterials = new List<string>(),
                Morphs = new List<GlbMorph>(),
            };
            foreach (var uvs in mesh.UvSets)
            {
                glb.UvSets.Add(Map(uvs, UnitySpace.Uv));
            }
            Skin(mesh, passBoneIndex, glb, label);

            var materialList = new JsonArray();
            foreach (var sub in mesh.SubMeshes)
            {
                string materialId;
                int sectionPass;
                if (sub.MaterialKey != null && sectionMaterialPass.TryGetValue(sub.MaterialKey, out sectionPass))
                {
                    if (sectionPass != currentPass)
                    {
                        throw new ExportException(label + " uses a material with a material section that another Pass captured.");
                    }
                    usedSectionMaterials.Add(sub.MaterialKey);
                }
                if (sub.MaterialKey == null || !materialIds.TryFind(sub.MaterialKey, out materialId))
                {
                    throw new ExportException(label + " uses a material that wasn't captured.");
                }
                glb.Primitives.Add(UnitySpace.Triangles(sub.Indices));
                glb.PrimitiveMaterials.Add(materialId);
                materialList.Add(materialId);
            }

            var targets = new HashSet<string>();
            foreach (var morph in mesh.Morphs)
            {
                string target = morph.TargetName;
                if (string.IsNullOrEmpty(target))
                {
                    throw new ExportException(label + " has a shape key with neither an Expression Name nor a game name.");
                }
                if (!targets.Add(target))
                {
                    throw new ExportException(label + " has two shape keys named '" + target + "'.");
                }
                if (morph.ExpressionName != null && ContractNames.CategoryOf(morph.ExpressionName) != morph.Category)
                {
                    throw new ExportException("Expression '" + morph.ExpressionName + "' doesn't belong to category " + ContractNames.Of(morph.Category) + ".");
                }
                CheckLength(label, "shape key '" + target + "' positions", morph.PositionDeltas, count);
                if (morph.PositionDeltas == null)
                {
                    throw new ExportException(label + " shape key '" + target + "' has no positions.");
                }
                CheckLength(label, "shape key '" + target + "' normals", morph.NormalDeltas, count);
                glb.Morphs.Add(new GlbMorph
                {
                    Name = target,
                    PositionDeltas = Map(morph.PositionDeltas, UnitySpace.Direction),
                    NormalDeltas = morph.NormalDeltas == null ? null : Map(morph.NormalDeltas, UnitySpace.Direction),
                });
                var record = new JsonObject()
                    .Add("mesh", id)
                    .Add("target", target)
                    .Add("category", ContractNames.Of(morph.Category))
                    .Add("name", morph.ExpressionName)
                    .Add("game_name", morph.GameName);
                AddExtensions(record, morph.Extensions);
                expressions.Add(record);
                if (morph.ShowsMeshKeys.Count + morph.HidesMeshKeys.Count + morph.MaterialChanges.Count > 0)
                {
                    linked.Add(morph);
                }
            }

            meshRecords.Add(new JsonObject()
                .Add("id", id)
                .Add("name", mesh.Name ?? "")
                .Add("materials", materialList)
                .Add("alternate", mesh.Alternate));
            return glb;
        }

        /// <summary>Merges, sorts and normalises each vertex's weights, then packs them into sets of four.</summary>
        private static void Skin(MeshData mesh, Dictionary<string, int> passBoneIndex, GlbMesh glb, string label)
        {
            int count = mesh.Positions.Length;
            int slots = mesh.InfluencesPerVertex;
            if (mesh.BoneKeys == null || mesh.BoneKeys.Length == 0 || slots <= 0
                || mesh.Joints == null || mesh.Weights == null || mesh.Joints.Length != count * slots || mesh.Weights.Length != count * slots)
            {
                throw new ExportException(label + " has missing or mismatched skin weights. Every mesh must be skinned.");
            }
            var boneIndex = new int[mesh.BoneKeys.Length];
            for (int i = 0; i < boneIndex.Length; i++)
            {
                if (!passBoneIndex.TryGetValue(mesh.BoneKeys[i], out boneIndex[i]))
                {
                    throw new ExportException(label + " is weighted to a bone that isn't in its Pass.");
                }
                if (boneIndex[i] > ushort.MaxValue)
                {
                    throw new ExportException("A Pass has more than 65536 bones.");
                }
            }

            var perVertex = new List<KeyValuePair<int, float>>[count];
            int widest = 1;
            for (int v = 0; v < count; v++)
            {
                var merged = new Dictionary<int, float>();
                float total = 0;
                for (int s = 0; s < slots; s++)
                {
                    float w = mesh.Weights[v * slots + s];
                    if (w <= 0)
                    {
                        continue;
                    }
                    int j = mesh.Joints[v * slots + s];
                    if (j < 0 || j >= boneIndex.Length)
                    {
                        throw new ExportException(label + " has a joint index outside its bone list.");
                    }
                    int joint = boneIndex[j];
                    float existing;
                    merged.TryGetValue(joint, out existing);
                    merged[joint] = existing + w;
                    total += w;
                }
                if (total <= 0)
                {
                    throw new ExportException(label + " has a vertex with no skin weight.");
                }
                // Normalise, drop weights too small to survive it, and give the rounding remainder to the
                // largest, so no joint is written with a zero weight.
                var list = new List<KeyValuePair<int, float>>();
                float sum = 0;
                foreach (var pair in merged)
                {
                    float w = pair.Value / total;
                    if (w > 0)
                    {
                        list.Add(new KeyValuePair<int, float>(pair.Key, w));
                        sum += w;
                    }
                }
                list.Sort((a, b) => a.Value != b.Value ? b.Value.CompareTo(a.Value) : a.Key.CompareTo(b.Key));
                list[0] = new KeyValuePair<int, float>(list[0].Key, list[0].Value + (1 - sum));
                perVertex[v] = list;
                widest = Math.Max(widest, list.Count);
            }

            int sets = (widest + 3) / 4;
            glb.JointSets = new List<ushort[]>();
            glb.WeightSets = new List<float[]>();
            for (int set = 0; set < sets; set++)
            {
                var joints = new ushort[count * 4];
                var weights = new float[count * 4];
                for (int v = 0; v < count; v++)
                {
                    for (int k = 0; k < 4; k++)
                    {
                        int i = set * 4 + k;
                        if (i < perVertex[v].Count)
                        {
                            joints[v * 4 + k] = (ushort)perVertex[v][i].Key;
                            weights[v * 4 + k] = perVertex[v][i].Value;
                        }
                    }
                }
                glb.JointSets.Add(joints);
                glb.WeightSets.Add(weights);
            }
        }

        private void AddPhysics(PassSink sink, object outfit)
        {
            foreach (var c in sink.Colliders)
            {
                if (string.IsNullOrEmpty(c.Name) || !colliderNames.Add(c.Name))
                {
                    throw new ExportException("Collider '" + c.Name + "' has no name, or its name was already used.");
                }
                colliders.Add(new JsonObject()
                    .Add("name", c.Name)
                    .Add("outfit", outfit)
                    .Add("bone", BoneId(c.BoneKey, "Collider '" + c.Name + "'"))
                    .Add("center", Vec(UnitySpace.Position(c.Center)))
                    .Add("rotation", Vec(Normalize(UnitySpace.Rotation(c.Rotation))))
                    .Add("radius", c.Radius)
                    .Add("height", c.Height)
                    .Add("direction", ContractNames.Of(c.Direction))
                    .Add("bound", ContractNames.Of(c.Bound)));
            }
            foreach (var chain in sink.Chains)
            {
                string label = "Physics chain at '" + chain.RootKey + "'";
                var chainColliders = new JsonArray();
                foreach (string name in chain.Colliders)
                {
                    // A chain may use colliders from another Pass, such as the body's; Finish checks them.
                    colliderUses.Add(new KeyValuePair<string, string>(label, name));
                    chainColliders.Add(name);
                }
                var exclusions = new JsonArray();
                foreach (string key in chain.ExclusionKeys)
                {
                    exclusions.Add(BoneId(key, label));
                }
                var particles = new JsonArray();
                foreach (var p in chain.Particles)
                {
                    particles.Add(new JsonObject()
                        .Add("bone", BoneId(p.BoneKey, label))
                        .Add("damping", p.Damping)
                        .Add("elasticity", p.Elasticity)
                        .Add("stiffness", p.Stiffness)
                        .Add("inert", p.Inert)
                        .Add("radius", p.Radius));
                }
                if (particles.Count == 0)
                {
                    throw new ExportException(label + " has no particles.");
                }
                chains.Add(new JsonObject()
                    .Add("root", BoneId(chain.RootKey, label))
                    .Add("outfit", outfit)
                    .Add("gravity", Vec(UnitySpace.Direction(chain.Gravity)))
                    .Add("force", Vec(UnitySpace.Direction(chain.Force)))
                    .Add("end_length", chain.EndLength)
                    .Add("end_offset", Vec(UnitySpace.Direction(chain.EndOffset)))
                    .Add("weight", chain.Weight)
                    .Add("colliders", chainColliders)
                    .Add("exclusions", exclusions)
                    .Add("particles", particles));
            }
        }

        private string BoneId(string key, string label)
        {
            BoneRecord record;
            if (key == null || !bonesByKey.TryGetValue(key, out record))
            {
                throw new ExportException(label + " refers to a bone that wasn't captured.");
            }
            return record.Id;
        }

        private static void AddExtensions(JsonObject target, JsonObject extensions)
        {
            if (extensions != null && extensions.Count > 0)
            {
                target.Add("extensions", extensions);
            }
        }

        private static void CheckPng(byte[] png, string label)
        {
            if (png == null || png.Length < PngSignature.Length)
            {
                throw new ExportException(label + " has no PNG data.");
            }
            for (int i = 0; i < PngSignature.Length; i++)
            {
                if (png[i] != PngSignature[i])
                {
                    throw new ExportException(label + " isn't PNG data.");
                }
            }
        }

        private static void CheckLength<T>(string label, string what, T[] values, int count)
        {
            if (values != null && values.Length != count)
            {
                throw new ExportException(label + " has " + values.Length + " " + what + " for " + count + " vertices.");
            }
        }

        private static TOut[] Map<TIn, TOut>(TIn[] values, Func<TIn, TOut> f)
        {
            var result = new TOut[values.Length];
            for (int i = 0; i < values.Length; i++)
            {
                result[i] = f(values[i]);
            }
            return result;
        }

        /// <summary>glTF needs unit quaternions; a game's float rotations are often slightly off.</summary>
        private static Quat Normalize(Quat q)
        {
            double length = Math.Sqrt((double)q.X * q.X + (double)q.Y * q.Y + (double)q.Z * q.Z + (double)q.W * q.W);
            if (length == 0)
            {
                throw new ExportException("A rotation is all zeros.");
            }
            return new Quat((float)(q.X / length), (float)(q.Y / length), (float)(q.Z / length), (float)(q.W / length));
        }

        private static List<string> SortedKeys(IEnumerable<string> keys)
        {
            var list = new List<string>(keys);
            list.Sort(string.CompareOrdinal);
            return list;
        }

        private static bool Near(Vec3 a, Vec3 b)
        {
            return Math.Abs(a.X - b.X) < 1e-5f && Math.Abs(a.Y - b.Y) < 1e-5f && Math.Abs(a.Z - b.Z) < 1e-5f;
        }

        private static bool Near(Quat a, Quat b)
        {
            return Math.Abs(a.X - b.X) < 1e-5f && Math.Abs(a.Y - b.Y) < 1e-5f && Math.Abs(a.Z - b.Z) < 1e-5f && Math.Abs(a.W - b.W) < 1e-5f;
        }

        private static JsonArray Vec(Vec3 v)
        {
            return new JsonArray { v.X, v.Y, v.Z };
        }

        private static JsonArray Vec(Quat q)
        {
            return new JsonArray { q.X, q.Y, q.Z, q.W };
        }
    }
}
