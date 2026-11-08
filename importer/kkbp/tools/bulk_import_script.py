"""Run by bulk_import.py in a background Blender: imports one Export Bundle with KKBP and saves the
scene beside the bundle folder. Not imported by the add-on."""

import argparse
import importlib
import sys
import traceback
from pathlib import Path

import addon_utils
import bpy


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", required=True)
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    folder = Path(args.bundle)
    bpy.ops.wm.read_homefile(use_empty=True)
    addon_utils.enable(args.module, default_set=False)
    kkbp = importlib.import_module(args.module)
    ok = False
    try:
        ok = kkbp.api.import_bundle(str(folder)).ok
    except Exception:
        traceback.print_exc()
    name = f"{folder.name}.blend" if ok else f"Error - {folder.name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(folder.parent / name))


main()
