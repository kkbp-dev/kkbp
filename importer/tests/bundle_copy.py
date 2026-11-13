"""Copies of a bundle for an import to write its kkbp_cache/ into. No bpy: the harness uses it on the host.

Every file the importer writes goes into the bundle's kkbp_cache/ (Bundle.cache_dir, the log), which
the copy leaves out, and no test writes into a bundle's own files. So the copy's files can be hard
links to the original's: a 50-60 MB Golden Sample then costs a few directory entries. Where a link
can't be made (another filesystem), the file is copied.
"""

import os
import shutil
from pathlib import Path


def _link_or_copy(source, target):
    try:
        os.link(source, target)
    except OSError:
        shutil.copy2(source, target)
    return target


def copy_bundle(source: Path, target: Path) -> Path:
    """`source` as a new folder `target`, without its kkbp_cache/; returns `target`."""
    shutil.copytree(source, target, ignore=shutil.ignore_patterns("kkbp_cache"), copy_function=_link_or_copy)
    return Path(target)
