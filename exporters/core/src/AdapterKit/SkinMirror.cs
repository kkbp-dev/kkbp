using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Makes a mesh's skin matrices (bone pose times bind pose) mirror images across X = 0, so a mesh the
    /// game made symmetrical is skinned symmetrical (ADR 0048). The game's meshes are symmetrical to well
    /// under a micrometre, but the pose they are captured in isn't: its left and right joint-correction
    /// and eye bones differ by up to 0.6 mm where they carry vertices. Each left and right pair (names
    /// that differ in one L and R) gets the mean of one and the other's mirror image; a bone with no
    /// pair gets the mean of itself and its own mirror image. Bones are found by the mesh's own bone
    /// list. A pair, or a bone, whose change would move a vertex it carries more than
    /// <see cref="MaxMove"/> is left as the game made it. Only the skinning changes, not the bones.
    ///
    /// Matrices are row-major arrays of 16, in Unity's space; the mirror is x to -x in both the mesh's
    /// space and the Character's, so mirroring a matrix negates the entries that mix X with Y, Z or the
    /// translation.
    /// </summary>
    public static class SkinMirror
    {
        /// <summary>The most mirroring may move a vertex, in metres.</summary>
        public const float MaxMove = 1e-3f;

        public sealed class Result
        {
            /// <summary>Left and right pairs mirrored.</summary>
            public int Pairs;

            /// <summary>Unpaired bones made their own mirror image.</summary>
            public int Centres;

            /// <summary>Bones left as they were because mirroring would move their vertices too far.</summary>
            public readonly List<string> Kept = new List<string>();
        }

        /// <summary>
        /// Mirrors `skin` in place. `bones` names each matrix's bone (null for none). `vertices` are the
        /// mesh's own (bind space) vertices, and `joints` and `weights` give each `influences` bone slots,
        /// or are null for a mesh on one bone.
        /// </summary>
        public static Result Mirror(IList<string> bones, float[][] skin, Vec3[] vertices, int[] joints, float[] weights, int influences)
        {
            if (bones == null || skin == null || bones.Count != skin.Length)
            {
                throw new ArgumentException("Each skin matrix needs a bone name.");
            }
            var carried = Carried(skin.Length, vertices, joints, weights, influences);
            var index = new Dictionary<string, int>();
            for (int i = 0; i < bones.Count; i++)
            {
                if (bones[i] != null && !index.ContainsKey(bones[i]))
                {
                    index[bones[i]] = i;
                }
            }
            var original = new float[skin.Length][];
            for (int i = 0; i < skin.Length; i++)
            {
                original[i] = (float[])skin[i].Clone();
            }
            var result = new Result();
            var done = new bool[skin.Length];
            for (int i = 0; i < skin.Length; i++)
            {
                if (done[i] || bones[i] == null)
                {
                    continue;
                }
                int j = Partner(bones[i], index, i, original, carried);
                if (j >= 0)
                {
                    var mean = Mean(original[i], Mirrored(original[j]));
                    var theirs = Mirrored(mean);
                    if (Moves(original[i], mean, carried[i]) > MaxMove || Moves(original[j], theirs, carried[j]) > MaxMove)
                    {
                        result.Kept.Add(bones[i]);
                        result.Kept.Add(bones[j]);
                    }
                    else
                    {
                        skin[i] = mean;
                        skin[j] = theirs;
                        result.Pairs++;
                    }
                    done[i] = done[j] = true;
                    continue;
                }
                var centred = Mean(original[i], Mirrored(original[i]));
                if (Moves(original[i], centred, carried[i]) > MaxMove)
                {
                    result.Kept.Add(bones[i]);
                }
                else
                {
                    skin[i] = centred;
                    result.Centres++;
                }
                done[i] = true;
            }
            return result;
        }

        /// <summary>A matrix's mirror image across X = 0 in both its spaces.</summary>
        public static float[] Mirrored(float[] m)
        {
            var r = (float[])m.Clone();
            // The entries in row 0 or column 0 but not both.
            r[1] = -r[1];
            r[2] = -r[2];
            r[3] = -r[3];
            r[4] = -r[4];
            r[8] = -r[8];
            r[12] = -r[12];
            return r;
        }

        /// <summary>
        /// The bone named like this one with one L swapped for R or the other way, whose mirror image is
        /// nearest this one's matrix where this one carries vertices; -1 if there is none.
        /// </summary>
        private static int Partner(string name, Dictionary<string, int> index, int self, float[][] skin, List<Vec3>[] carried)
        {
            int best = -1;
            double bestMove = double.MaxValue;
            for (int k = 0; k < name.Length; k++)
            {
                char c = name[k];
                if (c != 'L' && c != 'R')
                {
                    continue;
                }
                string other = name.Substring(0, k) + (c == 'L' ? 'R' : 'L') + name.Substring(k + 1);
                int j;
                if (!index.TryGetValue(other, out j) || j == self)
                {
                    continue;
                }
                double move = Moves(skin[self], Mirrored(skin[j]), carried[self]);
                if (move < bestMove)
                {
                    best = j;
                    bestMove = move;
                }
            }
            return best;
        }

        private static float[] Mean(float[] a, float[] b)
        {
            var r = new float[16];
            for (int i = 0; i < 16; i++)
            {
                r[i] = (float)(((double)a[i] + b[i]) / 2);
            }
            return r;
        }

        /// <summary>The farthest apart `a` and `b` put any of the points; 0 for none.</summary>
        private static double Moves(float[] a, float[] b, List<Vec3> points)
        {
            double most = 0;
            foreach (var p in points)
            {
                double dx = 0, dy = 0, dz = 0;
                for (int row = 0; row < 3; row++)
                {
                    double d = (a[row * 4] - b[row * 4]) * (double)p.X + (a[row * 4 + 1] - b[row * 4 + 1]) * (double)p.Y
                        + (a[row * 4 + 2] - b[row * 4 + 2]) * (double)p.Z + (a[row * 4 + 3] - b[row * 4 + 3]);
                    if (row == 0) dx = d; else if (row == 1) dy = d; else dz = d;
                }
                most = Math.Max(most, Math.Sqrt(dx * dx + dy * dy + dz * dz));
            }
            return most;
        }

        /// <summary>For each bone, the vertices with some weight on it.</summary>
        private static List<Vec3>[] Carried(int boneCount, Vec3[] vertices, int[] joints, float[] weights, int influences)
        {
            var carried = new List<Vec3>[boneCount];
            for (int b = 0; b < boneCount; b++)
            {
                carried[b] = new List<Vec3>();
            }
            if (vertices == null)
            {
                return carried;
            }
            for (int v = 0; v < vertices.Length; v++)
            {
                if (joints == null || weights == null)
                {
                    if (boneCount > 0)
                    {
                        carried[0].Add(vertices[v]);
                    }
                    continue;
                }
                for (int s = 0; s < influences; s++)
                {
                    int j = joints[v * influences + s];
                    if (weights[v * influences + s] > 0 && j >= 0 && j < boneCount)
                    {
                        carried[j].Add(vertices[v]);
                    }
                }
            }
            return carried;
        }
    }
}
