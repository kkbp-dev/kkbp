using System.Collections.Generic;
using System.IO;
using System.Text;
using ChaCustom;
using KKBP.Exporter.Core;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>Everything that differs between KK and KKS. The rest of the adapter is shared.</summary>
    internal static class Kks
    {
#if KKS
        public const string Game = "KKS";
#else
        public const string Game = "KK";
#endif

        /// <summary>
        /// The marks of the character cards the game loads, as its own card reader lists them. Its
        /// LoadFileLimited reports no error for other files, such as outfit cards, and keeps the
        /// Character it had.
        /// </summary>
#if KKS
        public static readonly string[] CardMarks = { "【KoiKatuChara】", "【KoiKatuCharaS】", "【KoiKatuCharaSP】", "【KoiKatuCharaSun】" };
#else
        public static readonly string[] CardMarks = { "【KoiKatuChara】" };
#endif

        /// <summary>The maker's pose list entry that is the T-pose.</summary>
        public const string TPoseState = "tpose";

        public static byte[] EncodePng(Texture2D texture)
        {
#if KKS
            return ImageConversion.EncodeToPNG(texture);
#else
            return texture.EncodeToPNG();
#endif
        }

        /// <summary>The maker's directional light, which the light and dark bake turns.</summary>
        public static Light MakerLight()
        {
            var lights = Object.FindObjectsOfType<Light>();
#if KKS
            return lights[1];
#else
            return lights[0];
#endif
        }

        /// <summary>Camera effects that would tint the bake, switched off until Restore.</summary>
        public sealed class CameraEffects
        {
            private readonly Component amplify;
            private readonly object mask;

            internal CameraEffects(Component amplify, object mask)
            {
                this.amplify = amplify;
                this.mask = mask;
            }

            public void Restore()
            {
                if (amplify != null)
                {
                    HarmonyLib.AccessTools.Field(amplify.GetType(), "MaskTexture").SetValue(amplify, mask);
                }
            }
        }

        /// <summary>KKS's maker camera grades colour through AmplifyColor's mask; the bake clears the mask.</summary>
        public static CameraEffects QuietCameraEffects(Camera camera)
        {
#if KKS
            var amplify = camera.GetComponent("AmplifyColorEffect");
            var field = amplify != null ? HarmonyLib.AccessTools.Field(amplify.GetType(), "MaskTexture") : null;
            if (field != null)
            {
                var mask = field.GetValue(amplify);
                field.SetValue(amplify, null);
                return new CameraEffects(amplify, mask);
            }
#endif
            return new CameraEffects(null, null);
        }

        /// <summary>Plays the maker's T-pose. Fails the export if the pose list has none.</summary>
        public static void PlayTPose()
        {
            var maker = CustomBase.Instance;
            int index = -1;
#if KKS
            for (int i = 0; i < maker.lstPose.Length; i++)
            {
                if (maker.lstPose[i].State == TPoseState)
                {
                    index = i;
                }
            }
#else
            index = maker.lstPose.FindIndex(p => p.list.Count > 4 && p.list[4] == TPoseState);
#endif
            if (index < 0)
            {
                throw new ExportException("The maker's pose list has no T-pose.");
            }
            Object.FindObjectOfType<CvsDrawCtrl>().ChangeAnimationForce(index, 0f);
        }

        /// <summary>The game's own names for its eyebrow and mouth patterns, by position, for reference only.</summary>
        public static List<string> PatternNames(bool mouth)
        {
            var maker = CustomBase.Instance;
            var names = new List<string>();
#if KKS
            foreach (var p in mouth ? maker.lstMouth : maker.lstEyebrow)
            {
                names.Add(p.Name);
            }
#else
            foreach (var p in mouth ? maker.lstMouth : maker.lstEyebrow)
            {
                names.Add(p.list.Count > 1 ? p.list[1] : "");
            }
#endif
            return names;
        }

#if !KKS
        private static Dictionary<string, List<ShaderProperty>> table;
#endif

        /// <summary>
        /// A shader's properties. KKS asks the shader; KK's Unity 5.6 can't, so KK reads a table made by
        /// dumping KKS's shaders (DumpShaders), which share their names and properties with KK's.
        /// </summary>
        public static List<ShaderProperty> Properties(Shader shader)
        {
            var result = new List<ShaderProperty>();
            if (shader == null)
            {
                return result;
            }
#if KKS
            int count = shader.GetPropertyCount();
            for (int i = 0; i < count; i++)
            {
                result.Add(new ShaderProperty { Name = shader.GetPropertyName(i), Kind = Kind(shader.GetPropertyType(i)) });
            }
#else
            if (table == null)
            {
                table = LoadTable();
            }
            List<ShaderProperty> known;
            if (table.TryGetValue(shader.name, out known))
            {
                result.AddRange(known);
            }
            else if (table.TryGetValue("", out known))
            {
                // An unknown shader: try every property any known shader has.
                result.AddRange(known);
            }
#endif
            return result;
        }

#if KKS
        private static char Kind(UnityEngine.Rendering.ShaderPropertyType type)
        {
            switch (type)
            {
                case UnityEngine.Rendering.ShaderPropertyType.Color: return 'c';
                case UnityEngine.Rendering.ShaderPropertyType.Vector: return 'v';
                case UnityEngine.Rendering.ShaderPropertyType.Texture: return 't';
                default: return 'f';
            }
        }

        /// <summary>
        /// Writes every loaded shader's properties as the table KK reads, plus those of the shaders in
        /// <paramref name="bundles"/>, which are loaded for the dump and unloaded after it. KK's own
        /// bundles hold shaders KKS doesn't load, such as KK's create shaders.
        /// </summary>
        public static void DumpShaders(string path, List<string> bundles)
        {
            var shaders = new SortedDictionary<string, Shader>(System.StringComparer.Ordinal);
            foreach (var shader in Resources.FindObjectsOfTypeAll<Shader>())
            {
                if (!string.IsNullOrEmpty(shader.name))
                {
                    shaders[shader.name] = shader;
                }
            }
            var loaded = new List<AssetBundle>();
            foreach (string file in bundles)
            {
                var bundle = AssetBundle.LoadFromFile(file);
                if (bundle == null)
                {
                    Plugin.Log.LogWarning("Couldn't load " + file + " for the shader dump.");
                    continue;
                }
                loaded.Add(bundle);
                var found = new List<Shader>(bundle.LoadAllAssets<Shader>());
                foreach (var material in bundle.LoadAllAssets<Material>())
                {
                    found.Add(material.shader);
                }
                foreach (var shader in found)
                {
                    if (shader != null && !string.IsNullOrEmpty(shader.name) && !shaders.ContainsKey(shader.name))
                    {
                        shaders[shader.name] = shader;
                        Plugin.Log.LogInfo("Shader dump: " + shader.name + " from " + file);
                    }
                }
            }
            var root = new JsonObject();
            foreach (var pair in shaders)
            {
                var props = new JsonObject();
                foreach (var p in Properties(pair.Value))
                {
                    if (!props.TryGet(p.Name, out _))
                    {
                        props.Add(p.Name, p.Kind.ToString());
                    }
                }
                root.Add(pair.Key, props);
            }
            File.WriteAllText(path, JsonWriter.Write(root, true), new UTF8Encoding(false));
            foreach (var bundle in loaded)
            {
                bundle.Unload(true);
            }
        }
#else
        private static Dictionary<string, List<ShaderProperty>> LoadTable()
        {
            var result = new Dictionary<string, List<ShaderProperty>>();
            var any = new Dictionary<string, char>();
            using (var stream = typeof(Kks).Assembly.GetManifestResourceStream("KKBP.ShaderProperties.json"))
            {
                if (stream == null)
                {
                    return result;
                }
                using (var reader = new StreamReader(stream))
                {
                    var root = (JsonObject)JsonReader.Parse(reader.ReadToEnd());
                    foreach (var shader in root.Members)
                    {
                        var list = new List<ShaderProperty>();
                        foreach (var p in ((JsonObject)shader.Value).Members)
                        {
                            char kind = ((string)p.Value)[0];
                            list.Add(new ShaderProperty { Name = p.Key, Kind = kind });
                            any[p.Key] = kind;
                        }
                        result[shader.Key] = list;
                    }
                }
            }
            var all = new List<ShaderProperty>();
            foreach (var p in any)
            {
                all.Add(new ShaderProperty { Name = p.Key, Kind = p.Value });
            }
            result[""] = all;
            return result;
        }
#endif
    }
}
