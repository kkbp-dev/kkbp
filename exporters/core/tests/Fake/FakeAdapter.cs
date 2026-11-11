using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using KKBP.Exporter.Core.Tests.Support;

namespace KKBP.Exporter.Core.Tests.Fake
{
    /// <summary>
    /// A Game Adapter over an in-memory Character: a small skeleton, a body with expression shape
    /// keys, and two Outfits. It covers the cases the Core must handle: shared bones across Passes,
    /// names that simplify to nothing, clashing names, rigid and alternate meshes, more than four
    /// weights per vertex, textures with Variants and patterns, expressions that show and hide meshes and
    /// change materials, Outfit textures on body materials, physics across Passes, and nested waits.
    /// </summary>
    public sealed class FakeAdapter : IGameAdapter
    {
        /// <summary>A valid 1x1 PNG. The Core never decodes textures, so one image serves for all.</summary>
        public static readonly byte[] Png = Convert.FromBase64String("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==");

        private readonly ExpressionTable table;

        /// <summary>When set, capturing this Outfit throws after its first wait.</summary>
        public int? FailInOutfit;

        public FakeAdapter()
        {
            table = ExpressionTable.Parse(File.ReadAllText(Repo.Path("contract/expressions/kk.json")));
            Character = new CharacterInfo
            {
                Name = "春野 テスト/Chika",
                CardPng = Png,
            };
            Options = new ExportOptions { AllOutfits = true };
        }

        public string Game => "KK";
        public string ExporterName => "KKBP Fake Exporter";
        public string ExporterVersion => "0.0.0-test";
        public ExportOptions Options { get; }
        public CharacterInfo Character { get; }

        public IList<PassInfo> Passes()
        {
            return new[] { PassInfo.Body(), PassInfo.ForOutfit(0), PassInfo.ForOutfit(1) };
        }

        public IEnumerator Capture(PassInfo pass, PassSink sink)
        {
            if (pass.Kind == PassKind.Body)
            {
                yield return null;
                yield return Wait("body", 2);
                CaptureBody(sink);
            }
            else
            {
                yield return "switch to outfit " + pass.Outfit;
                if (FailInOutfit == pass.Outfit)
                {
                    throw new InvalidOperationException("The fake game crashed while switching Outfits.");
                }
                yield return Wait("outfit " + pass.Outfit, 1);
                if (pass.Outfit == 0)
                {
                    CaptureOutfit0(sink);
                }
                else
                {
                    CaptureOutfit1(sink);
                }
            }
        }

        /// <summary>The values the Core should pass on for the given Passes, in order.</summary>
        public static List<object> ExpectedYields()
        {
            return new List<object>
            {
                null, "body frame 1", "body frame 2",
                "switch to outfit 0", "outfit 0 frame 1",
                "switch to outfit 1", "outfit 1 frame 1",
            };
        }

        private static IEnumerator Wait(string what, int frames)
        {
            for (int i = 1; i <= frames; i++)
            {
                yield return what + " frame " + i;
            }
        }

        // Skeleton -------------------------------------------------------------------------------------

        private static BoneData Bone(string key, string name, string parent, Vec3 position, BoneGroup group, BoneRole? role = null)
        {
            return new BoneData { Key = key, Name = name, ParentKey = parent, Position = position, Group = group, Role = role };
        }

        private static Quat AxisAngle(float x, float y, float z, float degrees)
        {
            float half = (float)(degrees * Math.PI / 360);
            float s = (float)Math.Sin(half);
            return new Quat(x * s, y * s, z * s, (float)Math.Cos(half));
        }

        /// <summary>The body skeleton. Every Pass repeats it with the same keys and rest pose.</summary>
        private static List<BoneData> BodyBones()
        {
            var head = Bone("/BodyTop/root/hips/spine/head", "cf_j_head", "/BodyTop/root/hips/spine", new Vec3(0, 0.5f, 0), BoneGroup.Deform, BoneRole.Head);
            head.Rotation = AxisAngle(0, 1, 0, 90);
            var spine = Bone("/BodyTop/root/hips/spine", "cf_j_spine01", "/BodyTop/root/hips", new Vec3(0, 0.1f, 0.02f), BoneGroup.Deform, BoneRole.Spine);
            spine.Rotation = AxisAngle(1, 0, 0, 10);
            var thigh = Bone("/BodyTop/root/hips/thigh_L", "cf_j_thigh00_L", "/BodyTop/root/hips", new Vec3(0.1f, -0.05f, 0), BoneGroup.Deform, BoneRole.LeftUpperLeg);
            thigh.Scale = new Vec3(1, 1.2f, 1);
            thigh.GameScale = new Vec3(0.9f, 1.1f, 0.9f);
            // Slightly longer than a unit quaternion, as game rotations often are: the Core must normalise it.
            thigh.Rotation = new Quat(0, 0, 0, 1.0000002f);
            return new List<BoneData>
            {
                Bone("/BodyTop", "BodyTop", null, Vec3.Zero, BoneGroup.Helper),
                // Listed before its parent on purpose: the Core must still record parents first.
                head,
                Bone("/BodyTop/root", "cf_j_root", "/BodyTop", Vec3.Zero, BoneGroup.Deform, BoneRole.BodyRoot),
                Bone("/BodyTop/root/hips", "cf_j_hips", "/BodyTop/root", new Vec3(0, 0.9f, 0), BoneGroup.Deform, BoneRole.Hips),
                spine,
                thigh,
                // Simplifies to nothing, so its Id is the kind prefix.
                Bone("/BodyTop/root/hips/spine/head/eye", "日本語", "/BodyTop/root/hips/spine/head", new Vec3(0.03f, 0.05f, 0.08f), BoneGroup.Face),
                // Two different bones with one game name.
                Bone("/BodyTop/root/hips/spine/a/cf_s_dup", "cf_s_dup", "/BodyTop/root/hips/spine", new Vec3(0, 0.02f, 0), BoneGroup.Helper),
                Bone("/BodyTop/root/hips/b/cf_s_dup", "cf_s_dup", "/BodyTop/root/hips", new Vec3(0, -0.02f, 0), BoneGroup.Helper),
            };
        }

        private const string Hips = "/BodyTop/root/hips";
        private const string Spine = "/BodyTop/root/hips/spine";
        private const string Head = "/BodyTop/root/hips/spine/head";
        private const string Thigh = "/BodyTop/root/hips/thigh_L";
        private const string Eye = "/BodyTop/root/hips/spine/head/eye";
        private const string DupA = "/BodyTop/root/hips/spine/a/cf_s_dup";
        private const string DupB = "/BodyTop/root/hips/b/cf_s_dup";
        private const string SkirtRoot = "/BodyTop/root/hips/sk_00_00";
        private const string SkirtTip = "/BodyTop/root/hips/sk_00_00/sk_00_01";
        private const string HairPin = "/BodyTop/root/hips/spine/head/a_n_hair_pin";
        private const string GagMesh = "/BodyTop/head/cf_O_gag_eye_00";
        private const string PupilMesh = "/BodyTop/head/cf_Ohitomi_L";

        // Body Pass ------------------------------------------------------------------------------------

        private void CaptureBody(PassSink sink)
        {
            sink.Bones.AddRange(BodyBones());

            sink.Materials.Add(new MaterialData
            {
                Key = "mat:body",
                Name = "cf_m_body",
                Shader = "Shader Forge/main_skin",
                Role = MaterialRole.Body,
                BlendMode = BlendMode.Opaque,
                Colors = { { "_ShadowColor", new Color(0.83f, 0.87f, 0.94f, 1) }, { "_Color", new Color(1, 0.9f, 0.8f, 1) } },
                Floats = { { "_rimpower", 0.5f }, { "_SpeclarHeight", 0.98f } },
                Vectors = { { "_LiquidTiling", new Vec4(0, 0, 1, 1) } },
                Textures =
                {
                    Texture("_MainTex", TextureRole.Main, TextureVariant.Light),
                    Texture("_MainTex", TextureRole.Main, TextureVariant.Dark),
                    Texture("_NormalMap", TextureRole.Normal),
                    Texture("_overtex1", TextureRole.Overlay),
                    Texture("_overtex2", TextureRole.Overlay),
                    // No Role: known by its Raw Property only.
                    Texture("_liquidmask", null),
                },
                // KK's create material, which composites the body's main texture.
                Sections = { Create("Custom/CreateTexture/BodySkin", Texture("_MainTex", TextureRole.Main), Texture("_ColorMask", TextureRole.ColorMask), Texture("_Texture3", null)) },
            });
            sink.Materials.Add(new MaterialData { Key = "mat:tooth", Name = "cf_m_tooth", Shader = "Shader Forge/main_item", Role = MaterialRole.Teeth, BlendMode = BlendMode.Opaque });
            sink.Materials.Add(new MaterialData
            {
                Key = "mat:face",
                Name = "cf_m_face_00",
                Shader = "Shader Forge/main_skin",
                Role = MaterialRole.Face,
                BlendMode = BlendMode.Opaque,
                Textures = { Texture("_MainTex", TextureRole.Main), Texture("_LineMask", TextureRole.LineMask), Texture("_DetailMask", TextureRole.DetailMask) },
            });
            var gag = new MaterialData { Key = "mat:gag", Name = "cf_m_gageye_00", Shader = "Shader Forge/toon_textureanimation", Role = MaterialRole.GagEyes, BlendMode = BlendMode.Cutout };
            gag.Textures.Add(Texture("_MainTex", TextureRole.Main, null, "cf_t_gageye_00"));
            gag.Textures.Add(Texture("_MainTex", TextureRole.Main, null, "cf_t_gageye_01"));
            gag.Textures[1].Offset = new Vec2(0, 0.03f);
            sink.Materials.Add(gag);
            var pupil = new MaterialData { Key = "mat:eye_l", Name = "cf_m_hitomi_00", Shader = "Shader Forge/toon_eye_lod0", Role = MaterialRole.EyeL, BlendMode = BlendMode.Alpha };
            pupil.Textures.Add(Texture("_MainTex", TextureRole.Main));
            pupil.Textures.Add(Texture("_expression", null, null, "cf_t_expression_00"));
            sink.Materials.Add(pupil);

            var body = Grid("/BodyTop/o_body_a", "o_body_a", 3, 3, new Vec3(0, 1.0f, 0.1f), new[] { Hips, Spine, Thigh }, 4);
            body.SubMeshes = SplitInTwo(body, "mat:body", "mat:tooth");
            body.Morphs.Add(Morph(body, ExpressionCategory.Eye, Pattern(ExpressionList.Eye, 0).Name, Pattern(ExpressionList.Eye, 0).GameName, 0.01f));
            body.Morphs.Add(Morph(body, ExpressionCategory.Other, null, "vagina.open", 0.02f));
            sink.Meshes.Add(body);

            var face = Grid("/BodyTop/head/cf_O_face", "cf_O_face", 4, 3, new Vec3(0, 1.5f, 0.12f), new[] { Head, Eye, Spine, Hips, DupA, DupB }, 6);
            face.SubMeshes = SplitInTwo(face, "mat:face", "mat:gag");
            var eye = Pattern(ExpressionList.Eye, 0);
            var mouth = Pattern(ExpressionList.Mouth, 0);
            var gagEyes = Pattern(ExpressionList.Eye, 26);
            face.Morphs.Add(Morph(face, ExpressionCategory.Eye, eye.Name, eye.GameName, 0.01f));
            face.Morphs.Add(Morph(face, ExpressionCategory.Mouth, mouth.Name, mouth.GameName, 0.02f));
            face.Morphs.Add(Morph(face, ExpressionCategory.Mouth, mouth.ClosedName, mouth.GameName, 0.015f));
            var gagMorph = Morph(face, ExpressionCategory.Gag, gagEyes.Name, gagEyes.GameName, 0.005f);
            gagMorph.ShowsMeshKeys.Add(GagMesh);
            gagMorph.HidesMeshKeys.Add(PupilMesh);
            gagMorph.MaterialChanges.Add(new MaterialChange
            {
                MaterialKey = "mat:gag",
                Textures = { { "_MainTex", "cf_t_gageye_01" } },
                Floats = { { "_SizeSpeed", 0.5f }, { "_angleSpeed", 0 } },
                Vectors = { { "_TileAnimation", new Vec4(1, 1, 0, 0) } },
            });
            face.Morphs.Add(gagMorph);
            var stars = PatternNamed("Eye Star Pupils");
            var starMorph = Morph(face, ExpressionCategory.Eye, stars.Name, stars.GameName, 0.007f);
            starMorph.MaterialChanges.Add(new MaterialChange { MaterialKey = "mat:eye_l", Textures = { { "_expression", "cf_t_expression_00" } }, Floats = { { "_exppower", 1 } } });
            face.Morphs.Add(starMorph);
            var chewing = table.Recipes.Find(r => r.Name == "Mouth Chewing");
            face.Morphs.Add(Morph(face, ExpressionCategory.Mouth, chewing.Name, chewing.Shapes[0].Key, 0.03f));
            face.Morphs.Add(Morph(face, ExpressionCategory.Tears, "Tears small", null, 0.004f));
            face.Morphs.Add(Morph(face, ExpressionCategory.Mouth, null, "kuti_face.f00_untranslated", 0.006f));
            sink.Meshes.Add(face);

            var gagMesh = Rigid(GagMesh, "cf_O_gag_eye_00", Head, "mat:gag");
            gagMesh.Morphs.Add(Morph(gagMesh, ExpressionCategory.Gag, "Gag eye 00", null, 0.05f));
            sink.Meshes.Add(gagMesh);
            sink.Meshes.Add(Rigid(PupilMesh, "cf_Ohitomi_L", Eye, "mat:eye_l"));

            sink.Colliders.Add(new PhysicsCollider
            {
                Name = "cf_hit_spine01",
                BoneKey = Spine,
                Center = new Vec3(0.01f, 0, 0.02f),
                Rotation = AxisAngle(0, 0, 1, 5),
                Radius = 0.09f,
                Height = 0.13f,
                Direction = ColliderDirection.Y,
                Bound = ColliderBound.Outside,
            });
        }

        private ExpressionPattern Pattern(ExpressionList list, int index)
        {
            var pattern = table.Find(list, index);
            if (pattern == null)
            {
                throw new InvalidOperationException("kk.json has no " + list + " pattern " + index);
            }
            return pattern;
        }

        private ExpressionPattern PatternNamed(string name)
        {
            foreach (var pattern in table.Patterns)
            {
                if (pattern.Name == name)
                {
                    return pattern;
                }
            }
            throw new InvalidOperationException("kk.json has no pattern named " + name);
        }

        // Outfit Passes --------------------------------------------------------------------------------

        private void CaptureOutfit0(PassSink sink)
        {
            sink.Bones.AddRange(BodyBones());
            sink.Bones.Add(Bone(SkirtRoot, "cf_j_sk_00_00", Hips, new Vec3(0.05f, -0.1f, 0.05f), BoneGroup.Skirt));
            sink.Bones.Add(Bone(SkirtTip, "cf_j_sk_00_01", SkirtRoot, new Vec3(0, -0.15f, 0.02f), BoneGroup.Skirt));
            sink.Bones.Add(Bone(HairPin, "a_n_hair_pin", Head, new Vec3(0.04f, 0.1f, 0), BoneGroup.Accessory));

            sink.Materials.Add(new MaterialData
            {
                Key = "mat:skirt",
                Name = "cf_m_bot_skirt01",
                Shader = "Shader Forge/main_alpha",
                BlendMode = BlendMode.Alpha,
                Textures = { Texture("_MainTex", TextureRole.Main), Texture("_ColorMask", TextureRole.ColorMask), Texture("_AlphaMask", TextureRole.AlphaMask), Texture("_PatternMask1", null) },
                Sections = { Create("Custom/CreateTexture/Clothes", Texture("_MainTex", TextureRole.Main), Texture("_ColorMask", TextureRole.ColorMask), Texture("_PatternMask1", null), Texture("_PatternMask2", null)) },
            });
            sink.Materials.Add(new MaterialData { Key = "mat:acs", Name = "cf_m_acs_ribbon", Shader = "Shader Forge/main_item_glasses", BlendMode = BlendMode.Glasses });
            sink.BodyTextures.Add(new BodyTexture { MaterialKey = "mat:body", Texture = Texture("_AlphaMask", TextureRole.AlphaMask) });

            var skirt = Grid("/outfit0/o_bot_skirt", "o_bot_skirt", 3, 4, new Vec3(0, 0.8f, 0.1f), new[] { SkirtRoot, SkirtTip, Hips }, 3);
            skirt.SubMeshes = SplitInTwo(skirt, "mat:skirt", null);
            sink.Meshes.Add(skirt);
            var alternate = Grid("/outfit0/o_bot_skirt_half", "o_bot_skirt", 3, 3, new Vec3(0, 0.75f, 0.1f), new[] { SkirtRoot, Hips }, 2);
            alternate.Alternate = true;
            alternate.SubMeshes = SplitInTwo(alternate, "mat:skirt", null);
            sink.Meshes.Add(alternate);
            sink.Meshes.Add(Rigid("/outfit0/acs_ribbon", "acs_ribbon", HairPin, "mat:acs"));

            var chain = new PhysicsChain
            {
                RootKey = SkirtRoot,
                Gravity = new Vec3(0, -0.01f, 0),
                Force = new Vec3(0.001f, -0.0005f, 0),
                EndLength = 0.1f,
                EndOffset = new Vec3(0.01f, 0, 0),
                Colliders = { "cf_hit_spine01", "cf_hit_thigh_L" },
                ExclusionKeys = { SkirtTip },
            };
            chain.Particles.Add(new PhysicsParticle { BoneKey = SkirtRoot, Damping = 0.2f, Elasticity = 0.2f, Stiffness = 0.1f, Inert = 0.7f, Radius = 0.01f });
            chain.Particles.Add(new PhysicsParticle { BoneKey = SkirtTip, Damping = 0.25f, Elasticity = 0.15f, Stiffness = 0.1f, Inert = 0.7f, Radius = 0.012f });
            sink.Chains.Add(chain);
            sink.Colliders.Add(new PhysicsCollider { Name = "cf_hit_thigh_L", BoneKey = Thigh, Radius = 0.07f, Height = 0.3f, Direction = ColliderDirection.Y, Bound = ColliderBound.Inside });
        }

        private void CaptureOutfit1(PassSink sink)
        {
            sink.Bones.AddRange(BodyBones());
            sink.Bones.Add(Bone(HairPin, "a_n_hair_pin", Head, new Vec3(0.04f, 0.1f, 0), BoneGroup.Accessory));
            // Two more names that simplify to nothing: bone_2 and bone_3.
            sink.Bones.Add(Bone(HairPin + "/kami", "髪", HairPin, new Vec3(0, 0.02f, 0), BoneGroup.Hair));
            sink.Bones.Add(Bone(HairPin + "/kazari", "飾り", HairPin, new Vec3(0, 0.03f, 0), BoneGroup.Accessory));

            // Two hats whose names simplify to nothing: mat and mat_2.
            sink.Materials.Add(new MaterialData { Key = "mat:hat1", Name = "帽子", Shader = "Shader Forge/main_opaque", BlendMode = BlendMode.Opaque, Textures = { Texture("_MainTex", TextureRole.Main) } });
            sink.Materials.Add(new MaterialData { Key = "mat:hat2", Name = "帽子", Shader = "Shader Forge/main_opaque", BlendMode = BlendMode.Opaque });
            // Captured again: the Core keeps the first one.
            sink.Materials.Add(new MaterialData { Key = "mat:acs", Name = "cf_m_acs_ribbon", Shader = "Shader Forge/main_item_glasses", BlendMode = BlendMode.Glasses });

            sink.Meshes.Add(Rigid("/outfit1/hat", "", HairPin + "/kami", "mat:hat1"));
            sink.Meshes.Add(Rigid("/outfit1/hat2", "日本語", HairPin + "/kazari", "mat:hat2"));
            sink.Meshes.Add(Rigid("/outfit1/acs_ribbon", "acs_ribbon", HairPin, "mat:acs"));
            // A weight so small that normalising can leave it at zero: the Core must not write a joint with it.
            var pin = Rigid("/outfit1/pin", "pin", HairPin, "mat:acs");
            pin.BoneKeys = new[] { HairPin, HairPin + "/kami" };
            pin.InfluencesPerVertex = 2;
            pin.Joints = new[] { 0, 1, 0, 1, 0, 1 };
            pin.Weights = new[] { 1f, 1e-9f, 1f, 1e-9f, 1f, 1e-9f };
            sink.Meshes.Add(pin);
            // Each Outfit has its own body mask, in the same slot.
            sink.BodyTextures.Add(new BodyTexture { MaterialKey = "mat:body", Texture = Texture("_AlphaMask", TextureRole.AlphaMask) });
        }

        // Mesh builders --------------------------------------------------------------------------------

        /// <summary>A KK create material as the adapter attaches it: extensions.kk.create.</summary>
        public static MaterialSection Create(string shader, params TextureData[] textures)
        {
            var section = new MaterialSection
            {
                Extension = "kk",
                Field = "create",
                Shader = shader,
                Colors = { { "_Color", new Color(1, 0.87f, 0.79f, 1) }, { "_Color2", new Color(0.9f, 0.7f, 0.6f, 1) } },
                Floats = { { "_PatternScale", 0.5f } },
                Vectors = { { "_Patternuv1", new Vec4(0, 0, 1, 1) } },
            };
            section.Textures.AddRange(textures);
            return section;
        }

        private static TextureData Texture(string raw, TextureRole? role, TextureVariant? variant = null, string pattern = null)
        {
            return new TextureData { Raw = raw, Role = role, Variant = variant, Pattern = pattern, Png = Png };
        }

        /// <summary>A flat grid facing +Z, with tangents, two UV sets and colours, weighted across the given bones.</summary>
        private static MeshData Grid(string key, string name, int columns, int rows, Vec3 origin, string[] bones, int influences)
        {
            int count = columns * rows;
            var mesh = new MeshData
            {
                Key = key,
                Name = name,
                Positions = new Vec3[count],
                Normals = new Vec3[count],
                Tangents = new Vec4[count],
                Colors = new Color[count],
                BoneKeys = bones,
                InfluencesPerVertex = influences,
                Joints = new int[count * influences],
                Weights = new float[count * influences],
            };
            var uv0 = new Vec2[count];
            var uv1 = new Vec2[count];
            for (int r = 0; r < rows; r++)
            {
                for (int c = 0; c < columns; c++)
                {
                    int v = r * columns + c;
                    mesh.Positions[v] = origin + new Vec3(c * 0.05f - 0.05f, r * 0.05f, 0);
                    mesh.Normals[v] = new Vec3(0, 0, 2); // Not unit length: the Core normalises.
                    mesh.Tangents[v] = new Vec4(1, 0, 0, -1);
                    mesh.Colors[v] = new Color(1, 1, 1, 1);
                    uv0[v] = new Vec2(c / (float)(columns - 1), r / (float)(rows - 1));
                    uv1[v] = new Vec2(uv0[v].X * 0.5f, uv0[v].Y * 0.5f);
                    for (int s = 0; s < influences; s++)
                    {
                        // Spread weight over every slot, with one bone repeated so the Core must merge it.
                        mesh.Joints[v * influences + s] = (v + s) % bones.Length;
                        mesh.Weights[v * influences + s] = 1 + s + (v % 3);
                    }
                }
            }
            mesh.UvSets.Add(uv0);
            mesh.UvSets.Add(uv1);

            var indices = new List<int>();
            for (int r = 0; r < rows - 1; r++)
            {
                for (int c = 0; c < columns - 1; c++)
                {
                    int a = r * columns + c;
                    indices.AddRange(new[] { a, a + columns, a + 1, a + 1, a + columns, a + columns + 1 });
                }
            }
            mesh.SubMeshes.Add(new SubMesh { Indices = indices.ToArray() });
            return mesh;
        }

        /// <summary>Splits the grid's triangles between two materials, or keeps one if the second is null.</summary>
        private static List<SubMesh> SplitInTwo(MeshData mesh, string first, string second)
        {
            int[] all = mesh.SubMeshes[0].Indices;
            if (second == null)
            {
                return new List<SubMesh> { new SubMesh { Indices = all, MaterialKey = first } };
            }
            int half = all.Length / 6 * 3;
            var a = new int[half];
            var b = new int[all.Length - half];
            Array.Copy(all, a, half);
            Array.Copy(all, half, b, 0, b.Length);
            return new List<SubMesh> { new SubMesh { Indices = a, MaterialKey = first }, new SubMesh { Indices = b, MaterialKey = second } };
        }

        private static MorphData Morph(MeshData mesh, ExpressionCategory category, string name, string gameName, float amount)
        {
            int count = mesh.Positions.Length;
            var positions = new Vec3[count];
            var normals = new Vec3[count];
            for (int v = 0; v < count; v++)
            {
                positions[v] = new Vec3(amount * (v % 2), amount, -amount * (v % 3));
                normals[v] = new Vec3(0, amount, 0);
            }
            return new MorphData { Category = category, ExpressionName = name, GameName = gameName, PositionDeltas = positions, NormalDeltas = normals };
        }

        /// <summary>A small rigid mesh, written skinned to one bone with weight 1 (ADR 0006).</summary>
        private static MeshData Rigid(string key, string name, string bone, string material)
        {
            var mesh = new MeshData
            {
                Key = key,
                Name = name,
                Positions = new[] { new Vec3(0, 1.6f, 0), new Vec3(0.02f, 1.6f, 0), new Vec3(0, 1.62f, 0) },
                Normals = new[] { new Vec3(0, 0, 1), new Vec3(0, 0, 1), new Vec3(0, 0, 1) },
                BoneKeys = new[] { bone },
                InfluencesPerVertex = 1,
                Joints = new[] { 0, 0, 0 },
                Weights = new[] { 1f, 1f, 1f },
            };
            mesh.UvSets.Add(new[] { new Vec2(0, 0), new Vec2(1, 0), new Vec2(0, 1) });
            mesh.SubMeshes.Add(new SubMesh { Indices = new[] { 0, 1, 2 }, MaterialKey = material });
            return mesh;
        }
    }
}
