using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core
{
    /// <summary>
    /// Mirrors the Body Pass exactly across X = 0 where it is nearly mirrored already (ADR 0047), so
    /// Blender's X Mirror finds every vertex's partner. Each vertex within <see cref="MaxOffset"/> of
    /// another's mirror image is paired with it, and both move to the halfway mirror positions; one
    /// within half of it of X = 0 is its own partner and moves onto X = 0. Vertices farther off stay.
    ///
    /// It works on positions, not vertices: every vertex at one position moves together, so the copies
    /// <see cref="Welds"/> made the same stay the same. A position is paired inside one mesh first, then
    /// across meshes (the left and right eyes are separate meshes). Normals and shape keys stay as they are.
    /// </summary>
    public static class Symmetry
    {
        /// <summary>The farthest a vertex may be from its partner's mirror image and still be paired, in metres.</summary>
        public const float MaxOffset = 1e-4f;

        public sealed class Result
        {
            /// <summary>Positions paired with another.</summary>
            public int Paired;

            /// <summary>Positions put on X = 0.</summary>
            public int Centred;

            /// <summary>Positions left as they were, with no partner within MaxOffset.</summary>
            public int Unpaired;
        }

        public static Result Mirror(IList<MeshData> meshes)
        {
            var points = new List<Point>();
            var byPosition = new Dictionary<Vec3, Point>(new ExactComparer());
            var usable = new List<MeshData>();
            foreach (var mesh in meshes)
            {
                if (mesh != null && mesh.Positions != null)
                {
                    usable.Add(mesh);
                }
            }
            for (int m = 0; m < usable.Count; m++)
            {
                var positions = usable[m].Positions;
                for (int v = 0; v < positions.Length; v++)
                {
                    Point p;
                    if (!byPosition.TryGetValue(positions[v], out p))
                    {
                        p = new Point { Id = points.Count, At = positions[v] };
                        byPosition[positions[v]] = p;
                        points.Add(p);
                    }
                    if (!p.Meshes.Contains(m))
                    {
                        p.Meshes.Add(m);
                    }
                    p.Vertices.Add(new KeyValuePair<int, int>(m, v));
                }
            }

            var result = new Result();
            for (int m = 0; m < usable.Count; m++)
            {
                Pair(points.FindAll(p => p.Partner == null && p.Meshes.Contains(m)), result);
            }
            Pair(points.FindAll(p => p.Partner == null), result);

            foreach (var p in points)
            {
                if (p.Partner == null)
                {
                    result.Unpaired++;
                    continue;
                }
                if (p.Partner == p)
                {
                    p.To = new Vec3(0, p.At.Y, p.At.Z);
                    continue;
                }
                // Computed the same way from either side, so the two end as exact mirror images.
                var lo = p.Id < p.Partner.Id ? p : p.Partner;
                var hi = lo == p ? p.Partner : p;
                float x = (float)(((double)lo.At.X - hi.At.X) / 2);
                float y = (float)(((double)lo.At.Y + hi.At.Y) / 2);
                float z = (float)(((double)lo.At.Z + hi.At.Z) / 2);
                p.To = new Vec3(lo == p ? x : -x, y, z);
            }
            foreach (var p in points)
            {
                if (p.Partner == null)
                {
                    continue;
                }
                foreach (var vertex in p.Vertices)
                {
                    usable[vertex.Key].Positions[vertex.Value] = p.To;
                }
            }
            return result;
        }

        /// <summary>Pairs each point with the one nearest its mirror image, where each is the other's nearest.</summary>
        private static void Pair(List<Point> candidates, Result result)
        {
            var grid = new Grid(MaxOffset);
            foreach (var p in candidates)
            {
                grid.Add(p.At, p.Id);
            }
            var byId = new Dictionary<int, Point>();
            foreach (var p in candidates)
            {
                byId[p.Id] = p;
            }
            foreach (var p in candidates)
            {
                if (p.Partner != null)
                {
                    continue;
                }
                var q = Nearest(grid, byId, Mirrored(p.At));
                if (q == null)
                {
                    continue;
                }
                if (q == p)
                {
                    p.Partner = p;
                    result.Centred++;
                    continue;
                }
                if (Nearest(grid, byId, Mirrored(q.At)) != p)
                {
                    continue;
                }
                p.Partner = q;
                q.Partner = p;
                result.Paired += 2;
            }
        }

        /// <summary>The unpaired candidate nearest `at` within MaxOffset, or null.</summary>
        private static Point Nearest(Grid grid, Dictionary<int, Point> byId, Vec3 at)
        {
            Point best = null;
            float bestDistance = float.MaxValue;
            foreach (int id in grid.Near(at))
            {
                var p = byId[id];
                if (p.Partner != null)
                {
                    continue;
                }
                float d = (p.At - at).Length;
                if (d <= MaxOffset && (d < bestDistance || (d == bestDistance && p.Id < best.Id)))
                {
                    best = p;
                    bestDistance = d;
                }
            }
            return best;
        }

        private static Vec3 Mirrored(Vec3 v)
        {
            return new Vec3(-v.X, v.Y, v.Z);
        }

        private sealed class Point
        {
            public int Id;
            public Vec3 At;
            public Vec3 To;
            public Point Partner;
            public readonly List<int> Meshes = new List<int>();
            public readonly List<KeyValuePair<int, int>> Vertices = new List<KeyValuePair<int, int>>();
        }

        /// <summary>Positions equal to the bit, except that 0 and -0 are one.</summary>
        private sealed class ExactComparer : IEqualityComparer<Vec3>
        {
            public bool Equals(Vec3 a, Vec3 b)
            {
                return a.X == b.X && a.Y == b.Y && a.Z == b.Z;
            }

            public int GetHashCode(Vec3 v)
            {
                return ((v.X == 0 ? 0f : v.X).GetHashCode() * 397 ^ (v.Y == 0 ? 0f : v.Y).GetHashCode()) * 397 ^ (v.Z == 0 ? 0f : v.Z).GetHashCode();
            }
        }
    }
}
