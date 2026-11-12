"""Draws the face cards' SVS eye white mask from an SVS Export Bundle's eye white UVs (ADR 0037).

    importer/.venv/bin/python importer/tools/make_svs_eye_white_mask.py BUNDLE [OUTPUT]

BUNDLE is an SVS Export Bundle, such as the Golden Sample `contract/samples/svs`; it is only read.
OUTPUT defaults to `importer/library-src/images/SVS Eye_White_Alpha.png`, which
scripts/build-library.sh packs into face_cards.blend.

The face cards' Eyewhite card shows the Character's whole eye white texture and cuts out the eye
white with a mask. The legacy mask, `Eye_White_Alpha`, is the outline of KK's eye white UV island;
SVS's eye white texture is laid out by SVS's eye mesh instead, so it needs its own mask. This one is
white inside the UV island of the bundle's first `eye_white` material (the left eye, the one the
Hook puts on the card) and black outside, at the legacy mask's 512 x 512, drawn 4x larger and scaled
down for smooth edges. The game's eye mesh is the same for every SVS Character, so the mask is drawn
once and committed.

Runs on Blender's Python (the importer's venv) for Pillow; it needs no bpy.
"""

import json
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = 512  # the legacy Eye_White_Alpha's size
SUPERSAMPLE = 4
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "library-src" / "images" / "SVS Eye_White_Alpha.png"

# glTF component types and element counts
COMPONENTS = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}
COUNTS = {"SCALAR": 1, "VEC2": 2}


def main():
    args = sys.argv[1:]
    if not 1 <= len(args) <= 2:
        sys.exit(__doc__)
    bundle = Path(args[0])
    output = Path(args[1]) if len(args) == 2 else DEFAULT_OUTPUT
    triangles = eye_white_uv_triangles(bundle)
    mask(triangles).save(output)
    print(f"Wrote {output}: {len(triangles)} triangles")


def eye_white_uv_triangles(bundle: Path) -> list:
    """The UV triangles, as ((u, v), …) with v down as in glTF, of the bundle's first eye white."""
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("game") != "SVS":
        sys.exit(f"{bundle} is a {manifest.get('game')} bundle, not an SVS one")
    materials = json.loads((bundle / "materials.json").read_text(encoding="utf-8"))["materials"]
    eye_white = next((m["id"] for m in materials if m.get("role") == "eye_white"), None)
    if eye_white is None:
        sys.exit(f"{bundle} has no eye_white material")
    gltf, binary = read_glb(bundle / "body.glb")
    names = [m.get("name") for m in gltf["materials"]]
    triangles = []
    for mesh in gltf["meshes"]:
        for primitive in mesh["primitives"]:
            if names[primitive["material"]] != eye_white:
                continue
            if primitive.get("mode", 4) != 4:
                sys.exit(f"{mesh.get('name')}: the eye white isn't drawn with triangles")
            uvs = accessor(gltf, binary, primitive["attributes"]["TEXCOORD_0"])
            indices = [i for (i,) in accessor(gltf, binary, primitive["indices"])]
            triangles += [tuple(uvs[i] for i in indices[t:t + 3]) for t in range(0, len(indices), 3)]
    if not triangles:
        sys.exit(f"body.glb has no faces with the material {eye_white}")
    return triangles


def mask(triangles) -> Image.Image:
    """White inside the triangles, black outside, as an RGB image like the legacy mask."""
    big = SIZE * SUPERSAMPLE
    image = Image.new("L", (big, big), 0)
    draw = ImageDraw.Draw(image)
    for triangle in triangles:
        draw.polygon([(u * big, v * big) for u, v in triangle], fill=255)  # glTF's v already runs down
    return image.resize((SIZE, SIZE), Image.Resampling.BOX).convert("RGB")


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
