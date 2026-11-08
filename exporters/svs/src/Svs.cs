using System.Collections.Generic;
using Character;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>What the SVS adapter needs from the game beyond the shared capture code.</summary>
    internal static class Svs
    {
        /// <summary>
        /// Roles for SVS names the shared table doesn't have. SVS has no cf_J_hitomi_tx bones; the eye
        /// movers are cf_J_Eye_tx. (KK has those too, but uses hitomi for its eyes.)
        /// </summary>
        public static BoneRole? Role(string name)
        {
            switch (name)
            {
                case "cf_J_Eye_tx_L": return BoneRole.LeftEye;
                case "cf_J_Eye_tx_R": return BoneRole.RightEye;
                case "cf_j_FaceRoot": return BoneRole.FaceRoot;
                default: return null;
            }
        }

        public static byte[] EncodePng(Texture2D texture)
        {
            return Seam.Bytes(ImageConversion.EncodeToPNG(texture));
        }

        public static List<ShaderProperty> Properties(Shader shader)
        {
            var result = new List<ShaderProperty>();
            if (shader == null)
            {
                return result;
            }
            int count = shader.GetPropertyCount();
            for (int i = 0; i < count; i++)
            {
                char kind;
                switch (shader.GetPropertyType(i))
                {
                    case UnityEngine.Rendering.ShaderPropertyType.Color: kind = 'c'; break;
                    case UnityEngine.Rendering.ShaderPropertyType.Vector: kind = 'v'; break;
                    case UnityEngine.Rendering.ShaderPropertyType.Texture: kind = 't'; break;
                    default: kind = 'f'; break;
                }
                result.Add(new ShaderProperty { Name = shader.GetPropertyName(i), Kind = kind });
            }
            return result;
        }

        /// <summary>The maker's directional light.</summary>
        public static Light MakerLight()
        {
            foreach (var light in Object.FindObjectsOfType<Light>())
            {
                if (light.type == LightType.Directional)
                {
                    return light;
                }
            }
            throw new ExportException("The maker has no directional light.");
        }

        /// <summary>
        /// The game's T-pose clips (tpose_S, tpose_M, tpose_L) belong to its craft-mode animator controllers,
        /// which the maker's pose list doesn't offer. They are humanoid animations, so any of them fits.
        /// </summary>
        private static readonly string[][] TPoseControllers =
        {
            new[] { "craft/anime/023_01.unity3d", "sv_dc_rez_f2_base_01" },
            new[] { "craft/anime/023_00.unity3d", "sv_dc_m_23" },
        };

        private static readonly string[] TPoseClips = { "tpose_M", "tpose_S", "tpose_L" };

        /// <summary>
        /// Loads a craft-mode controller into the maker and plays its T-pose clip in place of the clip the
        /// animator plays now. Fails the export if none is found. The adapter checks the arms again before
        /// recording the skeleton.
        /// </summary>
        public static void PlayTPose(Human human)
        {
            var custom = CharacterCreation.HumanCustom.Instance;
            var animator = human.body.animBody;
            animator.enabled = true;
            foreach (var entry in TPoseControllers)
            {
                custom.LoadAnimation(entry[0], entry[1]);
                var controller = animator.runtimeAnimatorController;
                var playing = animator.GetCurrentAnimatorClipInfo(0);
                if (controller == null || playing.Length == 0)
                {
                    continue;
                }
                foreach (string name in TPoseClips)
                {
                    foreach (var clip in controller.animationClips)
                    {
                        if (clip != null && clip.name == name)
                        {
                            var overrides = new AnimatorOverrideController(controller);
                            overrides[playing[0].clip] = clip;
                            animator.runtimeAnimatorController = overrides;
                            Plugin.Logger.LogInfo("T-pose: " + name + " of " + entry[1]);
                            return;
                        }
                    }
                }
            }
            throw new ExportException("None of the game's craft-mode animators has a T-pose clip.");
        }

        /// <summary>True when both arms point sideways, not down.</summary>
        public static bool ArmsLevel(Human human, bool log)
        {
            foreach (string side in new[] { "_L", "_R" })
            {
                var upper = Find(human.objTop.transform, "cf_j_arm00" + side);
                var lower = Find(human.objTop.transform, "cf_j_forearm01" + side);
                if (upper == null || lower == null)
                {
                    return false;
                }
                var direction = (lower.position - upper.position).normalized;
                if (log)
                {
                    Plugin.Logger.LogInfo("Upper arm" + side + " points " + direction);
                }
                if (Mathf.Abs(direction.y) > 0.25f)
                {
                    return false;
                }
            }
            return true;
        }

        public static Transform Find(Transform root, string name)
        {
            foreach (var t in root.GetComponentsInChildren<Transform>(true))
            {
                if (t.name == name)
                {
                    return t;
                }
            }
            return null;
        }

        /// <summary>Switches the Character to an Outfit and reloads its clothes and accessories.</summary>
        public static void ChangeOutfit(Human human, int outfit)
        {
            human.coorde.ChangeCoordinateType((ChaFileDefine.CoordinateType)outfit);
            human.ReloadCoordinate(Human.ReloadFlags.Coorde);
        }

        /// <summary>The Character's card as the game saves it: the picture, then the Character data.</summary>
        public static byte[] Card(Human human)
        {
            var stream = new Il2CppSystem.IO.MemoryStream();
            human.data.SaveFile(stream.Cast<Il2CppSystem.IO.Stream>(), HumanData.SaveFileInfo.Flags.Default);
            return Seam.Bytes(stream.ToArray());
        }
    }
}
