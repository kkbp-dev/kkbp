using System.Collections.Generic;

namespace KKBP.Exporter.Core
{
    // Plain data the Game Adapter hands to the Core. Everything is in Unity's space and
    // conventions (left-handed, UV origin bottom left); the Core converts it once, in UnitySpace.
    //
    // Keys are the adapter's stable names for game objects, such as a transform path. The Core turns
    // each key into an Id (ADR 0005); the same key always gets the same Id within one export.

    public sealed class CharacterInfo
    {
        public string Name;

        /// <summary>The Card's PNG bytes, or null if there is none.</summary>
        public byte[] CardPng;

        public JsonObject Extensions;
    }

    /// <summary>The export options, which are also what the Manifest records.</summary>
    public sealed class ExportOptions
    {
        public bool AllOutfits;
        public bool AllVariations;
        public bool Physics = true;
        public bool EnabledShapeKeys;
        public bool CurrentPose;

        /// <summary>Game-only options, keyed by Game Extension (kk, kks, svs).</summary>
        public JsonObject Extensions;
    }

    public enum PassKind
    {
        Body,
        Outfit,
    }

    public sealed class PassInfo
    {
        public readonly PassKind Kind;

        /// <summary>The Outfit index, or null for the Body Pass.</summary>
        public readonly int? Outfit;

        private PassInfo(PassKind kind, int? outfit)
        {
            Kind = kind;
            Outfit = outfit;
        }

        public static PassInfo Body()
        {
            return new PassInfo(PassKind.Body, null);
        }

        public static PassInfo ForOutfit(int index)
        {
            if (index < 0 || index > 99)
            {
                throw new System.ArgumentOutOfRangeException("index", "Outfit index must be 0 to 99.");
            }
            return new PassInfo(PassKind.Outfit, index);
        }

        public override string ToString()
        {
            return Kind == PassKind.Body ? "Body Pass" : "Outfit Pass " + Outfit.Value.ToString("00");
        }
    }

    public sealed class BoneData
    {
        public string Key;
        public string Name;

        /// <summary>The parent bone's key, or null for the Pass's root bone.</summary>
        public string ParentKey;

        /// <summary>Rest pose relative to the parent.</summary>
        public Vec3 Position;
        public Quat Rotation = Quat.Identity;
        public Vec3 Scale = Vec3.One;

        /// <summary>
        /// The scale the game has on the bone, parents included (Unity's lossyScale). It isn't part of
        /// the rest pose (ADR 0008); the importer's joint corrections need it to work in the game's units.
        /// </summary>
        public Vec3 GameScale = Vec3.One;

        public BoneRole? Role;
        public BoneGroup Group;
    }

    public sealed class MeshData
    {
        public string Key;
        public string Name;

        /// <summary>True if the mesh only shows in the game's alternate clothing state.</summary>
        public bool Alternate;

        /// <summary>Vertex positions in model space, already in the skeleton's rest pose (ADR 0006).</summary>
        public Vec3[] Positions;
        public Vec3[] Normals;

        /// <summary>Optional. W is the bitangent sign.</summary>
        public Vec4[] Tangents;

        /// <summary>Optional vertex colours.</summary>
        public Color[] Colors;

        /// <summary>UV sets in Unity's convention; each has one entry per vertex.</summary>
        public List<Vec2[]> UvSets = new List<Vec2[]>();

        /// <summary>The bones this mesh's joint indices point into.</summary>
        public string[] BoneKeys;

        /// <summary>Joint slots per vertex. Every mesh is skinned; a rigid mesh uses one slot.</summary>
        public int InfluencesPerVertex;

        /// <summary>VertexCount * InfluencesPerVertex indices into BoneKeys.</summary>
        public int[] Joints;

        /// <summary>VertexCount * InfluencesPerVertex weights. The Core normalises them.</summary>
        public float[] Weights;

        public List<SubMesh> SubMeshes = new List<SubMesh>();
        public List<MorphData> Morphs = new List<MorphData>();
    }

    public sealed class SubMesh
    {
        /// <summary>Triangle list, in Unity's winding.</summary>
        public int[] Indices;

        public string MaterialKey;
    }

    /// <summary>One expression shape key on one mesh (ADR 0003).</summary>
    public sealed class MorphData
    {
        public ExpressionCategory Category;

        /// <summary>The Expression Name, or null if the table has none for this key.</summary>
        public string ExpressionName;

        /// <summary>The game's own name, or null for keys the exporter made itself.</summary>
        public string GameName;

        /// <summary>Per-vertex position offsets from the base mesh.</summary>
        public Vec3[] PositionDeltas;

        /// <summary>Optional per-vertex normal offsets.</summary>
        public Vec3[] NormalDeltas;

        // What the expression shows, hides and changes is set on one of its shape keys, on any mesh;
        // the Core writes it once per expression, in expressions.json's "effects".

        /// <summary>
        /// Keys of meshes in the same Pass that the game shows while this expression is on. Each must
        /// have a showing key (a tears or gag shape key with no game name, ADR 0010).
        /// </summary>
        public List<string> ShowsMeshKeys = new List<string>();

        /// <summary>Keys of meshes in the same Pass that the game hides while this expression is on.</summary>
        public List<string> HidesMeshKeys = new List<string>();

        /// <summary>Material values the game sets while this expression is on, such as a gag-eye texture.</summary>
        public List<MaterialChange> MaterialChanges = new List<MaterialChange>();

        public JsonObject Extensions;

        /// <summary>The morph target name: the Expression Name if there is one, otherwise the game name.</summary>
        public string TargetName
        {
            get { return ExpressionName ?? GameName; }
        }
    }

    /// <summary>
    /// Values one expression sets on one captured material, keyed by Raw Property. A texture is named by
    /// its pattern, which must be one of the material's own textures.
    /// </summary>
    public sealed class MaterialChange
    {
        public string MaterialKey;

        /// <summary>Raw Property to texture pattern.</summary>
        public Dictionary<string, string> Textures = new Dictionary<string, string>();

        public Dictionary<string, float> Floats = new Dictionary<string, float>();
        public Dictionary<string, Vec4> Vectors = new Dictionary<string, Vec4>();
    }

    /// <summary>
    /// A texture an Outfit puts on a body material, such as the body alpha mask that hides skin under
    /// clothes. The Body Pass leaves these slots out.
    /// </summary>
    public sealed class BodyTexture
    {
        public string MaterialKey;
        public TextureData Texture;
    }

    public sealed class MaterialData
    {
        public string Key;
        public string Name;
        public string Shader;
        public MaterialRole? Role;
        public BlendMode BlendMode;
        public Dictionary<string, Color> Colors = new Dictionary<string, Color>();
        public Dictionary<string, float> Floats = new Dictionary<string, float>();
        public Dictionary<string, Vec4> Vectors = new Dictionary<string, Vec4>();
        public List<TextureData> Textures = new List<TextureData>();
        public JsonObject Extensions;

        /// <summary>Shader data the Core writes into this material's Game Extension, such as KK's create material.</summary>
        public List<MaterialSection> Sections = new List<MaterialSection>();
    }

    /// <summary>
    /// Shader data that belongs to a material but lives in its Game Extension, such as the KK and KKS
    /// create material that makes its main texture. The Core writes it like the material's own shader
    /// data, as <c>extensions.&lt;Extension&gt;.&lt;Field&gt;</c>, and writes its textures into textures/
    /// right after the material's own. A material that carries a section may be used only by meshes of
    /// the Pass that captured it.
    /// </summary>
    public sealed class MaterialSection
    {
        /// <summary>The Game Extension key, such as <c>kk</c>.</summary>
        public string Extension;

        /// <summary>The field within that extension, such as <c>create</c>.</summary>
        public string Field;

        public string Shader;
        public Dictionary<string, Color> Colors = new Dictionary<string, Color>();
        public Dictionary<string, float> Floats = new Dictionary<string, float>();
        public Dictionary<string, Vec4> Vectors = new Dictionary<string, Vec4>();
        public List<TextureData> Textures = new List<TextureData>();
    }

    public sealed class TextureData
    {
        public TextureRole? Role;

        /// <summary>The Raw Property: the game shader's name for the slot.</summary>
        public string Raw;

        public TextureVariant? Variant;

        /// <summary>For slots the game swaps at runtime: the game's texture name.</summary>
        public string Pattern;

        /// <summary>Encoded PNG bytes. The Core writes them as they are and never decodes them.</summary>
        public byte[] Png;

        /// <summary>Unity's _ST offset and scale, in Unity's UV convention.</summary>
        public Vec2 Offset;
        public Vec2 Scale = new Vec2(1, 1);
    }

    public sealed class PhysicsChain
    {
        public string RootKey;
        public Vec3 Gravity;
        public Vec3 Force;
        public float EndLength;
        public Vec3 EndOffset;
        public float Weight = 1;

        /// <summary>Names of colliders captured in this or any other Pass.</summary>
        public List<string> Colliders = new List<string>();

        public List<string> ExclusionKeys = new List<string>();
        public List<PhysicsParticle> Particles = new List<PhysicsParticle>();
    }

    public sealed class PhysicsParticle
    {
        public string BoneKey;
        public float Damping;
        public float Elasticity;
        public float Stiffness;
        public float Inert;
        public float Radius;
    }

    public enum ColliderDirection
    {
        X,
        Y,
        Z,
    }

    public enum ColliderBound
    {
        Outside,
        Inside,
    }

    public sealed class PhysicsCollider
    {
        public string Name;

        /// <summary>The exported bone the collider is attached to.</summary>
        public string BoneKey;

        public Vec3 Center;
        public Quat Rotation = Quat.Identity;
        public float Radius;
        public float Height;
        public ColliderDirection Direction;
        public ColliderBound Bound;
    }
}
