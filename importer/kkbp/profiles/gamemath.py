"""The little vector maths the joint corrections need, in the games' own terms: Unity's left-handed
space, quaternions as (x, y, z, w), angles in degrees, and the games' `ConvertRotation` Euler orders.
Pure Python, so the host tests can run the corrections without Blender.
"""

from __future__ import annotations

import math

Vec = tuple[float, float, float]
Quat = tuple[float, float, float, float]

IDENTITY: Quat = (0.0, 0.0, 0.0, 1.0)
_AXES = {"x": (1.0, 0.0, 0.0), "y": (0.0, 1.0, 0.0), "z": (0.0, 0.0, 1.0)}
# The games' RotationOrder names give the order of the product: "zyx" is Rz * Ry * Rx.
ORDERS = ("xyz", "xzy", "yxz", "yzx", "zxy", "zyx")
# Unity's own Euler angles (Quaternion.Euler, eulerAngles) are Ry * Rx * Rz.
UNITY = "yxz"


def add(a: Vec, b: Vec) -> Vec:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a: Vec, b: Vec) -> Vec:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a: Vec, b: Vec) -> Vec:
    return (a[0] * b[0], a[1] * b[1], a[2] * b[2])


def div(a: Vec, b: Vec) -> Vec:
    return (a[0] / b[0], a[1] / b[1], a[2] / b[2])


def qmul(a: Quat, b: Quat) -> Quat:
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qinv(q: Quat) -> Quat:
    return (-q[0], -q[1], -q[2], q[3])


def qnorm(q: Quat) -> Quat:
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return (q[0] / n, q[1] / n, q[2] / n, q[3] / n)


def rotate(q: Quat, v: Vec) -> Vec:
    x, y, z, w = q
    # v + 2w(q x v) + 2 q x (q x v)
    cx, cy, cz = y * v[2] - z * v[1], z * v[0] - x * v[2], x * v[1] - y * v[0]
    dx, dy, dz = y * cz - z * cy, z * cx - x * cz, x * cy - y * cx
    return (v[0] + 2 * (w * cx + dx), v[1] + 2 * (w * cy + dy), v[2] + 2 * (w * cz + dz))


def axis_angle(axis: str, degrees: float) -> Quat:
    h = math.radians(degrees) / 2
    s = math.sin(h)
    a = _AXES[axis]
    return (a[0] * s, a[1] * s, a[2] * s, math.cos(h))


def from_euler(order: str, e: Vec) -> Quat:
    """`ConvertRotation.ConvertDegreeToQuaternion`: the product of the three axis turns in `order`."""
    q = IDENTITY
    for axis in order:
        q = qmul(q, axis_angle(axis, e["xyz".index(axis)]))
    return q


def matrix(q: Quat) -> tuple[Vec, Vec, Vec]:
    """Rows of the rotation matrix, as Unity's Matrix4x4.TRS gives them (m[row][column])."""
    x, y, z, w = qnorm(q)
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def to_euler(order: str, q: Quat) -> Vec:
    """`ConvertRotation.ConvertDegreeFromQuaternion`, with its own branch at the pole."""
    m = matrix(q)

    def clamp(v):
        return max(-1.0, min(1.0, v))

    if order == "yzx":
        n = m[1][0]
        z = math.asin(clamp(n))
        if n > 0.9999:
            x, y = 0.0, math.atan2(m[0][2], m[2][2])
        else:
            x, y = math.atan2(-m[1][2], m[1][1]), math.atan2(-m[2][0], m[0][0])
    elif order == "zxy":
        n = m[2][1]
        x = math.asin(clamp(n))
        if n > 0.9999:
            y, z = 0.0, math.atan2(m[1][0], m[0][0])
        else:
            y, z = math.atan2(-m[2][0], m[2][2]), math.atan2(-m[0][1], m[1][1])
    elif order == "zyx":
        n = -m[2][0]
        y = math.asin(clamp(n))
        if n > 0.9999:
            x, z = 0.0, math.atan2(-m[0][1], m[1][1])
        else:
            x, z = math.atan2(m[2][1], m[2][2]), math.atan2(m[1][0], m[0][0])
    elif order == "yxz":
        n = -m[1][2]
        x = math.asin(clamp(n))
        if n > 0.9999:
            z, y = 0.0, math.atan2(-m[2][0], m[0][0])
        else:
            y, z = math.atan2(m[0][2], m[2][2]), math.atan2(m[1][0], m[1][1])
    else:
        raise ValueError(f"Euler order {order!r} isn't one the corrections use")
    return (math.degrees(x), math.degrees(y), math.degrees(z))
