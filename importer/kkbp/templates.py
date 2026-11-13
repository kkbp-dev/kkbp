"""Material Templates in the user's file (docs/design/material-template.md, "Interface").

    templates.apply(ch, blender_material, bundle_material)  # pick, append/copy, set textures + parameters, tag
    templates.param(material, "light_alpha")                # the socket for a named parameter
    templates.texture(material, "main", variant="light")    # the image node for a Role
    templates.swap(material, "cycles")                      # used by the convert-shaders Hook

Everything goes through the Template Descriptions in library/, so no other code names a node or a
socket. Templates are appended from library.blend, never linked; each node group is appended once
per file and shared by every material and every Character.
"""

from __future__ import annotations

import logging

import bpy

from . import appending, library, profiles
from .character import KEY

log = logging.getLogger("kkbp")

TEMPLATE = "kkbp_template"  # on a template material in the file, and on every material made from it
PATTERNS = "kkbp_patterns"  # on a material: its pattern slot's patterns, in choice order
VARIANT = "kkbp_variant"  # on a material whose shader `swap` replaced: the variant


class TemplateError(Exception):
    pass


# --- making materials ----------------------------------------------------------------------

def apply(ch, blender_material, bundle_material, *, pack: bool = True, warn=None):
    """Replaces `blender_material` (the glTF placeholder) with a copy of the template its Template
    Set picks for `bundle_material`, with the bundle's textures and parameter values, tagged with the
    Character's Key and the material's Id. Returns the new material."""
    warn = warn or log.warning
    profile = profiles.get(ch.game)
    textures = [(t, _slot(profile, t)) for t in bundle_material.textures]
    present = [slot for t, slot in textures if slot and t.pattern is None]
    template, row, values = library.choose(profile.template_set, bundle_material.role, bundle_material.blend_mode,
                                           present)
    mat = _template_material(template.name).copy()
    mat.use_fake_user = False
    mat.name = bundle_material.id
    mat[TEMPLATE] = template.name
    ch.tag_material(mat, bundle_material.id, bundle_material.role)
    if blender_material is not None:
        blender_material.user_remap(mat)
        if blender_material.users == 0:
            bpy.data.materials.remove(blender_material)
            mat.name = bundle_material.id  # the placeholder had the name until now

    emblem = "emblem" in (bundle_material.shader or "").rpartition("/")[2]
    for texture, slot in textures:
        if texture.pattern is None and slot in template.textures:
            set_texture(ch, mat, slot, texture, owner=bundle_material.id, pack=pack)
            if emblem:  # drawn once: it doesn't repeat over the clothes (issue 72)
                texture_node(mat, slot).extension = "CLIP"
    if template.patterns:
        _set_patterns(ch, mat, template, [t for t, slot in textures if t.pattern and slot == template.patterns.slot],
                      bundle_material.id, pack, warn)
    for name, value in values.items():
        param(mat, name).default_value = value
    if row.render_method:
        mat.surface_render_method = row.render_method
    if row.transparent_shadow is not None:
        mat.use_transparent_shadow = row.transparent_shadow
    return mat


def set_texture(ch, material, slot: str, texture, *, owner: str | None = None, pack: bool = True) -> bool:
    """Puts a bundle texture into the template's image node for `slot`, with its offset and scale.
    False if the material's template has no such slot."""
    node = texture_node(material, slot)
    if node is None:
        return False
    owner = owner or material.get("kkbp_id", material.name)
    node.image = _image(ch, texture, f"{owner} {slot}", pack)
    node.texture_mapping.translation[:2] = texture.offset
    node.texture_mapping.scale[:2] = texture.scale
    return True


def slot_of(ch, texture) -> str | None:
    """The template slot a bundle texture goes to: its Role and Variant, or the Game Profile's slot
    for its Raw Property, or None."""
    return _slot(profiles.get(ch.game), texture)


def _slot(profile, texture):
    if texture.role is not None:
        return library.slot(texture.role, texture.variant)
    return profile.raw_textures.get(texture.raw)


def _set_patterns(ch, mat, template, textures, owner, pack, warn):
    patterns = template.patterns
    names = []
    if patterns.nodes:
        if len(textures) > len(patterns.nodes):
            warn(f"{owner}: the {template.name} template shows {len(patterns.nodes)} {patterns.slot} patterns; "
                 f"{', '.join(t.pattern for t in textures[len(patterns.nodes):])} are left out")
        for node_name, texture in zip(patterns.nodes, textures):
            node = mat.node_tree.nodes[node_name]
            node.image = _image(ch, texture, f"{owner} {patterns.slot} {texture.pattern}", pack)
            names.append(texture.pattern)
    else:
        names = _build_chain(ch, mat, template, textures, owner, pack)
    mat[PATTERNS] = names
    param(mat, patterns.choice).default_value = patterns.off


def _build_chain(ch, mat, template, textures, owner, pack):
    """One uv group, image and pick group per pattern, picked by the choice param."""
    patterns, chain = template.patterns, template.patterns.chain
    sockets = chain.sockets
    tree = mat.node_tree
    uv_group, pick_group = (_library_group(n) for n in (chain.uv_group, chain.pick_group))
    frame, choice = param(mat, chain.frame), param(mat, patterns.choice)
    output = tree.nodes[chain.output]
    previous = None
    names = []
    for i, texture in enumerate(textures):
        x, y = -600.0, -250.0 * i
        uv = tree.nodes.new("ShaderNodeGroup")
        uv.node_tree = uv_group
        uv.name = uv.label = f"{patterns.slot}.uv.{i}"
        uv.location = (x - 450, y)
        image = tree.nodes.new("ShaderNodeTexImage")
        image.name = image.label = f"tex.{patterns.slot}.{i}"
        image.extension = "CLIP"
        image.image = _image(ch, texture, f"{owner} {patterns.slot} {texture.pattern}", pack)
        image.location = (x - 250, y)
        pick = tree.nodes.new("ShaderNodeGroup")
        pick.node_tree = pick_group
        pick.name = pick.label = f"{patterns.slot}.pick.{i}"
        pick.location = (x + 50, y)
        tree.links.new(frame, uv.inputs[sockets["frame"]])
        tree.links.new(uv.outputs[sockets["vector"]], image.inputs["Vector"])
        tree.links.new(choice, pick.inputs[sockets["choice"]])
        pick.inputs[sockets["index"]].default_value = patterns.first + i
        tree.links.new(image.outputs["Color"], pick.inputs[sockets["color"]])
        tree.links.new(image.outputs["Alpha"], pick.inputs[sockets["alpha"]])
        if previous is not None:
            tree.links.new(previous.outputs[sockets["picked_color"]], pick.inputs[sockets["previous_color"]])
            tree.links.new(previous.outputs[sockets["picked_alpha"]], pick.inputs[sockets["previous_alpha"]])
        previous = pick
        names.append(texture.pattern)
    if previous is not None:
        tree.links.new(previous.outputs[sockets["picked_color"]], output.inputs[sockets["output_color"]])
        tree.links.new(previous.outputs[sockets["picked_alpha"]], output.inputs[sockets["output_alpha"]])
    return names


def _image(ch, texture, name, pack):
    """The Blender image for a bundle texture file, loaded once per Character."""
    id = f"{texture.file.parent.name}/{texture.file.name}"
    image = ch.image(id)
    if image is None:
        image = bpy.data.images.load(str(texture.file), check_existing=False)
        image.name = name
        if pack:
            image.pack()
        ch.tag_image(image, id)
    return image


# --- looking things up -----------------------------------------------------------------------

def template_of(material) -> library.Template:
    name = material.get(TEMPLATE)
    if name not in library.TEMPLATES:
        raise TemplateError(f"{material.name} wasn't made from a KKBP Material Template")
    return library.TEMPLATES[name]


def param(material, name: str):
    """The socket for the named parameter of the material's template, or of the variant `swap` put in."""
    template = template_of(material)
    params = {**template.params, **template.variant_params.get(material.get(VARIANT), {})}
    if name not in params:
        raise TemplateError(f"the {template.name} template has no parameter {name}"
                            + (f" with the {material[VARIANT]} variant" if VARIANT in material else ""))
    node_name, socket = params[name]
    node = node_at(material, node_name)
    return node.outputs[socket] if node.type in ("VALUE", "ATTRIBUTE") else node.inputs[socket]


def params(material) -> tuple[str, ...]:
    """The named parameters of the material's template, with those of the variant `swap` put in."""
    template = template_of(material)
    return tuple({**template.params, **template.variant_params.get(material.get(VARIANT), {})})


def node_at(material, path: str):
    """The node at a description's path (`textures/_CM.png`: node `_CM.png` in the group of node
    `textures`), or None."""
    tree, node = material.node_tree, None
    for name in path.split("/"):
        node = tree.nodes.get(name) if tree else None
        if node is None:
            return None
        tree = node.node_tree if node.type == "GROUP" else None
    return node


def texture(material, role: str, variant: str | None = None):
    """The image node for a Texture Role and Variant (or a raw slot name), or None."""
    return texture_node(material, library.slot(role, variant))


def texture_node(material, slot: str):
    node_name = template_of(material).textures.get(slot)
    return node_at(material, node_name) if node_name else None


def slots(material) -> tuple[str, ...]:
    """The texture slots of the material's template."""
    return tuple(template_of(material).textures)


# --- materials of their own (edit templates) -------------------------------------------------

def copy_groups(material) -> list:
    """Gives `material` its own copy of each group its template `copies` (ADR 0025), outermost
    first, and returns the copies. They are named after the material."""
    made = []
    for path in template_of(material).copies:
        node = node_at(material, path)
        node.node_tree = node.node_tree.copy()
        node.node_tree.name = f"{appending.base_name(node.node_tree.name)} {material.name}"
        node.node_tree.use_fake_user = False
        made.append(node.node_tree)
    return made


def own_groups(material) -> list:
    """The groups `copy_groups` gave `material`."""
    return [node_at(material, path).node_tree for path in template_of(material).copies]


def set_position(material, slot: str, offset, scale) -> bool:
    """Places a positioned slot (the template's `positions`) by a texture's offset and scale, in
    place of the image node's own mapping. False if the slot isn't positioned.

    The `Scale Vector` group maps uv to (uv - position / 50) * scale + 0.5, the texture's own
    transform is uv * scale + offset; they agree for position = 50 * (0.5 - offset) / scale.
    """
    path = template_of(material).positions.get(slot)
    if path is None:
        return False
    group, sockets = node_at(material, path), library.POSITION_SOCKETS
    for axis, i in (("x", 0), ("y", 1)):
        s = scale[i] or 1.0
        group.inputs[sockets[f"scale_{axis}"]].default_value = s
        group.inputs[sockets[f"position_{axis}"]].default_value = 50 * (0.5 - offset[i]) / s
    image = texture_node(material, slot)
    image.texture_mapping.translation[:2] = (0.0, 0.0)
    image.texture_mapping.scale[:2] = (1.0, 1.0)
    return True


def template_material(name: str):
    """The file's copy of library template `name` (appended on first use), to copy from."""
    return _template_material(name)


def patterns(material) -> list[str]:
    """The patterns the material's pattern slot holds, in choice order."""
    return list(material.get(PATTERNS, []))


def choice_value(material, pattern_index: int | None) -> int:
    """The choice param's value that shows the pattern at `pattern_index`, or none for None."""
    p = template_of(material).patterns
    return p.off if pattern_index is None else p.first + pattern_index


def add_picker(ch, material, labels: list[str]):
    """Adds the pattern slot's dropdown to `material`, listing `labels`: its output is the picked
    label's place in the list, from 1, or its number input while that is above 0, since Blender
    can't keyframe a dropdown (ADR 0042). Returns the group node."""
    patterns = template_of(material).patterns
    picker = patterns.picker
    group = bpy.data.node_groups.new(f"{picker.group} {ch.name}", "ShaderNodeTree")
    group[KEY] = ch.key
    group.interface.new_socket(picker.menu, in_out="INPUT", socket_type="NodeSocketMenu")
    number = group.interface.new_socket(picker.number, in_out="INPUT", socket_type="NodeSocketInt")
    number.min_value, number.max_value = 0, len(labels)
    number.description = "Picks by place in the list while above 0, for keyframes; at 0 the dropdown picks"
    group.interface.new_socket(picker.output, in_out="OUTPUT", socket_type="NodeSocketFloat")
    nodes, links = group.nodes, group.links
    inputs, outputs = nodes.new("NodeGroupInput"), nodes.new("NodeGroupOutput")
    inputs.location, outputs.location = (-700.0, 0.0), (300.0, 0.0)
    menu = nodes.new("GeometryNodeMenuSwitch")
    menu.data_type = "FLOAT"
    menu.location = (-400.0, 150.0)
    # Drivers read a dropdown as its item's number, given in the order the items were made, from 0.
    # The node comes with two items; renaming them keeps the numbers in the list's order (ADR 0042).
    items = menu.enum_items
    while len(items) > len(labels):
        items.remove(items[len(items) - 1])
    for i, name in enumerate(labels):
        if i < len(items):
            items[i].name = name
        else:
            items.new(name)
    for i in range(len(labels)):
        menu.inputs[i + 1].default_value = i + 1
    unset = nodes.new("ShaderNodeMath")
    unset.operation = "LESS_THAN"
    unset.location = (-400.0, -150.0)
    unset.inputs[1].default_value = 0.5
    pick = nodes.new("ShaderNodeMath")
    pick.operation = "MULTIPLY_ADD"  # menu * (number is 0) + number
    pick.location = (0.0, 0.0)
    links.new(inputs.outputs[picker.menu], menu.inputs[0])
    links.new(inputs.outputs[picker.number], unset.inputs[0])
    links.new(menu.outputs[0], pick.inputs[0])
    links.new(unset.outputs[0], pick.inputs[1])
    links.new(inputs.outputs[picker.number], pick.inputs[2])
    links.new(pick.outputs[0], outputs.inputs[picker.output])

    node = material.node_tree.nodes.new("ShaderNodeGroup")
    node.node_tree = group
    node.name = picker.node
    node.label = picker.group
    output = material.node_tree.nodes[patterns.chain.output]
    node.location = (output.location.x - 1600.0, output.location.y + 300.0)
    node.width = 220.0
    node.inputs[picker.menu].default_value = labels[0]
    return node


def picker(material):
    """The material's dropdown (`add_picker`), or None."""
    if material.get(TEMPLATE) is None:
        return None
    p = template_of(material).patterns
    if p is None or p.picker is None:
        return None
    node = material.node_tree.nodes.get(p.picker.node)
    return node if node is not None and node.type == "GROUP" else None


def picker_paths(material) -> tuple[str, str]:
    """Data paths from the material to its dropdown's menu and number values, for drivers."""
    p = template_of(material).patterns.picker
    node = f'node_tree.nodes["{p.node}"]'
    return (f'{node}.inputs["{p.menu}"].default_value', f'{node}.inputs["{p.number}"].default_value')


def pick_by(material, picks, *, from_picker: bool):
    """Replaces the chained pattern slot's pick nodes with one per (pattern index, choice) in
    `picks`, which shows that pattern while the choice is that number, so patterns can repeat. The
    choice comes from the material's dropdown if `from_picker`, else from its choice param. With no
    picks the slot draws nothing."""
    patterns = template_of(material).patterns
    chain, sockets = patterns.chain, patterns.chain.sockets
    tree = material.node_tree
    for node in [n for n in tree.nodes if n.name.startswith(f"{patterns.slot}.pick.")]:
        tree.nodes.remove(node)
    output = tree.nodes[chain.output]
    if from_picker:
        choice = tree.nodes[patterns.picker.node].outputs[patterns.picker.output]
        # Linked into the output only so the material panel lists the dropdown under Surface.
        tree.links.new(choice, output.inputs[sockets["output_picked"]])
    else:
        choice = param(material, patterns.choice)
    pick_group = _library_group(chain.pick_group)
    previous = None
    for i, (pattern, number) in enumerate(picks):
        image = tree.nodes[f"tex.{patterns.slot}.{pattern}"]
        pick = tree.nodes.new("ShaderNodeGroup")
        pick.node_tree = pick_group
        pick.name = pick.label = f"{patterns.slot}.pick.{i}"
        pick.location = (image.location.x + 300.0, -250.0 * i)
        tree.links.new(choice, pick.inputs[sockets["choice"]])
        pick.inputs[sockets["index"]].default_value = number
        tree.links.new(image.outputs["Color"], pick.inputs[sockets["color"]])
        tree.links.new(image.outputs["Alpha"], pick.inputs[sockets["alpha"]])
        if previous is not None:
            tree.links.new(previous.outputs[sockets["picked_color"]], pick.inputs[sockets["previous_color"]])
            tree.links.new(previous.outputs[sockets["picked_alpha"]], pick.inputs[sockets["previous_alpha"]])
        previous = pick
    if previous is not None:
        tree.links.new(previous.outputs[sockets["picked_color"]], output.inputs[sockets["output_color"]])
        tree.links.new(previous.outputs[sockets["picked_alpha"]], output.inputs[sockets["output_alpha"]])
    else:
        output.inputs[sockets["output_alpha"]].default_value = 0.0


def pattern_param(material, pattern_index: int, name: str):
    """The socket for a per-pattern parameter (such as `angle_speed`) of a chained pattern slot."""
    p = template_of(material).patterns
    if not p or not p.chain or name not in p.chain.pattern_params:
        raise TemplateError(f"{material.name}'s template has no pattern parameter {name}")
    return material.node_tree.nodes[f"{p.slot}.uv.{pattern_index}"].inputs[p.chain.pattern_params[name]]


# --- swapping shaders ------------------------------------------------------------------------

def swap(material, variant: str) -> list[str]:
    """Puts the template's `variant` group (such as `cycles`) in place of its shader group. Returns
    the shader's linked inputs the variant lacks, whose links went (the template's `variant_drops`)."""
    template = template_of(material)
    if variant not in template.variants:
        raise TemplateError(f"the {template.name} template has no {variant} variant")
    tree = material.node_tree
    node = tree.nodes[template.shader]
    # Blender keeps a group node's links across a swap by socket identifier, which each group in
    # library.blend numbers on its own (ADR 0040), so a variant doesn't share .KK's; they are put back by name.
    inputs = [(l.from_socket, l.to_socket.name) for l in tree.links if l.to_node == node]
    outputs = [(l.from_socket.name, l.to_socket) for l in tree.links if l.from_node == node]
    node.node_tree = _library_group(template.variants[variant])
    material[VARIANT] = variant
    for from_socket, name in inputs:
        socket = node.inputs.get(name)
        if socket is not None and not socket.is_linked:
            tree.links.new(from_socket, socket)
    for name, to_socket in outputs:
        socket = node.outputs.get(name)
        if socket is not None and not any(l.from_socket == socket and l.to_socket == to_socket for l in tree.links):
            tree.links.new(socket, to_socket)
    return sorted({name for _, name in inputs} - {s.name for s in node.inputs})


def variant(material) -> str | None:
    """The variant `swap` put into the material, or None."""
    return material.get(VARIANT)


def extra(name: str):
    """A library datablock that isn't part of a template (library.EXTRAS), appended once."""
    kind, datablock = library.EXTRAS[name]
    found = appending.existing(kind, datablock)
    if found is None:
        _append(kind, datablock)
        found = appending.existing(kind, datablock)
    return found


# --- the library -----------------------------------------------------------------------------

def _template_material(name):
    """The file's copy of library template `name`, appended on first use."""
    found = [m for m in bpy.data.materials if m.get(TEMPLATE) == name and KEY not in m and m.library is None]
    if found:
        return found[0]
    added = _append("materials", name)
    mat = next(m for m in added if appending.base_name(m.name) == name)
    mat[TEMPLATE] = name
    mat.use_fake_user = True  # kept for the next material, the next import and `swap`
    for group_name in library.TEMPLATES[name].groups:
        _library_group(group_name)
    return mat


def _library_group(name):
    """The file's copy of library node group `name`, appended once."""
    found = appending.existing("node_groups", name)
    if found is None:
        _append("node_groups", name)
        found = appending.existing("node_groups", name)
    return found


def _append(kind, name):
    """Appends one material or node group from library.blend and returns what the file gained.
    Node groups and images the file already has from the library are shared by every material and
    Character (appending.py)."""
    try:
        return appending.append(library.LIBRARY, kind, name, library.VERSION_PROP)
    except appending.AppendError as ex:
        raise TemplateError(str(ex)) from None
