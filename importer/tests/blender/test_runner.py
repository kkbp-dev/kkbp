"""The in-Blender test setup itself."""

import bpy

from conftest import MODULE


def test_add_on_is_enabled_from_the_test_profile():
    assert MODULE in bpy.context.preferences.addons


def test_each_test_starts_with_an_empty_scene():
    assert len(bpy.data.objects) == 0
    bpy.data.objects.new("leftover", None)


def test_the_last_test_left_nothing_behind():
    assert len(bpy.data.objects) == 0
