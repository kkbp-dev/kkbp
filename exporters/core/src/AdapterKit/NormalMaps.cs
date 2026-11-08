using System;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Converts normal maps from Unity's packed form to standard tangent-space maps, which is what the
    /// contract stores. The adapter reads the texture's pixels and calls this before encoding the PNG.
    /// </summary>
    public static class NormalMaps
    {
        /// <summary>
        /// Unpacks RGBA32 pixels in place the way Unity's <c>UnpackNormal</c> does: X is R times A (A alone
        /// for DXT5nm, where R is 1; R alone for plain maps, where A is 1), Y is G, and Z is rebuilt. The
        /// result is (X, Y, Z) mapped to 0–255 with an opaque alpha. Y stays +Y up, as in Unity and Blender.
        /// </summary>
        public static void UnpackUnity(byte[] rgba)
        {
            if (rgba == null || rgba.Length % 4 != 0)
            {
                throw new ArgumentException("Pixels must be RGBA32: four bytes each.", "rgba");
            }
            for (int i = 0; i < rgba.Length; i += 4)
            {
                double x = rgba[i] / 255.0 * (rgba[i + 3] / 255.0) * 2 - 1;
                double y = rgba[i + 1] / 255.0 * 2 - 1;
                double z = Math.Sqrt(Math.Max(0, 1 - x * x - y * y));
                rgba[i] = ToByte(x);
                rgba[i + 1] = ToByte(y);
                rgba[i + 2] = ToByte(z);
                rgba[i + 3] = 255;
            }
        }

        private static byte ToByte(double v)
        {
            return (byte)Math.Round(Math.Max(0, Math.Min(255, (v * 0.5 + 0.5) * 255)));
        }
    }
}
