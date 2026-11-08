using System;
using System.Collections.Generic;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>Captures the game's dynamic bone colliders.</summary>
    internal sealed class Physics
    {
        private readonly Rig rig;
        private readonly Dictionary<int, string> names = new Dictionary<int, string>();
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
                if (inPass(collider.transform) && !names.ContainsKey(collider.GetInstanceID()))
                {
                    sink.Colliders.Add(Collider(collider));
                }
            }
            // SVS moves hair, clothes and breasts with MagicaCloth, not dynamic bones, and physics.json has no
            // place for MagicaCloth yet, so SVS bundles carry colliders but no chains.
        }

        private PhysicsCollider Collider(DynamicBoneCollider c)
        {
            string name = c.name;
            for (int i = 2; !used.Add(name); i++)
            {
                name = c.name + "_" + i;
            }
            names[c.GetInstanceID()] = name;

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
    }
}
