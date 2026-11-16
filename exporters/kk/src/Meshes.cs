using System.Collections.Generic;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Captures renderers as meshes at the rest pose (ADR 0006). The adapter skins each vertex itself
    /// against the Rig's poses, the way Unity does, so positions match the bones exactly.
    /// </summary>
    internal sealed class Meshes
    {
        private readonly Rig rig;
        private readonly bool mirror;

        /// <summary>With <paramref name="mirror"/>, each mesh is skinned with mirrored skin matrices (MirrorSkin).</summary>
        public Meshes(Rig rig, bool mirror)
        {
            this.rig = rig;
            this.mirror = mirror;
        }

        /// <summary>Why the last renderer was skipped, or null.</summary>
        public string Skipped { get; private set; }

        /// <summary>The mesh a renderer draws, or null if it has none, or none the adapter can read.</summary>
        public static Mesh SourceMesh(Renderer renderer)
        {
            var smr = renderer as SkinnedMeshRenderer;
            if (smr != null)
            {
                return smr.sharedMesh;
            }
            var filter = renderer.GetComponent<MeshFilter>();
            return filter != null ? filter.sharedMesh : null;
        }

        /// <summary>
        /// Captures one renderer. Each material slot becomes a sub-mesh keyed "&lt;mesh key&gt;#slot"; the
        /// caller captures the materials. Returns null, with <see cref="Skipped"/> set, if it can't.
        /// </summary>
        public MeshData Capture(Renderer renderer, Material[] slots, string key, bool freezeShapeKeys)
        {
            Skipped = null;
            var mesh = SourceMesh(renderer);
            if (mesh == null || mesh.vertexCount == 0)
            {
                Skipped = "it has no mesh";
                return null;
            }
            int count = mesh.vertexCount;
            var smr = renderer as SkinnedMeshRenderer;
            if (!mesh.isReadable)
            {
                if (smr == null)
                {
                    Skipped = "its mesh isn't readable";
                    return null;
                }
                return CaptureBaked(smr, slots, mesh, key);
            }

            // Skin matrices: bone pose times bind pose, or the renderer's own pose for a rigid mesh.
            Transform[] bones;
            Matrix4x4[] skin;
            BoneWeight[] weights = smr != null ? mesh.boneWeights : null;
            if (smr != null && smr.bones.Length > 0 && weights.Length == count)
            {
                bones = smr.bones;
                var bind = mesh.bindposes;
                skin = new Matrix4x4[bones.Length];
                for (int i = 0; i < bones.Length; i++)
                {
                    skin[i] = bones[i] != null && i < bind.Length ? rig.PoseOf(bones[i]).Matrix * bind[i] : rig.PoseOf(rig.Top).Matrix;
                }
            }
            else
            {
                bones = new[] { renderer.transform };
                skin = new[] { rig.PoseOf(renderer.transform).Matrix };
                weights = null;
            }

            var data = new MeshData
            {
                Key = key,
                Name = renderer.name,
                BoneKeys = new string[bones.Length],
                InfluencesPerVertex = weights != null ? 4 : 1,
            };
            for (int i = 0; i < bones.Length; i++)
            {
                data.BoneKeys[i] = rig.BoneKey(bones[i] != null ? bones[i] : rig.Top);
            }

            var basis = mesh.vertices;
            var normals = mesh.normals;
            var tangents = mesh.tangents;
            if (freezeShapeKeys && smr != null)
            {
                AddCurrentShapeKeys(smr, mesh, basis, normals);
            }

            if (mirror)
            {
                MirrorSkin(skin, bones, basis, weights);
            }

            data.Positions = new Vec3[count];
            data.Normals = normals.Length == count ? new Vec3[count] : null;
            data.Tangents = tangents.Length == count ? new Vec4[count] : null;
            data.Joints = new int[count * data.InfluencesPerVertex];
            data.Weights = new float[count * data.InfluencesPerVertex];
            for (int v = 0; v < count; v++)
            {
                Matrix4x4 m = Blend(skin, weights, v);
                data.Positions[v] = Seam.V3(m.MultiplyPoint3x4(basis[v]));
                if (data.Normals != null)
                {
                    data.Normals[v] = Seam.V3(m.MultiplyVector(normals[v]));
                }
                if (data.Tangents != null)
                {
                    var t = m.MultiplyVector(tangents[v]);
                    data.Tangents[v] = new Vec4(t.x, t.y, t.z, tangents[v].w);
                }
                if (weights == null)
                {
                    data.Weights[v] = 1;
                    continue;
                }
                var w = weights[v];
                data.Joints[v * 4] = w.boneIndex0;
                data.Joints[v * 4 + 1] = w.boneIndex1;
                data.Joints[v * 4 + 2] = w.boneIndex2;
                data.Joints[v * 4 + 3] = w.boneIndex3;
                data.Weights[v * 4] = w.weight0;
                data.Weights[v * 4 + 1] = w.weight1;
                data.Weights[v * 4 + 2] = w.weight2;
                data.Weights[v * 4 + 3] = w.weight3;
            }

            var colors = mesh.colors;
            if (colors.Length == count)
            {
                data.Colors = new Core.Color[count];
                for (int v = 0; v < count; v++)
                {
                    data.Colors[v] = Seam.C(colors[v]);
                }
            }
            AddUvSets(data, mesh, count);
            AddSubMeshes(data, slots, mesh, key);
            Skin = skin;
            SkinWeights = weights;
            return data.SubMeshes.Count > 0 ? data : Fail(data, "it has no materials");
        }

        /// <summary>
        /// A skinned mesh whose vertices the game doesn't let scripts read (KKS ships clothes this way).
        /// Unity can still skin it into a new, readable mesh at the current pose, and the skin weights stay
        /// readable, so it is captured from that. Its shape keys can't be read, so it has none.
        /// </summary>
        private MeshData CaptureBaked(SkinnedMeshRenderer smr, Material[] slots, Mesh mesh, string key)
        {
            int count = mesh.vertexCount;
            var weights = mesh.boneWeights;
            if (weights.Length != count || smr.bones.Length == 0)
            {
                return Fail(null, "its mesh isn't readable and the game gives no skin weights for it");
            }
            var baked = new Mesh();
            smr.BakeMesh(baked);
            try
            {
                if (baked.vertexCount != count)
                {
                    return Fail(null, "its mesh isn't readable and baking it changed its vertex count");
                }
                var bones = smr.bones;
                var data = new MeshData { Key = key, Name = smr.name, BoneKeys = new string[bones.Length], InfluencesPerVertex = 4 };
                for (int i = 0; i < bones.Length; i++)
                {
                    data.BoneKeys[i] = rig.BoneKey(bones[i] != null ? bones[i] : rig.Top);
                }
                // BakeMesh gives vertices in the renderer's space, without its scale.
                var t = smr.transform;
                var m = rig.RootInverse * Matrix4x4.TRS(t.position, t.rotation, Vector3.one);
                var vertices = baked.vertices;
                var normals = baked.normals;
                var tangents = baked.tangents;
                data.Positions = new Vec3[count];
                data.Normals = normals.Length == count ? new Vec3[count] : null;
                data.Tangents = tangents.Length == count ? new Vec4[count] : null;
                data.Joints = new int[count * 4];
                data.Weights = new float[count * 4];
                for (int v = 0; v < count; v++)
                {
                    data.Positions[v] = Seam.V3(m.MultiplyPoint3x4(vertices[v]));
                    if (data.Normals != null)
                    {
                        data.Normals[v] = Seam.V3(m.MultiplyVector(normals[v]));
                    }
                    if (data.Tangents != null)
                    {
                        var tv = m.MultiplyVector(tangents[v]);
                        data.Tangents[v] = new Vec4(tv.x, tv.y, tv.z, tangents[v].w);
                    }
                    var w = weights[v];
                    data.Joints[v * 4] = w.boneIndex0;
                    data.Joints[v * 4 + 1] = w.boneIndex1;
                    data.Joints[v * 4 + 2] = w.boneIndex2;
                    data.Joints[v * 4 + 3] = w.boneIndex3;
                    data.Weights[v * 4] = w.weight0;
                    data.Weights[v * 4 + 1] = w.weight1;
                    data.Weights[v * 4 + 2] = w.weight2;
                    data.Weights[v * 4 + 3] = w.weight3;
                }
                var colors = baked.colors;
                if (colors.Length == count)
                {
                    data.Colors = new Core.Color[count];
                    for (int v = 0; v < count; v++)
                    {
                        data.Colors[v] = Seam.C(colors[v]);
                    }
                }
                AddUvSets(data, baked, count);
                AddSubMeshes(data, slots, baked, key);
                Skin = null;
                SkinWeights = null;
                return data.SubMeshes.Count > 0 ? data : Fail(data, "it has no materials");
            }
            finally
            {
                // Now, not at the frame's end: a Pass captures every mesh in one frame (see Bake).
                Object.DestroyImmediate(baked);
            }
        }

        /// <summary>
        /// Makes the skin matrices mirror images across X = 0 where the game's nearly are (SkinMirror,
        /// ADR 0048), so a symmetrical mesh is skinned symmetrical. Only the skinning changes, not the bones.
        /// </summary>
        private static void MirrorSkin(Matrix4x4[] skin, Transform[] bones, Vector3[] basis, BoneWeight[] weights)
        {
            var names = new string[skin.Length];
            var rows = new float[skin.Length][];
            for (int i = 0; i < skin.Length; i++)
            {
                names[i] = i < bones.Length && bones[i] != null ? bones[i].name : null;
                rows[i] = new float[16];
                for (int k = 0; k < 16; k++)
                {
                    rows[i][(k % 4) * 4 + k / 4] = skin[i][k]; // Unity indexes column by column
                }
            }
            var vertices = new Vec3[basis.Length];
            for (int v = 0; v < basis.Length; v++)
            {
                vertices[v] = Seam.V3(basis[v]);
            }
            int[] joints = null;
            float[] amounts = null;
            if (weights != null)
            {
                joints = new int[weights.Length * 4];
                amounts = new float[weights.Length * 4];
                for (int v = 0; v < weights.Length; v++)
                {
                    var w = weights[v];
                    joints[v * 4] = w.boneIndex0;
                    joints[v * 4 + 1] = w.boneIndex1;
                    joints[v * 4 + 2] = w.boneIndex2;
                    joints[v * 4 + 3] = w.boneIndex3;
                    amounts[v * 4] = w.weight0;
                    amounts[v * 4 + 1] = w.weight1;
                    amounts[v * 4 + 2] = w.weight2;
                    amounts[v * 4 + 3] = w.weight3;
                }
            }
            Core.AdapterKit.SkinMirror.Mirror(names, rows, vertices, joints, amounts, 4);
            for (int i = 0; i < skin.Length; i++)
            {
                var m = skin[i];
                for (int k = 0; k < 16; k++)
                {
                    m[k] = rows[i][(k % 4) * 4 + k / 4];
                }
                skin[i] = m;
            }
        }

        /// <summary>The skin matrices of the mesh just captured, for baking its shape keys; null if it has none.</summary>
        public Matrix4x4[] Skin { get; private set; }

        /// <summary>The skin weights of the mesh just captured, or null for a rigid mesh.</summary>
        public BoneWeight[] SkinWeights { get; private set; }

        /// <summary>The weighted sum of the vertex's skin matrices.</summary>
        public static Matrix4x4 Blend(Matrix4x4[] skin, BoneWeight[] weights, int v)
        {
            if (weights == null)
            {
                return skin[0];
            }
            var w = weights[v];
            var m = new Matrix4x4();
            Accumulate(ref m, skin, w.boneIndex0, w.weight0);
            Accumulate(ref m, skin, w.boneIndex1, w.weight1);
            Accumulate(ref m, skin, w.boneIndex2, w.weight2);
            Accumulate(ref m, skin, w.boneIndex3, w.weight3);
            return m;
        }

        private static void Accumulate(ref Matrix4x4 m, Matrix4x4[] skin, int index, float weight)
        {
            if (weight <= 0 || index < 0 || index >= skin.Length)
            {
                return;
            }
            var s = skin[index];
            for (int i = 0; i < 16; i++)
            {
                m[i] += s[i] * weight;
            }
        }

        private MeshData Fail(MeshData data, string why)
        {
            Skipped = why;
            return null;
        }

        private static void AddCurrentShapeKeys(SkinnedMeshRenderer smr, Mesh mesh, Vector3[] basis, Vector3[] normals)
        {
            var deltas = new Vector3[basis.Length];
            var normalDeltas = new Vector3[basis.Length];
            var tangentDeltas = new Vector3[basis.Length];
            for (int s = 0; s < mesh.blendShapeCount; s++)
            {
                float weight = smr.GetBlendShapeWeight(s);
                if (weight == 0)
                {
                    continue;
                }
                ShapeKeys.Frame(mesh, s, weight, deltas, normalDeltas, tangentDeltas);
                for (int v = 0; v < basis.Length; v++)
                {
                    basis[v] += deltas[v];
                    if (normals.Length == basis.Length)
                    {
                        normals[v] += normalDeltas[v];
                    }
                }
            }
        }

        private static void AddUvSets(MeshData data, Mesh mesh, int count)
        {
            var sets = new List<Vector2[]> { mesh.uv, mesh.uv2, mesh.uv3, mesh.uv4 };
            int last = -1;
            for (int i = 0; i < sets.Count; i++)
            {
                if (sets[i].Length == count)
                {
                    last = i;
                }
            }
            for (int i = 0; i <= last; i++)
            {
                var uvs = new Vec2[count];
                if (sets[i].Length == count)
                {
                    for (int v = 0; v < count; v++)
                    {
                        uvs[v] = Seam.V2(sets[i][v]);
                    }
                }
                data.UvSets.Add(uvs);
            }
        }

        /// <summary>One sub-mesh per material slot. As in Unity, slots beyond the sub-mesh count draw the last sub-mesh again.</summary>
        private static void AddSubMeshes(MeshData data, Material[] materials, Mesh mesh, string key)
        {
            for (int slot = 0; slot < materials.Length; slot++)
            {
                if (materials[slot] == null)
                {
                    continue;
                }
                int sub = Mathf.Min(slot, mesh.subMeshCount - 1);
                var indices = mesh.GetTriangles(sub);
                if (indices.Length == 0)
                {
                    continue;
                }
                data.SubMeshes.Add(new SubMesh { Indices = indices, MaterialKey = MaterialKey(key, slot) });
            }
        }

        public static string MaterialKey(string meshKey, int slot)
        {
            return meshKey + "#" + slot;
        }
    }
}
