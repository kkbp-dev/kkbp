using System;
using System.Collections.Generic;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// The Bone Group rules both adapters share. KK, KKS and SVS name their body bones the same way,
    /// so one set of name rules serves all three.
    /// </summary>
    public static class BoneRules
    {
        private static readonly string[] NsfwNames =
        {
            "cf_j_kokan", "cf_d_kokan", "cf_s_kokan", "cf_j_ana", "cf_d_ana", "cf_s_ana",
        };

        private static readonly Dictionary<string, BoneRole> RolesByName = BuildRoles();

        /// <summary>The Bone Role of a body bone from its game name, or null. KK, KKS and SVS share these names.</summary>
        public static BoneRole? Role(string name)
        {
            BoneRole role;
            return name != null && RolesByName.TryGetValue(name, out role) ? role : (BoneRole?)null;
        }

        private static Dictionary<string, BoneRole> BuildRoles()
        {
            var roles = new Dictionary<string, BoneRole>
            {
                { "cf_n_height", BoneRole.BodyRoot },
                { "cf_j_hips", BoneRole.Hips },
                { "cf_j_spine01", BoneRole.Spine },
                { "cf_j_spine02", BoneRole.Chest },
                { "cf_j_spine03", BoneRole.UpperChest },
                { "cf_j_neck", BoneRole.Neck },
                { "cf_j_head", BoneRole.Head },
                { "cf_J_FaceRoot", BoneRole.FaceRoot },
                { "cf_j_tang_01", BoneRole.TongueRoot },
            };
            foreach (bool left in new[] { true, false })
            {
                string s = left ? "_L" : "_R";
                Add(roles, "cf_j_shoulder" + s, left ? BoneRole.LeftShoulder : BoneRole.RightShoulder);
                Add(roles, "cf_j_arm00" + s, left ? BoneRole.LeftUpperArm : BoneRole.RightUpperArm);
                Add(roles, "cf_j_forearm01" + s, left ? BoneRole.LeftLowerArm : BoneRole.RightLowerArm);
                Add(roles, "cf_j_hand" + s, left ? BoneRole.LeftHand : BoneRole.RightHand);
                Add(roles, "cf_j_thigh00" + s, left ? BoneRole.LeftUpperLeg : BoneRole.RightUpperLeg);
                Add(roles, "cf_j_leg01" + s, left ? BoneRole.LeftLowerLeg : BoneRole.RightLowerLeg);
                Add(roles, "cf_j_foot" + s, left ? BoneRole.LeftFoot : BoneRole.RightFoot);
                Add(roles, "cf_j_toes" + s, left ? BoneRole.LeftToes : BoneRole.RightToes);
                Add(roles, "cf_J_hitomi_tx" + s, left ? BoneRole.LeftEye : BoneRole.RightEye);
                Add(roles, "cf_j_bust01" + s, left ? BoneRole.LeftBreast : BoneRole.RightBreast);
                Add(roles, "cf_pv_hand" + s, left ? BoneRole.LeftHandIk : BoneRole.RightHandIk);
                Add(roles, "cf_pv_foot" + s, left ? BoneRole.LeftFootIk : BoneRole.RightFootIk);
                Add(roles, "cf_pv_elbo" + s, left ? BoneRole.LeftElbowPole : BoneRole.RightElbowPole);
                Add(roles, "cf_pv_knee" + s, left ? BoneRole.LeftKneePole : BoneRole.RightKneePole);
                string[] fingers = { "thumb", "index", "middle", "ring", "little" };
                string[] parts = { "Proximal", "Intermediate", "Distal" };
                for (int f = 0; f < fingers.Length; f++)
                {
                    for (int p = 0; p < 3; p++)
                    {
                        string role = (left ? "Left" : "Right") + char.ToUpperInvariant(fingers[f][0]) + fingers[f].Substring(1) + parts[p];
                        Add(roles, "cf_j_" + fingers[f] + "0" + (p + 1) + s, (BoneRole)Enum.Parse(typeof(BoneRole), role));
                    }
                }
            }
            return roles;
        }

        private static void Add(Dictionary<string, BoneRole> roles, string name, BoneRole role)
        {
            roles.Add(name, role);
        }

        /// <summary>
        /// The group of a body skeleton bone, from its game name. The adapter says whether the bone is
        /// below the face root (<c>cf_J_FaceRoot</c>). First match wins.
        /// </summary>
        public static BoneGroup BodyGroup(string name, bool underFaceRoot)
        {
            name = name ?? "";
            if (Starts(name, "cf_j_sk_") || Starts(name, "cf_d_sk_"))
            {
                return BoneGroup.Skirt;
            }
            string lower = name.ToLowerInvariant();
            if (lower.Contains("bust") || lower.Contains("bnip"))
            {
                return BoneGroup.Breast;
            }
            if (Starts(name, "cf_J_Vagina") || Array.IndexOf(NsfwNames, name) >= 0 || Starts(name, "cm_J_dan") || Starts(name, "cf_j_dan"))
            {
                return BoneGroup.Nsfw;
            }
            if (Starts(name, "cf_j_tang"))
            {
                return BoneGroup.Mouth;
            }
            if (underFaceRoot)
            {
                if (Starts(name, "cf_J_Eye") || Starts(name, "cf_J_hitomi"))
                {
                    return BoneGroup.Eye;
                }
                if (Starts(name, "cf_J_Mayu"))
                {
                    return BoneGroup.Eyebrow;
                }
                if (Starts(name, "cf_J_Mouth"))
                {
                    return BoneGroup.Mouth;
                }
                return BoneGroup.Face;
            }
            if (Starts(name, "cf_j_") || Starts(name, "cf_s_") || Starts(name, "cf_d_"))
            {
                return BoneGroup.Deform;
            }
            return BoneGroup.Helper;
        }

        /// <summary>
        /// The group of a bone a rule made a helper although a mesh weights it or a bone below it, or physics
        /// uses one, so it isn't safe to delete: <c>face</c> if every such bone is at or below the face
        /// root (<paramref name="underFaceRoot"/>, one per bone), as for the bones between the head and the
        /// face root, and <c>deform</c> otherwise, as for the root's chain.
        /// </summary>
        public static BoneGroup NeededHelperGroup(IList<bool> underFaceRoot)
        {
            foreach (bool under in underFaceRoot)
            {
                if (!under)
                {
                    return BoneGroup.Deform;
                }
            }
            return BoneGroup.Face;
        }

        /// <summary>The keys of every bone that some mesh weights with more than zero.</summary>
        public static HashSet<string> WeightedBones(IEnumerable<MeshData> meshes)
        {
            var result = new HashSet<string>();
            foreach (var mesh in meshes)
            {
                for (int i = 0; i < mesh.Joints.Length; i++)
                {
                    if (mesh.Weights[i] > 0)
                    {
                        result.Add(mesh.BoneKeys[mesh.Joints[i]]);
                    }
                }
            }
            return result;
        }

        /// <summary>The keys of every bone a physics chain or collider uses.</summary>
        public static HashSet<string> PhysicsBones(IEnumerable<PhysicsChain> chains, IEnumerable<PhysicsCollider> colliders)
        {
            var result = new HashSet<string>();
            foreach (var chain in chains)
            {
                result.Add(chain.RootKey);
                result.UnionWith(chain.ExclusionKeys);
                foreach (var particle in chain.Particles)
                {
                    result.Add(particle.BoneKey);
                }
            }
            foreach (var collider in colliders)
            {
                result.Add(collider.BoneKey);
            }
            return result;
        }

        /// <summary>
        /// Makes Outfit-owned bones helpers when nothing weights them or any bone below them, and no
        /// physics uses them (ADR 0011). Deleting every helper then leaves the tree and physics intact.
        /// </summary>
        public static void MarkUnweightedHelpers(IList<BoneData> outfitBones, ICollection<string> weighted, ICollection<string> physics)
        {
            var needed = new HashSet<string>();
            var byKey = new Dictionary<string, BoneData>();
            foreach (var bone in outfitBones)
            {
                byKey[bone.Key] = bone;
            }
            foreach (var bone in outfitBones)
            {
                if (!weighted.Contains(bone.Key) && !physics.Contains(bone.Key))
                {
                    continue;
                }
                // Keep the bone and every Outfit-owned bone above it.
                for (BoneData b = bone; b != null && needed.Add(b.Key); )
                {
                    b = b.ParentKey != null && byKey.ContainsKey(b.ParentKey) ? byKey[b.ParentKey] : null;
                }
            }
            foreach (var bone in outfitBones)
            {
                if (!needed.Contains(bone.Key))
                {
                    bone.Group = BoneGroup.Helper;
                }
            }
        }

        private static bool Starts(string name, string prefix)
        {
            return name.StartsWith(prefix, StringComparison.Ordinal);
        }
    }
}
