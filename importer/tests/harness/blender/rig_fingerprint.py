"""Rig fingerprint: everything the Rigify Hook makes, for checking that a rewrite of the Hook leaves the
rig as it was.

Runs inside Blender, started by run.py (`run.py fingerprint`):

    blender --background --factory-startup --python-exit-code 1 --python rig_fingerprint.py -- \
        --bundle DIR --pillow WHEEL --out FILE

It imports the bundle with the Core Import and the Rigify Hook alone, and writes JSON with:

- `metarig`: the metarig as the Hook hands it to Rigify (taken inside `compat.generate_rigify`);
- `rig`: the generated rig when the Hook is done;
- for both, every bone collection in order, every bone's and pose bone's RNA properties, custom
  properties with their UI data, Rigify types and the Rigify parameters that are set, and every
  constraint in stack order with all its properties;
- every driver on the scene's objects, their data and their shape keys;
- the Character's meshes: modifiers, vertex groups with a hash of their weights, shape keys with
  a hash of their positions, parenting;
- the widgets and the collections under the Character's, and Rigify's UI script (hashed);
- the scene tool settings and the Hook's log lines.

The scene summary (scene_summary.py) records only bone positions and counts; this records the
settings a rewrite could change by mistake. Floats are rounded to DIGITS places. The Character's name
becomes "{character}", the metarig's random id bone "{random}" and Rigify's rig_id "{rig_id}".
"""

import argparse
import hashlib
import importlib
import json
import os
import sys
import traceback

import addon_utils
import bpy

sys.path.insert(0, os.path.dirname(__file__))
from fingerprint_names import Cleaner, sorted_sets  # noqa: E402

FINGERPRINT_VERSION = 1
MODULE = "bl_ext.user_default.kkbp"
HOOK = "Rigify"
DIGITS = 5
# Properties that are selection state or say nothing about the rig.
SKIPPED = frozenset({"rna_type", "select", "select_head", "select_tail", "is_property_set"})
# Nested structs (pointers without a name) are followed this deep.
DEPTH = 3


clean = Cleaner()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--pillow", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    bpy.ops.wm.read_homefile(use_empty=True)
    if addon_utils.enable(MODULE, default_set=True, handle_error=_raise) is None:
        raise SystemExit(f"Could not enable {MODULE}")
    pillow = importlib.import_module(f"{MODULE}.pillow")
    if not pillow.available():
        pillow.use_wheel(args.pillow)
        if not pillow.install_from_manifest():
            raise SystemExit("Blender didn't install the Pillow wheel")
    kkbp = importlib.import_module(MODULE)
    compat = importlib.import_module(f"{MODULE}.compat")
    character = importlib.import_module(f"{MODULE}.character")

    captured = {}
    generate = compat.generate_rigify

    def generate_and_capture(metarig):
        captured["metarig"] = armature(metarig)
        captured["metarig_drivers"] = drivers_of(metarig)
        return generate(metarig)

    compat.generate_rigify = generate_and_capture
    try:
        result = kkbp.api.import_bundle(args.bundle, hooks=[HOOK])
    finally:
        compat.generate_rigify = generate
    if not result.ok:
        raise SystemExit(f"Import failed in Step {result.failed_step}: {result.error}")
    failed = [f"{h.name}: {h.reason}" for h in result.hooks if h.status != "ran"]
    if failed:
        raise SystemExit(f"Hook didn't run: {'; '.join(failed)}")
    if "metarig" not in captured:
        raise SystemExit("The Hook never called compat.generate_rigify")

    ch = character.Character(result.character_key)
    clean.replacements[ch.name] = "{character}"
    clean.replacements[result.character_key] = "{key}"  # random per import (character.py)
    rig = ch.rig
    rig_id = rig.data.get("rig_id")
    if isinstance(rig_id, str):
        clean.replacements[rig_id] = "{rig_id}"
    # The metarig was captured before the rig_id existed; its names need the Character's only.
    metarig = _cleaned(captured["metarig"])
    fingerprint = {
        "fingerprint_version": FINGERPRINT_VERSION,
        "metarig": metarig,
        "metarig_drivers": _cleaned(captured["metarig_drivers"]),
        "rig": armature(rig),
        "rig_object": object_settings(rig),
        "metarig_object": object_settings(ch.armature),
        "drivers": {clean(o.name): drivers_of(o) for o in sorted(bpy.data.objects, key=lambda o: o.name)
                    if drivers_of(o)},
        "meshes": {clean(o.name): mesh(o) for o in sorted(ch.parts(), key=lambda o: o.name) if o.type == "MESH"},
        "collections": collection_tree(ch.collection, bpy.context.view_layer.layer_collection),
        "widgets": widgets(ch),
        "texts": {clean(t.name): [sorted_sets(line) for line in clean(t.as_string()).splitlines()]
                  for t in sorted(bpy.data.texts, key=lambda t: t.name)},
        "tool_settings": {
            "transform_pivot_point": bpy.context.scene.tool_settings.transform_pivot_point,
            "mesh_select_mode": list(bpy.context.scene.tool_settings.mesh_select_mode),
        },
        "log": hook_log(result.log_path),
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(fingerprint, f, ensure_ascii=False, indent=1, sort_keys=True)


# --- armatures -----------------------------------------------------------------------------

def armature(obj):
    data = obj.data
    return {
        "data": {name: value(data, name) for name in _names(data)
                 if name.startswith("rigify") or name in ("display_type", "pose_position", "show_axes",
                                                          "show_names", "show_bone_colors", "show_bone_custom_shapes")},
        "data_properties": custom_properties(data),
        "collections": [collection(c) for c in data.collections_all],
        "bones": {clean(b.name): bone(b) for b in data.bones},
        "pose_bones": {clean(pb.name): pose_bone(pb) for pb in obj.pose.bones},
    }


def collection(c):
    out = rna(c, skip={"bones", "bones_all", "children"})
    out["children"] = [clean(child.name) for child in c.children]
    out["bones"] = sorted(clean(b.name) for b in c.bones)
    out["properties"] = custom_properties(c)
    return out


def bone(b):
    out = rna(b, skip={"children", "collections"})
    out["children"] = sorted(clean(c.name) for c in b.children)
    out["collections"] = [clean(c.name) for c in b.collections]
    out["properties"] = custom_properties(b)
    return out


def pose_bone(pb):
    out = rna(pb, skip={"constraints", "rigify_parameters", "bone", "child", "matrix_channel"})
    out["constraints"] = [constraint(c) for c in pb.constraints]
    out["properties"] = custom_properties(pb)
    params = getattr(pb, "rigify_parameters", None)
    if params is not None:
        out["rigify_parameters"] = rigify_parameters(params)
    return out


def rigify_parameters(params):
    """Only the parameters that are set: the rest are Rigify's defaults, hundreds per bone."""
    out = {}
    for prop in params.bl_rna.properties:
        name = prop.identifier
        if name in SKIPPED:
            continue
        if prop.type == "COLLECTION":
            items = getattr(params, name)
            if len(items):
                out[name] = [rna(item) for item in items]
        elif params.is_property_set(name):
            out[name] = value(params, name)
    return out


def constraint(c):
    out = rna(c, skip={"targets"})
    if hasattr(c, "targets"):
        out["targets"] = [rna(t) for t in c.targets]
    return out


def object_settings(obj):
    return {
        "name": clean(obj.name),
        "parent": clean(obj.parent.name) if obj.parent else None,
        "matrix_world": _round(list(map(list, obj.matrix_world))),
        "show_in_front": obj.show_in_front,
        "display_type": obj.display_type,
        "hide_viewport": obj.hide_viewport,
        "hide_render": obj.hide_render,
        "collections": sorted(clean(c.name) for c in obj.users_collection),
        "properties": custom_properties(obj),
    }


# --- drivers -------------------------------------------------------------------------------

def drivers_of(obj):
    """Every driver on `obj`, its data and its shape keys, by owner and path."""
    out = {}
    owners = [("object", obj)]
    data = getattr(obj, "data", None)
    if data is not None:
        owners.append(("data", data))
        keys = getattr(data, "shape_keys", None)
        if keys is not None:
            owners.append(("shape_keys", keys))
    for label, owner in owners:
        anim = owner.animation_data
        if anim is None:
            continue
        for fcurve in anim.drivers:
            out[f"{label}:{clean(fcurve.data_path)}[{fcurve.array_index}]"] = driver(fcurve)
    return out


def driver(fcurve):
    d = fcurve.driver
    return {
        "type": d.type,
        "expression": clean(d.expression),
        "use_self": d.use_self,
        "variables": [{"name": v.name, "type": v.type, "targets": [rna(t) for t in v.targets]} for v in d.variables],
        "modifiers": [rna(m, skip={"active", "show_expanded"}) for m in fcurve.modifiers],
        "keyframes": [_round(list(k.co)) for k in fcurve.keyframe_points],
        "mute": fcurve.mute,
    }


# --- meshes, widgets, collections ----------------------------------------------------------

def mesh(obj):
    keys = obj.data.shape_keys
    return {
        "parent": clean(obj.parent.name) if obj.parent else None,
        "parent_type": obj.parent_type,
        "parent_bone": clean(obj.parent_bone),
        "matrix_parent_inverse": _round(list(map(list, obj.matrix_parent_inverse))),
        "modifiers": [rna(m, skip={"is_active", "show_expanded", "is_override_data"}) for m in obj.modifiers],
        "vertex_groups": [clean(g.name) for g in obj.vertex_groups],
        "weights": weights(obj),
        "shape_keys": [shape_key(k) for k in keys.key_blocks] if keys else [],
    }


def weights(obj):
    """A hash of each vertex group's weights."""
    by_group = {g.index: [] for g in obj.vertex_groups}
    for v in obj.data.vertices:
        for g in v.groups:
            by_group[g.group].append((v.index, round(g.weight, DIGITS)))
    return {clean(g.name): _hash(by_group[g.index]) for g in obj.vertex_groups}


def shape_key(key):
    co = [0.0] * (len(key.data) * 3)
    key.data.foreach_get("co", co)
    return {
        "name": clean(key.name),
        "value": round(key.value, DIGITS),
        "slider_min": round(key.slider_min, DIGITS),
        "slider_max": round(key.slider_max, DIGITS),
        "mute": key.mute,
        "relative_key": clean(key.relative_key.name),
        "vertex_group": clean(key.vertex_group),
        "positions": _hash(_round(co)),
    }


def widgets(ch):
    """The objects in the Character's collections that aren't Parts: the rig's widgets."""
    parts = set(ch.parts())
    out = {}
    for obj in sorted(ch.collection.all_objects, key=lambda o: o.name):
        if obj in parts or obj.type == "ARMATURE":
            continue
        entry = {"type": obj.type, "parent": clean(obj.parent.name) if obj.parent else None,
                 "matrix_world": _round(list(map(list, obj.matrix_world))),
                 "collections": sorted(clean(c.name) for c in obj.users_collection)}
        if obj.type == "MESH":
            co = [0.0] * (len(obj.data.vertices) * 3)
            obj.data.vertices.foreach_get("co", co)
            entry["vertices"] = _hash(_round(co))
            entry["edges"] = _hash([tuple(e.vertices) for e in obj.data.edges])
            entry["faces"] = _hash([tuple(p.vertices) for p in obj.data.polygons])
        out[clean(obj.name)] = entry
    return out


def collection_tree(collection, layer_root):
    layer = _layer(layer_root, collection)
    return {
        "objects": sorted(clean(o.name) for o in collection.objects),
        "hide_viewport": collection.hide_viewport,
        "hide_render": collection.hide_render,
        "exclude": layer.exclude if layer else None,
        "children": {clean(c.name): collection_tree(c, layer_root) for c in collection.children},
    }


def _layer(layer, collection):
    if layer.collection == collection:
        return layer
    for child in layer.children:
        found = _layer(child, collection)
        if found is not None:
            return found
    return None


def hook_log(path):
    """The Hook's log lines, without their timestamps."""
    if not path or not os.path.exists(path):
        return []
    tag = f"[hook {HOOK}] "  # the source the pipeline gives a Hook's lines (pipeline/run.py)
    lines = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if tag in line:
                level, _, message = line.split("s ", 1)[1].partition(tag)
                lines.append(f"{level.strip()} {clean(message.rstrip())}")
    return lines


# --- RNA -----------------------------------------------------------------------------------

def _names(struct):
    return [p.identifier for p in struct.bl_rna.properties if p.identifier not in SKIPPED]


def rna(struct, skip=(), depth=DEPTH):
    """Every RNA property of `struct`, as plain JSON."""
    return {name: value(struct, name, depth) for name in _names(struct) if name not in skip}


def value(struct, name, depth=DEPTH):
    prop = struct.bl_rna.properties[name]
    try:
        v = getattr(struct, name)
    except (AttributeError, RuntimeError) as ex:
        return f"<unreadable: {type(ex).__name__}>"
    if prop.type == "POINTER":
        return _pointer(v, depth)
    if prop.type == "COLLECTION":
        items = list(v)
        if all(hasattr(i, "name") and isinstance(i.name, str) for i in items):
            return [clean(i.name) for i in items]
        return [rna(i, depth=depth - 1) for i in items] if depth > 0 else len(items)
    if prop.type == "ENUM" and getattr(prop, "is_enum_flag", False):
        return sorted(v)
    if prop.type == "STRING":
        return clean(v)
    if getattr(prop, "array_length", 0) or getattr(prop, "is_array", False):
        try:
            return _round(_plainlist(v))
        except TypeError:
            pass
    return _round(v)


def _pointer(v, depth):
    if v is None:
        return None
    if isinstance(v, bpy.types.ID):
        return clean(v.name)
    name = getattr(v, "name", None)
    if isinstance(name, str):
        return clean(name)
    return rna(v, depth=depth - 1) if depth > 0 else None


def _plainlist(v):
    out = []
    for item in v:
        out.append(_plainlist(item) if hasattr(item, "__iter__") and not isinstance(item, str) else item)
    return out


def custom_properties(idblock):
    out = {}
    for key in idblock.keys():
        if key.startswith("_"):
            continue
        entry = {"value": _round(_plain(idblock[key]))}
        try:
            entry["ui"] = _round(_plain(idblock.id_properties_ui(key).as_dict()))
        except TypeError:
            pass
        out[clean(key)] = entry
    return out


def _plain(v):
    if isinstance(v, str):
        return clean(v)
    if hasattr(v, "to_dict"):
        return {clean(k): _plain(x) for k, x in v.to_dict().items()}
    if hasattr(v, "to_list"):
        return [_plain(x) for x in v.to_list()]
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {clean(k): _plain(x) for k, x in v.items()}
    if isinstance(v, bpy.types.ID):
        return clean(v.name)
    return v


def _round(v):
    if isinstance(v, float):
        return round(v, DIGITS) + 0.0  # + 0.0: no -0.0
    if isinstance(v, dict):
        return {k: _round(x) for k, x in v.items()}
    if isinstance(v, (set, frozenset)):
        return sorted(v)
    if isinstance(v, (str, bool, int)) or v is None:
        return v
    try:  # lists, bpy arrays, mathutils types (a Matrix iterates over its rows)
        items = list(v)
    except TypeError:
        raise TypeError(f"Can't record a {type(v).__name__}") from None
    return [_round(x) for x in items]


def _cleaned(data):
    """`data` with the names known only after the rig was generated replaced as well."""
    return json.loads(clean(json.dumps(data, ensure_ascii=False)))


def _hash(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _raise(ex):
    raise ex


try:
    main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    sys.exit(1)
