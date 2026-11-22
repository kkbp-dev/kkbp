"""Draws the SDF face shading's SVS hair contact shadows mask from KK's, through the two faces' meshes.

    importer/.venv/bin/python importer/tools/make_svs_hair_contact_mask.py KK_BUNDLE SVS_BUNDLE [OUTPUT]

KK_BUNDLE and SVS_BUNDLE are Export Bundles of each Game, such as the Golden Samples
`contract/samples/kk` and `contract/samples/svs`; they are only read. OUTPUT defaults to
`importer/library-src/images/SVS hair contact shadows mask.png`, which scripts/build-library.sh packs
into library.blend.

The `.SDF_Cel_Shader` group hands the face back to Eevee's own lighting, and so to the hair's cast
shadows, where its hair contact shadows mask is white: a band under the bangs, with the eyes and
eyebrows left black. KK's mask is drawn in KK's face UV layout, which SVS's face doesn't share. This
one is KK's carried across: each texel of the SVS face takes the KK mask's value at the point of the
KK face in front of or behind it, seen straight on, with the two faces lined up by their eye whites.
The back of SVS's head, which KK's face mesh doesn't have, is white above the eyes and black below
(the hair covers it). The face meshes are the same for every Character of a Game, so the mask is
drawn once and committed.

Runs on Blender's Python (the importer's venv) for Pillow and NumPy; it needs no bpy.
"""

import json
import struct
import sys
import warnings
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
IMAGES = HERE.parent / "library-src" / "images"
KK_MASK = IMAGES / "SDF hair contact shadows mask 2.png"
DEFAULT_OUTPUT = IMAGES / "SVS hair contact shadows mask.png"
SIZE = 2048  # KK's mask's size
GRID = 0.001  # metres per cell of the straight-on lookup
BEHIND = 0.0  # SVS texels behind this depth (the back of the head) aren't looked up on KK's face

COMPONENTS = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}
COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}


def main():
    args = sys.argv[1:]
    if not 2 <= len(args) <= 3:
        sys.exit(__doc__)
    kk, svs = Path(args[0]), Path(args[1])
    output = Path(args[2]) if len(args) == 3 else DEFAULT_OUTPUT
    kk_face, kk_eyes = face(kk, ("KK", "KKS"))
    svs_face, svs_eyes = face(svs, ("SVS",))
    offset = kk_eyes - svs_eyes
    offset[0] = 0.0  # both are centred on x = 0
    kk_mask = np.asarray(Image.open(KK_MASK).convert("L"), dtype=np.float32) / 255.0
    picture = carry(kk_face, svs_face, offset, kk_mask, svs_eyes[1])
    Image.fromarray((picture * 255 + 0.5).astype(np.uint8)).convert("RGB").save(output)
    print(f"Wrote {output}")


def face(bundle: Path, games):
    """The bundle's face as (positions, uvs, triangles), and the middle of its two eye whites."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("game") not in games:
        sys.exit(f"{bundle} is a {manifest.get('game')} bundle, not a {' or '.join(games)} one")
    materials = json.loads((bundle / "materials.json").read_text(encoding="utf-8"))["materials"]
    roles = {m["id"]: m.get("role") for m in materials}
    gltf, binary = read_glb(bundle / "body.glb")
    names = [m.get("name") for m in gltf["materials"]]
    found, eyes = None, []
    for mesh in gltf["meshes"]:
        for primitive in mesh["primitives"]:
            role = roles.get(names[primitive["material"]])
            positions = np.array(accessor(gltf, binary, primitive["attributes"]["POSITION"]), dtype=np.float64)
            if role == "eye_white":
                eyes.append(positions.mean(axis=0))
            elif role == "face" and found is None:
                uvs = np.array(accessor(gltf, binary, primitive["attributes"]["TEXCOORD_0"]), dtype=np.float64)
                triangles = np.array(accessor(gltf, binary, primitive["indices"]), dtype=np.int64).reshape(-1, 3)
                found = (positions, uvs, triangles)
    if found is None or not eyes:
        sys.exit(f"{bundle}: body.glb has no face or no eye whites")
    return found, np.mean(eyes, axis=0)


def rasterize(positions, uvs, triangles, size):
    """Each texel's position on the mesh (glTF's v already runs down), and which texels it covers."""
    where = np.zeros((size, size, 3))
    covered = np.zeros((size, size), bool)
    corners = uvs[triangles] * size
    for t, (a, b, c) in enumerate(corners):
        lo = np.maximum(np.floor(np.minimum(np.minimum(a, b), c)).astype(int), 0)
        hi = np.minimum(np.ceil(np.maximum(np.maximum(a, b), c)).astype(int), size - 1)
        if (hi < lo).any():
            continue
        xs, ys = np.meshgrid(np.arange(lo[0], hi[0] + 1) + 0.5, np.arange(lo[1], hi[1] + 1) + 0.5)
        area = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(area) < 1e-14:
            continue
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / area
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / area
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        rows, cols = ys[inside].astype(int), xs[inside].astype(int)
        weights = np.stack([w0[inside], w1[inside], w2[inside]], -1)
        where[rows, cols] = weights @ positions[triangles[t]]
        covered[rows, cols] = True
    return where, covered


def carry(kk_face, svs_face, offset, kk_mask, svs_eye_height):
    """The SVS face's mask: KK's value at the KK texel nearest the front at the same height and x."""
    kk_where, kk_covered = rasterize(*kk_face, kk_mask.shape[0])
    svs_where, svs_covered = rasterize(*svs_face, SIZE)
    svs_where = svs_where + offset

    # The straight-on lookup: per (x, y) cell, the KK texel furthest forward (glTF faces +Z).
    lo = np.minimum(kk_where[kk_covered].min(axis=0), svs_where[svs_covered].min(axis=0))[:2] - GRID
    hi = np.maximum(kk_where[kk_covered].max(axis=0), svs_where[svs_covered].max(axis=0))[:2] + GRID
    shape = tuple(np.ceil((hi - lo) / GRID).astype(int) + 1)
    value = np.full(shape, np.nan)
    rows, cols = np.nonzero(kk_covered)
    cells = np.floor((kk_where[rows, cols, :2] - lo) / GRID).astype(int)
    order = np.argsort(kk_where[rows, cols, 2])  # nearer texels last: NumPy keeps the last write
    value[cells[order, 0], cells[order, 1]] = kk_mask[rows[order], cols[order]]
    # Cells the KK face doesn't reach take their nearest filled neighbour, a ring at a time.
    for _ in range(64):
        empty = np.isnan(value)
        if not empty.any():
            break
        padded = np.pad(value, 1, constant_values=np.nan)
        near = np.stack([padded[1 + di:1 + di + shape[0], 1 + dj:1 + dj + shape[1]]
                         for di in (-1, 0, 1) for dj in (-1, 0, 1)])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # cells with no filled neighbour yet
            filled = np.nanmean(near, axis=0)
        value = np.where(empty & ~np.isnan(filled), filled, value)

    picture = np.zeros((SIZE, SIZE), np.float32)
    rows, cols = np.nonzero(svs_covered)
    p = svs_where[rows, cols]
    cells = np.clip(np.floor((p[:, :2] - lo) / GRID).astype(int), 0, np.array(shape) - 1)
    looked_up = value[cells[:, 0], cells[:, 1]]
    behind = (p[:, 2] < BEHIND) | np.isnan(looked_up)
    above = p[:, 1] > svs_eye_height + offset[1]
    picture[rows, cols] = np.where(behind, above.astype(np.float32), np.nan_to_num(looked_up))
    return picture


def read_glb(path: Path):
    data = path.read_bytes()
    magic, _, _ = struct.unpack_from("<4sII", data, 0)
    if magic != b"glTF":
        sys.exit(f"{path} isn't a binary glTF file")
    offset, gltf, binary = 12, None, b""
    while offset < len(data):
        length, kind = struct.unpack_from("<I4s", data, offset)
        chunk = data[offset + 8:offset + 8 + length]
        if kind == b"JSON":
            gltf = json.loads(chunk)
        elif kind == b"BIN\x00":
            binary = chunk
        offset += 8 + length
    return gltf, binary


def accessor(gltf, binary, index) -> list:
    a = gltf["accessors"][index]
    view = gltf["bufferViews"][a["bufferView"]]
    fmt, count = COMPONENTS[a["componentType"]], COUNTS[a["type"]]
    size = struct.calcsize("<" + fmt * count)
    stride = view.get("byteStride") or size
    start = view.get("byteOffset", 0) + a.get("byteOffset", 0)
    return [struct.unpack_from("<" + fmt * count, binary, start + i * stride) for i in range(a["count"])]


if __name__ == "__main__":
    main()
