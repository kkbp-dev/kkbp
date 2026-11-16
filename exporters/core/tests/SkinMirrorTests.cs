using KKBP.Exporter.Core.AdapterKit;
using Xunit;

namespace KKBP.Exporter.Core.Tests
{
    public class SkinMirrorTests
    {
        /// <summary>A row-major translation matrix.</summary>
        private static float[] Move(float x, float y, float z)
        {
            return new float[] { 1, 0, 0, x, 0, 1, 0, y, 0, 0, 1, z, 0, 0, 0, 1 };
        }

        /// <summary>A row-major rotation about Z by a small angle, then a move.</summary>
        private static float[] Turn(float radians, float x, float y, float z)
        {
            float c = (float)System.Math.Cos(radians), s = (float)System.Math.Sin(radians);
            return new float[] { c, -s, 0, x, s, c, 0, y, 0, 0, 1, z, 0, 0, 0, 1 };
        }

        private static Vec3 Apply(float[] m, Vec3 p)
        {
            return new Vec3(m[0] * p.X + m[1] * p.Y + m[2] * p.Z + m[3], m[4] * p.X + m[5] * p.Y + m[6] * p.Z + m[7],
                m[8] * p.X + m[9] * p.Y + m[10] * p.Z + m[11]);
        }

        // A left vertex on the left bone, its mirror image on the right bone, and one on the middle bone.
        private static readonly Vec3[] Vertices = { new Vec3(0.2f, 1.4f, 0), new Vec3(-0.2f, 1.4f, 0), new Vec3(0.05f, 1.2f, 0.1f) };
        private static readonly int[] Joints = { 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0 };
        private static readonly float[] Weights = { 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0 };

        [Fact]
        public void A_pair_skins_a_symmetrical_mesh_symmetrically()
        {
            // The left shoulder's correction is 0.4 mm and a little turn further than the right's.
            var skin = new[] { Turn(0.0004f, 0.0004f, 0, 0), Move(0, 0, 0), Move(2e-5f, 0, 0) };
            var result = SkinMirror.Mirror(new[] { "cf_s_shoulder02_L", "cf_s_shoulder02_R", "cf_j_spine03" }, skin, Vertices, Joints, Weights, 4);

            Assert.Equal(1, result.Pairs);
            Assert.Equal(1, result.Centres);
            Assert.Empty(result.Kept);
            var left = Apply(skin[0], Vertices[0]);
            var right = Apply(skin[1], Vertices[1]);
            Assert.Equal(-left.X, right.X);
            Assert.Equal(left.Y, right.Y);
            Assert.Equal(left.Z, right.Z);
            Assert.Equal(SkinMirror.Mirrored(skin[0]), skin[1]);
            Assert.Equal(0f, skin[2][3]); // the middle bone no longer moves anything sideways
        }

        [Fact]
        public void A_bone_named_with_its_side_inside_finds_its_partner()
        {
            var skin = new[] { Move(0.0002f, 0, 0), Move(0, 0, 0) };
            var result = SkinMirror.Mirror(new[] { "k_f_handL_00", "k_f_handR_00" }, skin, Vertices, new[] { 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0 }, Weights, 4);
            Assert.Equal(1, result.Pairs);
            Assert.Equal(0.0001f, skin[0][3], 6);
            Assert.Equal(-0.0001f, skin[1][3], 6);
        }

        [Fact]
        public void A_pair_that_would_move_too_far_stays()
        {
            // A physics bone that settled 3 mm off its partner is left as the game posed it.
            var skin = new[] { Move(0.003f, 0, 0), Move(0, 0, 0), Move(0, 0, 0) };
            var before = (float[])skin[0].Clone();
            var result = SkinMirror.Mirror(new[] { "cf_j_bust01_L", "cf_j_bust01_R", "cf_j_spine03" }, skin, Vertices, Joints, Weights, 4);
            Assert.Equal(0, result.Pairs);
            Assert.Equal(new[] { "cf_j_bust01_L", "cf_j_bust01_R" }, result.Kept);
            Assert.Equal(before, skin[0]);
        }

        [Fact]
        public void A_bone_off_the_middle_with_no_partner_stays()
        {
            // A one-sided bone: its own mirror image is far from it where it carries vertices.
            var skin = new[] { Turn(0.3f, 0.1f, 0, 0) };
            var before = (float[])skin[0].Clone();
            var result = SkinMirror.Mirror(new[] { "cf_J_hairSide" }, skin, new[] { new Vec3(0.1f, 1.5f, 0) }, null, null, 1);
            Assert.Equal(new[] { "cf_J_hairSide" }, result.Kept);
            Assert.Equal(before, skin[0]);
        }

        [Fact]
        public void Mirroring_twice_gives_the_matrix_back()
        {
            var m = Turn(0.5f, 0.1f, 0.2f, 0.3f);
            Assert.Equal(m, SkinMirror.Mirrored(SkinMirror.Mirrored(m)));
        }
    }
}
