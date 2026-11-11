"""Writes a .blend's images, meshes, objects, armatures and collections as files under
`importer/library-src/` (docs/design/library-from-code.md, "One-time extraction").

    blender --background --factory-startup FILE.blend --python importer/tools/library/export_assets.py -- LIBRARY_SRC FILE_KEY

- `images/<file>`: each packed image's own bytes, never re-encoded; `images.json` gets its settings
  (generated images get their generator settings and no file).
- `meshes/<name>.json`: geometry by the mesh data API's own arrays (vertices, edges, loops, polygons),
  so a rebuilt mesh keeps every element's order; attributes, UV maps and shape keys.
- `scenes/<FILE_KEY>.json`: collections, objects (with modifiers, constraints, vertex groups and
  weights) and armatures (bones, bone collections, pose bones and their constraints).

Properties are written where they differ from a fresh datablock or struct of the same type.
"""

import json
import re
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from introspect import diff  # noqa: E402

_OBJECT_SKIP = {"rna_type", "name", "name_full", "data", "parent", "parent_type", "parent_bone", "modifiers",
                "constraints", "vertex_groups", "material_slots", "pose", "animation_data", "matrix_world",
                "matrix_local", "matrix_basis", "matrix_parent_inverse", "bound_box", "dimensions", "mode",
                "active_material", "active_material_index", "active_shape_key", "active_shape_key_index",
                "users_collection", "users_scene", "children", "children_recursive", "field", "collision",
                "rigid_body", "rigid_body_constraint", "soft_body", "particle_systems", "shader_effects",
                "grease_pencil_modifiers", "lightgroup", "light_linking", "image_user", "motion_path",
                "animation_visualization", "use_fake_user", "use_extra_user", "is_evaluated", "original",
                "users", "session_uid", "tag", "is_runtime_data", "is_missing", "is_embedded_data",
                "library", "library_weak_reference", "override_library", "asset_data", "preview", "id_type",
                "is_library_indirect", "is_editmode", "shape_key_add", "select", "hide", "visible_get"}
_MOD_SKIP = {"rna_type", "name", "type", "is_override_data", "execution_time", "persistent_uid", "show_expanded",
             "is_active", "use_pin_to_last", "object", "vertex_group"}
_CON_SKIP = {"rna_type", "name", "type", "is_override_data", "is_valid", "show_expanded", "active", "target",
             "subtarget", "space_object", "space_subtarget", "error_location", "error_rotation"}
_BONE_SKIP = {"rna_type", "name", "parent", "children", "head", "tail", "head_local", "tail_local", "matrix",
              "matrix_local", "center", "length", "vector", "x_axis", "y_axis", "z_axis", "collections",
              "bbone_custom_handle_start", "bbone_custom_handle_end", "select", "select_head", "select_tail"}
_POSE_SKIP = {"rna_type", "name", "bone", "parent", "child", "children", "custom_shape", "custom_shape_transform",
              "head", "tail", "matrix", "matrix_channel", "matrix_basis", "length", "constraints", "motion_path",
              "is_in_ik_chain", "location", "rotation_euler", "rotation_quaternion", "rotation_axis_angle", "scale",
              "bbone_custom_handle_start", "bbone_custom_handle_end", "select"}


def jsonable(v):
    if isinstance(v, bpy.types.ID):
        return {"ref": [type(v).__name__, v.name]}
    if isinstance(v, (set, frozenset)):
        return {"set": sorted(v)}
    if isinstance(v, dict):
        return {k: jsonable(x) for k, x in v.items()}
    if isinstance(v, tuple):
        return [jsonable(x) for x in v]
    return v


def file_name(name, fmt):
    ext = {"PNG": ".png", "OPEN_EXR": ".exr", "WEBP": ".webp", "JPEG": ".jpg", "TARGA": ".tga"}.get(fmt, ".bin")
    base = re.sub(r'[<>:"/\\|?*]', "", name).strip()
    return base if base.lower().endswith(ext) else base + ext


# --- images -----------------------------------------------------------------------------

def images(out):
    table = {}
    folder = out / "images"
    folder.mkdir(parents=True, exist_ok=True)
    for i in bpy.data.images:
        entry = {"source": i.source, "colorspace": i.colorspace_settings.name, "alpha_mode": i.alpha_mode}
        if i.source == "GENERATED":
            entry.update(size=list(i.size), generated_type=i.generated_type, generated_color=list(i.generated_color),
                         float=i.use_generated_float, file_format=i.file_format)
        elif i.packed_file is not None:
            name = file_name(i.name, i.file_format)
            (folder / name).write_bytes(bytes(i.packed_file.data))
            entry["file"] = name
        else:
            entry["missing"] = True  # e.g. V9's broken Template: Black; build.py says what replaces it
        table[i.name] = entry
    return table


# --- meshes -----------------------------------------------------------------------------

def mesh(m):
    def arr(coll, attr, n):
        a = [0] * (len(coll) * n)
        coll.foreach_get(attr, a)
        return a
    data = {
        "vertices": arr(m.vertices, "co", 3),
        "edges": arr(m.edges, "vertices", 2),
        "loops": {"vertex_index": arr(m.loops, "vertex_index", 1), "edge_index": arr(m.loops, "edge_index", 1)},
        "polygons": {"loop_start": arr(m.polygons, "loop_start", 1), "loop_total": arr(m.polygons, "loop_total", 1)},
        "uv_layers": {},
        "attributes": [],
        "materials": [x.name if x else None for x in m.materials],
        # With auto texture space, Blender works the texture space out from the geometry.
        "props": diff(m, bpy.data.meshes.new("~scratch"), _OBJECT_SKIP | (
            {"texspace_location", "texspace_size"} if m.use_auto_texspace else set()) | {"vertices", "edges", "loops", "polygons",
                      "uv_layers", "attributes", "materials", "shape_keys", "loop_triangles", "loop_triangle_polygons",
                      "vertex_colors", "color_attributes", "skin_vertices", "vertex_normals", "polygon_normals",
                      "corner_normals", "normals_domain", "cycles", "texture_mesh", "edge_creases", "vertex_creases",
                      "has_custom_normals", "total_vert_sel", "total_edge_sel", "total_face_sel", "is_editmode",
                      "uv_layer_clone", "uv_layer_stencil", "uv_layer_clone_index", "uv_layer_stencil_index"}, depth=0),
    }
    for uv in m.uv_layers:
        values = [0.0] * (len(uv.data) * 2)
        uv.data.foreach_get("uv", values)
        data["uv_layers"][uv.name] = {"uv": values, "active": uv.active, "active_render": uv.active_render}
    uv_names = {u.name for u in m.uv_layers}
    for a in m.attributes:
        if a.is_internal or a.is_required or a.name in uv_names or a.name.startswith("."):
            continue
        width = {"FLOAT": 1, "INT": 1, "BOOLEAN": 1, "INT8": 1, "FLOAT2": 2, "FLOAT_VECTOR": 3, "FLOAT_COLOR": 4,
                 "BYTE_COLOR": 4, "QUATERNION": 4, "INT32_2D": 2}[a.data_type]
        key = {"FLOAT_VECTOR": "vector", "FLOAT2": "vector", "FLOAT_COLOR": "color", "BYTE_COLOR": "color",
               "QUATERNION": "value", "INT32_2D": "value"}.get(a.data_type, "value")
        values = [0] * (len(a.data) * width)
        a.data.foreach_get(key, values)
        data["attributes"].append({"name": a.name, "domain": a.domain, "data_type": a.data_type, "key": key,
                                   "values": values})
    bpy.data.meshes.remove(bpy.data.meshes["~scratch"])
    if m.shape_keys:
        k = m.shape_keys
        data["shape_keys"] = {
            "name": k.name, "use_relative": k.use_relative,
            "blocks": [{"name": b.name, "relative_key": b.relative_key.name, "value": b.value,
                        "slider_min": b.slider_min, "slider_max": b.slider_max, "mute": b.mute,
                        "vertex_group": b.vertex_group, "interpolation": b.interpolation,
                        "co": arr(b.data, "co", 3)} for b in k.key_blocks]}
    return data


# --- objects ----------------------------------------------------------------------------

def scratch_object(o):
    return bpy.data.objects.new("~scratch", o.data)


def objects():
    out = {}
    for o in bpy.data.objects:
        fresh = scratch_object(o)
        entry = {
            "type": o.type,
            "data": [type(o.data).__name__, o.data.name] if o.data else None,
            "parent": o.parent.name if o.parent else None, "parent_type": o.parent_type, "parent_bone": o.parent_bone,
            "matrix_parent_inverse": [list(r) for r in o.matrix_parent_inverse],
            "props": diff(o, fresh, _OBJECT_SKIP, depth=1),
            "vertex_groups": [{"name": g.name, "lock_weight": g.lock_weight} for g in o.vertex_groups],
            "material_slots": [[s.link, s.material.name if s.material else None] for s in o.material_slots],
            "modifiers": [], "constraints": [],
        }
        for md in o.modifiers:
            probe = fresh.modifiers.new("~", md.type)
            entry["modifiers"].append({"name": md.name, "type": md.type,
                                       "object": md.object.name if getattr(md, "object", None) else None,
                                       "vertex_group": getattr(md, "vertex_group", None),
                                       "props": diff(md, probe, _MOD_SKIP, depth=0)})
        for c in o.constraints:
            entry["constraints"].append(constraint(c, fresh.constraints.new(c.type)))
        if o.type == "MESH" and o.vertex_groups:
            entry["weights"] = [[[g.group, g.weight] for g in v.groups] for v in o.data.vertices]
        if o.type == "ARMATURE":
            entry["pose"] = pose(o)
        bpy.data.objects.remove(fresh)
        out[o.name] = entry
    return out


def constraint(c, probe):
    return {"name": c.name, "type": c.type, "target": c.target.name if getattr(c, "target", None) else None,
            "subtarget": getattr(c, "subtarget", None), "props": diff(c, probe, _CON_SKIP, depth=0)}


def pose(o):
    scratch_arm = bpy.data.armatures.new("~scratch")
    scratch = bpy.data.objects.new("~scratch", scratch_arm)
    bpy.context.scene.collection.objects.link(scratch)
    bpy.context.view_layer.objects.active = scratch
    bpy.ops.object.mode_set(mode="EDIT")
    scratch_arm.edit_bones.new("b").tail = (0, 0, 1)
    bpy.ops.object.mode_set(mode="OBJECT")
    fresh = scratch.pose.bones["b"]
    out = {}
    for p in o.pose.bones:
        out[p.name] = {
            "custom_shape": p.custom_shape.name if p.custom_shape else None,
            "custom_shape_transform": p.custom_shape_transform.name if p.custom_shape_transform else None,
            "location": list(p.location), "rotation_quaternion": list(p.rotation_quaternion),
            "rotation_euler": list(p.rotation_euler), "rotation_axis_angle": list(p.rotation_axis_angle),
            "scale": list(p.scale),
            "props": diff(p, fresh, _POSE_SKIP, depth=0),
            "constraints": [constraint(c, fresh.constraints.new(c.type)) for c in p.constraints],
        }
    bpy.data.objects.remove(scratch)
    bpy.data.armatures.remove(scratch_arm)
    return out


def armatures():
    out = {}
    for a in bpy.data.armatures:
        owner = next(o for o in bpy.data.objects if o.data == a)
        scratch_arm = bpy.data.armatures.new("~scratch")
        scratch = bpy.data.objects.new("~scratch", scratch_arm)
        bpy.context.scene.collection.objects.link(scratch)
        bpy.context.view_layer.objects.active = scratch
        bpy.ops.object.mode_set(mode="EDIT")
        scratch_arm.edit_bones.new("b").tail = (0, 0, 1)
        bpy.ops.object.mode_set(mode="OBJECT")
        fresh_bone = scratch_arm.bones["b"]
        # Edit-bone data: head, tail and roll as edit mode has them.
        bpy.context.scene.collection.objects.link(owner) if owner.name not in bpy.context.scene.collection.objects else None
        bpy.context.view_layer.objects.active = owner
        bpy.ops.object.mode_set(mode="EDIT")
        edit = {b.name: {"head": list(b.head), "tail": list(b.tail), "roll": b.roll, "use_connect": b.use_connect}
                for b in a.edit_bones}
        bpy.ops.object.mode_set(mode="OBJECT")
        out[a.name] = {
            "props": diff(a, scratch_arm, _OBJECT_SKIP | {"bones", "edit_bones", "collections", "collections_all"}, depth=0),
            "collections": [{"name": c.name, "parent": c.parent.name if c.parent else None,
                             "props": diff(c, None, {"rna_type", "name", "parent", "children", "bones", "index",
                                                    "child_number", "is_editable", "is_local_override",
                                                    "has_ancestors", "is_visible_ancestors", "is_visible_effectively",
                                                    "is_expanded"}, depth=0)}
                            for c in a.collections_all],
            "bones": [{"name": b.name, "parent": b.parent.name if b.parent else None, **edit[b.name],
                       "collections": [c.name for c in b.collections],
                       "props": diff(b, fresh_bone, _BONE_SKIP | {"use_connect"}, depth=0)} for b in a.bones],
        }
        bpy.data.objects.remove(scratch)
        bpy.data.armatures.remove(scratch_arm)
    return out


def collections():
    return {c.name: {"objects": [o.name for o in c.objects], "children": [x.name for x in c.children],
                     "use_fake_user": c.use_fake_user, "hide_viewport": c.hide_viewport, "hide_render": c.hide_render,
                     "hide_select": c.hide_select} for c in bpy.data.collections}


def dumps(data):
    """Indented JSON with each list of numbers on one line, so a diff shows which array changed."""
    text = json.dumps(data, indent=1)
    return re.sub(r"\[\s*([-0-9.eE+,\s]+?)\s*\]", lambda m: "[" + re.sub(r"\s+", "", m.group(1)).replace(",", ", ") + "]", text)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    out, key = Path(args[0]), args[1]
    table_path = out / "images.json"
    table = json.loads(table_path.read_text()) if table_path.is_file() else {}
    for name, entry in images(out).items():
        if name in table and table[name] != entry:
            raise RuntimeError(f"image {name!r} differs between files: {table[name]} / {entry}")
        table[name] = entry
    table_path.write_text(dumps(dict(sorted(table.items()))) + "\n")
    (out / "meshes").mkdir(exist_ok=True)
    for m in bpy.data.meshes:
        name = re.sub(r"[^0-9a-zA-Z]+", "_", m.name).strip("_").lower()
        (out / "meshes" / f"{name}.json").write_text(dumps({"name": m.name, **jsonable(mesh(m))}) + "\n")
    scene = {"collections": collections(), "armatures": jsonable(armatures()), "objects": jsonable(objects())}
    if bpy.data.objects or bpy.data.collections:
        (out / "scenes").mkdir(exist_ok=True)
        (out / "scenes" / f"{key}.json").write_text(dumps(scene) + "\n")
    print(f"{key}: {len(bpy.data.images)} images, {len(bpy.data.meshes)} meshes, {len(bpy.data.objects)} objects")


main()
