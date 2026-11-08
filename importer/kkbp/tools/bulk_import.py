"""Bulk import: imports every Export Bundle in a folder, each in its own Blender started in the
background, and saves `<bundle folder>.blend` beside it, or `Error - <bundle folder>.blend` when the
import fails (legacy bulklaunch and auto_import, D36)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("bulk_import_script.py")


def bundle_folders(parent) -> list[Path]:
    """The folders in `parent` that hold an Export Bundle (a finished one has its Manifest)."""
    return sorted(p for p in Path(parent).iterdir() if p.is_dir() and (p / "manifest.json").is_file())


def run(parent, blender: str, module: str, log=print) -> list[tuple[Path, Path]]:
    """Imports each bundle in `parent`; returns (bundle, saved .blend) pairs. `module` is this add-on's
    module name, which the background Blender enables from the same Blender profile."""
    done = []
    for folder in bundle_folders(parent):
        command = [blender, "--background", "--factory-startup", "--python-exit-code", "1", "--python", str(SCRIPT),
                   "--", "--module", module, "--bundle", str(folder)]
        result = subprocess.run(command, capture_output=True, text=True)
        saved = next((folder.parent / name for name in (f"{folder.name}.blend", f"Error - {folder.name}.blend")
                      if (folder.parent / name).is_file()), None)
        log(f"{folder.name}: {'saved ' + saved.name if saved else 'failed: ' + _last_line(result)}")
        done.append((folder, saved))
    return done


def _last_line(result):
    lines = [line for line in (result.stderr or result.stdout or "").splitlines() if line.strip()]
    return lines[-1] if lines else f"exit code {result.returncode}"
