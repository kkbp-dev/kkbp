using System;
using System.Collections.Generic;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>What an object in the Character belongs to.</summary>
    internal enum Owner
    {
        Body,
        Hair,
        Clothes,
        Accessory,
    }

    /// <summary>
    /// The Character's transforms: who owns each one, its key, and its pose. The body skeleton's pose is
    /// recorded once, when the Body Pass starts, and every later Pass reuses it, so physics moving body
    /// bones between Passes can't give one bone two rest poses. Outfit-owned transforms are posed from
    /// that record and their own local transforms. All poses are in the Character root's space.
    /// </summary>
    internal sealed class Rig
    {
        public struct Pose
        {
            /// <summary>Position and rotation, without scale: what the bone is written with (ADR 0008).</summary>
            public Vector3 Position;
            public Quaternion Rotation;

            /// <summary>The full matrix, with scale, that the game skins with.</summary>
            public Matrix4x4 Matrix;
        }

        /// <summary>
        /// A body bone as recorded at the Body Pass. Changing Outfits can replace body transforms, so
        /// later Passes find a bone's live transform by its key and take everything else from here.
        /// </summary>
        private sealed class Recorded
        {
            public string Key;
            public string ParentKey;
            public string Name;
            public Pose Pose;
            public BoneData Bone;
        }

        private readonly Transform root;
        private readonly Transform top;
        private readonly Matrix4x4 rootInverse;
        private readonly Quaternion rootRotationInverse;
        private readonly List<Recorded> bodyBones = new List<Recorded>();
        private readonly Dictionary<string, Recorded> bodyByKey = new Dictionary<string, Recorded>();

        // The live transform of each recorded body bone, found again at the start of each Pass.
        private readonly Dictionary<Transform, Recorded> bodyByTransform = new Dictionary<Transform, Recorded>();

        // Per Pass.
        private Dictionary<Transform, Owner> ownerRoots = new Dictionary<Transform, Owner>();
        private string passPrefix;
        private readonly Dictionary<Transform, Pose> poses = new Dictionary<Transform, Pose>();
        private readonly Dictionary<Transform, string> exportedKeys = new Dictionary<Transform, string>();

        public Rig(Transform root, Transform top)
        {
            this.root = root;
            this.top = top;
            rootInverse = Matrix4x4.TRS(root.position, root.rotation, Vector3.one).inverse;
            rootRotationInverse = Quaternion.Inverse(root.rotation);
        }

        public Transform Top
        {
            get { return top; }
        }

        /// <summary>From world space into the Character root's space, without scale.</summary>
        public Matrix4x4 RootInverse
        {
            get { return rootInverse; }
        }

        /// <summary>Hit transforms are never exported; their colliders move to the nearest exported bone.</summary>
        public static bool IsHit(Transform t)
        {
            string n = t.name;
            return n.StartsWith("cf_hit_", StringComparison.Ordinal) || n.StartsWith("cf_d_hit_", StringComparison.Ordinal)
                || n.StartsWith("o_hit_", StringComparison.Ordinal) || n.StartsWith("aim_hit", StringComparison.Ordinal);
        }

        /// <summary>Finds the hair, clothes and accessory objects that exist now.</summary>
        public void FindOwners()
        {
            ownerRoots = new Dictionary<Transform, Owner>();
            foreach (var c in top.GetComponentsInChildren<ChaClothesComponent>(true))
            {
                ownerRoots[c.transform] = Owner.Clothes;
            }
            foreach (var c in top.GetComponentsInChildren<ChaAccessoryComponent>(true))
            {
                ownerRoots[c.transform] = Owner.Accessory;
            }
            // Last, so a hair accessory counts as hair.
            foreach (var c in top.GetComponentsInChildren<ChaCustomHairComponent>(true))
            {
                ownerRoots[c.transform] = Owner.Hair;
            }
        }

        public Owner OwnerOf(Transform t)
        {
            for (; t != null && t != top.parent; t = t.parent)
            {
                Owner owner;
                if (ownerRoots.TryGetValue(t, out owner))
                {
                    return owner;
                }
            }
            return Owner.Body;
        }

        /// <summary>Records the body skeleton's pose. Called once, at the start of the Body Pass.</summary>
        public void RecordBody()
        {
            FindOwners();
            var transforms = new List<Transform>();
            foreach (var t in Walk(top))
            {
                if (OwnerOf(t) != Owner.Body)
                {
                    continue;
                }
                var r = new Recorded { Key = "body:" + Path(t), Name = t.name, Pose = WorldPose(t) };
                if (bodyByKey.ContainsKey(r.Key))
                {
                    continue;
                }
                bodyBones.Add(r);
                bodyByKey[r.Key] = r;
                bodyByTransform[t] = r;
                transforms.Add(t);
            }
            for (int i = 0; i < bodyBones.Count; i++)
            {
                var r = bodyBones[i];
                var t = transforms[i];
                Recorded parent = null;
                for (var p = t.parent; p != null && parent == null; p = p.parent)
                {
                    bodyByTransform.TryGetValue(p, out parent);
                }
                r.ParentKey = parent != null ? parent.Key : null;
                r.Bone = Bone(r.Key, r.Name, r.Pose, parent != null ? parent.Key : null, parent != null ? parent.Pose : (Pose?)null);
                r.Bone.Role = BoneRules.Role(r.Name);
                r.Bone.Group = BoneRules.BodyGroup(r.Name, UnderFaceRoot(t));
            }
        }

        /// <summary>
        /// Starts a Pass: the body skeleton plus, for an Outfit Pass, the active transforms of its hair,
        /// clothes and accessories. Returns the Pass's bones.
        /// </summary>
        public List<BoneData> BeginPass(PassInfo pass)
        {
            FindOwners();
            poses.Clear();
            exportedKeys.Clear();
            passPrefix = pass.Kind == PassKind.Body ? null : "outfit" + pass.Outfit.Value.ToString("00") + ":";

            // Find each recorded body bone's live transform again by its key.
            bodyByTransform.Clear();
            var outfitTransforms = new List<Transform>();
            foreach (var t in Walk(top))
            {
                if (OwnerOf(t) == Owner.Body)
                {
                    Recorded r;
                    if (bodyByKey.TryGetValue("body:" + Path(t), out r))
                    {
                        bodyByTransform[t] = r;
                        exportedKeys[t] = r.Key;
                    }
                }
                else if (passPrefix != null)
                {
                    exportedKeys[t] = passPrefix + Path(t);
                    outfitTransforms.Add(t);
                }
            }

            var bones = new List<BoneData>();
            Missing = new List<string>();
            var live = new HashSet<Recorded>(bodyByTransform.Values);
            foreach (var r in bodyBones)
            {
                bones.Add(Copy(r.Bone));
                if (!live.Contains(r))
                {
                    Missing.Add(r.Name);
                }
            }
            foreach (var t in outfitTransforms)
            {
                var parent = ParentOf(t);
                var bone = Bone(exportedKeys[t], t.name, PoseOf(t), parent != null ? exportedKeys[parent] : null, parent != null ? PoseOf(parent) : (Pose?)null);
                bone.Group = OwnerOf(t) == Owner.Hair ? BoneGroup.Hair : BoneGroup.Accessory;
                bones.Add(bone);
            }
            return bones;
        }

        /// <summary>Recorded body bones with no live transform in the Pass just begun; they keep their recorded pose.</summary>
        public List<string> Missing { get; private set; }

        /// <summary>The Outfit-owned bones of the Pass just begun, for the helper rule (ADR 0011).</summary>
        public static List<BoneData> OutfitBones(List<BoneData> bones)
        {
            return bones.FindAll(b => !b.Key.StartsWith("body:", StringComparison.Ordinal));
        }

        /// <summary>The key a mesh or material of this Pass gets for an object.</summary>
        public string ObjectKey(Transform t)
        {
            return (passPrefix ?? "body:") + Path(t);
        }

        /// <summary>The key of the bone that stands for a transform: itself, or its nearest exported ancestor.</summary>
        public string BoneKey(Transform t)
        {
            return exportedKeys[ExportedBone(t)];
        }

        /// <summary>The exported transform that stands for a transform: itself, or its nearest exported ancestor.</summary>
        public Transform ExportedBone(Transform t)
        {
            for (; t != null; t = t.parent)
            {
                if (exportedKeys.ContainsKey(t))
                {
                    return t;
                }
            }
            return top;
        }

        /// <summary>A transform's pose for this Pass: the body record, or composed from its parent's pose.</summary>
        public Pose PoseOf(Transform t)
        {
            Recorded r;
            if (bodyByTransform.TryGetValue(t, out r))
            {
                return r.Pose;
            }
            Pose pose;
            if (poses.TryGetValue(t, out pose))
            {
                return pose;
            }
            if (t.parent == null || t == root)
            {
                pose = WorldPose(t);
            }
            else
            {
                var parent = PoseOf(t.parent);
                pose = new Pose
                {
                    Position = parent.Matrix.MultiplyPoint3x4(t.localPosition),
                    Rotation = parent.Rotation * t.localRotation,
                    Matrix = parent.Matrix * Matrix4x4.TRS(t.localPosition, t.localRotation, t.localScale),
                };
            }
            poses[t] = pose;
            return pose;
        }

        private Pose WorldPose(Transform t)
        {
            return new Pose
            {
                Position = rootInverse.MultiplyPoint3x4(t.position),
                Rotation = rootRotationInverse * t.rotation,
                Matrix = rootInverse * t.localToWorldMatrix,
            };
        }

        private Transform ParentOf(Transform t)
        {
            for (var p = t.parent; p != null; p = p.parent)
            {
                if (exportedKeys.ContainsKey(p))
                {
                    return p;
                }
            }
            return null;
        }

        private static BoneData Copy(BoneData b)
        {
            return new BoneData { Key = b.Key, Name = b.Name, ParentKey = b.ParentKey, Position = b.Position, Rotation = b.Rotation, Scale = b.Scale, Role = b.Role, Group = b.Group };
        }

        private static BoneData Bone(string key, string name, Pose pose, string parentKey, Pose? parentPose)
        {
            var bone = new BoneData { Key = key, Name = name };
            if (parentKey == null)
            {
                bone.Position = Seam.V3(pose.Position);
                bone.Rotation = Seam.Q(pose.Rotation);
                return bone;
            }
            bone.ParentKey = parentKey;
            var p = parentPose.Value;
            var inverse = Quaternion.Inverse(p.Rotation);
            bone.Position = Seam.V3(inverse * (pose.Position - p.Position));
            bone.Rotation = Seam.Q(inverse * pose.Rotation);
            return bone;
        }

        private static bool UnderFaceRoot(Transform t)
        {
            for (; t != null; t = t.parent)
            {
                if (t.name == "cf_J_FaceRoot")
                {
                    return true;
                }
            }
            return false;
        }

        /// <summary>
        /// Active transforms under the top, depth first by child index. Hit transforms are left out but
        /// their children aren't; those are parented to the nearest exported ancestor.
        /// </summary>
        public static IEnumerable<Transform> Walk(Transform top)
        {
            var stack = new Stack<Transform>();
            stack.Push(top);
            while (stack.Count > 0)
            {
                var t = stack.Pop();
                if (!t.gameObject.activeInHierarchy)
                {
                    continue;
                }
                if (!IsHit(t))
                {
                    yield return t;
                }
                for (int i = t.childCount - 1; i >= 0; i--)
                {
                    stack.Push(t.GetChild(i));
                }
            }
        }

        /// <summary>The transform's path from the top. Siblings sharing a name get "#2", "#3", … in child order.</summary>
        private string Path(Transform t)
        {
            var parts = new List<string>();
            for (; t != null && t != top.parent; t = t.parent)
            {
                string part = t.name;
                if (t.parent != null)
                {
                    int same = 0;
                    for (int i = 0; i < t.GetSiblingIndex(); i++)
                    {
                        if (t.parent.GetChild(i).name == t.name)
                        {
                            same++;
                        }
                    }
                    if (same > 0)
                    {
                        part += "#" + (same + 1);
                    }
                }
                parts.Add(part);
            }
            parts.Reverse();
            return string.Join("/", parts.ToArray());
        }
    }
}
