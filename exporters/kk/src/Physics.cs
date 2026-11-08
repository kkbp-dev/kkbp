using System;
using System.Collections;
using System.Collections.Generic;
using HarmonyLib;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>
    /// Captures the game's dynamic bone chains and colliders. DynamicBone, DynamicBone_Ver01 and
    /// DynamicBone_Ver02 keep their per-bone values (distribution curves and Ver02's active pattern
    /// already applied) in a private particle list, which is read through reflection (ADR 0007).
    /// </summary>
    internal sealed class Physics
    {
        private readonly Rig rig;
        private readonly Dictionary<DynamicBoneCollider, string> names = new Dictionary<DynamicBoneCollider, string>();
        private readonly HashSet<string> used = new HashSet<string>();

        public Physics(Rig rig)
        {
            this.rig = rig;
        }

        /// <summary>Adds the colliders and chains on objects this Pass owns.</summary>
        public void Capture(Transform top, PassSink sink, Func<Transform, bool> inPass)
        {
            foreach (var collider in top.GetComponentsInChildren<DynamicBoneCollider>(false))
            {
                if (inPass(collider.transform) && !names.ContainsKey(collider))
                {
                    sink.Colliders.Add(Collider(collider));
                }
            }
            foreach (var component in top.GetComponentsInChildren<MonoBehaviour>(false))
            {
                if (component == null || !inPass(component.transform))
                {
                    continue;
                }
                if (component is DynamicBone || component is DynamicBone_Ver01 || component is DynamicBone_Ver02)
                {
                    var chain = Chain(component);
                    if (chain != null)
                    {
                        sink.Chains.Add(chain);
                    }
                }
            }
        }

        private PhysicsCollider Collider(DynamicBoneCollider c)
        {
            string name = c.name;
            for (int i = 2; !used.Add(name); i++)
            {
                name = c.name + "_" + i;
            }
            names[c] = name;

            // Re-express the collider in the bone it ends up on, which may be an ancestor (hit transforms
            // aren't exported). Bones carry no scale, so the transform's scale goes into the sizes.
            var boneTransform = rig.ExportedBone(c.transform);
            string boneKey = rig.BoneKey(boneTransform);
            var bone = rig.PoseOf(boneTransform);
            var own = rig.PoseOf(c.transform);
            var inverse = Quaternion.Inverse(bone.Rotation);
            float scale = Mathf.Abs(c.transform.lossyScale.x);
            return new PhysicsCollider
            {
                Name = name,
                BoneKey = boneKey,
                Center = Seam.V3(inverse * (own.Matrix.MultiplyPoint3x4(c.m_Center) - bone.Position)),
                Rotation = Seam.Q(inverse * own.Rotation),
                Radius = c.m_Radius * scale,
                Height = c.m_Height * scale,
                Direction = (ColliderDirection)(int)c.m_Direction,
                Bound = c.m_Bound == DynamicBoneCollider.Bound.Inside ? ColliderBound.Inside : ColliderBound.Outside,
            };
        }

        private PhysicsChain Chain(MonoBehaviour component)
        {
            var root = Get<Transform>(component, "m_Root", "Root");
            if (root == null)
            {
                return null;
            }
            var chain = new PhysicsChain
            {
                RootKey = rig.BoneKey(root),
                Gravity = Seam.V3(WorldToRoot(Get<Vector3>(component, "m_Gravity", "Gravity"))),
                Force = Seam.V3(WorldToRoot(Get<Vector3>(component, "m_Force", "Force"))),
                EndLength = Get<float>(component, "m_EndLength"),
                EndOffset = Seam.V3(Get<Vector3>(component, "m_EndOffset")),
                Weight = Has(component, "m_Weight") ? Get<float>(component, "m_Weight") : Get<float>(component, "Weight"),
            };
            var colliders = Get<IList>(component, "m_Colliders", "Colliders");
            if (colliders != null)
            {
                foreach (var c in colliders)
                {
                    string name;
                    var collider = c as DynamicBoneCollider;
                    if (collider != null && names.TryGetValue(collider, out name) && !chain.Colliders.Contains(name))
                    {
                        chain.Colliders.Add(name);
                    }
                }
            }
            var exclusions = Get<IList>(component, "m_Exclusions");
            if (exclusions != null)
            {
                foreach (var e in exclusions)
                {
                    var t = e as Transform;
                    if (t != null)
                    {
                        chain.ExclusionKeys.Add(rig.BoneKey(t));
                    }
                }
            }
            var particles = Get<IList>(component, "m_Particles", "Particles");
            if (particles != null)
            {
                foreach (var p in particles)
                {
                    var t = Get<Transform>(p, "m_Transform", "Transform");
                    if (t == null)
                    {
                        continue; // The end particle past the last bone has no transform.
                    }
                    chain.Particles.Add(new PhysicsParticle
                    {
                        BoneKey = rig.BoneKey(t),
                        Damping = Get<float>(p, "m_Damping", "Damping"),
                        Elasticity = Get<float>(p, "m_Elasticity", "Elasticity"),
                        Stiffness = Get<float>(p, "m_Stiffness", "Stiffness"),
                        Inert = Get<float>(p, "m_Inert", "Inert"),
                        Radius = Get<float>(p, "m_Radius", "Radius"),
                    });
                }
            }
            return chain.Particles.Count > 0 ? chain : null;
        }

        /// <summary>Gravity and force are world directions; the Character root's rotation is taken out.</summary>
        private Vector3 WorldToRoot(Vector3 v)
        {
            return rig.RootInverse.MultiplyVector(v);
        }

        private static bool Has(object o, string name)
        {
            return AccessTools.Field(o.GetType(), name) != null;
        }

        /// <summary>The first of the named fields the object has, or the default when it has none.</summary>
        private static T Get<T>(object o, params string[] fieldNames)
        {
            foreach (string name in fieldNames)
            {
                var field = AccessTools.Field(o.GetType(), name);
                if (field != null)
                {
                    var value = field.GetValue(o);
                    return value is T ? (T)value : default(T);
                }
            }
            return default(T);
        }
    }
}
