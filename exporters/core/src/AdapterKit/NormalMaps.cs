using System;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Converts normal maps from Unity's packed form to standard tangent-space maps, which is what the
    /// contract stores. The adapter reads the texture's pixels and calls the unpacking its game's Unity
    /// does before encoding the PNG.
    /// </summary>
    public static class NormalMaps
    {
        /// <summary>
        /// Unpacks RGBA32 pixels in place the way Unity 2017.1 and later's <c>UnpackNormal</c> does
        /// (<c>UnpackNormalmapRGorAG</c>; KKS, SVS): X is R times A (A alone for DXT5nm, which these
        /// versions store with R at 1; R alone for plain and BC5 maps, where A is 1), Y is G, and Z is
        /// rebuilt. The result is (X, Y, Z) mapped to 0–255 with an opaque alpha. Y stays +Y up, as in
        /// Unity and Blender.
        /// </summary>
        public static void UnpackUnity(byte[] rgba)
        {
            Unpack(rgba, false);
        }

        /// <summary>
        /// Unpacks RGBA32 pixels in place the way Unity 5.6's <c>UnpackNormal</c> does
        /// (<c>UnpackNormalDXT5nm</c>; KK): X is A and Y is G, whatever R holds. KK's normal maps are
        /// DXT5nm with Y copied into R, G and B, so a flat normal is about (128, 128, 128, 128) and R
        /// times A would tilt every normal by half.
        /// </summary>
        public static void UnpackDxt5nm(byte[] rgba)
        {
            Unpack(rgba, true);
        }

        private static void Unpack(byte[] rgba, bool xFromAlpha)
        {
            if (rgba == null || rgba.Length % 4 != 0)
            {
                throw new ArgumentException("Pixels must be RGBA32: four bytes each.", "rgba");
            }
            for (int i = 0; i < rgba.Length; i += 4)
            {
                double a = rgba[i + 3] / 255.0;
                double x = (xFromAlpha ? a : rgba[i] / 255.0 * a) * 2 - 1;
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
