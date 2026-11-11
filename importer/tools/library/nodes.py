"""The small builder the library's node modules call (docs/design/library-from-code.md).

Each module in `groups/` and `materials/` has a `build(lib)` function that makes its datablock with
these helpers. They exist so a module reads like the graph: one line per socket, node and link.

- Sockets of ordinary nodes are named by identifier (`A_Color`, `Factor_Float`), which is unique where
  socket names aren't. Sockets of group nodes and group input/output nodes are named by the interface
  socket's name, or by position (an int) where a name repeats.
- `props` are set before sockets and links, and the enums that decide which sockets a node has
  (`data_type`, `operation`, `mode`, ...) before the rest.
"""

from __future__ import annotations

import bpy

# Set first: they change which sockets or other properties a node or socket has. `default_value`
# goes last, after the `min_value` and `max_value` that would clamp it.
_FIRST = ("node_tree", "data_type", "domain", "input_type", "mode", "operation", "blend_type", "factor_mode",
          "distribution", "component", "rotation_type", "vector_type", "space", "feature", "socket_type",
          "subtype", "min_value", "max_value")
_LAST = ("default_value",)


def _order(name):
    if name in _FIRST:
        return (0, _FIRST.index(name))
    return (2, 0) if name in _LAST else (1, 0)


def set_props(target, props):
    """Sets each property; a dict sets the properties of a nested struct (`texture_mapping`)."""
    for name in sorted(props, key=_order):
        value = props[name]
        if isinstance(value, dict):
            set_props(getattr(target, name), value)
        else:
            setattr(target, name, value)


class Tree:
    """A node tree being built: a group's or a material's."""

    def __init__(self, lib, tree, owner):
        self.lib = lib
        self.tree = tree
        self.owner = owner  # the group or the material, for drivers and custom properties

    # --- interface ---------------------------------------------------------------------

    def panel(self, name, parent=None, **props):
        item = self.tree.interface.new_panel(name)
        set_props(item, props)
        if parent is not None:
            self._move(item, parent)
        return item

    def socket(self, in_out, name, socket_type, parent=None, **props):
        item = self.tree.interface.new_socket(name=name, in_out=in_out, socket_type=socket_type)
        if socket_type == "NodeSocketMenu" and "default_value" in props:
            # A menu's items come from the Menu Switch it is linked to, so its value waits for the links.
            value = props.pop("default_value")
            self.lib.later(lambda: setattr(item, "default_value", value))
        set_props(item, props)
        if parent is not None:
            self._move(item, parent)
        return item

    def _move(self, item, parent):
        panel = next(i for i in self.tree.interface.items_tree if i.item_type == "PANEL" and i.name == parent)
        self.tree.interface.move_to_parent(item, panel, len(panel.interface_items))

    # --- nodes -------------------------------------------------------------------------

    def node(self, idname, name, *, parent=None, props=None, enum_items=None, inputs=None, outputs=None,
             hide_inputs=(), hide_outputs=(), color_ramp=None, mapping=None):
        """A node. `props` can hold datablocks (`lib.group(...)`, `lib.image(...)`) and nested
        structs as dicts; `parent` (a frame's name) is set before `props`, so `location` is the
        node's own, as Blender stores it."""
        n = self.tree.nodes.new(idname)
        n.name = name
        if n.name != name:
            raise RuntimeError(f"node name {name!r} became {n.name!r} in {self.tree.name}")
        if parent is not None:
            n.parent = self.tree.nodes[parent]
        set_props(n, props or {})
        if enum_items is not None:  # a Menu Switch's menu: (name, description) per item
            n.enum_items.clear()
            for item_name, description in enum_items:
                n.enum_items.new(item_name).description = description
        for key, value in (inputs or {}).items():
            s = _socket(n.inputs, key)
            if s.type == "MENU":
                self.lib.later(lambda s=s, value=value: setattr(s, "default_value", value))
            else:
                s.default_value = value
        for key, value in (outputs or {}).items():
            _socket(n.outputs, key).default_value = value
        for key in hide_inputs:
            _socket(n.inputs, key).hide = True
        for key in hide_outputs:
            _socket(n.outputs, key).hide = True
        if color_ramp is not None:
            _set_ramp(n.color_ramp, color_ramp)
        if mapping is not None:
            _set_curve_mapping(n.mapping, mapping)
        return n

    def make(self, idname, name, location, props=None, ins=None, **kwargs):
        """A node and its inputs in one call, for hand-written groups: `ins` maps an input to a value
        or to a (node name, output) it is linked from. Returns the node's name."""
        n = self.node(idname, name, props={"location": location, **(props or {})}, **kwargs)
        for key, source in (ins or {}).items():
            if isinstance(source, tuple) and len(source) == 2 and isinstance(source[0], str):
                self.link(source[0], source[1], name, key)
            else:
                _socket(n.inputs, key).default_value = source
        return name

    def math(self, name, operation, a, b=None, c=None, location=(0, 0), clamp=False):
        """A Math node: `a`, `b`, `c` are values or (node name, output) sources. Returns (name, 'Value'),
        a source for the next node."""
        ins = {key: v for key, v in zip(("Value", "Value_001", "Value_002"), (a, b, c)) if v is not None}
        self.make("ShaderNodeMath", name, location, {"operation": operation, "use_clamp": clamp}, ins)
        return (name, "Value")

    def link(self, from_node, from_socket, to_node, to_socket, muted=False):
        a = _socket(self.tree.nodes[from_node].outputs, from_socket)
        b = _socket(self.tree.nodes[to_node].inputs, to_socket)
        link = self.tree.links.new(a, b)
        link.is_muted = muted
        return link

    # --- drivers -----------------------------------------------------------------------

    def driver(self, data_path, expression, index=-1, type="SCRIPTED", use_self=False, variables=()):
        """A driver on the tree. `variables`: (name, type, [target dicts]); a target's `id` is a
        datablock name (`id_type` defaults to OBJECT). Added when the whole file is built, since a
        target may be an object made after the tree."""
        self.lib.later(lambda: self._driver(data_path, expression, index, type, use_self, variables))

    def _driver(self, data_path, expression, index, type, use_self, variables):
        fc = self.tree.driver_add(data_path, index) if index >= 0 else self.tree.driver_add(data_path)
        d = fc.driver
        d.type = type
        d.expression = expression
        d.use_self = use_self
        for name, kind, targets in variables:
            v = d.variables.new()
            v.name = name
            v.type = kind
            for target, data in zip(v.targets, targets):
                data = dict(data)
                id_type = data.pop("id_type", "OBJECT")
                if v.type == "SINGLE_PROP":
                    target.id_type = id_type
                id_name = data.pop("id", None)
                if id_name is not None:
                    target.id = getattr(bpy.data, _ID_COLLECTIONS[id_type])[id_name]
                set_props(target, data)
        return fc


_ID_COLLECTIONS = {"OBJECT": "objects", "MATERIAL": "materials", "NODETREE": "node_groups", "MESH": "meshes",
                   "ARMATURE": "armatures", "SCENE": "scenes", "KEY": "shape_keys"}


def _socket(sockets, key):
    if isinstance(key, int):
        return sockets[key]
    found = [s for s in sockets if s.identifier == key]
    if not found:
        found = [s for s in sockets if s.name == key]
    if len(found) != 1:
        raise KeyError(f"socket {key!r}: {len(found)} matches on {sockets[0].node.name if len(sockets) else '?'}")
    return found[0]


def _set_ramp(ramp, data):
    ramp.color_mode = data["color_mode"]
    ramp.interpolation = data["interpolation"]
    ramp.hue_interpolation = data["hue_interpolation"]
    elements = data["elements"]
    while len(ramp.elements) > len(elements):
        ramp.elements.remove(ramp.elements[-1])
    while len(ramp.elements) < len(elements):
        ramp.elements.new(0.5)
    # Positions first, by setting each in order: elements stay sorted by position.
    for e, d in zip(ramp.elements, elements):
        e.position = d["position"]
    for e, d in zip(ramp.elements, elements):
        e.position = d["position"]
        e.color = d["color"]


def _set_curve_mapping(m, data):
    for key in ("extend", "use_clip", "clip_min_x", "clip_min_y", "clip_max_x", "clip_max_y",
                "black_level", "white_level", "tone"):
        setattr(m, key, data[key])
    for curve, d in zip(m.curves, data["curves"]):
        points = d["points"]
        while len(curve.points) > len(points):
            curve.points.remove(curve.points[-1])
        while len(curve.points) < len(points):
            curve.points.new(0.5, 0.5)
        for p, pd in zip(curve.points, points):
            p.location = pd["location"]
            p.handle_type = pd["handle_type"]
    m.update()
