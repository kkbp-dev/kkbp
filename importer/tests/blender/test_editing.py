"""editing() always restores the mode, active object and selection."""

import bpy
import pytest

from conftest import submodule

editing = submodule("editing").editing


def _mesh(name):
    obj = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _armature(name):
    obj = bpy.data.objects.new(name, bpy.data.armatures.new(name))
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _state():
    vl = bpy.context.view_layer
    active = vl.objects.active
    return (active.name if active else None, active.mode if active else None,
            sorted(o.name for o in vl.objects if o.select_get()))


def test_enters_the_mode_and_restores_everything():
    a, b, other = _mesh("a"), _mesh("b"), _mesh("other")
    vl = bpy.context.view_layer
    other.select_set(True)
    vl.objects.active = other
    before = _state()
    with editing(a, "EDIT") as obj:
        assert obj == a and a.mode == "EDIT"
        assert vl.objects.active == a
        assert not other.select_get()
    assert a.mode == "OBJECT"
    assert _state() == before
    assert not b.select_get()


def test_restores_after_an_error():
    a, other = _mesh("a"), _mesh("other")
    bpy.context.view_layer.objects.active = other
    other.select_set(True)
    before = _state()
    with pytest.raises(RuntimeError, match="inside"):
        with editing(a, "EDIT"):
            raise RuntimeError("inside")
    assert a.mode == "OBJECT"
    assert _state() == before


def test_edit_bones_through_the_data_api():
    arm = _armature("rig")
    with editing(arm, "EDIT"):
        bone = arm.data.edit_bones.new("root")
        bone.tail = (0.0, 0.0, 1.0)
    assert [b.name for b in arm.data.bones] == ["root"]


def test_restores_a_previous_non_object_mode():
    arm, mesh = _armature("rig"), _mesh("body")
    with editing(arm, "EDIT"):
        arm.data.edit_bones.new("root").tail = (0.0, 0.0, 1.0)
    bpy.context.view_layer.objects.active = arm
    with bpy.context.temp_override(active_object=arm, object=arm):
        bpy.ops.object.mode_set(mode="POSE")
    with editing(mesh, "EDIT"):
        assert mesh.mode == "EDIT" and arm.mode == "OBJECT"
    assert arm.mode == "POSE" and mesh.mode == "OBJECT"
    assert bpy.context.view_layer.objects.active == arm


def test_several_objects_edit_together():
    a, b = _mesh("a"), _mesh("b")
    with editing([a, b], "EDIT") as objs:
        assert objs == [a, b]
        assert a.mode == "EDIT" and b.mode == "EDIT"
    assert a.mode == "OBJECT" and b.mode == "OBJECT"


def test_nested():
    a, b = _mesh("a"), _mesh("b")
    with editing(a, "EDIT"):
        with editing(b, "EDIT"):
            assert b.mode == "EDIT" and a.mode == "OBJECT"
        assert a.mode == "EDIT" and b.mode == "OBJECT"
    assert a.mode == "OBJECT"


def test_an_object_removed_inside_is_skipped():
    a, other = _mesh("a"), _mesh("other")
    bpy.context.view_layer.objects.active = other
    with editing(a, "OBJECT"):
        bpy.data.objects.remove(other)
    assert bpy.context.view_layer.objects.active is None


def test_hidden_objects_are_a_clear_error():
    a = _mesh("a")
    a.hide_set(True)
    with pytest.raises(ValueError, match="a is hidden or not in the view layer"):
        with editing(a, "EDIT"):
            pass
