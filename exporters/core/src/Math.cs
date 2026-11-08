using System;

namespace KKBP.Exporter.Core
{
    public struct Vec2
    {
        public float X, Y;

        public Vec2(float x, float y)
        {
            X = x;
            Y = y;
        }
    }

    public struct Vec3
    {
        public float X, Y, Z;

        public Vec3(float x, float y, float z)
        {
            X = x;
            Y = y;
            Z = z;
        }

        public static readonly Vec3 Zero = new Vec3(0, 0, 0);
        public static readonly Vec3 One = new Vec3(1, 1, 1);

        public float Length
        {
            get { return (float)Math.Sqrt(X * X + Y * Y + Z * Z); }
        }

        public static Vec3 operator +(Vec3 a, Vec3 b) { return new Vec3(a.X + b.X, a.Y + b.Y, a.Z + b.Z); }
        public static Vec3 operator -(Vec3 a, Vec3 b) { return new Vec3(a.X - b.X, a.Y - b.Y, a.Z - b.Z); }
        public static Vec3 operator *(Vec3 a, float s) { return new Vec3(a.X * s, a.Y * s, a.Z * s); }

        public override string ToString()
        {
            return "(" + X + ", " + Y + ", " + Z + ")";
        }
    }

    public struct Vec4
    {
        public float X, Y, Z, W;

        public Vec4(float x, float y, float z, float w)
        {
            X = x;
            Y = y;
            Z = z;
            W = w;
        }
    }

    /// <summary>A rotation quaternion.</summary>
    public struct Quat
    {
        public float X, Y, Z, W;

        public Quat(float x, float y, float z, float w)
        {
            X = x;
            Y = y;
            Z = z;
            W = w;
        }

        public static readonly Quat Identity = new Quat(0, 0, 0, 1);
    }

    /// <summary>A colour exactly as set on the game material, sRGB-encoded.</summary>
    public struct Color
    {
        public float R, G, B, A;

        public Color(float r, float g, float b, float a)
        {
            R = r;
            G = g;
            B = b;
            A = a;
        }
    }

    /// <summary>A column-major 4x4 affine matrix, as glTF stores it.</summary>
    internal struct Matrix4
    {
        // m[column * 4 + row]
        private readonly float[] m;

        private Matrix4(float[] values)
        {
            m = values;
        }

        public float this[int row, int column]
        {
            get { return m[column * 4 + row]; }
        }

        public static Matrix4 FromTrs(Vec3 t, Quat r, Vec3 s)
        {
            float x = r.X, y = r.Y, z = r.Z, w = r.W;
            float xx = x * x, yy = y * y, zz = z * z;
            float xy = x * y, xz = x * z, yz = y * z, wx = w * x, wy = w * y, wz = w * z;
            return new Matrix4(new[]
            {
                (1 - 2 * (yy + zz)) * s.X, 2 * (xy + wz) * s.X, 2 * (xz - wy) * s.X, 0,
                2 * (xy - wz) * s.Y, (1 - 2 * (xx + zz)) * s.Y, 2 * (yz + wx) * s.Y, 0,
                2 * (xz + wy) * s.Z, 2 * (yz - wx) * s.Z, (1 - 2 * (xx + yy)) * s.Z, 0,
                t.X, t.Y, t.Z, 1,
            });
        }

        public static Matrix4 operator *(Matrix4 a, Matrix4 b)
        {
            var r = new float[16];
            for (int c = 0; c < 4; c++)
            {
                for (int row = 0; row < 4; row++)
                {
                    float sum = 0;
                    for (int k = 0; k < 4; k++)
                    {
                        sum += a.m[k * 4 + row] * b.m[c * 4 + k];
                    }
                    r[c * 4 + row] = sum;
                }
            }
            return new Matrix4(r);
        }

        /// <summary>Inverts an affine matrix (last row 0, 0, 0, 1).</summary>
        public Matrix4 InverseAffine()
        {
            // Invert the 3x3 part with doubles, then the translation.
            double a = m[0], b = m[4], c = m[8];
            double d = m[1], e = m[5], f = m[9];
            double g = m[2], h = m[6], i = m[10];
            double det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
            if (Math.Abs(det) < 1e-12)
            {
                throw new ExportException("A bone's rest transform has zero scale and cannot be inverted.");
            }
            double inv = 1.0 / det;
            double ia = (e * i - f * h) * inv, ib = (c * h - b * i) * inv, ic = (b * f - c * e) * inv;
            double id = (f * g - d * i) * inv, ie = (a * i - c * g) * inv, iF = (c * d - a * f) * inv;
            double ig = (d * h - e * g) * inv, ih = (b * g - a * h) * inv, ii = (a * e - b * d) * inv;
            double tx = m[12], ty = m[13], tz = m[14];
            return new Matrix4(new[]
            {
                (float)ia, (float)id, (float)ig, 0,
                (float)ib, (float)ie, (float)ih, 0,
                (float)ic, (float)iF, (float)ii, 0,
                (float)-(ia * tx + ib * ty + ic * tz), (float)-(id * tx + ie * ty + iF * tz), (float)-(ig * tx + ih * ty + ii * tz), 1,
            });
        }

        public float[] ToArray()
        {
            return (float[])m.Clone();
        }
    }
}
