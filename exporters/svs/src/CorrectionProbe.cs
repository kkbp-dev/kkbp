using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Records what the game's joint corrections do, for checking the importer's copy of them
    /// (docs/design/joint-corrections.md). For each pose in a list it sets the named bones' local
    /// rotations, runs the game's correction once, and writes every transform that then differs from
    /// the Character as it stood, which is what an export would capture. An empty pose shows what the
    /// correction does to that. The Character is put back afterwards.
    ///
    /// The poses file is a JSON array of objects, { "bone name": [x, y, z] }, Unity Euler angles in degrees.
    /// </summary>
    internal static class CorrectionProbe
    {
        private struct Local
        {
            public Vector3 Position;
            public Quaternion Rotation;
            public Vector3 Scale;
        }

        public static void Run(Transform top, Action correct, string posesPath, string outPath)
        {
            var poses = (JsonArray)JsonReader.Parse(File.ReadAllText(posesPath));
            var all = top.GetComponentsInChildren<Transform>(true);
            var transforms = new List<Transform>();
            var byName = new Dictionary<string, Transform>();
            for (int i = 0; i < all.Length; i++)
            {
                var t = all[i];
                if (t.GetInstanceID() == top.GetInstanceID() || byName.ContainsKey(t.name))
                {
                    continue;
                }
                byName[t.name] = t;
                transforms.Add(t);
            }

            var rest = new List<Local>();
            var bones = new JsonArray();
            foreach (var t in transforms)
            {
                rest.Add(Read(t));
                var bone = Write(t);
                bone.Add("parent", t.parent != null ? t.parent.name : null);
                bone.Add("lossy_scale", Vec(t.lossyScale));
                bones.Add(bone);
            }

            var results = new JsonArray();
            foreach (var entry in poses)
            {
                var pose = (JsonObject)entry;
                Restore(transforms, rest);
                var set = new JsonObject();
                foreach (var member in pose.Members)
                {
                    string name = member.Key;
                    Transform t;
                    if (!byName.TryGetValue(name, out t))
                    {
                        throw new InvalidOperationException("The Character has no bone named " + name + ".");
                    }
                    var e = (JsonArray)member.Value;
                    t.localRotation = Quaternion.Euler((float)(double)e[0], (float)(double)e[1], (float)(double)e[2]);
                    set.Add(name, Quat(t.localRotation));
                }
                correct();
                var moved = new JsonArray();
                for (int i = 0; i < transforms.Count; i++)
                {
                    object ignored;
                    if (!pose.TryGet(transforms[i].name, out ignored) && Differs(Read(transforms[i]), rest[i]))
                    {
                        moved.Add(Write(transforms[i]));
                    }
                }
                results.Add(new JsonObject().Add("set", set).Add("moved", moved));
            }
            Restore(transforms, rest);

            var root = new JsonObject().Add("bones", bones).Add("poses", results);
            File.WriteAllText(outPath, JsonWriter.Write(root, false), new UTF8Encoding(false));
        }

        private static Local Read(Transform t)
        {
            return new Local { Position = t.localPosition, Rotation = t.localRotation, Scale = t.localScale };
        }

        private static void Restore(List<Transform> transforms, List<Local> rest)
        {
            for (int i = 0; i < transforms.Count; i++)
            {
                transforms[i].localPosition = rest[i].Position;
                transforms[i].localRotation = rest[i].Rotation;
                transforms[i].localScale = rest[i].Scale;
            }
        }

        private static bool Differs(Local a, Local b)
        {
            const float least = 1e-7f;
            return (a.Position - b.Position).sqrMagnitude > least * least || (a.Scale - b.Scale).sqrMagnitude > least * least
                || Mathf.Abs(Quaternion.Dot(a.Rotation, b.Rotation)) < 1 - 1e-9f;
        }

        private static JsonObject Write(Transform t)
        {
            return new JsonObject().Add("name", t.name).Add("position", Vec(t.localPosition)).Add("rotation", Quat(t.localRotation)).Add("scale", Vec(t.localScale));
        }

        private static JsonArray Vec(Vector3 v)
        {
            return new JsonArray { (double)v.x, (double)v.y, (double)v.z };
        }

        private static JsonArray Quat(Quaternion q)
        {
            return new JsonArray { (double)q.x, (double)q.y, (double)q.z, (double)q.w };
        }
    }
}
