using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using Character;
using CharacterCreation;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>Describes the maker's Character as the game exposes it, for writing and checking the adapter.</summary>
    internal static class Diagnostics
    {
        public static string Describe(Human human)
        {
            var sb = new StringBuilder();
            sb.AppendLine("name: " + human.fileParam.fullname);
            sb.AppendLine("objTop: " + human.objTop.name + " root: " + human.transform.name);
            var anim = human.body.animBody;
            sb.AppendLine("animator: " + (anim != null ? anim.name : "none") + " avatar human: " + (anim != null && anim.avatar != null && anim.avatar.isHuman));
            if (anim != null && anim.avatar != null && anim.avatar.isHuman)
            {
                foreach (HumanBodyBones b in new[] { HumanBodyBones.Hips, HumanBodyBones.Spine, HumanBodyBones.Chest, HumanBodyBones.UpperChest, HumanBodyBones.Head, HumanBodyBones.LeftEye, HumanBodyBones.Jaw, HumanBodyBones.LeftFoot, HumanBodyBones.LeftToes })
                {
                    var t = anim.GetBoneTransform(b);
                    sb.AppendLine("  " + b + " -> " + (t != null ? t.name : "-"));
                }
            }
            sb.AppendLine("coordinates: now " + human.fileStatus.coordinateType + " count " + human.data.Coordinates.Length);

            var custom = HumanCustom.Instance;
            var poses = custom.PoseList.TryCast<Il2CppSystem.Collections.Generic.List<CharacterCreation.ListInfo.PoseInfoData>>();
            sb.AppendLine("poses: " + (poses != null ? poses.Count.ToString() : "not a List") + " now " + custom.NowPose);
            for (int i = 0; poses != null && i < poses.Count; i++)
            {
                sb.AppendLine("  " + i + ": " + Props(poses[i]));
            }

            var face = human.face;
            sb.AppendLine("face ctrls: eyes " + face.eyesCtrl.GetMaxPtn() + " eyebrow " + face.eyebrowCtrl.GetMaxPtn() + " mouth " + face.mouthCtrl.GetMaxPtn()
                + " eyes open " + face.eyesCtrl.OpenMin + ".." + face.eyesCtrl.OpenMax + " gags " + (face.objGags != null ? face.objGags.Length : -1));
            foreach (ChaListDefine.CategoryNo c in Enum.GetValues(typeof(ChaListDefine.CategoryNo)))
            {
                string n = c.ToString();
                if (n.IndexOf("eye", StringComparison.OrdinalIgnoreCase) >= 0 || n.IndexOf("mouth", StringComparison.OrdinalIgnoreCase) >= 0 || n.IndexOf("brow", StringComparison.OrdinalIgnoreCase) >= 0)
                {
                    var info = Human.lstCtrl.GetCategoryInfo(c);
                    sb.AppendLine("list " + n + ": " + (info != null ? info.Count : -1));
                }
            }

            sb.AppendLine("lights:");
            foreach (var l in UnityEngine.Object.FindObjectsOfType<Light>())
            {
                sb.AppendLine("  " + l.name + " " + l.type + " " + l.intensity + " rot " + l.transform.rotation.eulerAngles + " layer mask " + l.cullingMask);
            }
            var cam = Camera.main;
            sb.AppendLine("camera: " + (cam != null ? cam.name + " mask " + cam.cullingMask : "none"));

            var counts = new SortedDictionary<string, int>();
            foreach (var c in human.objTop.GetComponentsInChildren<MonoBehaviour>(true))
            {
                string type = c.GetIl2CppType().FullName;
                if (type.Contains("Dynamic") || type.Contains("Magica") || type.Contains("Cha") || type.Contains("FBS"))
                {
                    counts.TryGetValue(type, out int n);
                    counts[type] = n + 1;
                }
            }
            sb.AppendLine("components: " + string.Join(", ", counts.Select(p => p.Key + "=" + p.Value)));

            sb.AppendLine("renderers:");
            foreach (var r in human.objTop.GetComponentsInChildren<Renderer>(true))
            {
                Mesh mesh = null;
                var smr = r.TryCast<SkinnedMeshRenderer>();
                if (smr != null)
                {
                    mesh = smr.sharedMesh;
                }
                else
                {
                    var filter = r.GetComponent<MeshFilter>();
                    mesh = filter != null ? filter.sharedMesh : null;
                }
                var shaders = string.Join("|", r.sharedMaterials.Select(m => m != null ? m.name + "<" + m.shader.name + ">" : "null"));
                sb.AppendLine("  " + Path(r.transform, human.objTop.transform) + " [" + (smr != null ? "smr" : r.GetIl2CppType().Name) + "] on " + r.enabled + " active " + r.gameObject.activeInHierarchy
                    + " owner " + Owner(r.transform, human.objTop.transform)
                    + (mesh != null ? " mesh " + mesh.name + " v" + mesh.vertexCount + " readable " + mesh.isReadable + " shapes " + mesh.blendShapeCount + " sub " + mesh.subMeshCount : " no mesh")
                    + " layer " + r.gameObject.layer + " mats " + shaders);
            }
            return sb.ToString();
        }

        private static string Owner(Transform t, Transform top)
        {
            for (; t != null && t != top.parent; t = t.parent)
            {
                if (t.GetComponent<ChaCustomHairComponent>() != null) return "hair";
                if (t.GetComponent<ChaClothesComponent>() != null) return "clothes";
                if (t.GetComponent<ChaAccessoryComponent>() != null) return "accessory";
            }
            return "body";
        }

        private static string Path(Transform t, Transform top)
        {
            var parts = new List<string>();
            for (; t != null && t != top.parent; t = t.parent)
            {
                parts.Add(t.name);
            }
            parts.Reverse();
            return string.Join("/", parts);
        }

        private static string Props(object o)
        {
            if (o == null)
            {
                return "null";
            }
            var sb = new StringBuilder();
            foreach (var p in o.GetType().GetProperties())
            {
                if (p.GetIndexParameters().Length > 0 || p.Name == "Pointer" || p.Name == "ObjectClass" || p.Name == "WasCollected")
                {
                    continue;
                }
                object v;
                try
                {
                    v = p.GetValue(o, null);
                }
                catch
                {
                    continue;
                }
                sb.Append(p.Name).Append('=').Append(v).Append(' ');
            }
            return sb.ToString();
        }
    }
}
