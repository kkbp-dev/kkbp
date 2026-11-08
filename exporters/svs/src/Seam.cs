using System;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Converts Unity values into the Core's types. Unity and IL2CPP types stop here: nothing the adapter
    /// hands the Core refers to UnityEngine or the interop assemblies.
    /// </summary>
    internal static class Seam
    {
        public static Core.Vec2 V2(Vector2 v)
        {
            return new Core.Vec2(v.x, v.y);
        }

        public static Core.Vec3 V3(Vector3 v)
        {
            return new Core.Vec3(v.x, v.y, v.z);
        }

        public static Core.Vec4 V4(Vector4 v)
        {
            return new Core.Vec4(v.x, v.y, v.z, v.w);
        }

        public static Core.Quat Q(Quaternion q)
        {
            return new Core.Quat(q.x, q.y, q.z, q.w);
        }

        public static Core.Color C(Color c)
        {
            return new Core.Color(c.r, c.g, c.b, c.a);
        }

        /// <summary>Copies an IL2CPP byte array into a managed one.</summary>
        public static byte[] Bytes(Il2CppInterop.Runtime.InteropTypes.Arrays.Il2CppStructArray<byte> data)
        {
            var bytes = new byte[data.Length];
            for (int i = 0; i < bytes.Length; i++)
            {
                bytes[i] = data[i];
            }
            return bytes;
        }

        /// <summary>A material or texture name without the " (Instance)" Unity adds to copies.</summary>
        public static string CleanName(string name)
        {
            const string suffix = " (Instance)";
            while (name != null && name.EndsWith(suffix, StringComparison.Ordinal))
            {
                name = name.Substring(0, name.Length - suffix.Length);
            }
            return name ?? "";
        }
    }
}
