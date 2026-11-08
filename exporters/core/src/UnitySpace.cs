namespace KKBP.Exporter.Core
{
    /// <summary>
    /// The one place that converts from Unity's space (left-handed, +Y up, UV origin bottom left)
    /// to glTF's (right-handed, +Y up, UV origin top left). It mirrors X.
    /// </summary>
    public static class UnitySpace
    {
        public static Vec3 Position(Vec3 v)
        {
            return new Vec3(-v.X, v.Y, v.Z);
        }

        /// <summary>Normals and other directions mirror the same way as positions.</summary>
        public static Vec3 Direction(Vec3 v)
        {
            return new Vec3(-v.X, v.Y, v.Z);
        }

        /// <summary>A mirror flips the bitangent's handedness, so W changes sign too.</summary>
        public static Vec4 Tangent(Vec4 t)
        {
            return new Vec4(-t.X, t.Y, t.Z, -t.W);
        }

        public static Quat Rotation(Quat q)
        {
            return new Quat(q.X, -q.Y, -q.Z, q.W);
        }

        /// <summary>Scale is unchanged by a mirror.</summary>
        public static Vec3 Scale(Vec3 s)
        {
            return s;
        }

        /// <summary>glTF's UV origin is the top left.</summary>
        public static Vec2 Uv(Vec2 uv)
        {
            return new Vec2(uv.X, 1 - uv.Y);
        }

        /// <summary>A mirror reverses triangle winding, so each triangle's last two corners swap.</summary>
        public static int[] Triangles(int[] indices)
        {
            if (indices.Length % 3 != 0)
            {
                throw new ExportException("A triangle list's length is not a multiple of 3.");
            }
            var result = new int[indices.Length];
            for (int i = 0; i < indices.Length; i += 3)
            {
                result[i] = indices[i];
                result[i + 1] = indices[i + 2];
                result[i + 2] = indices[i + 1];
            }
            return result;
        }
    }
}
