"""Dumps a Unity game's compiled shaders as readable disassembly, for writing the edit templates' node
groups (docs/design/library-from-code.md, "Getting the shaders").

    importer/.venv/bin/python -I importer/tools/game_shaders/dump.py FILTER OUT_DIR ASSET_FILE...
    importer/.venv/bin/python -I importer/tools/game_shaders/dump.py --find FOLDER...

UnityPy comes from the dev venv (importer/requirements-dev.txt, installed by
scripts/setup-importer-dev.sh); it never goes into Blender.
FILTER is a comma-separated list of name parts (`create,main_skin`) or `*`. Writes one text file per
distinct D3D11 sub-program: `<shader>.<index>.<vs|ps>.txt`, with the shader's keywords and a header
naming every constant (cbuffer, byte offset, components) and texture slot, then the disassembly with
`cb0[3].x` replaced by the property it is (`_Color.r`) and `t2` by its texture.

The output is the games' code: it goes under `importer/tests/.work/` and is never committed.
Reads Unity 5.6 (Koikatsu), 2019 (Koikatsu Sunshine) and 2021 (Summer Vacation Scramble)
sub-programs. The first two keep a sub-program's constants after its bytecode (`parse_subprogram`);
2021 keeps them in the pass and a parameter blob of their own (`dump_passes`). A 2021 file is named
`<shader>.<pass>.<index>.<vs|ps>.txt`; the pass to read is `Forward` (URP's UniversalForward).
"""

from __future__ import annotations

import re
import struct
import sys
from pathlib import Path

D3D11 = 4  # Unity's ShaderCompilerPlatform for Direct3D 11


class Reader:
    def __init__(self, data, pos=0):
        self.data, self.pos = data, pos

    def i32(self):
        v = struct.unpack_from("<i", self.data, self.pos)[0]
        self.pos += 4
        return v

    def i8(self):
        v = struct.unpack_from("<b", self.data, self.pos)[0]
        self.pos += 1
        return v

    def align(self):
        self.pos = (self.pos + 3) & ~3

    def string(self):
        n = self.i32()
        s = self.data[self.pos:self.pos + n].decode("utf-8", "replace")
        self.pos += n
        self.align()
        return s

    def strings(self):
        return [self.string() for _ in range(self.i32())]

    def blob(self):
        n = self.i32()
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        self.align()
        return b


def tokens(data, pos):
    """The bytes from `pos` as ints and length-prefixed names (each padded to 4 bytes)."""
    out = []
    while pos + 4 <= len(data):
        n = struct.unpack_from("<i", data, pos)[0]
        name = data[pos + 4:pos + 4 + n] if 1 <= n <= 64 else b""
        if name and re.fullmatch(rb"[$A-Za-z_][A-Za-z0-9_\[\]]*", name):
            out.append(name.decode())
            pos += 4 + ((n + 3) & ~3)
        else:
            out.append(n)
            pos += 4
    return out


def parse_subprogram(sub, unity):
    """One sub-program: its keywords, its D3D11 bytecode and its parameter bindings.

    After the bytecode, both Unity 5.6 and 2019 write a few counts, then each constant buffer as
    (name, size, count, count x (name, type, rows, columns, is matrix, array size, byte offset)),
    2017.3 and later followed by a struct count, then the bindings as (count, count x (name, kind,
    slot, extra)): kind 0 is a texture, its extra `sampler << 8 | dimension`; kind 1 a buffer."""
    r = Reader(sub)
    r.i32()  # version
    kind = r.i32()  # program type: 15 vertex, 17 fragment for D3D11 on these versions
    r.i32(), r.i32(), r.i32(), r.i32()  # stats: ALU, TEX, flow, temp registers
    keywords = r.strings()
    if unity >= (2019, 1):
        keywords += r.strings()  # local keywords
    code = r.blob()
    start = code.find(b"DXBC")
    dxbc = code[start:start + struct.unpack_from("<I", code, start + 24)[0]] if start >= 0 else b""
    cbuffers, textures, bindings = _parameters(_grouped(sub, r.pos))
    return {"kind": kind, "keywords": keywords, "dxbc": dxbc, "vectors": [], "matrices": [],
            "textures": textures, "cbuffers": cbuffers, "bindings": bindings}


# Sub-programs of this version and later (Unity 2021) have one keyword list, and their constants
# live in the pass (`m_CommonParameters`) and a parameter blob, not after the bytecode.
SPLIT_PARAMETERS = 202012090


def _bytecode(sub):
    """A sub-program's version, program type, keywords and DXBC: (version, type, 4 stats, keywords,
    code), as every version writes them; before 2021, a second keyword list follows."""
    r = Reader(sub)
    version, kind = r.i32(), r.i32()
    r.i32(), r.i32(), r.i32(), r.i32()
    keywords = r.strings()
    code = r.blob()
    start = code.find(b"DXBC")
    dxbc = code[start:start + struct.unpack_from("<I", code, start + 24)[0]] if start >= 0 else b""
    return version, kind, keywords, dxbc


def _parameters(items):
    """Constant buffers, textures and buffer bindings from a token list (`tokens`, grouped by name):
    a constant buffer is (name, size, count, count x (name, type, rows, columns, is matrix, array
    size, byte offset)), a binding (name, kind, slot, extra) with kind 0 a texture, 1 a buffer."""
    cbuffers, textures, bindings = [], [], {}
    i = 0
    while i < len(items):
        name, ints = items[i]
        if len(ints) >= 2 and ints[0] >= 16 and ints[0] % 16 == 0 and i + ints[1] < len(items):
            vectors, matrices = [], []
            for vname, v in items[i + 1:i + 1 + ints[1]]:
                _type, rows, cols, is_matrix, array, offset = v[:6]
                entry = {"name": vname, "offset": offset, "array": array, "dim": cols, "rows": rows}
                (matrices if is_matrix else vectors).append(entry)
            cbuffers.append({"name": name, "size": ints[0], "vectors": vectors, "matrices": matrices})
            i += 1 + ints[1]
            continue
        if len(ints) >= 3 and ints[0] in (0, 1):
            if ints[0] == 0:
                textures.append({"name": name, "index": ints[1], "sampler": ints[2] >> 8, "dim": ints[2] & 0xFF})
            else:
                bindings[name] = ints[1]
        i += 1
    return cbuffers, textures, bindings


def _grouped(data, pos):
    """`tokens` from `pos`, each name with the ints after it, up to the next name."""
    items = []
    for tok in tokens(data, pos):
        if isinstance(tok, str):
            items.append((tok, []))
        elif items:
            items[-1][1].append(tok)
    return items


def _common(common, names):
    """A 2021 program's shared constants (`m_CommonParameters`), with names from the pass's
    `m_NameIndices`. A vector's `m_Index` is its byte offset."""
    cbuffers = []
    for cb in common.m_ConstantBuffers:
        vectors = [{"name": names[v.m_NameIndex], "offset": v.m_Index, "array": v.m_ArraySize, "dim": v.m_Dim, "rows": 1}
                   for v in cb.m_VectorParams]
        matrices = [{"name": names[m.m_NameIndex], "offset": m.m_Index, "array": m.m_ArraySize, "dim": 4, "rows": m.m_RowCount}
                    for m in cb.m_MatrixParams]
        cbuffers.append({"name": names[cb.m_NameIndex], "size": cb.m_Size, "vectors": vectors, "matrices": matrices})
    textures = [{"name": names[t.m_NameIndex], "index": t.m_Index, "sampler": t.m_SamplerIndex, "dim": t.m_Dim}
                for t in common.m_TextureParams]
    bindings = {names[b.m_NameIndex]: b.m_Index for b in common.m_ConstantBufferBindings}
    return cbuffers, textures, bindings


def _merged(cbuffers):
    """Constant buffers of one name, from the shared and per-variant parameters, as one."""
    out = {}
    for cb in cbuffers:
        m = out.setdefault(cb["name"], {"name": cb["name"], "size": cb["size"], "vectors": [], "matrices": []})
        m["vectors"] += cb["vectors"]
        m["matrices"] += cb["matrices"]
    return list(out.values())


def dump_passes(shader, blob, out, dis):
    """Unity 2021: every pass's vertex and fragment variants. A pass's program lists, per platform,
    its variants (`m_PlayerSubPrograms`, each a blob index) and the parameter blob of each
    (`m_ParameterBlobIndices`, the same table); the blob holds what differs per variant in the
    older token layout, from byte 24, and `m_CommonParameters` the rest. Returns the count written."""
    name = shader.m_ParsedForm.m_Name
    safe = re.sub(r"[^0-9A-Za-z]+", "_", name)
    count = struct.unpack_from("<i", blob, 0)[0]
    entries = [struct.unpack_from("<iii", blob, 4 + 12 * i) for i in range(count)]
    written = 0
    for sub_shader in shader.m_ParsedForm.m_SubShaders:
        for p in sub_shader.m_Passes:
            names = {i: n for n, i in p.m_NameIndices}
            for stage, prog in (("vs", p.progVertex), ("ps", p.progFragment)):
                common = _common(prog.m_CommonParameters, names)
                for platform, variants in enumerate(prog.m_PlayerSubPrograms):
                    for k, sp in enumerate(variants):
                        off, length, _segment = entries[sp.m_BlobIndex]
                        _version, kind, keywords, dxbc = _bytecode(blob[off:off + length])
                        if not dxbc:
                            continue
                        poff, plen, _ = entries[prog.m_ParameterBlobIndices[platform][k]]
                        own = _parameters(_grouped(blob[poff:poff + plen], 24))
                        prog_info = {"kind": kind, "keywords": keywords, "cbuffers": _merged(common[0] + own[0]),
                                     "textures": common[1] + own[1], "bindings": {**common[2], **own[2]}}
                        text = dis(dxbc)
                        path = out / f"{safe}.{p.m_State.m_Name}.{sp.m_BlobIndex}.{stage}.txt"
                        path.write_text(header(name, sp.m_BlobIndex, prog_info) + "\n" + annotate(text, prog_info) + "\n")
                        written += 1
    return written


def unity_version(env_file):
    text = env_file.unity_version if hasattr(env_file, "unity_version") else "5.6.0"
    major, minor = (int(x) for x in re.match(r"(\d+)\.(\d+)", text).groups())
    return (major, minor)


def blobs(shader):
    """The decompressed D3D11 blob of a Shader object, for either layout: Unity 5.6 keeps one offset
    per platform, 2019 a list of segments per platform."""
    import lz4.block
    platforms = list(shader.platforms)
    p = platforms.index(D3D11) if D3D11 in platforms else 0
    offsets, comp, decomp = shader.offsets[p], shader.compressedLengths[p], shader.decompressedLengths[p]
    if isinstance(offsets, int):
        offsets, comp, decomp = [offsets], [comp], [decomp]
    raw = bytes(shader.compressedBlob)
    return b"".join(lz4.block.decompress(raw[o:o + c], uncompressed_size=u) for o, c, u in zip(offsets, comp, decomp))


def subprograms(blob, unity):
    """The blob's sub-programs. Its index is (offset, length) per entry, and from Unity 2019.3 on
    (offset, length, segment)."""
    count = struct.unpack_from("<i", blob, 0)[0]
    stride = 12 if unity >= (2019, 3) else 8
    for i in range(count):
        off, length = struct.unpack_from("<ii", blob, 4 + stride * i)
        yield i, blob[off:off + length]


# --- naming the disassembly ----------------------------------------------------------------

CHANNELS = "xyzw"


def annotate(text, prog):
    """Replaces `cbN[r].xy` with the properties at that register and component, and `tN` with
    its texture. A float packed into a vector's lane gets that lane's name."""
    lanes = {}  # (cbuffer slot, register, component) -> name
    for order, cb in enumerate(prog["cbuffers"]):
        slot = slot_of(prog, cb, order)
        if slot is None:
            continue
        for v in cb["vectors"]:
            reg, comp = divmod(v["offset"], 16)
            count = max(v["array"], 1)
            for e in range(count):  # an array's elements each start a register
                for k in range(v["dim"]):
                    c = comp // 4 + k
                    element = f"[{e}]" if count > 1 else ""
                    lanes[(slot, reg + e + c // 4, c % 4)] = v["name"] + element + (f".{'rgba'[k]}" if v["dim"] > 1 else "")
        for m in cb["matrices"]:
            reg = m["offset"] // 16
            for row in range(4 * max(m["array"], 1)):
                for c in range(4):
                    lanes[(slot, reg + row, c)] = f"{m['name']}[{row}].{CHANNELS[c]}"

    def operand(match):
        slot, reg, swizzle = int(match.group(1)), int(match.group(2)), match.group(3) or ".xyzw"
        names = [lanes.get((slot, reg, CHANNELS.index(ch))) for ch in swizzle[1:]]
        if all(names):
            uniq = list(dict.fromkeys(names))
            if len(uniq) == 1:
                return uniq[0]
            bases = {n.rsplit(".", 1)[0] for n in names}
            if len(bases) == 1 and all("." in n for n in names):  # lanes of one vector: _Color.rgbr
                return bases.pop() + "." + "".join(n.rsplit(".", 1)[1] for n in names)
            return "{" + ", ".join(names) + "}"
        return match.group(0)
    text = re.sub(r"cb(\d+)\[(\d+)\](\.[xyzw]+)?", operand, text)
    textures = {t["index"]: t["name"] for t in prog["textures"]}
    return re.sub(r"\bt(\d+)\.xyzw", lambda m: textures.get(int(m.group(1)), m.group(0)), text)


def slot_of(prog, cb, order):
    """A constant buffer's slot: its binding, or its place in the list when it has none (2019 writes
    no binding for a lone $Globals)."""
    return prog["bindings"].get(cb["name"], order)


def header(name, i, prog):
    lines = [f"// {name}  sub-program {i}  type {prog['kind']}  keywords {prog['keywords']}"]
    for order, cb in enumerate(prog["cbuffers"]):
        lines.append(f"// cbuffer {cb['name']} (slot {slot_of(prog, cb, order)}, {cb['size']} bytes)")
        for v in sorted(cb["vectors"], key=lambda v: v["offset"]):
            lines.append(f"//   {v['offset']:4d}  {v['name']}  dim {v['dim']}" + (f" x{v['array']}" if v["array"] > 1 else ""))
        for m in cb["matrices"]:
            lines.append(f"//   {m['offset']:4d}  {m['name']}  matrix")
    for t in prog["textures"]:
        lines.append(f"// texture t{t['index']} sampler s{t['sampler']}  {t['name']}")
    return "\n".join(lines)


def find(folders):
    """Prints which asset file holds each shader: `dump.py --find FOLDER...`."""
    import UnityPy
    for folder in folders:
        for path in sorted(Path(folder).rglob("*")):
            if not path.is_file() or path.suffix not in (".unity3d", ".assets", ""):
                continue
            try:
                env = UnityPy.load(str(path))
                names = [o.read().m_ParsedForm.m_Name for o in env.objects if o.type.name == "Shader"]
            except Exception as e:  # noqa: BLE001 - not every file there is an asset file
                names = [f"(unreadable: {type(e).__name__})"] if path.suffix == ".unity3d" else []
            for name in names:
                print(f"{name}\t{path}", flush=True)


def main():
    if sys.argv[1] == "--find":
        return find(sys.argv[2:])
    want, out = sys.argv[1], Path(sys.argv[2])
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import UnityPy
    import dxdis
    out.mkdir(parents=True, exist_ok=True)
    for path in sys.argv[3:]:
        env = UnityPy.load(path)
        for o in env.objects:
            if o.type.name != "Shader":
                continue
            shader = o.read()
            name = shader.m_ParsedForm.m_Name
            if want != "*" and not any(k in name.lower() for k in want.split(",")):
                continue
            unity = unity_version(o.assets_file)
            blob = blobs(shader)
            first = next((sub for _, sub in subprograms(blob, unity) if len(sub) >= 4), b"")
            if first and struct.unpack_from("<i", first, 0)[0] >= SPLIT_PARAMETERS:
                print(f"{name}: unity {unity[0]}.{unity[1]}, {dump_passes(shader, blob, out, dxdis.dis)} programs")
                continue
            seen = set()
            for i, sub in subprograms(blobs(shader), unity):
                prog = parse_subprogram(sub, unity)
                if not prog["dxbc"]:
                    continue
                text = dxdis.dis(prog["dxbc"])
                stage = "ps" if "dcl_input_ps" in text or "dcl_output o0" in text else "vs"
                key = (tuple(prog["keywords"]), text)
                if key in seen:
                    continue
                seen.add(key)
                safe = re.sub(r"[^0-9A-Za-z]+", "_", name)
                (out / f"{safe}.{i}.{stage}.txt").write_text(header(name, i, prog) + "\n" + annotate(text, prog) + "\n")
            print(f"{name}: unity {unity[0]}.{unity[1]}, {len(seen)} programs")


if __name__ == "__main__":
    main()
