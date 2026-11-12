"""Writes a structural fingerprint of a .blend as sorted JSON, to prove a rebuilt library is the
same as the one it replaces (docs/design/library-from-code.md, "Equality check").

    blender --background --factory-startup FILE.blend --python importer/tools/library/fingerprint.py -- OUT.json

Covers node groups, materials, images (pixels by hash), meshes, armatures, objects, collections and
shape keys. Scenes and worlds are left out: no Hook or template appends them.
"""

import hashlib
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import introspect as ins  # noqa: E402

DIGITS = ins.DIGITS


def id_common(d):
    return {"use_fake_user": d.use_fake_user, "props": ins.custom_props(d)}


def material(m):
    out = ins.rna(m, skip={"grease_pencil", "paint_active_slot", "texture_paint_images", "texture_paint_slots",
                           "line_priority"}, depth=0)
    out.update(id_common(m))
    out["tree"] = ins.tree(m.node_tree) if m.node_tree else None
    out["drivers"] = ins.drivers(m)
    return out


def image(i):
    out = {"size": list(i.size), "source": i.source, "file_format": i.file_format,
           "colorspace": i.colorspace_settings.name, "alpha_mode": i.alpha_mode, "filepath": i.filepath,
           "packed": i.packed_file is not None, "use_view_as_render": i.use_view_as_render,
           "use_half_precision": i.use_half_precision, "is_float": i.is_float}
    if i.packed_file is not None:
        out["packed_sha1"] = hashlib.sha1(bytes(i.packed_file.data)).hexdigest()
        out["packed_size"] = i.packed_file.size
    if i.source == "GENERATED":
        out["generated"] = {"type": i.generated_type, "color": ins.value(i.generated_color),
                            "float": i.use_generated_float}
    if i.size[0] and i.size[1]:
        import numpy as np
        px = np.empty(i.size[0] * i.size[1] * i.channels, dtype=np.float32)
        i.pixels.foreach_get(px)
        out["pixels_sha1"] = hashlib.sha1(np.round(px, 4).tobytes()).hexdigest()
    out.update(id_common(i))
    return out


def mesh(m):
    r = lambda v: [round(x, DIGITS) for x in v]  # noqa: E731
    out = {"vertices": [r(v.co) for v in m.vertices], "edges": [list(e.vertices) for e in m.edges],
           "polygons": [[list(p.vertices), p.material_index, p.use_smooth] for p in m.polygons],
           "uv_layers": {u.name: [r(d.uv) for d in u.data] for u in m.uv_layers},
           "attributes": sorted((a.name, a.domain, a.data_type) for a in m.attributes if not a.is_internal),
           "materials": [x.name if x else None for x in m.materials],
           "shape_keys": None}
    if m.shape_keys:
        k = m.shape_keys
        out["shape_keys"] = {"use_relative": k.use_relative, "reference": k.reference_key.name,
                             "blocks": [{"name": b.name, "value": ins.num(b.value), "relative_key": b.relative_key.name,
                                         "slider_min": ins.num(b.slider_min), "slider_max": ins.num(b.slider_max),
                                         "mute": b.mute, "vertex_group": b.vertex_group, "interpolation": b.interpolation,
                                         "co": [r(p.co) for p in b.data]} for b in k.key_blocks],
                             "drivers": ins.drivers(k)}
    out.update(id_common(m))
    return out


def armature(a):
    out = {"collections": [ins.rna(c, depth=0) for c in a.collections_all],
           "bones": {b.name: {"parent": b.parent.name if b.parent else None,
                              "head": ins.value(b.head_local), "tail": ins.value(b.tail_local),
                              "matrix": ins.value([list(row) for row in b.matrix_local]),
                              "props": ins.rna(b, skip={"parent", "children", "matrix", "matrix_local", "head",
                                                        "tail", "head_local", "tail_local", "center", "length",
                                                        "vector", "x_axis", "y_axis", "z_axis", "collections"}, depth=0),
                              "collections": [c.name for c in b.collections]} for b in a.bones}}
    out["props_armature"] = ins.rna(a, skip={"bones", "edit_bones", "collections", "collections_all"}, depth=0)
    out.update(id_common(a))
    return out


def obj(o):
    out = {"type": o.type, "data": o.data.name if o.data else None,
           "parent": o.parent.name if o.parent else None, "parent_type": o.parent_type, "parent_bone": o.parent_bone,
           "matrix_parent_inverse": ins.value([list(r) for r in o.matrix_parent_inverse]),
           "location": ins.value(o.location), "rotation_mode": o.rotation_mode,
           "rotation_euler": ins.value(o.rotation_euler), "rotation_quaternion": ins.value(o.rotation_quaternion),
           "scale": ins.value(o.scale), "hide_viewport": o.hide_viewport, "hide_render": o.hide_render,
           "display_type": o.display_type, "show_in_front": o.show_in_front,
           "vertex_groups": [g.name for g in o.vertex_groups],
           "material_slots": [[s.link, s.material.name if s.material else None] for s in o.material_slots],
           "modifiers": [ins.rna(m, skip={"is_override_data", "execution_time", "persistent_uid"}, depth=1)
                         for m in o.modifiers],
           "constraints": [ins.rna(c, depth=0) for c in o.constraints],
           "collections": sorted(c.name for c in o.users_collection),
           "drivers": ins.drivers(o)}
    if o.type == "MESH" and o.vertex_groups:
        out["weights"] = [[[o.vertex_groups[g.group].name, round(g.weight, DIGITS)] for g in v.groups]
                          for v in o.data.vertices]
    if o.type == "ARMATURE":
        out["pose"] = {p.name: {"custom_shape": p.custom_shape.name if p.custom_shape else None,
                                "props": ins.rna(p, skip={"bone", "parent", "child", "children", "custom_shape",
                                                          "head", "tail", "matrix", "matrix_channel", "length",
                                                          "constraints", "custom_shape_transform"}, depth=0),
                                "custom_shape_transform": p.custom_shape_transform.name if p.custom_shape_transform else None,
                                "constraints": [ins.rna(c, depth=0) for c in p.constraints]}
                       for p in o.pose.bones}
    out.update(id_common(o))
    return out


def collection(c):
    out = {"objects": sorted(o.name for o in c.objects), "children": sorted(x.name for x in c.children),
           "hide_viewport": c.hide_viewport, "hide_render": c.hide_render, "hide_select": c.hide_select}
    out.update(id_common(c))
    return out


def main():
    out_path = sys.argv[sys.argv.index("--") + 1]
    data = {
        "node_groups": {g.name: {"bl_idname": g.bl_idname, **id_common(g), "tree": ins.tree(g),
                                 "props_tree": ins.rna(g, skip={"is_modifier", "is_tool"}, depth=0)}
                        for g in bpy.data.node_groups},
        "materials": {m.name: material(m) for m in bpy.data.materials},
        "images": {i.name: image(i) for i in bpy.data.images},
        "meshes": {m.name: mesh(m) for m in bpy.data.meshes},
        "armatures": {a.name: armature(a) for a in bpy.data.armatures},
        "objects": {o.name: obj(o) for o in bpy.data.objects},
        "collections": {c.name: collection(c) for c in bpy.data.collections},
    }
    Path(out_path).write_text(json.dumps(data, indent=1, sort_keys=True, default=str))
    print(f"Wrote {out_path}: " + ", ".join(f"{len(v)} {k}" for k, v in data.items()))


main()
