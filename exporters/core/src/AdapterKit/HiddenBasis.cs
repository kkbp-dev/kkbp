using System;

namespace KKBP.Exporter.Core.AdapterKit
{
    /// <summary>
    /// Hides a tear or gag-eye mesh inside the head and gives it the shape key that shows it (ADR 0010).
    /// </summary>
    public static class HiddenBasis
    {
        /// <summary>
        /// How far to push a mesh back: half the face mesh's depth along Unity's +Z, which is the way the
        /// Character faces at the capture pose, so the mesh rests in the middle of the head. A whole depth
        /// put it out through the back of the head. The result points backwards.
        /// </summary>
        public static Vec3 Offset(Vec3[] facePositions)
        {
            if (facePositions == null || facePositions.Length == 0)
            {
                throw new ArgumentException("The face mesh has no vertices.", "facePositions");
            }
            float min = float.MaxValue;
            float max = float.MinValue;
            foreach (var p in facePositions)
            {
                min = Math.Min(min, p.Z);
                max = Math.Max(max, p.Z);
            }
            return new Vec3(0, 0, -(max - min) / 2);
        }

        /// <summary>
        /// How much of its width a hidden mesh keeps. The head narrows towards its back, so at its
        /// full width a mesh that is as wide as the eyes comes out through the sides there (issue 84).
        /// </summary>
        public const float Width = 0.5f;

        /// <summary>The middle of the face mesh from left to right, which hidden meshes narrow towards.</summary>
        public static float Middle(Vec3[] facePositions)
        {
            if (facePositions == null || facePositions.Length == 0)
            {
                throw new ArgumentException("The face mesh has no vertices.", "facePositions");
            }
            float min = float.MaxValue;
            float max = float.MinValue;
            foreach (var p in facePositions)
            {
                min = Math.Min(min, p.X);
                max = Math.Max(max, p.X);
            }
            return (min + max) / 2;
        }

        /// <summary>
        /// Moves the mesh's vertices by the offset, narrows them towards `middle`, and adds the showing
        /// key, which puts them back. Shape keys already on the mesh are deltas, so they stay as they are.
        /// </summary>
        public static void Apply(MeshData mesh, Vec3 offset, float middle, ExpressionCategory category, string expressionName)
        {
            if (category != ExpressionCategory.Tears && category != ExpressionCategory.Gag)
            {
                throw new ArgumentException("Only tear and gag-eye meshes have a showing key.", "category");
            }
            var show = new Vec3[mesh.Positions.Length];
            for (int i = 0; i < show.Length; i++)
            {
                var shown = mesh.Positions[i];
                var hidden = shown + offset;
                hidden.X = middle + (hidden.X - middle) * Width;
                mesh.Positions[i] = hidden;
                show[i] = shown - hidden;
            }
            mesh.Morphs.Add(new MorphData { Category = category, ExpressionName = expressionName, PositionDeltas = show });
        }
    }
}
