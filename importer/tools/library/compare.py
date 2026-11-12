"""Compares two fingerprints from fingerprint.py and prints every difference, by path.

    python3 importer/tools/library/compare.py BEFORE.json AFTER.json [--limit N]
"""

import json
import sys


def walk(a, b, path, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((f"{path}/{k}", "<missing>", b[k]))
            elif k not in b:
                out.append((f"{path}/{k}", a[k], "<missing>"))
            else:
                walk(a[k], b[k], f"{path}/{k}", out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, f"{path}[{i}]", out)
    elif a != b:
        out.append((path, a, b))


# Agreed differences (docs/design/library-from-code.md, "Equality check"), as path regexes.
AGREED = [
    r"^/images/Template: Black/",  # V9's was broken (0 x 0, no pixels); now a 4 x 4 black image
    r"^/images/[^/]+/filepath$",  # packed images: V9 held placeholder text, now "//<file>"
]


SUBTYPE_SUFFIXES = ("Factor", "Percentage", "Angle", "Distance", "Unsigned", "Time", "Translation",
                    "Direction", "Xyz", "Euler", "Velocity", "Acceleration", "Wavelength")


def subtype_idname(d):
    """Blender now names a socket by type and subtype (`NodeSocketFloatFactor`); older files kept
    the plain type's name (`NodeSocketFloat`) with the same subtype."""
    path, before, after = d
    return (path.endswith(("/bl_socket_idname", "/bl_idname")) and isinstance(before, str) and isinstance(after, str)
            and after.startswith(before) and after[len(before):] in SUBTYPE_SUFFIXES)


def empty_group(d):
    """Empty custom property groups other add-ons (Cycles, MMD tools, ...) left on V9's datablocks."""
    path, before, after = d
    return "/props/" in path and path.count("/props/") == 1 and before == [] and after == "<missing>"


def main():
    import re
    args = sys.argv[1:]
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 200
    a, b = (json.load(open(p)) for p in args[:2])
    out = []
    walk(a, b, "", out)
    agreed = [d for d in out if any(re.search(p, d[0]) for p in AGREED) or subtype_idname(d) or empty_group(d)]
    out = [d for d in out if d not in agreed]
    print(f"{len(agreed)} agreed differences left out")
    for path, x, y in out[:limit]:
        sx, sy = json.dumps(x)[:150], json.dumps(y)[:150]
        print(f"{path}\n    before {sx}\n    after  {sy}")
    print(f"{len(out)} differences")
    sys.exit(1 if out else 0)


main()
