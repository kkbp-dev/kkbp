using System;
using HarmonyLib;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Converts Unity values into the Core's types. Unity types stop here: nothing the adapter hands the
    /// Core refers to UnityEngine.
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

        /// <summary>Reads a private field or property the game doesn't expose (ADR 0007: nothing is publicized).</summary>
        public static T Private<T>(object instance, string name)
        {
            var type = instance.GetType();
            var field = AccessTools.Field(type, name);
            if (field != null)
            {
                return (T)field.GetValue(instance);
            }
            var property = AccessTools.Property(type, name);
            if (property != null)
            {
                return (T)property.GetValue(instance, null);
            }
            throw new MissingMemberException(type.FullName, name);
        }
    }
}
