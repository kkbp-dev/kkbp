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
        /// Moves the mesh's vertices by the offset and adds the showing key, which moves them back.
        /// Shape keys already on the mesh are deltas, so they stay as they are.
        /// </summary>
        public static void Apply(MeshData mesh, Vec3 offset, ExpressionCategory category, string expressionName)
        {
            if (category != ExpressionCategory.Tears && category != ExpressionCategory.Gag)
            {
                throw new ArgumentException("Only tear and gag-eye meshes have a showing key.", "category");
            }
            var show = new Vec3[mesh.Positions.Length];
            for (int i = 0; i < show.Length; i++)
            {
                mesh.Positions[i] = mesh.Positions[i] + offset;
                show[i] = offset * -1;
            }
            mesh.Morphs.Add(new MorphData { Category = category, ExpressionName = expressionName, PositionDeltas = show });
        }
    }
}
