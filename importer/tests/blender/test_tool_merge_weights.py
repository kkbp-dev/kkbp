"""Merge Weights on a hand-built Character."""

import bpy

from conftest import submodule

character = submodule("character")
merge = submodule("tools.merge_weights")
editing = submodule("editing")


def _scene():
    ch = character.Character.new("Chika", "KK", "/nowhere")
    data = bpy.data.armatures.new("Armature")
    arm = bpy.data.objects.new("Armature", data)
    bpy.context.scene.collection.objects.link(arm)
    with editing.editing(arm, "EDIT"):
        for name, parent in (("root", None), ("a", "root"), ("b", "a"), ("c", "b")):
            bone = data.edit_bones.new(name)
            bone.tail = (0, 0, 1)
            if parent:
                bone.parent = data.edit_bones[parent]
    ch.add_part(arm, "armature")
    mesh = bpy.data.meshes.new("Body")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0)], [], [])
    body = bpy.data.objects.new("Body", mesh)
    bpy.context.scene.collection.objects.link(body)
    ch.add_part(body, "body")
    for name in ("a", "b", "c"):
        body.vertex_groups.new(name=name)
    body.vertex_groups["a"].add([0], 0.25, "REPLACE")
    body.vertex_groups["b"].add([0], 0.5, "REPLACE")
    body.vertex_groups["c"].add([1], 1.0, "REPLACE")
    return ch, arm, body


def test_weights_go_to_the_nearest_unmerged_ancestor():
    ch, arm, body = _scene()
    assert merge.targets(arm, ["b", "c"]) == {"b": "a", "c": "a"}
    assert merge.merge_weights(ch, arm, ["b", "c"]) == 2
    assert set(arm.data.bones.keys()) == {"root", "a"}
    assert set(body.vertex_groups.keys()) == {"a"}
    a = body.vertex_groups["a"]
    assert abs(a.weight(0) - 0.75) < 1e-6 and abs(a.weight(1) - 1.0) < 1e-6
