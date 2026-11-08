"""Bulk import, on two builder bundles and an unfinished one."""

import bpy

from conftest import MODULE, submodule

bulk_import = submodule("tools.bulk_import")


def test_each_bundle_gets_a_blend_beside_it(build, tmp_path):
    parent = tmp_path / "bundles"
    parent.mkdir()
    for name in ("a", "b"):
        built = build()
        built.rename(parent / name)
    (parent / "unfinished").mkdir()  # no manifest: not a bundle
    assert [p.name for p in bulk_import.bundle_folders(parent)] == ["a", "b"]
    done = bulk_import.run(parent, bpy.app.binary_path, MODULE, log=lambda m: None)
    assert [saved.name if saved else None for _, saved in done] == ["a.blend", "b.blend"]
