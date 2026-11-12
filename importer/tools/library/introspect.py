"""Reads Blender datablocks into plain data (dicts, lists, numbers, strings), for the library's
fingerprint and its node decompiler (docs/design/library-from-code.md).

Runs inside Blender. `rna(struct)` walks a struct's RNA properties generically, so a property a
future Blender adds is read without a change here; the few properties a generic walk can't read
usefully (pointers to other datablocks, socket collections, curves) are read by the functions below.
"""

from __future__ import annotations

import bpy

DIGITS = 6

# Properties every struct has, or that Blender derives, recomputes or only uses for drawing.
_ALWAYS_SKIP = {"rna_type", "bl_rna", "original", "users", "session_uid", "is_evaluated", "tag",
                "is_runtime_data", "is_missing", "is_embedded_data", "is_editmode", "use_extra_user",
                "is_library_indirect", "library", "library_weak_reference", "override_library",
                "asset_data", "preview", "id_type", "name_full", "is_dirty", "bindcode",
                "select", "dimensions", "internal_links", "inputs", "outputs", "interface",
                "nodes", "links", "animation_data", "node_tree", "image", "parent", "is_linked",
                "links", "is_unavailable", "is_icon_visible", "is_inactive", "location_absolute",
                "is_multi_input", "is_output", "is_panel_toggle", "show_expanded", "warning_propagation",
                "view_center", "is_local_override", "active_index", "active_item", "persistent_uid", "frame_current"}


def num(value):
    if isinstance(value, float):
        r = round(value, DIGITS)
        return 0.0 if r == 0 else r
    return value


def value(v):
    """A property value as plain data; datablocks by name."""
    if isinstance(v, bpy.types.ID):
        return {"id": type(v).__name__, "name": v.name}
    if isinstance(v, (str, bool, int, float)) or v is None:
        return num(v)
    if isinstance(v, (set, frozenset)):
        return sorted(v)
    try:
        return [value(x) for x in v]
    except TypeError:
        return repr(v)


def rna(struct, skip=(), depth=2):
    """Every RNA property of `struct` as plain data. Pointers to non-ID structs recurse `depth` levels;
    collections of structs become lists. Read-only values are included (they still describe the data)."""
    out = {}
    for prop in struct.bl_rna.properties:
        name = prop.identifier
        if name in _ALWAYS_SKIP or name in skip:
            continue
        try:
            v = getattr(struct, name)
        except Exception:  # noqa: BLE001 - some properties raise outside their context
            continue
        if prop.type == "POINTER":
            if v is None or isinstance(v, bpy.types.ID):
                out[name] = value(v)
            elif depth > 0:
                out[name] = rna(v, depth=depth - 1)
        elif prop.type == "COLLECTION":
            if depth > 0:
                out[name] = [rna(x, depth=depth - 1) if not isinstance(x, bpy.types.ID) else value(x) for x in v]
        else:
            out[name] = value(v)
    return out


# --- node trees ---------------------------------------------------------------------------

# Nodes whose sockets come from a group interface: Blender numbers their identifiers itself
# (`Socket_3`, or `Input_3` in older files) and they can't be set, so they are compared by position.
# A Menu Switch's item sockets are numbered from its items' own ids, which can't be set either.
GROUP_LIKE = {"NodeGroupInput", "NodeGroupOutput", "ShaderNodeGroup", "GeometryNodeGroup", "GeometryNodeMenuSwitch"}


def socket(s):
    group_like = s.node.bl_idname in GROUP_LIKE
    out = {"identifier": "~" if group_like else s.identifier, "name": s.name, "bl_idname": s.bl_idname,
           "hide": s.hide, "enabled": s.enabled, "hide_value": s.hide_value}
    # A Group Input or Output node's own socket values do nothing (the caller's are used), and older
    # files hold stale ones there.
    if hasattr(s, "default_value") and s.node.bl_idname not in ("NodeGroupInput", "NodeGroupOutput"):
        out["default_value"] = value(s.default_value)
    return out


def interface_item(item):
    out = rna(item, skip={"parent", "position", "index", "identifier"}, depth=0)
    out["parent"] = item.parent.name if item.parent and item.parent.parent else None
    return out


def node(n):
    skip = {"color_ramp", "mapping", "texture_mapping", "color_mapping", "image_user"}
    if n.bl_idname == "NodeReroute":
        skip.add("width")  # reroutes draw at a fixed size; older files hold any width
    out = rna(n, skip=skip, depth=1)
    out["parent"] = n.parent.name if n.parent else None
    out["node_tree"] = n.node_tree.name if getattr(n, "node_tree", None) else None
    out["image"] = n.image.name if getattr(n, "image", None) else None
    out["inputs"] = [socket(s) for s in n.inputs]
    out["outputs"] = [socket(s) for s in n.outputs]
    if getattr(n, "color_ramp", None) is not None:
        out["color_ramp"] = color_ramp(n.color_ramp)
    if getattr(n, "enum_items", None) is not None:
        out["enum_items"] = [[e.name, e.description] for e in n.enum_items]
    if getattr(n, "mapping", None) is not None:
        out["mapping"] = curve_mapping(n.mapping)
    for name in ("texture_mapping", "color_mapping", "image_user"):
        if getattr(n, name, None) is not None:
            out[name] = rna(getattr(n, name), depth=1)
    return out


def color_ramp(ramp):
    return {"color_mode": ramp.color_mode, "interpolation": ramp.interpolation,
            "hue_interpolation": ramp.hue_interpolation,
            "elements": [{"position": num(e.position), "color": value(e.color)} for e in ramp.elements]}


def curve_mapping(m):
    return {"extend": m.extend, "use_clip": m.use_clip, "clip_min_x": num(m.clip_min_x),
            "clip_min_y": num(m.clip_min_y), "clip_max_x": num(m.clip_max_x), "clip_max_y": num(m.clip_max_y),
            "black_level": value(m.black_level), "white_level": value(m.white_level), "tone": m.tone,
            "curves": [{"points": [{"location": value(p.location), "handle_type": p.handle_type}
                                   for p in c.points]} for c in m.curves]}


def socket_index(s):
    sockets = s.node.outputs if s.is_output else s.node.inputs
    return next(i for i, x in enumerate(sockets) if x == s)


def link(l):
    """A link by node names and socket positions (identifiers renumber, see GROUP_LIKE)."""
    return [l.from_node.name, socket_index(l.from_socket), l.from_socket.name, l.to_node.name,
            socket_index(l.to_socket), l.to_socket.name, l.is_muted, l.is_valid, l.multi_input_sort_id]


def drivers(id_data):
    ad = id_data.animation_data
    if ad is None:
        return []
    out = []
    for fc in ad.drivers:
        d = fc.driver
        out.append({"data_path": fc.data_path, "index": fc.array_index, "type": d.type,
                    "expression": d.expression, "use_self": d.use_self,
                    "variables": [{"name": v.name, "type": v.type, "targets": [
                        {"id_type": t.id_type, "id": t.id.name if t.id else None, "data_path": t.data_path,
                         "bone_target": t.bone_target, "transform_type": t.transform_type,
                         "transform_space": t.transform_space, "rotation_mode": t.rotation_mode}
                        for t in list(v.targets)[:{"SINGLE_PROP": 1, "TRANSFORMS": 1, "CONTEXT_PROP": 1}.get(v.type, 2)]]}
                        for v in d.variables],
                    "modifiers": len(fc.modifiers), "keyframes": len(fc.keyframe_points)})
    return out


def tree(t):
    return {
        "interface": [interface_item(i) for i in t.interface.items_tree] if hasattr(t, "interface") else [],
        "nodes": {n.name: node(n) for n in t.nodes},
        "links": [link(l) for l in t.links],
        "drivers": drivers(t),
    }


def custom_props(id_data):
    return {k: value(id_data[k]) for k in id_data.keys()}


# --- differences from a fresh struct, for the exporters ----------------------------------

def plain(v):
    """A property value as plain Python: datablocks stay datablocks, arrays become tuples."""
    if isinstance(v, bpy.types.ID) or v is None or isinstance(v, (str, bool, int, float)):
        return v
    if isinstance(v, (set, frozenset)):
        return set(v)
    try:
        return tuple(plain(x) for x in v)
    except TypeError:
        return v


def same(a, b):
    if isinstance(a, bpy.types.ID) or isinstance(b, bpy.types.ID):
        return a == b
    if isinstance(a, (str, bool, int, float)) or a is None:
        return a == b
    if isinstance(a, (set, frozenset)):
        return set(a) == set(b)
    try:
        la, lb = list(a), list(b)
    except TypeError:
        return a == b
    return len(la) == len(lb) and all(same(x, y) for x, y in zip(la, lb))


# Runtime state an image user keeps; never part of a datablock's design.
_DIFF_ALWAYS_SKIP = {"frame_current"}


def diff(struct, fresh, skip, depth=1):
    """The writable properties of `struct` that differ from `fresh`, as {name: source}; nested
    structs as nested dicts."""
    out = {}
    for prop in struct.bl_rna.properties:
        name = prop.identifier
        if name in skip or name in _DIFF_ALWAYS_SKIP or name.startswith("bl_"):
            continue
        try:
            v = getattr(struct, name)
            f = getattr(fresh, name) if fresh is not None else None
        except Exception:  # noqa: BLE001
            continue
        if prop.type == "POINTER":
            if isinstance(v, bpy.types.ID) or v is None:
                if not prop.is_readonly and not same(v, f):
                    out[name] = plain(v)
            elif depth > 0 and v is not None:
                nested = diff(v, f, skip=set(), depth=depth - 1)
                if nested:
                    out[name] = nested
            continue
        if prop.type == "COLLECTION" or prop.is_readonly:
            continue
        if not same(v, f):
            out[name] = plain(v)
    return out


