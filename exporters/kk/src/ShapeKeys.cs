using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>Reads Unity blend shapes and turns weighted sums of them into rest-pose shape keys.</summary>
    internal static class ShapeKeys
    {
        /// <summary>
        /// The deltas of one blend shape at a weight from 0 to 100, interpolated between its frames as
        /// Unity does. The arrays are overwritten.
        /// </summary>
        public static void Frame(Mesh mesh, int shape, float weight, Vector3[] deltas, Vector3[] normals, Vector3[] tangents)
        {
            int frames = mesh.GetBlendShapeFrameCount(shape);
            int upper = 0;
            while (upper < frames - 1 && mesh.GetBlendShapeFrameWeight(shape, upper) < weight)
            {
                upper++;
            }
            float upperWeight = mesh.GetBlendShapeFrameWeight(shape, upper);
            mesh.GetBlendShapeFrameVertices(shape, upper, deltas, normals, tangents);
            float lowerWeight = upper > 0 ? mesh.GetBlendShapeFrameWeight(shape, upper - 1) : 0;
            float t = upperWeight > lowerWeight ? (weight - lowerWeight) / (upperWeight - lowerWeight) : 1;
            if (upper == 0 || t >= 1)
            {
                Scale(deltas, normals, upper == 0 && upperWeight > 0 ? weight / upperWeight : 1);
                return;
            }
            var lowDeltas = new Vector3[deltas.Length];
            var lowNormals = new Vector3[deltas.Length];
            var lowTangents = new Vector3[deltas.Length];
            mesh.GetBlendShapeFrameVertices(shape, upper - 1, lowDeltas, lowNormals, lowTangents);
            for (int v = 0; v < deltas.Length; v++)
            {
                deltas[v] = Vector3.Lerp(lowDeltas[v], deltas[v], t);
                normals[v] = Vector3.Lerp(lowNormals[v], normals[v], t);
            }
        }

        private static void Scale(Vector3[] deltas, Vector3[] normals, float s)
        {
            if (s == 1)
            {
                return;
            }
            for (int v = 0; v < deltas.Length; v++)
            {
                deltas[v] *= s;
                normals[v] *= s;
            }
        }

        /// <summary>
        /// A shape key from blend-shape weights (index to 0–100), carried into the rest pose through the
        /// mesh's skin. Returns null when it moves nothing.
        /// </summary>
        public static Core.MorphData Bake(Mesh mesh, System.Collections.Generic.IDictionary<int, float> weights, Matrix4x4[] skin, BoneWeight[] skinWeights)
        {
            int count = mesh.vertexCount;
            var sum = new Vector3[count];
            var sumNormals = new Vector3[count];
            var deltas = new Vector3[count];
            var normals = new Vector3[count];
            var tangents = new Vector3[count];
            bool any = false;
            foreach (var pair in weights)
            {
                if (pair.Value == 0 || pair.Key < 0 || pair.Key >= mesh.blendShapeCount)
                {
                    continue;
                }
                any = true;
                Frame(mesh, pair.Key, pair.Value, deltas, normals, tangents);
                for (int v = 0; v < count; v++)
                {
                    sum[v] += deltas[v];
                    sumNormals[v] += normals[v];
                }
            }
            if (!any)
            {
                return null;
            }
            var morph = new Core.MorphData { PositionDeltas = new Vec3[count], NormalDeltas = new Vec3[count] };
            for (int v = 0; v < count; v++)
            {
                var m = Meshes.Blend(skin, skinWeights, v);
                morph.PositionDeltas[v] = Seam.V3(m.MultiplyVector(sum[v]));
                morph.NormalDeltas[v] = Seam.V3(m.MultiplyVector(sumNormals[v]));
            }
            return Core.AdapterKit.Deltas.IsEmpty(morph.PositionDeltas) ? null : morph;
        }
    }
}
