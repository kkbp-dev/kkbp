using System.Collections.Generic;
using System.IO;
using System.Text;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Records how the Body Pass meshes are skinned, for finding where the Body stops being symmetrical
    /// (issue 106): for each captured mesh, the game's own vertices, its bind poses, the skin matrices the
    /// capture used (pose times bind pose), the bone names and weights, and the positions written. The
    /// export runs as usual; the request's "probe_symmetry" names the file.
    /// </summary>
    internal static class SymmetryProbe
    {
        public static void Write(string path, List<CapturedMesh> captured)
        {
            var meshes = new JsonArray();
            foreach (var m in captured)
            {
                if (m.Source == null || m.Skin == null || !m.Source.isReadable)
                {
                    continue;
                }
                var smr = m.Renderer.TryCast<SkinnedMeshRenderer>();
                var bones = new JsonArray();
                if (smr != null && m.Weights != null)
                {
                    foreach (var b in smr.bones)
                    {
                        bones.Add(b != null ? b.name : null);
                    }
                }
                else
                {
                    bones.Add(m.Renderer.name);
                }
                var vertices = new JsonArray();
                foreach (var v in m.Source.vertices)
                {
                    vertices.Add((double)v.x);
                    vertices.Add((double)v.y);
                    vertices.Add((double)v.z);
                }
                var bind = new JsonArray();
                if (smr != null && m.Weights != null)
                {
                    foreach (var b in m.Source.bindposes)
                    {
                        Matrix(bind, b);
                    }
                }
                var skin = new JsonArray();
                foreach (var s in m.Skin)
                {
                    Matrix(skin, s);
                }
                var weights = new JsonArray();
                if (m.Weights != null)
                {
                    foreach (var w in m.Weights)
                    {
                        weights.Add((double)w.boneIndex0);
                        weights.Add((double)w.boneIndex1);
                        weights.Add((double)w.boneIndex2);
                        weights.Add((double)w.boneIndex3);
                        weights.Add((double)w.weight0);
                        weights.Add((double)w.weight1);
                        weights.Add((double)w.weight2);
                        weights.Add((double)w.weight3);
                    }
                }
                var positions = new JsonArray();
                foreach (var p in m.Data.Positions)
                {
                    positions.Add((double)p.X);
                    positions.Add((double)p.Y);
                    positions.Add((double)p.Z);
                }
                meshes.Add(new JsonObject()
                    .Add("name", m.Renderer.name)
                    .Add("bones", bones)
                    .Add("vertices", vertices)
                    .Add("bindposes", bind)
                    .Add("skin", skin)
                    .Add("weights", weights)
                    .Add("positions", positions));
            }
            File.WriteAllText(path, JsonWriter.Write(new JsonObject().Add("meshes", meshes), false), new UTF8Encoding(false));
        }

        /// <summary>A matrix as 16 numbers, row by row.</summary>
        private static void Matrix(JsonArray into, Matrix4x4 m)
        {
            for (int r = 0; r < 4; r++)
            {
                for (int c = 0; c < 4; c++)
                {
                    into.Add((double)m[r, c]);
                }
            }
        }
    }
}
