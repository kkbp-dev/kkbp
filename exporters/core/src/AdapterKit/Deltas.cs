using System;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Shape-key arithmetic for baking expressions (ADR 0003). The adapter evaluates each expression in
    /// the game, reads back the posed vertices, and turns them into deltas from the basis here.
    /// </summary>
    public static class Deltas
    {
        /// <summary>Below this a coordinate difference counts as no change, in metres.</summary>
        public const float Tolerance = 1e-6f;

        public static Vec3[] Subtract(Vec3[] posed, Vec3[] basis)
        {
            if (posed == null || basis == null || posed.Length != basis.Length)
            {
                throw new ArgumentException("Posed and basis vertices must have the same count.");
            }
            var result = new Vec3[posed.Length];
            for (int i = 0; i < posed.Length; i++)
            {
                result[i] = posed[i] - basis[i];
            }
            return result;
        }

        /// <summary>True if no vertex moves by more than the tolerance.</summary>
        public static bool IsEmpty(Vec3[] deltas)
        {
            foreach (var d in deltas)
            {
                if (Math.Abs(d.X) > Tolerance || Math.Abs(d.Y) > Tolerance || Math.Abs(d.Z) > Tolerance)
                {
                    return false;
                }
            }
            return true;
        }

        /// <summary>True if the two shape keys move every vertex the same way, within the tolerance.</summary>
        public static bool Same(Vec3[] a, Vec3[] b)
        {
            if (a.Length != b.Length)
            {
                return false;
            }
            for (int i = 0; i < a.Length; i++)
            {
                if (Math.Abs(a[i].X - b[i].X) > Tolerance || Math.Abs(a[i].Y - b[i].Y) > Tolerance || Math.Abs(a[i].Z - b[i].Z) > Tolerance)
                {
                    return false;
                }
            }
            return true;
        }
    }
}
