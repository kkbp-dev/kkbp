using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Closes the seam a shape key nearly closes (ADR 0033). SVS's face has a separate disc in each eye
    /// socket whose open edge pairs with the socket rim's; the game's gag shape moves the disc forward
    /// but leaves its edge about half a millimetre off the rim, a crack that shows in Blender. Each
    /// open-edge vertex the key moves is put exactly on the nearest open-edge vertex it leaves still.
    /// </summary>
    public static class SeamClosing
    {
        /// <summary>The farthest a moved edge vertex may end from its partner and still be closed, in metres.</summary>
        public const float MaxGap = 0.001f;

        /// <summary>Vertices closer than this count as one when finding open edges (UV seams split them), in metres.</summary>
        public const float WeldTolerance = 1e-5f;

        /// <summary>
        /// Closes the seams of the mesh's shape keys in the category. A key is changed only if every
        /// open-edge vertex it moves ends within MaxGap of one it doesn't move; one that moves the
        /// rim as well, or stops farther off, stays as the game made it. Returns the keys it closed.
        /// </summary>
        public static List<MorphData> Close(MeshData mesh, ExpressionCategory category)
        {
            if (mesh == null || mesh.Positions == null)
            {
                throw new ArgumentException("The mesh has no vertices.", "mesh");
            }
            var closed = new List<MorphData>();
            var open = OpenEdgeVertices(mesh);
            if (open.Count == 0)
            {
                return closed;
            }
            var positions = mesh.Positions;
            foreach (var morph in mesh.Morphs)
            {
                if (morph.Category != category || morph.PositionDeltas == null || morph.PositionDeltas.Length != positions.Length)
                {
                    continue;
                }
                var deltas = morph.PositionDeltas;
                var moved = new List<int>();
                var still = new List<int>();
                foreach (int v in open)
                {
                    (Moves(deltas[v]) ? moved : still).Add(v);
                }
                if (moved.Count == 0 || still.Count == 0)
                {
                    continue;
                }
                var targets = new Vec3[moved.Count];
                bool closes = true;
                for (int i = 0; i < moved.Count && closes; i++)
                {
                    var at = positions[moved[i]] + deltas[moved[i]];
                    float best = float.MaxValue;
                    foreach (int s in still)
                    {
                        var to = positions[s] + deltas[s];
                        float gap = (to - at).Length;
                        if (gap < best)
                        {
                            best = gap;
                            targets[i] = to;
                        }
                    }
                    closes = best <= MaxGap;
                }
                if (!closes)
                {
                    continue;
                }
                for (int i = 0; i < moved.Count; i++)
                {
                    deltas[moved[i]] = targets[i] - positions[moved[i]];
                }
                closed.Add(morph);
            }
            return closed;
        }

        /// <summary>
        /// The vertices on an edge only one triangle uses, after welding vertices at the same
        /// position, so a UV seam isn't taken for an open edge.
        /// </summary>
        public static List<int> OpenEdgeVertices(MeshData mesh)
        {
            var weld = Weld(mesh.Positions);
            var edges = new Dictionary<long, int>();
            foreach (var sub in mesh.SubMeshes)
            {
                var idx = sub.Indices;
                for (int t = 0; t + 2 < idx.Length; t += 3)
                {
                    Count(edges, weld[idx[t]], weld[idx[t + 1]]);
                    Count(edges, weld[idx[t + 1]], weld[idx[t + 2]]);
                    Count(edges, weld[idx[t + 2]], weld[idx[t]]);
                }
            }
            var openIds = new HashSet<int>();
            foreach (var pair in edges)
            {
                if (pair.Value == 1)
                {
                    openIds.Add((int)(pair.Key >> 32));
                    openIds.Add((int)(pair.Key & 0xffffffff));
                }
            }
            var result = new List<int>();
            for (int v = 0; v < weld.Length; v++)
            {
                if (openIds.Contains(weld[v]))
                {
                    result.Add(v);
                }
            }
            return result;
        }

        private static bool Moves(Vec3 d)
        {
            return Math.Abs(d.X) > Deltas.Tolerance || Math.Abs(d.Y) > Deltas.Tolerance || Math.Abs(d.Z) > Deltas.Tolerance;
        }

        private static int[] Weld(Vec3[] positions)
        {
            var ids = new Dictionary<string, int>();
            var weld = new int[positions.Length];
            for (int v = 0; v < positions.Length; v++)
            {
                var p = positions[v];
                string key = Cell(p.X) + "," + Cell(p.Y) + "," + Cell(p.Z);
                int id;
                if (!ids.TryGetValue(key, out id))
                {
                    id = ids.Count;
                    ids[key] = id;
                }
                weld[v] = id;
            }
            return weld;
        }

        private static long Cell(float x)
        {
            return (long)Math.Round(x / WeldTolerance);
        }

        private static void Count(Dictionary<long, int> edges, int a, int b)
        {
            if (a == b)
            {
                return;
            }
            long key = a < b ? ((long)a << 32) | (uint)b : ((long)b << 32) | (uint)a;
            int n;
            edges.TryGetValue(key, out n);
            edges[key] = n + 1;
        }
    }
}
