using System.Collections.Generic;
using KKBP.Exporter.Core;
using KKBP.Exporter.Core.AdapterKit;
using UnityEngine;

namespace KKBP.Exporter
{
    /// <summary>A shader property and its kind.</summary>
    internal struct ShaderProperty
    {
        public string Name;

        /// <summary>'c' colour, 'f' float or range, 'v' vector, 't' texture.</summary>
        public char Kind;
    }

    /// <summary>Captures materials: shader values by Raw Property, textures as PNG, Material Role and Blend Mode.</summary>
    internal sealed class Materials
    {
        private static readonly HashSet<string> GlassesShaders = new HashSet<string>
        {
            "Shader Forge/toon_glasses_lod0", "Koikano/main_clothes_item_glasses",
        };

        private static readonly HashSet<string> AlphaShaders = new HashSet<string>
        {
            "Shader Forge/main_alpha", "Koikano/main_clothes_alpha", "xukmi/MainAlphaPlus", "xukmi/MainAlphaPlusTess",
            "xukmi/MainItemAlphaPlus", "IBL_Shader_alpha",
        };

        /// <summary>Face overlays the game draws blended over the face.</summary>
        private static readonly HashSet<MaterialRole> OverlayRoles = new HashSet<MaterialRole>
        {
            MaterialRole.Eyebrow, MaterialRole.EyelineUpper, MaterialRole.EyelineLower, MaterialRole.EyelineShadow,
            MaterialRole.NoseLine, MaterialRole.EyeL, MaterialRole.EyeR,
        };

        private readonly Dictionary<int, byte[]> pngs = new Dictionary<int, byte[]>();

        /// <summary>Captures a material, leaving out the texture slots in <paramref name="skip"/>.</summary>
        public MaterialData Capture(Material material, string key, MaterialRole? role, ICollection<string> skip = null)
        {
            string shader = material.shader != null ? material.shader.name : "";
            var data = new MaterialData
            {
                Key = key,
                Name = Seam.CleanName(material.name),
                Shader = shader,
                Role = role,
            };
            data.BlendMode = role.HasValue && OverlayRoles.Contains(role.Value)
                ? BlendMode.Alpha
                : BlendModes.From(shader, material.renderQueue, false, GlassesShaders, AlphaShaders);

            foreach (var p in Svs.Properties(material.shader))
            {
                if (!material.HasProperty(p.Name))
                {
                    continue;
                }
                switch (p.Kind)
                {
                    case 'c':
                        data.Colors[p.Name] = Seam.C(material.GetColor(p.Name));
                        break;
                    case 'f':
                        data.Floats[p.Name] = material.GetFloat(p.Name);
                        break;
                    case 'v':
                        data.Vectors[p.Name] = Seam.V4(material.GetVector(p.Name));
                        break;
                    case 't':
                        var texture = material.GetTexture(p.Name);
                        if (texture != null && (skip == null || !skip.Contains(p.Name)))
                        {
                            data.Textures.Add(Texture(p.Name, texture, material.GetTextureOffset(p.Name), material.GetTextureScale(p.Name), null));
                        }
                        break;
                }
            }
            return data;
        }

        /// <summary>A texture for a slot, as PNG. Normal maps are unpacked from Unity's format first.</summary>
        public TextureData Texture(string raw, Texture texture, Vector2 offset, Vector2 scale, string pattern)
        {
            return new TextureData
            {
                Role = TextureRoles.For(raw),
                Raw = raw,
                Pattern = pattern,
                Png = Png(texture, TextureRoles.IsNormalMap(raw)),
                Offset = Seam.V2(offset),
                Scale = Seam.V2(scale),
            };
        }

        public byte[] Png(Texture texture, bool normalMap)
        {
            int id = texture.GetInstanceID() * 2 + (normalMap ? 1 : 0);
            byte[] png;
            if (pngs.TryGetValue(id, out png))
            {
                return png;
            }
            var readable = Read(texture);
            if (normalMap)
            {
                var pixels = readable.GetPixels32();
                var bytes = new byte[pixels.Length * 4];
                for (int i = 0; i < pixels.Length; i++)
                {
                    bytes[i * 4] = pixels[i].r;
                    bytes[i * 4 + 1] = pixels[i].g;
                    bytes[i * 4 + 2] = pixels[i].b;
                    bytes[i * 4 + 3] = pixels[i].a;
                }
                NormalMaps.UnpackUnity(bytes);
                for (int i = 0; i < pixels.Length; i++)
                {
                    pixels[i] = new Color32(bytes[i * 4], bytes[i * 4 + 1], bytes[i * 4 + 2], bytes[i * 4 + 3]);
                }
                readable.SetPixels32(pixels);
                readable.Apply();
            }
            png = Svs.EncodePng(readable);
            Object.Destroy(readable);
            pngs[id] = png;
            return png;
        }

        /// <summary>Copies any texture, readable or not, into a readable RGBA32 one through a render texture.</summary>
        private static Texture2D Read(Texture texture)
        {
            int w = Mathf.Max(1, texture.width);
            int h = Mathf.Max(1, texture.height);
            var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Linear);
            var previous = RenderTexture.active;
            Graphics.Blit(texture, rt);
            RenderTexture.active = rt;
            var result = new Texture2D(w, h, TextureFormat.RGBA32, false, true);
            result.ReadPixels(new Rect(0, 0, w, h), 0, 0);
            result.Apply();
            RenderTexture.active = previous;
            RenderTexture.ReleaseTemporary(rt);
            return result;
        }
    }
}
