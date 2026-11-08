using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core
{
    /// <summary>
    /// Unit-length normals and tangents, as glTF requires. Game meshes sometimes carry a zero-length or
    /// non-finite normal or tangent (degenerate clothes and accessory vertices): such a vertex takes the
    /// average of its triangle neighbours' good ones, or failing that any direction that fits.
    /// </summary>
    public static class MeshVectors
    {
        /// <summary>Below this length a vector has no usable direction.</summary>
        public const float MinLength = 1e-6f;

        /// <summary>Unit normals for <paramref name="normals"/>; bad ones are rebuilt from the vertices they share a triangle with.</summary>
        public static Vec3[] Normals(Vec3[] normals, IEnumerable<int[]> triangles)
        {
            var result = new Vec3[normals.Length];
            var bad = new List<int>();
            for (int i = 0; i < normals.Length; i++)
            {
                Vec3 unit;
                if (TryUnit(normals[i], out unit))
                {
                    result[i] = unit;
                }
                else
                {
                    bad.Add(i);
                }
            }
            if (bad.Count == 0)
            {
                return result;
            }
            var neighbours = Neighbours(bad, triangles);
            foreach (int i in bad)
            {
                var sum = Vec3.Zero;
                foreach (int n in neighbours[i])
                {
                    Vec3 unit;
                    if (TryUnit(normals[n], out unit))
                    {
                        sum = sum + unit;
                    }
                }
                Vec3 average;
                result[i] = TryUnit(sum, out average) ? average : new Vec3(0, 0, 1);
            }
            return result;
        }

        /// <summary>
        /// Unit tangents for <paramref name="tangents"/>, with W of 1 or -1. A bad one takes its triangle
        /// neighbours' tangents, made perpendicular to its (unit) normal, or else a direction perpendicular
        /// to the normal.
        /// </summary>
        public static Vec4[] Tangents(Vec4[] tangents, Vec3[] unitNormals, IEnumerable<int[]> triangles)
        {
            var result = new Vec4[tangents.Length];
            var bad = new List<int>();
            for (int i = 0; i < tangents.Length; i++)
            {
                Vec3 unit;
                if (TryUnit(Xyz(tangents[i]), out unit))
                {
                    result[i] = new Vec4(unit.X, unit.Y, unit.Z, Sign(tangents[i].W));
                }
                else
                {
                    bad.Add(i);
                }
            }
            if (bad.Count == 0)
            {
                return result;
            }
            var neighbours = Neighbours(bad, triangles);
            foreach (int i in bad)
            {
                Vec3 normal = unitNormals != null && i < unitNormals.Length ? unitNormals[i] : new Vec3(0, 0, 1);
                var sum = Vec3.Zero;
                float w = 0;
                foreach (int n in neighbours[i])
                {
                    Vec3 unit;
                    if (TryUnit(Xyz(tangents[n]), out unit))
                    {
                        sum = sum + unit;
                        w += Sign(tangents[n].W);
                    }
                }
                Vec3 tangent;
                if (!TryUnit(Perpendicular(sum, normal), out tangent))
                {
                    var axis = Math.Abs(normal.X) < 0.9f ? new Vec3(1, 0, 0) : new Vec3(0, 1, 0);
                    TryUnit(Perpendicular(axis, normal), out tangent);
                }
                float own = tangents[i].W;
                result[i] = new Vec4(tangent.X, tangent.Y, tangent.Z, own != 0 && !float.IsNaN(own) ? Sign(own) : Sign(w));
            }
            return result;
        }

        /// <summary><paramref name="v"/> at unit length, in double precision, if it has a direction.</summary>
        public static bool TryUnit(Vec3 v, out Vec3 unit)
        {
            double length = Math.Sqrt((double)v.X * v.X + (double)v.Y * v.Y + (double)v.Z * v.Z);
            if (double.IsNaN(length) || double.IsInfinity(length) || length < MinLength)
            {
                unit = Vec3.Zero;
                return false;
            }
            unit = new Vec3((float)(v.X / length), (float)(v.Y / length), (float)(v.Z / length));
            return true;
        }

        private static Vec3 Perpendicular(Vec3 v, Vec3 unitNormal)
        {
            float along = v.X * unitNormal.X + v.Y * unitNormal.Y + v.Z * unitNormal.Z;
            return v - unitNormal * along;
        }

        private static Vec3 Xyz(Vec4 t)
        {
            return new Vec3(t.X, t.Y, t.Z);
        }

        private static float Sign(float w)
        {
            return w < 0 ? -1 : 1;
        }

        /// <summary>For each vertex in <paramref name="vertices"/>, the other vertices of the triangles it is in.</summary>
        private static Dictionary<int, List<int>> Neighbours(List<int> vertices, IEnumerable<int[]> triangles)
        {
            var result = new Dictionary<int, List<int>>();
            foreach (int v in vertices)
            {
                result[v] = new List<int>();
            }
            foreach (var indices in triangles)
            {
                for (int t = 0; t + 2 < indices.Length; t += 3)
                {
                    for (int k = 0; k < 3; k++)
                    {
                        List<int> list;
                        if (result.TryGetValue(indices[t + k], out list))
                        {
                            list.Add(indices[t + (k + 1) % 3]);
                            list.Add(indices[t + (k + 2) % 3]);
                        }
                    }
                }
            }
            return result;
        }
    }
}
