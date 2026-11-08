using System;
using System.Collections.Generic;
using System.IO;

namespace KKBP.Exporter.Core
{
    /// <summary>A bone of one Pass, with its Id resolved.</summary>
    internal sealed class GlbBone
    {
        public string Id;
        public int Parent = -1;
        public Vec3 Translation;
        public Quat Rotation;
        public Vec3 Scale;
    }

    /// <summary>A mesh of one Pass, with its Ids resolved and already in glTF space.</summary>
    internal sealed class GlbMesh
    {
        public string Id;
        public Vec3[] Positions;
        public Vec3[] Normals;
        public Vec4[] Tangents;
        public Color[] Colors;
        public List<Vec2[]> UvSets;

        /// <summary>Per joint set: VertexCount * 4 joint indices (into the Pass's bones) and weights.</summary>
        public List<ushort[]> JointSets;
        public List<float[]> WeightSets;

        public List<int[]> Primitives;
        public List<string> PrimitiveMaterials;
        public List<GlbMorph> Morphs;
    }

    internal sealed class GlbMorph
    {
        public string Name;
        public Vec3[] PositionDeltas;
        public Vec3[] NormalDeltas;
    }

    /// <summary>
    /// Writes one Pass as a binary glTF 2.0 file (ADR 0001, ADR 0006): the bones as the node tree,
    /// every mesh skinned at the scene root, one skin, placeholder materials, no textures.
    /// </summary>
    internal sealed class GlbWriter
    {
        private const int ArrayBuffer = 34962;
        private const int ElementArrayBuffer = 34963;
        private const int UnsignedShort = 5123;
        private const int UnsignedInt = 5125;
        private const int Float = 5126;

        private readonly MemoryStream bin = new MemoryStream();
        private readonly BinaryWriter binWriter;
        private readonly JsonArray bufferViews = new JsonArray();
        private readonly JsonArray accessors = new JsonArray();

        private GlbWriter()
        {
            binWriter = new BinaryWriter(bin);
        }

        public static byte[] Write(string generator, IList<GlbBone> bones, IList<GlbMesh> meshes)
        {
            return new GlbWriter().Build(generator, bones, meshes);
        }

        private byte[] Build(string generator, IList<GlbBone> bones, IList<GlbMesh> meshes)
        {
            int root = FindRoot(bones);

            var nodes = new JsonArray();
            var children = new List<int>[bones.Count];
            for (int i = 0; i < bones.Count; i++)
            {
                children[i] = new List<int>();
            }
            for (int i = 0; i < bones.Count; i++)
            {
                if (bones[i].Parent >= 0)
                {
                    children[bones[i].Parent].Add(i);
                }
            }
            for (int i = 0; i < bones.Count; i++)
            {
                var b = bones[i];
                var node = new JsonObject()
                    .Add("name", b.Id)
                    .Add("translation", Array(b.Translation))
                    .Add("rotation", Array(b.Rotation))
                    .Add("scale", Array(b.Scale));
                if (children[i].Count > 0)
                {
                    node.Add("children", Ints(children[i]));
                }
                node.Add("extras", new JsonObject().Add("id", b.Id));
                nodes.Add(node);
            }

            var joints = new JsonArray();
            for (int i = 0; i < bones.Count; i++)
            {
                joints.Add(i);
            }
            var skins = new JsonArray
            {
                new JsonObject()
                    .Add("inverseBindMatrices", InverseBindMatrices(bones))
                    .Add("joints", joints)
                    .Add("skeleton", root),
            };

            var materialIndex = new Dictionary<string, int>();
            var materials = new JsonArray();
            var gltfMeshes = new JsonArray();
            var sceneNodes = new JsonArray { root };
            foreach (var mesh in meshes)
            {
                foreach (var materialId in mesh.PrimitiveMaterials)
                {
                    if (!materialIndex.ContainsKey(materialId))
                    {
                        materialIndex.Add(materialId, materials.Count);
                        materials.Add(new JsonObject().Add("name", materialId).Add("extras", new JsonObject().Add("id", materialId)));
                    }
                }
                gltfMeshes.Add(WriteMesh(mesh, materialIndex));
                sceneNodes.Add(nodes.Count);
                nodes.Add(new JsonObject()
                    .Add("name", mesh.Id)
                    .Add("mesh", gltfMeshes.Count - 1)
                    .Add("skin", 0)
                    .Add("extras", new JsonObject().Add("id", mesh.Id)));
            }

            var gltf = new JsonObject()
                .Add("asset", new JsonObject().Add("version", "2.0").Add("generator", generator))
                .Add("scene", 0)
                .Add("scenes", new JsonArray { new JsonObject().Add("nodes", sceneNodes) })
                .Add("nodes", nodes);
            if (gltfMeshes.Count > 0)
            {
                gltf.Add("meshes", gltfMeshes);
                gltf.Add("materials", materials);
            }
            gltf.Add("skins", skins);
            gltf.Add("accessors", accessors);
            gltf.Add("bufferViews", bufferViews);
            gltf.Add("buffers", new JsonArray { new JsonObject().Add("byteLength", (int)bin.Length) });
            return Pack(JsonWriter.ToUtf8(gltf, false), bin.ToArray());
        }

        private static int FindRoot(IList<GlbBone> bones)
        {
            if (bones.Count == 0)
            {
                throw new ExportException("A Pass has no bones.");
            }
            int root = -1;
            for (int i = 0; i < bones.Count; i++)
            {
                if (bones[i].Parent < 0)
                {
                    if (root >= 0)
                    {
                        throw new ExportException("A Pass's bones must form one tree, but '" + bones[root].Id + "' and '" + bones[i].Id + "' both have no parent.");
                    }
                    root = i;
                }
            }
            // Every bone must reach the root; otherwise the parents form a cycle.
            for (int i = 0; i < bones.Count; i++)
            {
                int at = i;
                for (int steps = 0; at != root; steps++)
                {
                    if (at < 0 || steps > bones.Count)
                    {
                        throw new ExportException("Bone '" + bones[i].Id + "' is in a parent cycle.");
                    }
                    at = bones[at].Parent;
                }
            }
            return root;
        }

        private int InverseBindMatrices(IList<GlbBone> bones)
        {
            var world = new Matrix4?[bones.Count];
            var data = new float[bones.Count * 16];
            for (int i = 0; i < bones.Count; i++)
            {
                float[] m = World(bones, world, i).InverseAffine().ToArray();
                System.Array.Copy(m, 0, data, i * 16, 16);
            }
            return AddFloats(data, bones.Count, "MAT4", -1, false);
        }

        private static Matrix4 World(IList<GlbBone> bones, Matrix4?[] world, int i)
        {
            if (world[i].HasValue)
            {
                return world[i].Value;
            }
            var b = bones[i];
            var local = Matrix4.FromTrs(b.Translation, b.Rotation, b.Scale);
            var result = b.Parent < 0 ? local : World(bones, world, b.Parent) * local;
            world[i] = result;
            return result;
        }

        private JsonObject WriteMesh(GlbMesh mesh, Dictionary<string, int> materialIndex)
        {
            int count = mesh.Positions.Length;
            var attributes = new JsonObject();
            attributes.Add("POSITION", AddVec3(mesh.Positions, true));
            if (mesh.Normals != null)
            {
                attributes.Add("NORMAL", AddVec3(mesh.Normals, false));
            }
            if (mesh.Tangents != null)
            {
                var data = new float[count * 4];
                for (int i = 0; i < count; i++)
                {
                    var t = mesh.Tangents[i];
                    data[i * 4] = t.X;
                    data[i * 4 + 1] = t.Y;
                    data[i * 4 + 2] = t.Z;
                    data[i * 4 + 3] = t.W;
                }
                attributes.Add("TANGENT", AddFloats(data, count, "VEC4", ArrayBuffer, false));
            }
            for (int set = 0; set < mesh.UvSets.Count; set++)
            {
                var uvs = mesh.UvSets[set];
                var data = new float[count * 2];
                for (int i = 0; i < count; i++)
                {
                    data[i * 2] = uvs[i].X;
                    data[i * 2 + 1] = uvs[i].Y;
                }
                attributes.Add("TEXCOORD_" + set, AddFloats(data, count, "VEC2", ArrayBuffer, false));
            }
            if (mesh.Colors != null)
            {
                var data = new float[count * 4];
                for (int i = 0; i < count; i++)
                {
                    var c = mesh.Colors[i];
                    data[i * 4] = c.R;
                    data[i * 4 + 1] = c.G;
                    data[i * 4 + 2] = c.B;
                    data[i * 4 + 3] = c.A;
                }
                attributes.Add("COLOR_0", AddFloats(data, count, "VEC4", ArrayBuffer, false));
            }
            for (int set = 0; set < mesh.JointSets.Count; set++)
            {
                attributes.Add("JOINTS_" + set, AddJoints(mesh.JointSets[set], count));
                attributes.Add("WEIGHTS_" + set, AddFloats(mesh.WeightSets[set], count, "VEC4", ArrayBuffer, false));
            }

            var targets = new JsonArray();
            var targetNames = new JsonArray();
            foreach (var morph in mesh.Morphs)
            {
                var target = new JsonObject().Add("POSITION", AddVec3(morph.PositionDeltas, true));
                if (morph.NormalDeltas != null)
                {
                    target.Add("NORMAL", AddVec3(morph.NormalDeltas, false));
                }
                targets.Add(target);
                targetNames.Add(morph.Name);
            }

            var primitives = new JsonArray();
            for (int p = 0; p < mesh.Primitives.Count; p++)
            {
                var primitive = new JsonObject()
                    .Add("attributes", attributes)
                    .Add("indices", AddIndices(mesh.Primitives[p], count))
                    .Add("material", materialIndex[mesh.PrimitiveMaterials[p]]);
                if (targets.Count > 0)
                {
                    primitive.Add("targets", targets);
                }
                primitives.Add(primitive);
            }

            var extras = new JsonObject().Add("id", mesh.Id);
            if (targetNames.Count > 0)
            {
                extras.Add("targetNames", targetNames);
            }
            return new JsonObject().Add("name", mesh.Id).Add("primitives", primitives).Add("extras", extras);
        }

        private int AddVec3(Vec3[] values, bool withBounds)
        {
            var data = new float[values.Length * 3];
            for (int i = 0; i < values.Length; i++)
            {
                data[i * 3] = values[i].X;
                data[i * 3 + 1] = values[i].Y;
                data[i * 3 + 2] = values[i].Z;
            }
            return AddFloats(data, values.Length, "VEC3", ArrayBuffer, withBounds);
        }

        private int AddFloats(float[] data, int count, string type, int target, bool withBounds)
        {
            int start = BeginView();
            foreach (float f in data)
            {
                if (float.IsNaN(f) || float.IsInfinity(f))
                {
                    throw new ExportException("Mesh data contains NaN or infinity.");
                }
                binWriter.Write(f);
            }
            int view = EndView(start, target);
            var accessor = new JsonObject()
                .Add("bufferView", view)
                .Add("componentType", Float)
                .Add("count", count)
                .Add("type", type);
            if (withBounds)
            {
                int width = data.Length / Math.Max(count, 1);
                var min = new float[width];
                var max = new float[width];
                for (int c = 0; c < width; c++)
                {
                    min[c] = float.MaxValue;
                    max[c] = float.MinValue;
                }
                for (int i = 0; i < data.Length; i++)
                {
                    int c = i % width;
                    min[c] = Math.Min(min[c], data[i]);
                    max[c] = Math.Max(max[c], data[i]);
                }
                accessor.Add("min", Floats(min)).Add("max", Floats(max));
            }
            accessors.Add(accessor);
            return accessors.Count - 1;
        }

        private int AddJoints(ushort[] joints, int count)
        {
            int start = BeginView();
            foreach (ushort j in joints)
            {
                binWriter.Write(j);
            }
            int view = EndView(start, ArrayBuffer);
            accessors.Add(new JsonObject()
                .Add("bufferView", view)
                .Add("componentType", UnsignedShort)
                .Add("count", count)
                .Add("type", "VEC4"));
            return accessors.Count - 1;
        }

        private int AddIndices(int[] indices, int vertexCount)
        {
            // The largest value of the index type is reserved, so 16-bit indices allow 65535 vertices.
            bool wide = vertexCount > 65535;
            int start = BeginView();
            foreach (int i in indices)
            {
                if (i < 0 || i >= vertexCount)
                {
                    throw new ExportException("A triangle index is outside the mesh's vertices.");
                }
                if (wide)
                {
                    binWriter.Write((uint)i);
                }
                else
                {
                    binWriter.Write((ushort)i);
                }
            }
            int view = EndView(start, ElementArrayBuffer);
            accessors.Add(new JsonObject()
                .Add("bufferView", view)
                .Add("componentType", wide ? UnsignedInt : UnsignedShort)
                .Add("count", indices.Length)
                .Add("type", "SCALAR"));
            return accessors.Count - 1;
        }

        private int BeginView()
        {
            while (bin.Length % 4 != 0)
            {
                binWriter.Write((byte)0);
            }
            return (int)bin.Length;
        }

        private int EndView(int start, int target)
        {
            binWriter.Flush();
            var view = new JsonObject()
                .Add("buffer", 0)
                .Add("byteOffset", start)
                .Add("byteLength", (int)bin.Length - start);
            if (target >= 0)
            {
                view.Add("target", target);
            }
            bufferViews.Add(view);
            return bufferViews.Count - 1;
        }

        private static byte[] Pack(byte[] json, byte[] binary)
        {
            int jsonLength = Pad(json.Length);
            int binLength = Pad(binary.Length);
            var output = new MemoryStream();
            var w = new BinaryWriter(output);
            w.Write(0x46546C67u); // "glTF"
            w.Write(2u);
            w.Write((uint)(12 + 8 + jsonLength + 8 + binLength));
            w.Write((uint)jsonLength);
            w.Write(0x4E4F534Au); // "JSON"
            w.Write(json);
            for (int i = json.Length; i < jsonLength; i++)
            {
                w.Write((byte)' ');
            }
            w.Write((uint)binLength);
            w.Write(0x004E4942u); // "BIN\0"
            w.Write(binary);
            for (int i = binary.Length; i < binLength; i++)
            {
                w.Write((byte)0);
            }
            w.Flush();
            return output.ToArray();
        }

        private static int Pad(int length)
        {
            return (length + 3) & ~3;
        }

        private static JsonArray Array(Vec3 v)
        {
            return new JsonArray { v.X, v.Y, v.Z };
        }

        private static JsonArray Array(Quat q)
        {
            return new JsonArray { q.X, q.Y, q.Z, q.W };
        }

        private static JsonArray Ints(List<int> values)
        {
            var a = new JsonArray();
            foreach (int v in values)
            {
                a.Add(v);
            }
            return a;
        }

        private static JsonArray Floats(float[] values)
        {
            var a = new JsonArray();
            foreach (float v in values)
            {
                a.Add(v);
            }
            return a;
        }
    }
}
