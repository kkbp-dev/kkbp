using System.Collections.Generic;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// The Raw Properties each Texture Role covers, as contract/README.md lists them. A slot outside
    /// this table has no Role and is known by its Raw Property only.
    /// </summary>
    public static class TextureRoles
    {
        private static readonly Dictionary<string, TextureRole> ByRaw = new Dictionary<string, TextureRole>
        {
            { "_MainTex", TextureRole.Main }, { "_Main_texture", TextureRole.Main },
            { "_ColorMask", TextureRole.ColorMask }, { "_Main_color_mask", TextureRole.ColorMask }, { "_Hair_color_mask", TextureRole.ColorMask },
            { "_NormalMap", TextureRole.Normal }, { "_Normal_map", TextureRole.Normal },
            { "_NormalMapDetail", TextureRole.DetailNormal }, { "_DetailNormal", TextureRole.DetailNormal },
            { "_AlphaMask", TextureRole.AlphaMask }, { "_Cloth_alpha", TextureRole.AlphaMask },
            { "_LineMask", TextureRole.LineMask }, { "_Line_mask", TextureRole.LineMask },
            { "_DetailMask", TextureRole.DetailMask }, { "_Detail_mask", TextureRole.DetailMask },
            { "_overtex1", TextureRole.Overlay }, { "_overtex2", TextureRole.Overlay }, { "_overtex3", TextureRole.Overlay },
        };

        public static TextureRole? For(string raw)
        {
            TextureRole role;
            return raw != null && ByRaw.TryGetValue(raw, out role) ? role : (TextureRole?)null;
        }

        /// <summary>True for slots holding a normal map, which must be unpacked before export.</summary>
        public static bool IsNormalMap(string raw)
        {
            var role = For(raw);
            return (role == TextureRole.Normal || role == TextureRole.DetailNormal) || raw == "_BumpMap";
        }
    }
}
