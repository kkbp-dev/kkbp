"""What the expressions change on a material is driven on the objects that use it. A Hook
that makes an object or moves a material to one must take the properties and their drivers along."""

import bpy
import pytest

from conftest import submodule

templates = submodule("templates")

HOOKS = [("Convert shaders", {"convert_shaders": "cycles"}), ("Separate meshes", {"separation_type": "by_material"}),
         ("Outlines", {"use_outlines": True}), ("Face cards", {"use_face_cards": True}), ("SFW", {"sfw_mode": True}),
         ("Rigify", {"use_rigify": True}), ("Separate Eyes", {"separate_eyes": True})]


@pytest.mark.parametrize("sample", ["kk", "svs"])  # KKS takes KK's path through every Hook
@pytest.mark.parametrize("hook, options", [(None, {})] + HOOKS, ids=["core"] + [h for h, _ in HOOKS])
def test_every_object_has_the_properties_its_materials_read(sample, hook, options, golden_import):
    result, ch = golden_import(sample, hooks=[hook] if hook else [], options=options)
    assert all(h.status == "ran" for h in result.hooks), result.hooks
    reading = 0
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        used = {p.material_index for p in obj.data.polygons}
        driven = {fc.data_path for fc in obj.animation_data.drivers} if obj.animation_data else set()
        for index, slot in enumerate(obj.material_slots):
            if index not in used:
                continue
            for prop in templates.object_properties(slot.material):
                reading += 1
                assert prop in obj, (obj.name, slot.material.name, prop)
                assert f'["{prop}"]' in driven, (obj.name, slot.material.name, prop)
    assert reading
