using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Gives an eye mesh whose one material draws both the eye white and the pupil (SVS) a separate eye
    /// white mesh, as KK and KKS have (ADR 0034): a copy of the eye pushed back along its normals, so the
    /// eye white rests behind the pupil as KK's does.
    /// </summary>
    public static class EyeWhites
    {
        /// <summary>
        /// How far behind the eye the copy rests, in metres. KK's eye whites sit a median 1.2 mm behind
        /// their pupils; SVS's face is at least 2.1 mm behind the eye, so 1 mm leaves it clear.
        /// </summary>
        public const float Depth = 0.001f;

        /// <summary>Appended to the eye's mesh and material keys, and its names, for the copy's.</summary>
        public const string Suffix = "_white";

        /// <summary>
        /// A copy of the eye mesh, keyed and named with <see cref="Suffix"/>, its vertices moved
        /// <see cref="Depth"/> back along their normals and each sub-mesh's material key mapped by
        /// <paramref name="materialKey"/>. Shape keys and weights are copied as they are.
        /// </summary>
        public static MeshData Copy(MeshData eye, Func<string, string> materialKey)
        {
            if (eye.Normals == null || eye.Normals.Length != eye.Positions.Length)
            {
                throw new ArgumentException("The eye mesh needs a normal for every vertex.", "eye");
            }
            var copy = new MeshData
            {
                Key = eye.Key + Suffix,
                Name = eye.Name + Suffix,
                Alternate = eye.Alternate,
                Positions = new Vec3[eye.Positions.Length],
                Normals = (Vec3[])eye.Normals.Clone(),
                Tangents = eye.Tangents != null ? (Vec4[])eye.Tangents.Clone() : null,
                Colors = eye.Colors != null ? (Color[])eye.Colors.Clone() : null,
                BoneKeys = eye.BoneKeys != null ? (string[])eye.BoneKeys.Clone() : null,
                InfluencesPerVertex = eye.InfluencesPerVertex,
                Joints = eye.Joints != null ? (int[])eye.Joints.Clone() : null,
                Weights = eye.Weights != null ? (float[])eye.Weights.Clone() : null,
            };
            for (int i = 0; i < copy.Positions.Length; i++)
            {
                copy.Positions[i] = eye.Positions[i] - Unit(eye.Normals[i]) * Depth;
            }
            foreach (var uv in eye.UvSets)
            {
                copy.UvSets.Add((Vec2[])uv.Clone());
            }
            foreach (var sub in eye.SubMeshes)
            {
                copy.SubMeshes.Add(new SubMesh { Indices = (int[])sub.Indices.Clone(), MaterialKey = materialKey(sub.MaterialKey) });
            }
            foreach (var morph in eye.Morphs)
            {
                copy.Morphs.Add(new MorphData
                {
                    Category = morph.Category,
                    ExpressionName = morph.ExpressionName,
                    GameName = morph.GameName,
                    PositionDeltas = morph.PositionDeltas != null ? (Vec3[])morph.PositionDeltas.Clone() : null,
                    NormalDeltas = morph.NormalDeltas != null ? (Vec3[])morph.NormalDeltas.Clone() : null,
                });
            }
            return copy;
        }

        /// <summary>Makes every shape key that hides the eye hide its copy too, as the game hides them together.</summary>
        public static void HideWith(IEnumerable<MeshData> meshes, string eyeKey, string copyKey)
        {
            foreach (var mesh in meshes)
            {
                foreach (var morph in mesh.Morphs)
                {
                    if (morph.HidesMeshKeys.Contains(eyeKey) && !morph.HidesMeshKeys.Contains(copyKey))
                    {
                        morph.HidesMeshKeys.Add(copyKey);
                    }
                }
            }
        }

        private static Vec3 Unit(Vec3 v)
        {
            float length = v.Length;
            return length > 0 ? v * (1 / length) : Vec3.Zero;
        }
    }
}
