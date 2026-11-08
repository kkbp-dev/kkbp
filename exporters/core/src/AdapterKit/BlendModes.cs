using System.Collections.Generic;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Chooses a material's Blend Mode: from the Game's shader tables first, then from the render queue.
    /// </summary>
    public static class BlendModes
    {
        /// <summary>Unity's first alpha-tested queue.</summary>
        public const int AlphaTestQueue = 2450;

        /// <summary>Unity's first transparent queue.</summary>
        public const int TransparentQueue = 3000;

        public static BlendMode From(string shader, int renderQueue, bool alphaClip, ICollection<string> glassesShaders, ICollection<string> alphaShaders)
        {
            if (shader != null && glassesShaders.Contains(shader))
            {
                return BlendMode.Glasses;
            }
            if ((shader != null && alphaShaders.Contains(shader)) || renderQueue >= TransparentQueue)
            {
                return BlendMode.Alpha;
            }
            if (alphaClip || renderQueue >= AlphaTestQueue)
            {
                return BlendMode.Cutout;
            }
            return BlendMode.Opaque;
        }
    }
}
