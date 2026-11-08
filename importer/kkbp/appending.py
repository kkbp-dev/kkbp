"""Appending from KKBP's own .blend files: the template library and the Hooks' asset files.

Datablocks are appended, never linked, so a .blend works without KKBP. Node groups and images the
user's file already has from one of these files are shared: the appended copy is remapped onto the
existing one when both carry the same version, so each is in the file once, whatever imports it.
"""

from __future__ import annotations

from pathlib import Path

import bpy

SHARED = "kkbp_library"  # on every node group and image appended from a KKBP file
SHARED_KINDS = ("node_groups", "images")


class AppendError(Exception):
    pass


def append(path, kind: str, name: str, version_prop: str) -> list:
    """Appends datablock `name` of `kind` (`materials`, `collections`, …) from the file at `path`
    and returns the datablocks of that kind the file gained, with what they use. Node groups and
    images that are already in the file (same name, same `version_prop`) are shared."""
    path = Path(path)
    if not path.is_file():
        raise AppendError(f"a KKBP asset file is missing: {path}")
    kinds = sorted({kind, *SHARED_KINDS})
    before = {k: set(getattr(bpy.data, k)) for k in kinds}
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        if name not in getattr(source, kind):
            raise AppendError(f"{path.name} has no {kind[:-1].replace('_', ' ')} {name}")
        setattr(target, kind, [name])
    added = {k: [d for d in getattr(bpy.data, k) if d not in before[k]] for k in kinds}
    for k in SHARED_KINDS:
        for datablock in added[k]:
            keep = _shared(k, datablock, before[k], version_prop)
            if keep is not None:
                datablock.user_remap(keep)
                getattr(bpy.data, k).remove(datablock)
            else:
                datablock[SHARED] = True
                if k == "node_groups":
                    datablock.use_fake_user = False  # the source files keep some alive this way; the user's doesn't need to
    return [d for d in added[kind] if alive(d)]


def existing(kind: str, name: str):
    """The file's own shared copy of node group or image `name` (appended from a KKBP file), or None."""
    for datablock in getattr(bpy.data, kind):
        if datablock.library is None and base_name(datablock.name) == name and datablock.get(SHARED):
            return datablock
    return None


def _shared(kind, datablock, before, version_prop):
    """The datablock of the same name the file already had from a KKBP file, or None."""
    base = base_name(datablock.name)
    for other in before:
        if other.library is None and other.name == base and other.get(SHARED) and \
                (kind == "images" or other.get(version_prop) == datablock.get(version_prop)):
            return other
    return None


def alive(datablock) -> bool:
    try:
        datablock.name
        return True
    except ReferenceError:
        return False


def base_name(name: str) -> str:
    """A name without Blender's .001 suffix."""
    head, dot, tail = name.rpartition(".")
    return head if dot and len(tail) == 3 and tail.isdigit() else name
