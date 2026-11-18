using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core
{
    /// <summary>
    /// Makes the vertices that sit on top of each other the same vertex in everything but their corners
    /// (ADR 0047). A UV seam or a hard edge needs two glTF vertices where Blender wants one, and the game
    /// writes those copies up to a few micrometres apart, with weights and shape keys that can differ. Each
    /// group of copies gets one position, one set of weights and one offset per shape key, so the importer
    /// can weld them without choosing between them; normals, tangents, UVs and colours stay per copy.
    ///
    /// Copies are grouped within <see cref="Distance"/> inside one mesh, by their unposed positions where
    /// the adapter gives them, so physics can't change which vertices are copies (ADR 0052), and between a face and a body
    /// mesh within <see cref="SeamDistance"/>, where the neck meets: SVS writes those pairs up to 0.026 mm
    /// apart. Two vertices of one triangle are never grouped (that would collapse it), and nor are the
    /// vertices of two triangles that would then be the same triangle (a double-sided card's back).
    /// </summary>
    public static class Welds
    {
        /// <summary>
        /// How far apart two copies in one mesh may be, in metres. Up to here the Golden Samples group
        /// every UV-seam copy and nothing else; from 0.03 mm short edges begin to collapse.
        /// </summary>
        public const float Distance = 1e-5f;

        /// <summary>How far a face vertex may be from a body vertex at the neck and still be its copy, in metres.</summary>
        public const float SeamDistance = 1e-4f;

        public sealed class Result
        {
            /// <summary>Groups of two or more copies.</summary>
            public int Groups;

            /// <summary>Copies that join one in another mesh (the neck).</summary>
            public int SeamCopies;

            /// <summary>Vertices left out because grouping them would make two triangles one.</summary>
            public int KeptApart;
        }

        /// <summary>
        /// Welds the Pass's meshes. <paramref name="roles"/> gives each captured material's Material Role,
        /// by material key; the seam joins vertices on a Face material to vertices on a Body material.
        /// A mesh with arrays that don't fit is left alone: the Core's own checks report it.
        /// </summary>
        public static Result Weld(IList<MeshData> meshes, IDictionary<string, MaterialRole> roles)
        {
            var all = new List<MeshData>();
            foreach (var mesh in meshes)
            {
                if (Usable(mesh))
                {
                    all.Add(mesh);
                }
            }
            var graph = new Graph(all, roles);
            var result = new Result();
            for (int m = 0; m < all.Count; m++)
            {
                graph.GroupWithin(m);
            }
            result.SeamCopies = graph.GroupAcrossSeam();
            result.KeptApart = graph.KeepDoubledTrianglesApart();
            result.Groups = graph.Apply();
            return result;
        }

        /// <summary>True if the mesh's arrays fit its vertex count, so welding can't index past them.</summary>
        public static bool Usable(MeshData mesh)
        {
            if (mesh == null || mesh.Positions == null || mesh.Positions.Length == 0 || mesh.BoneKeys == null)
            {
                return false;
            }
            int count = mesh.Positions.Length;
            int slots = mesh.InfluencesPerVertex;
            if (slots <= 0 || mesh.Joints == null || mesh.Weights == null
                || mesh.Joints.Length != count * slots || mesh.Weights.Length != count * slots)
            {
                return false;
            }
            foreach (var sub in mesh.SubMeshes)
            {
                if (sub == null || sub.Indices == null || sub.Indices.Length % 3 != 0)
                {
                    return false;
                }
                foreach (int i in sub.Indices)
                {
                    if (i < 0 || i >= count)
                    {
                        return false;
                    }
                }
            }
            foreach (var morph in mesh.Morphs)
            {
                if (morph == null || (morph.PositionDeltas != null && morph.PositionDeltas.Length != count))
                {
                    return false;
                }
            }
            return true;
        }

        /// <summary>Every vertex of every mesh, numbered in one range, with the groups found so far.</summary>
        private sealed class Graph
        {
            private readonly List<MeshData> meshes;
            private readonly int[] offset;
            private readonly int[] meshOf;
            private readonly Vec3[] position;

            /// <summary>Where each vertex is found from: its unposed position, or its position without one.</summary>
            private readonly Vec3[] found;
            private readonly bool[] onFace;
            private readonly bool[] onBody;
            private readonly List<int>[] neighbours;
            private readonly int[] parent;
            private readonly List<int>[] members;
            private readonly bool[] apart;

            public Graph(List<MeshData> meshes, IDictionary<string, MaterialRole> roles)
            {
                this.meshes = meshes;
                offset = new int[meshes.Count + 1];
                for (int m = 0; m < meshes.Count; m++)
                {
                    offset[m + 1] = offset[m] + meshes[m].Positions.Length;
                }
                int n = offset[meshes.Count];
                meshOf = new int[n];
                position = new Vec3[n];
                found = new Vec3[n];
                onFace = new bool[n];
                onBody = new bool[n];
                neighbours = new List<int>[n];
                parent = new int[n];
                members = new List<int>[n];
                apart = new bool[n];
                for (int m = 0; m < meshes.Count; m++)
                {
                    var mesh = meshes[m];
                    var unposed = mesh.UnposedPositions != null && mesh.UnposedPositions.Length == mesh.Positions.Length
                        ? mesh.UnposedPositions : mesh.Positions;
                    for (int v = 0; v < mesh.Positions.Length; v++)
                    {
                        int g = offset[m] + v;
                        meshOf[g] = m;
                        position[g] = mesh.Positions[v];
                        found[g] = unposed[v];
                        parent[g] = g;
                    }
                    foreach (var sub in mesh.SubMeshes)
                    {
                        MaterialRole role;
                        bool known = sub.MaterialKey != null && roles != null && roles.TryGetValue(sub.MaterialKey, out role);
                        bool face = known && roles[sub.MaterialKey] == MaterialRole.Face;
                        bool body = known && roles[sub.MaterialKey] == MaterialRole.Body;
                        var idx = sub.Indices;
                        for (int t = 0; t < idx.Length; t += 3)
                        {
                            for (int k = 0; k < 3; k++)
                            {
                                int g = offset[m] + idx[t + k];
                                onFace[g] |= face;
                                onBody[g] |= body;
                                Link(g, offset[m] + idx[t + (k + 1) % 3]);
                            }
                        }
                    }
                }
            }

            private void Link(int a, int b)
            {
                if (a == b)
                {
                    return;
                }
                (neighbours[a] ?? (neighbours[a] = new List<int>())).Add(b);
                (neighbours[b] ?? (neighbours[b] = new List<int>())).Add(a);
            }

            /// <summary>
            /// Groups the copies inside mesh m, by their unposed positions (ADR 0052): physics moves SVS hair
            /// copies a few micrometres between exports, which carried some across the distance. Each vertex
            /// joins its candidates in index order, not the grid's: where a cluster can't all be one (it would
            /// collapse a triangle), the pair joined first wins.
            /// </summary>
            public void GroupWithin(int m)
            {
                var grid = new Grid(Distance);
                for (int g = offset[m]; g < offset[m + 1]; g++)
                {
                    grid.Add(found[g], g);
                }
                var near = new List<int>();
                for (int g = offset[m]; g < offset[m + 1]; g++)
                {
                    near.Clear();
                    foreach (int other in grid.Near(found[g]))
                    {
                        if (other > g && (found[other] - found[g]).Length <= Distance)
                        {
                            near.Add(other);
                        }
                    }
                    near.Sort();
                    foreach (int other in near)
                    {
                        Unite(g, other);
                    }
                }
            }

            /// <summary>Joins each face vertex to the nearest body vertex of another mesh within SeamDistance.</summary>
            public int GroupAcrossSeam()
            {
                var grid = new Grid(SeamDistance);
                bool any = false;
                for (int g = 0; g < position.Length; g++)
                {
                    if (onBody[g])
                    {
                        grid.Add(position[g], g);
                        any = true;
                    }
                }
                if (!any)
                {
                    return 0;
                }
                int joined = 0;
                for (int g = 0; g < position.Length; g++)
                {
                    if (!onFace[g])
                    {
                        continue;
                    }
                    int best = -1;
                    float bestDistance = float.MaxValue;
                    foreach (int other in grid.Near(position[g]))
                    {
                        float d = (position[other] - position[g]).Length;
                        if (meshOf[other] != meshOf[g] && d <= SeamDistance && d < bestDistance)
                        {
                            best = other;
                            bestDistance = d;
                        }
                    }
                    if (best >= 0 && Find(best) != Find(g) && Unite(g, best))
                    {
                        joined++;
                    }
                }
                return joined;
            }

            /// <summary>
            /// Takes out of their groups the vertices of triangles that would become the same triangle,
            /// until none would. Returns how many vertices were taken out. Each pass reads the groups as
            /// they stood when it began: taking vertices out halfway through would hide the triangles they
            /// double from the rest of the pass.
            /// </summary>
            public int KeepDoubledTrianglesApart()
            {
                int taken = 0;
                bool changed = true;
                while (changed)
                {
                    changed = false;
                    var ids = new int[position.Length];
                    for (int g = 0; g < ids.Length; g++)
                    {
                        ids[g] = Id(g);
                    }
                    var doubled = new List<int>();
                    for (int m = 0; m < meshes.Count; m++)
                    {
                        var seen = new Dictionary<Triple, int[]>();
                        foreach (var sub in meshes[m].SubMeshes)
                        {
                            var idx = sub.Indices;
                            for (int t = 0; t < idx.Length; t += 3)
                            {
                                var corners = new[] { offset[m] + idx[t], offset[m] + idx[t + 1], offset[m] + idx[t + 2] };
                                var key = new Triple(ids[corners[0]], ids[corners[1]], ids[corners[2]]);
                                int[] first;
                                if (!seen.TryGetValue(key, out first))
                                {
                                    seen[key] = corners;
                                    continue;
                                }
                                if (new Triple(first[0], first[1], first[2]).Equals(new Triple(corners[0], corners[1], corners[2])))
                                {
                                    continue; // the game lists the same triangle twice: welding doesn't change that
                                }
                                doubled.AddRange(first);
                                doubled.AddRange(corners);
                            }
                        }
                    }
                    foreach (int g in doubled)
                    {
                        changed |= TakeApart(g, ref taken);
                    }
                }
                return taken;
            }

            private bool TakeApart(int g, ref int taken)
            {
                if (apart[g] || Members(Find(g)).Count < 2)
                {
                    return false;
                }
                apart[g] = true;
                taken++;
                return true;
            }

            /// <summary>
            /// The group a vertex ends in: its own if it was taken apart, numbered past the vertices so it
            /// can't match the group it left, whose id may be this vertex's index.
            /// </summary>
            private int Id(int g)
            {
                return apart[g] ? position.Length + g : Find(g);
            }

            /// <summary>Writes each group's shared position, weights and shape keys. Returns the number of groups.</summary>
            public int Apply()
            {
                var groups = new Dictionary<int, List<int>>();
                for (int g = 0; g < position.Length; g++)
                {
                    if (apart[g])
                    {
                        continue;
                    }
                    int root = Find(g);
                    List<int> list;
                    if (!groups.TryGetValue(root, out list))
                    {
                        groups[root] = list = new List<int>();
                    }
                    list.Add(g);
                }
                var boneIndex = new List<Dictionary<string, int>>();
                var boneKeys = new List<List<string>>();
                foreach (var mesh in meshes)
                {
                    var index = new Dictionary<string, int>();
                    for (int i = 0; i < mesh.BoneKeys.Length; i++)
                    {
                        if (mesh.BoneKeys[i] != null && !index.ContainsKey(mesh.BoneKeys[i]))
                        {
                            index[mesh.BoneKeys[i]] = i;
                        }
                    }
                    boneIndex.Add(index);
                    boneKeys.Add(new List<string>(mesh.BoneKeys));
                }

                int count = 0;
                foreach (var group in groups.Values)
                {
                    if (group.Count < 2)
                    {
                        continue;
                    }
                    count++;
                    // Within one mesh every copy counts; across the neck the body's weights and shape keys
                    // win, as the body vertex is what the face's edge is welded onto.
                    bool spans = false;
                    foreach (int g in group)
                    {
                        spans |= meshOf[g] != meshOf[group[0]];
                    }
                    var sources = new List<int>();
                    foreach (int g in group)
                    {
                        if (!spans || onBody[g])
                        {
                            sources.Add(g);
                        }
                    }
                    if (sources.Count == 0)
                    {
                        sources.AddRange(group);
                    }

                    double x = 0, y = 0, z = 0;
                    foreach (int g in group)
                    {
                        x += position[g].X;
                        y += position[g].Y;
                        z += position[g].Z;
                    }
                    var shared = new Vec3((float)(x / group.Count), (float)(y / group.Count), (float)(z / group.Count));
                    foreach (int g in group)
                    {
                        meshes[meshOf[g]].Positions[g - offset[meshOf[g]]] = shared;
                    }
                    ShareWeights(group, sources, boneIndex, boneKeys);
                    ShareShapeKeys(group, sources);
                }
                for (int m = 0; m < meshes.Count; m++)
                {
                    if (boneKeys[m].Count != meshes[m].BoneKeys.Length)
                    {
                        meshes[m].BoneKeys = boneKeys[m].ToArray();
                    }
                }
                return count;
            }

            private void ShareWeights(List<int> group, List<int> sources, List<Dictionary<string, int>> boneIndex, List<List<string>> boneKeys)
            {
                var first = WeightsOf(group[0]);
                bool same = true;
                foreach (int g in group)
                {
                    same &= SameWeights(first, WeightsOf(g));
                }
                if (same)
                {
                    return;
                }
                var sum = new Dictionary<string, double>();
                foreach (int g in sources)
                {
                    foreach (var pair in WeightsOf(g))
                    {
                        double s;
                        sum.TryGetValue(pair.Key, out s);
                        sum[pair.Key] = s + pair.Value / sources.Count;
                    }
                }
                var ordered = new List<KeyValuePair<string, double>>(sum);
                ordered.Sort((a, b) => a.Value != b.Value ? b.Value.CompareTo(a.Value) : string.CompareOrdinal(a.Key, b.Key));
                foreach (int g in group)
                {
                    int m = meshOf[g];
                    var mesh = meshes[m];
                    int slots = mesh.InfluencesPerVertex;
                    int v = g - offset[m];
                    for (int s = 0; s < slots; s++)
                    {
                        int at = v * slots + s;
                        if (s >= ordered.Count)
                        {
                            mesh.Joints[at] = 0;
                            mesh.Weights[at] = 0;
                            continue;
                        }
                        string bone = ordered[s].Key;
                        int index;
                        if (!boneIndex[m].TryGetValue(bone, out index))
                        {
                            index = boneKeys[m].Count;
                            boneKeys[m].Add(bone);
                            boneIndex[m][bone] = index;
                        }
                        mesh.Joints[at] = index;
                        mesh.Weights[at] = (float)ordered[s].Value;
                    }
                }
            }

            /// <summary>The vertex's weights by bone key, normalised; empty if it has none.</summary>
            private Dictionary<string, double> WeightsOf(int g)
            {
                var mesh = meshes[meshOf[g]];
                int slots = mesh.InfluencesPerVertex;
                int v = g - offset[meshOf[g]];
                var result = new Dictionary<string, double>();
                double total = 0;
                for (int s = 0; s < slots; s++)
                {
                    float w = mesh.Weights[v * slots + s];
                    int j = mesh.Joints[v * slots + s];
                    if (w <= 0 || j < 0 || j >= mesh.BoneKeys.Length || mesh.BoneKeys[j] == null)
                    {
                        continue;
                    }
                    double e;
                    result.TryGetValue(mesh.BoneKeys[j], out e);
                    result[mesh.BoneKeys[j]] = e + w;
                    total += w;
                }
                if (total > 0)
                {
                    foreach (var key in new List<string>(result.Keys))
                    {
                        result[key] /= total;
                    }
                }
                return result;
            }

            private static bool SameWeights(Dictionary<string, double> a, Dictionary<string, double> b)
            {
                if (a.Count != b.Count)
                {
                    return false;
                }
                foreach (var pair in a)
                {
                    double other;
                    if (!b.TryGetValue(pair.Key, out other) || Math.Abs(other - pair.Value) > 1e-6)
                    {
                        return false;
                    }
                }
                return true;
            }

            /// <summary>
            /// Gives every copy one offset per shape key: the sources' mean in a mesh that has sources, and
            /// otherwise the sources' offset in the shape key of the same name, or none if they have no such key.
            /// </summary>
            private void ShareShapeKeys(List<int> group, List<int> sources)
            {
                var meshesInGroup = new List<int>();
                foreach (int g in group)
                {
                    if (!meshesInGroup.Contains(meshOf[g]))
                    {
                        meshesInGroup.Add(meshOf[g]);
                    }
                }
                foreach (int m in meshesInGroup)
                {
                    foreach (var morph in meshes[m].Morphs)
                    {
                        if (morph.PositionDeltas == null)
                        {
                            continue;
                        }
                        double x = 0, y = 0, z = 0;
                        int n = 0;
                        foreach (int g in sources)
                        {
                            var deltas = DeltasIn(meshOf[g], m, morph);
                            if (deltas == null)
                            {
                                continue;
                            }
                            var d = deltas[g - offset[meshOf[g]]];
                            x += d.X;
                            y += d.Y;
                            z += d.Z;
                            n++;
                        }
                        var shared = n == 0 ? Vec3.Zero : new Vec3((float)(x / n), (float)(y / n), (float)(z / n));
                        foreach (int g in group)
                        {
                            if (meshOf[g] == m)
                            {
                                morph.PositionDeltas[g - offset[m]] = shared;
                            }
                        }
                    }
                }
            }

            /// <summary>The offsets of mesh `source`'s shape key that matches `morph` of mesh `m`, or null.</summary>
            private Vec3[] DeltasIn(int source, int m, MorphData morph)
            {
                if (source == m)
                {
                    return morph.PositionDeltas;
                }
                foreach (var other in meshes[source].Morphs)
                {
                    if (other.PositionDeltas != null && other.TargetName == morph.TargetName)
                    {
                        return other.PositionDeltas;
                    }
                }
                return null;
            }

            private int Find(int g)
            {
                while (parent[g] != g)
                {
                    parent[g] = parent[parent[g]];
                    g = parent[g];
                }
                return g;
            }

            private List<int> Members(int root)
            {
                return members[root] ?? (members[root] = new List<int> { root });
            }

            /// <summary>Joins the groups of a and b, unless one holds a vertex the other shares a triangle with.</summary>
            private bool Unite(int a, int b)
            {
                int ra = Find(a), rb = Find(b);
                if (ra == rb)
                {
                    return true;
                }
                var ma = Members(ra);
                var mb = Members(rb);
                foreach (int g in ma)
                {
                    if (neighbours[g] == null)
                    {
                        continue;
                    }
                    foreach (int n in neighbours[g])
                    {
                        if (Find(n) == rb)
                        {
                            return false;
                        }
                    }
                }
                if (ma.Count < mb.Count)
                {
                    var t = ra; ra = rb; rb = t;
                    var l = ma; ma = mb; mb = l;
                }
                parent[rb] = ra;
                ma.AddRange(mb);
                members[rb] = null;
                return true;
            }
        }

        /// <summary>Three ids in either order, for finding triangles with the same corners.</summary>
        private struct Triple : IEquatable<Triple>
        {
            private readonly int a, b, c;

            public Triple(int x, int y, int z)
            {
                if (x > y) { var t = x; x = y; y = t; }
                if (y > z) { var t = y; y = z; z = t; }
                if (x > y) { var t = x; x = y; y = t; }
                a = x;
                b = y;
                c = z;
            }

            public bool Equals(Triple o)
            {
                return a == o.a && b == o.b && c == o.c;
            }

            public override bool Equals(object obj)
            {
                return obj is Triple && Equals((Triple)obj);
            }

            public override int GetHashCode()
            {
                return (a * 73856093) ^ (b * 19349663) ^ (c * 83492791);
            }
        }
    }

    /// <summary>Points bucketed in cubes of one size, for finding the points near another.</summary>
    internal sealed class Grid
    {
        private readonly float size;
        private readonly Dictionary<long, List<int>> cells = new Dictionary<long, List<int>>();

        public Grid(float size)
        {
            this.size = size;
        }

        public void Add(Vec3 p, int id)
        {
            long key = Key(Cell(p.X), Cell(p.Y), Cell(p.Z));
            List<int> list;
            if (!cells.TryGetValue(key, out list))
            {
                cells[key] = list = new List<int>();
            }
            list.Add(id);
        }

        /// <summary>The ids in p's cube and the 26 around it: every point within one cube size, and some farther.</summary>
        public IEnumerable<int> Near(Vec3 p)
        {
            long cx = Cell(p.X), cy = Cell(p.Y), cz = Cell(p.Z);
            for (long dx = -1; dx <= 1; dx++)
            {
                for (long dy = -1; dy <= 1; dy++)
                {
                    for (long dz = -1; dz <= 1; dz++)
                    {
                        List<int> list;
                        if (cells.TryGetValue(Key(cx + dx, cy + dy, cz + dz), out list))
                        {
                            foreach (int id in list)
                            {
                                yield return id;
                            }
                        }
                    }
                }
            }
        }

        private long Cell(float v)
        {
            return (long)Math.Floor(v / size);
        }

        private static long Key(long x, long y, long z)
        {
            const long mask = (1L << 21) - 1;
            return ((x & mask) << 42) | ((y & mask) << 21) | (z & mask);
        }
    }
}
