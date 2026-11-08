"""Delete default scene: Blender's startup cube, camera and light go only when nothing else is in
the file but imported Characters."""

import bpy

from bundle_builder import BundleBuilder
from conftest import kkbp

DEFAULTS = ("Cube", "Camera", "Light")


def _startup_file():
    """The startup file's three objects, made by hand: reading the factory startup file would reset
    the preferences and turn the add-on off."""
    import bmesh
    mesh = bpy.data.meshes.new("Cube")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)
    bm.to_mesh(mesh)
    bm.free()
    for obj in (bpy.data.objects.new("Cube", mesh), bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera")),
                bpy.data.objects.new("Light", bpy.data.lights.new("Light", "POINT"))):
        bpy.context.scene.collection.objects.link(obj)


def test_the_startup_scene_goes(build):
    _startup_file()
    assert kkbp.api.import_bundle(build(), hooks=["Delete default scene"]).ok
    assert not any(name in bpy.data.objects for name in DEFAULTS)
    assert "Cube" not in bpy.data.meshes and "Camera" not in bpy.data.cameras and "Light" not in bpy.data.lights


def test_it_stays_with_an_earlier_character(build):
    _startup_file()
    kkbp.api.import_bundle(build(), hooks=[])  # the Core Import alone keeps the startup scene
    assert all(name in bpy.data.objects for name in DEFAULTS)
    kkbp.api.import_bundle(build(BundleBuilder(name="Second")), hooks=["Delete default scene"])
    assert not any(name in bpy.data.objects for name in DEFAULTS)


def test_it_stays_in_a_scene_someone_started(build):
    _startup_file()
    mine = bpy.data.objects.new("My empty", None)
    bpy.context.scene.collection.objects.link(mine)
    assert kkbp.api.import_bundle(build(), hooks=["Delete default scene"]).ok
    assert all(name in bpy.data.objects for name in DEFAULTS)


def test_it_leaves_a_renamed_or_retyped_default_alone(build):
    _startup_file()
    bpy.data.objects["Light"].name = "Key light"
    assert kkbp.api.import_bundle(build(), hooks=["Delete default scene"]).ok
    assert "Cube" in bpy.data.objects and "Camera" in bpy.data.objects
