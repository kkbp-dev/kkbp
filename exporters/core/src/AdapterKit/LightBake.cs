using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// The pixel and geometry steps of baking a material's light and dark Texture Variants. The adapter
    /// renders the material with the game's own shader twice, lit from the front and from behind: once
    /// on a quad covering UV space, and, for shaders whose look depends on the mesh, once on the mesh
    /// flattened into UV space. These helpers combine the renders. Pixels are RGBA32, rows bottom up.
    /// </summary>
    public static class LightBake
    {
        /// <summary>
        /// Depths that keep overlapping UV islands of a flattened mesh apart. Islands are joined through
        /// shared triangles; an island whose UV bounds overlap an earlier island's goes one layer back.
        /// Returns one depth per vertex (0, -0.0001, -0.0002, …).
        /// </summary>
        public static float[] IslandDepths(int[] triangles, Vec2[] uvs)
        {
            int n = uvs.Length;
            var parent = new int[n];
            var minX = new float[n];
            var minY = new float[n];
            var maxX = new float[n];
            var maxY = new float[n];
            for (int i = 0; i < n; i++)
            {
                parent[i] = i;
                minX[i] = maxX[i] = uvs[i].X;
                minY[i] = maxY[i] = uvs[i].Y;
            }
            for (int t = 0; t + 2 < triangles.Length; t += 3)
            {
                int a = Find(parent, triangles[t]);
                foreach (int corner in new[] { triangles[t + 1], triangles[t + 2] })
                {
                    int b = Find(parent, corner);
                    if (a == b)
                    {
                        continue;
                    }
                    parent[b] = a;
                    minX[a] = Math.Min(minX[a], minX[b]);
                    minY[a] = Math.Min(minY[a], minY[b]);
                    maxX[a] = Math.Max(maxX[a], maxX[b]);
                    maxY[a] = Math.Max(maxY[a], maxY[b]);
                }
            }

            var layers = new List<List<int>>();
            var depthOf = new Dictionary<int, float>();
            var depths = new float[n];
            for (int i = 0; i < n; i++)
            {
                int island = Find(parent, i);
                float depth;
                if (!depthOf.TryGetValue(island, out depth))
                {
                    int layer = 0;
                    for (; layer < layers.Count; layer++)
                    {
                        if (!layers[layer].Exists(other => Overlap(other, island, minX, minY, maxX, maxY)))
                        {
                            break;
                        }
                    }
                    if (layer == layers.Count)
                    {
                        layers.Add(new List<int>());
                    }
                    layers[layer].Add(island);
                    depth = -0.0001f * layer;
                    depthOf[island] = depth;
                }
                depths[i] = depth;
            }
            return depths;
        }

        private static int Find(int[] parent, int i)
        {
            int root = i;
            while (parent[root] != root)
            {
                root = parent[root];
            }
            while (parent[i] != root)
            {
                int next = parent[i];
                parent[i] = root;
                i = next;
            }
            return root;
        }

        private static bool Overlap(int a, int b, float[] minX, float[] minY, float[] maxX, float[] maxY)
        {
            return !(minX[a] >= maxX[b] || maxX[a] <= minX[b] || minY[a] >= maxY[b] || maxY[a] <= minY[b]);
        }

        /// <summary>
        /// Folds a render covering several UV tiles (UVs outside 0–1) onto one tile of
        /// <paramref name="size"/> pixels square, keeping the most opaque pixel at each point.
        /// </summary>
        public static byte[] Fold(byte[] pixels, int size, int tilesAcross, int tilesUp)
        {
            if (tilesAcross == 1 && tilesUp == 1)
            {
                return pixels;
            }
            int width = size * tilesAcross;
            var result = new byte[size * size * 4];
            for (int y = 0; y < size; y++)
            {
                for (int x = 0; x < size; x++)
                {
                    int dst = (y * size + x) * 4;
                    for (int ty = 0; ty < tilesUp && result[dst + 3] < 255; ty++)
                    {
                        for (int tx = 0; tx < tilesAcross && result[dst + 3] < 255; tx++)
                        {
                            int src = ((ty * size + y) * width + tx * size + x) * 4;
                            if (pixels[src + 3] > result[dst + 3])
                            {
                                Array.Copy(pixels, src, result, dst, 4);
                            }
                        }
                    }
                }
            }
            return result;
        }

        /// <summary>Puts the fully opaque pixels of the mesh render over the quad render.</summary>
        public static void Overlay(byte[] quad, byte[] mesh)
        {
            if (quad.Length != mesh.Length)
            {
                throw new ArgumentException("Both renders must be the same size.");
            }
            for (int i = 0; i < quad.Length; i += 4)
            {
                if (mesh[i + 3] == 255)
                {
                    Array.Copy(mesh, i, quad, i, 4);
                }
            }
        }

        /// <summary>
        /// Grows a mesh render's islands outwards by <paramref name="offset"/> pixels in eight directions,
        /// so texture filtering at island edges doesn't pick up the empty background. Nearly opaque pixels
        /// keep their own colour.
        /// </summary>
        public static byte[] Pad(byte[] pixels, int width, int height, int offset)
        {
            var result = new byte[pixels.Length];
            int[,] shifts = { { 1, 1 }, { 1, -1 }, { -1, -1 }, { -1, 1 }, { 1, 0 }, { -1, 0 }, { 0, 1 }, { 0, -1 } };
            for (int s = 0; s < 8; s++)
            {
                int dx = shifts[s, 0] * offset;
                int dy = shifts[s, 1] * offset;
                for (int y = 0; y < height; y++)
                {
                    int sy = y - dy;
                    if (sy < 0 || sy >= height)
                    {
                        continue;
                    }
                    for (int x = 0; x < width; x++)
                    {
                        int sx = x - dx;
                        if (sx < 0 || sx >= width)
                        {
                            continue;
                        }
                        int src = (sy * width + sx) * 4;
                        int dst = (y * width + x) * 4;
                        if (pixels[src + 3] > result[dst + 3])
                        {
                            Array.Copy(pixels, src, result, dst, 4);
                        }
                    }
                }
            }
            for (int i = 0; i < pixels.Length; i += 4)
            {
                if (pixels[i + 3] > 250)
                {
                    Array.Copy(pixels, i, result, i, 4);
                }
            }
            return result;
        }
    }
}
