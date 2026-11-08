"""Builds the Material Template library from the legacy KK Shader V9.blend (ADR 0018).

    blender --background --factory-startup --python importer/tools/rework_templates.py -- SOURCE OUTPUT

Run it through scripts/rework-templates.sh. SOURCE is never changed. Every difference between the
legacy file and the library is made here (docs/design/material-template.md, "The library"):

- only the Material Templates stay, plus the node groups and images the shader variants need for
  `templates.swap`; the Rigify widgets, face cards, outlines and leftovers go;
- image nodes are named for what they hold (`tex.main.light`, `tex.alpha_mask`), not for file suffixes;
- the shader groups' sockets get one naming scheme, and gain a `Hidden` input;
- per-material data (image nodes, values) sits at the top level of each material and feeds group
  inputs, so every material shares one copy of each group;
- KK's three hand-wired gag templates are replaced by one Gag template whose expressions are built
  per material (ADR 0019);
- a `.Principled` variant group is added for the convert-shaders Hook (D18): the light texture as a
  Principled BSDF, in place of the legacy option that deleted every node but the light image;
- the legacy edit templates stay as they are for the edit material tool (D38, ADR 0025), with their
  UV map nodes on the importer's UV maps and the eyebrows multiplying their texture as the game does,
  and the game's colour grade `Lut_TimeDay.png` is packed;
- every template and group carries `kkbp_template_version`.
"""

import sys
from pathlib import Path

import bpy

TEMPLATE_VERSION = 1
VERSION_PROP = "kkbp_template_version"

# Socket renames on the shader groups and their variants: old name -> new name.
SOCKETS = {
    "Force visibility?": "Force visibility",
    "Dark image": "Dark", "Dark texture": "Dark",
    "Light image": "Light", "Light texture": "Light",
    "Light image alpha": "Light alpha", "Light txture Alpha": "Light alpha",
    "Normal color": "Normal",
    "Normal detail color": "Normal detail",
    "Alphamask color": "Alpha mask", "Alphamask alpha": "Alpha mask alpha",
    "Alphamask bot color": "Alpha mask bottom", "Alphamask bot alpha": "Alpha mask bottom alpha",
    "Surface": "Shader",
    # .KK Tears and .Expression
    "Mimic in game look? (overrides below)": "Game look",
    "Use HDRI? (overrides below)": "Use HDRI",
    "Expression Choice": "Choice",
}
SHADER_GROUPS = (".KK", ".SVS")
# The groups `templates.swap` puts in place of .KK (the convert-shaders Hook's variants).
VARIANT_GROUPS = (".Cycles", ".Cycles Classic", ".Cycles no shadows", ".Eevee Mod", ".Principled")
# What the variants also bring in, kept even though no template uses them.
VARIANT_EXTRAS = {"node_groups": (".Light Rotation Catcher", ".SDF_Cel_Shader"),
                  "images": ("Template: Black", "Template: Body neck shadow")}
# Groups `templates.apply` adds to a Gag material, one set per expression.
GAG_GROUPS = (".Gag UV", ".Gag pick")

# Image nodes in the Light Dark templates: legacy name -> role name.
LIGHT_DARK_IMAGES = {
    "_light.png": "tex.main.light",
    "_dark.png": "tex.main.dark",
    "_NMP_CNV.png": "tex.normal",
    "_NMPD_CNV.png": "tex.detail_normal",
    "_AM.png": "tex.alpha_mask",
    "_AMB.png": "tex.alpha_mask_bottom",
    "perma": "tex.permalight_mask",
}
# The legacy edit templates the edit material tool copies (D38), kept as they are. Glasses and the
# lower eyeline had transparent dummy templates in legacy; they aren't editable.
EDIT_TEMPLATES = ("KK Body", "KK Face", "KK General", "KK Hair", "KK EyeL (hitomi)", "KK EyeR (hitomi)",
                  "KK Eyewhites (sirome)", "KK Eyebrows (mayuge)", "KK Nose", "KK Eyeline up", "KK Teeth (tooth)")
# UV map nodes in the edit templates' groups: (group, node) -> the importer's UV map name
# (steps/mesh.py UV_NAMES). Legacy set these on every edit, in groups every material shares.
EDIT_UV_MAPS = {
    (".Position Face", "eyeshadowuv"): "uv_eyeshadow",
    (".NSFW positioning", "nippleuv"): "uv_nipple_and_shine",
    (".NSFW positioning", "underuv"): "uv_underhair",
    (".Hair highlight positioning", "hairuv"): "uv_nipple_and_shine",
}
# The game's colour grade, which the edit material tool saturates with (D42).
LUT = "Lut_TimeDay.png"
# Custom properties other add-ons left on the legacy templates.
FOREIGN_PROPS = ("vrm_addon_extension", "mmd_material")


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    source, output = args
    bpy.ops.wm.open_mainfile(filepath=source, load_ui=False)

    strip_scene()
    principled()
    for name in SHADER_GROUPS + VARIANT_GROUPS:
        group = bpy.data.node_groups[name]
        rename_sockets(group)
        add_hidden(group)

    templates = [
        light_dark("KK Light Dark Texture", "KK Light Dark"),
        light_dark("SVS Light Dark Texture", "SVS Light Dark"),
        tears(),
        transparent(),
    ]
    templates.append(eye(templates[0]))
    templates.append(gag())
    templates += edit_templates(source)

    keep = set(templates)
    for mat in list(bpy.data.materials):
        if mat not in keep:
            bpy.data.materials.remove(mat)
    for mat in templates:
        mat.use_fake_user = True
        for prop in FOREIGN_PROPS:
            mat.pop(prop, None)
    for datablock in list(bpy.data.node_groups) + list(bpy.data.images):
        datablock.use_fake_user = False  # the legacy file kept leftovers alive this way
    # Nothing in a template uses these, so a fake user keeps them in the library.
    for name in VARIANT_GROUPS + VARIANT_EXTRAS["node_groups"] + GAG_GROUPS:
        bpy.data.node_groups[name].use_fake_user = True
    for name in VARIANT_EXTRAS["images"] + (LUT,):
        bpy.data.images[name].use_fake_user = True
    bpy.data.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

    for mat in templates:
        mat[VERSION_PROP] = TEMPLATE_VERSION
    for group in bpy.data.node_groups:
        group[VERSION_PROP] = TEMPLATE_VERSION
    bpy.ops.wm.save_as_mainfile(filepath=output, compress=True, copy=False)
    print(f"Wrote {output}: {len(templates)} templates, {len(bpy.data.node_groups)} node groups, "
          f"{len(bpy.data.images)} images")


# --- edit templates ---------------------------------------------------------------------

def edit_templates(source):
    """The legacy edit templates, with their UV map nodes on the importer's UV maps, and the LUT."""
    for (group, node), uv_map in EDIT_UV_MAPS.items():
        bpy.data.node_groups[group].nodes[node].uv_map = uv_map
    eyebrows()
    lut = bpy.data.images.load(str(Path(source).parent / LUT), check_existing=False)
    lut.name = LUT
    lut.pack()
    return [bpy.data.materials[name] for name in EDIT_TEMPLATES]


def eyebrows():
    """The game's eyebrow shader (toon_eyew) multiplies its main texture by the colour, light and dark;
    legacy's group chose between them for the light colour and ignored the texture for the dark one.
    "Use main texture color?" now multiplies both, so 0 keeps legacy's colour-only look."""
    group = bpy.data.node_groups[".KK Eyebrows"]
    light = group.nodes["Mix"]
    light.blend_type = "MULTIPLY"
    inputs = next(n for n in group.nodes if n.type == "GROUP_INPUT")
    output = next(n for n in group.nodes if n.type == "GROUP_OUTPUT")
    dark = group.nodes.new("ShaderNodeMix")
    dark.name = "Mix dark"
    dark.data_type, dark.blend_type = "RGBA", "MULTIPLY"
    dark.location = (light.location.x, light.location.y - 220)
    for link in [l for l in group.links if l.to_node == output and l.to_socket.name == "Dark colors"]:
        group.links.remove(link)
    socket = lambda sockets, identifier: next(s for s in sockets if s.identifier == identifier)  # noqa: E731
    group.links.new(inputs.outputs["Use main texture color?"], socket(dark.inputs, "Factor_Float"))
    group.links.new(inputs.outputs["Eyebrow color dark"], socket(dark.inputs, "A_Color"))
    group.links.new(inputs.outputs["Main texture"], socket(dark.inputs, "B_Color"))
    group.links.new(socket(dark.outputs, "Result_Color"), output.inputs["Dark colors"])


# --- the legacy file's other assets -----------------------------------------------------

def strip_scene():
    """Removes every object, collection and text: the Rigify widgets, the face cards and the
    leftovers in 'Collection'. Their data goes with the orphan purge."""
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for collection in list(bpy.data.collections):
        bpy.data.collections.remove(collection)
    for text in list(bpy.data.texts):
        bpy.data.texts.remove(text)


# --- shader groups ------------------------------------------------------------------------

def rename_sockets(group):
    for item in group.interface.items_tree:
        if item.item_type == "SOCKET" and item.name in SOCKETS:
            item.name = SOCKETS[item.name]


def add_hidden(group):
    """Adds a `Hidden` input that fades the group's shader to transparent (D5: expression `hides`)."""
    if "Hidden" in group.interface.items_tree:
        return
    item = group.interface.new_socket(name="Hidden", in_out="INPUT", socket_type="NodeSocketFloat")
    item.subtype = "FACTOR"
    item.min_value, item.max_value, item.default_value = 0.0, 1.0, 0.0
    out = next(n for n in group.nodes if n.type == "GROUP_OUTPUT" and n.is_active_output)
    target = out.inputs["Shader"]
    source = target.links[0].from_socket
    clear = group.nodes.new("ShaderNodeBsdfTransparent")
    clear.name = clear.label = "hidden.transparent"
    mix = group.nodes.new("ShaderNodeMixShader")
    mix.name = mix.label = "hidden.mix"
    clear.location = (out.location.x - 200, out.location.y - 150)
    mix.location = (out.location.x - 20, out.location.y)
    out.location.x += 200
    links = group.links
    links.new(source, mix.inputs[1])
    links.new(clear.outputs[0], mix.inputs[2])
    links.new(_group_input(group).outputs["Hidden"], mix.inputs[0])
    links.new(mix.outputs[0], target)


def _group_input(group):
    found = [n for n in group.nodes if n.type == "GROUP_INPUT"]
    return found[0] if found else group.nodes.new("NodeGroupInput")


def principled():
    """`.Principled`: the light texture and its alpha as a Principled BSDF. Its inputs are every input
    of .KK and .SVS, so swapping it in from either loses no link; only Light and Light alpha are used."""
    inputs = [("Force visibility", "NodeSocketInt", 0), ("Dark", "NodeSocketColor", None),
              ("Light", "NodeSocketColor", (1.0, 1.0, 1.0, 1.0)), ("Normal", "NodeSocketColor", None),
              ("Normal alpha", "NodeSocketFloat", None), ("Normal detail", "NodeSocketColor", None),
              ("Normal detail alpha", "NodeSocketFloat", None), ("Permalight mask", "NodeSocketColor", None),
              ("Alpha mask", "NodeSocketColor", None), ("Alpha mask alpha", "NodeSocketFloat", None),
              ("Alpha mask bottom", "NodeSocketColor", None), ("Alpha mask bottom alpha", "NodeSocketFloat", None),
              ("Light alpha", "NodeSocketFloat", 1.0), ("Disable permalight mask", "NodeSocketBool", None)]
    group = _new_group(".Principled", inputs, [("Shader", "NodeSocketShader")])
    bsdf = group.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (0, 0)
    group_in = _group_input(group)
    out = next(n for n in group.nodes if n.type == "GROUP_OUTPUT")
    group.links.new(group_in.outputs["Light"], bsdf.inputs["Base Color"])
    group.links.new(group_in.outputs["Light alpha"], bsdf.inputs["Alpha"])
    group.links.new(bsdf.outputs["BSDF"], out.inputs["Shader"])
    out.is_active_output = True
    return group


# --- templates ----------------------------------------------------------------------------

def light_dark(source, name):
    mat = bpy.data.materials[source]
    mat.name = name
    for old, new in LIGHT_DARK_IMAGES.items():
        node = mat.node_tree.nodes.get(old)
        if node is not None:
            node.name = new
            node.label = new
    return mat


def tears():
    """KK Tears: the tear texture moves out of .KK Tears onto the material."""
    mat = bpy.data.materials["KK Tears"]
    group = bpy.data.node_groups[".KK Tears"]
    rename_sockets(group)
    image = group.nodes["_MT_CT.png"]
    targets = [link.to_socket for link in image.outputs["Color"].links]
    item = group.interface.new_socket(name="Main", in_out="INPUT", socket_type="NodeSocketColor")
    item.default_value = (0.0, 0.0, 0.0, 1.0)
    for socket in targets:
        group.links.new(_group_input(group).outputs["Main"], socket)
    group.nodes.remove(image)
    add_hidden(group)

    nodes = mat.node_tree.nodes
    shader = nodes["textures"]
    shader.name = "shader"
    tex = nodes.new("ShaderNodeTexImage")
    tex.name = tex.label = "tex.main"
    tex.location = (shader.location.x - 320, shader.location.y)
    mat.node_tree.links.new(tex.outputs["Color"], shader.inputs["Main"])
    return mat


def transparent():
    mat = bpy.data.materials["KK Transparent"]
    mat.name = "Transparent"
    return mat


def eye(light_dark_template):
    """KK Eye: KK Light Dark with the expression overlays (cf_t_expression_*) on top. The overlay
    group no longer holds the images; the material does."""
    group = bpy.data.node_groups["Expression"]
    group.name = ".Expression"
    rename_sockets(group)
    nodes = group.nodes
    feeds = {}
    for index, image in ((1, nodes["Expression 1"]), (2, nodes["Expression 2"])):
        for output in ("Color", "Alpha"):
            item = group.interface.new_socket(name=f"{output} {index}", in_out="INPUT",
                                              socket_type="NodeSocketColor" if output == "Color" else "NodeSocketFloat")
            feeds[item.name] = [link.to_socket for link in image.outputs[output].links]
    for name, sockets in feeds.items():
        for socket in sockets:
            group.links.new(_group_input(group).outputs[name], socket)
    uv, mapping, offset = nodes["UV Map"], nodes["Mapping"], nodes["Vector Math"]
    uv_settings = (tuple(mapping.inputs["Scale"].default_value), tuple(offset.inputs[1].default_value))
    for node in (nodes["Expression 1"], nodes["Expression 2"], uv, mapping, offset):
        nodes.remove(node)

    mat = light_dark_template.copy()
    mat.name = "KK Eye"
    tree = mat.node_tree
    out = next(n for n in tree.nodes if n.type == "OUTPUT_MATERIAL")
    shader = tree.nodes["shader"]
    overlay = tree.nodes.new("ShaderNodeGroup")
    overlay.node_tree = group
    overlay.name = overlay.label = "expression"
    overlay.inputs["Choice"].default_value = 2  # no overlay until an expression picks one
    overlay.location = (out.location.x, out.location.y)
    out.location.x += 250
    tree.links.new(shader.outputs["Shader"], overlay.inputs["Shader"])
    tree.links.new(overlay.outputs["Shader"], out.inputs["Surface"])

    uv = tree.nodes.new("ShaderNodeUVMap")
    uv.name = "expression.uv"
    mapping = tree.nodes.new("ShaderNodeMapping")
    mapping.name = "expression.mapping"
    mapping.vector_type = "VECTOR"
    mapping.inputs["Scale"].default_value = uv_settings[0]
    offset = tree.nodes.new("ShaderNodeVectorMath")
    offset.name = "expression.offset"
    offset.operation = "SUBTRACT"
    offset.inputs[1].default_value = uv_settings[1]
    tree.links.new(uv.outputs["UV"], mapping.inputs["Vector"])
    tree.links.new(mapping.outputs["Vector"], offset.inputs[0])
    base = (overlay.location.x - 900, overlay.location.y - 500)
    for k, node in enumerate((uv, mapping, offset)):
        node.location = (base[0] + 200 * k, base[1])
    for slot in (1, 2):
        tex = tree.nodes.new("ShaderNodeTexImage")
        tex.name = tex.label = f"tex.expression.{slot - 1}"
        tex.extension = "CLIP"
        tex.location = (base[0] + 650, base[1] - 300 * (slot - 1))
        tree.links.new(offset.outputs["Vector"], tex.inputs["Vector"])
        tree.links.new(tex.outputs["Color"], overlay.inputs[f"Color {slot}"])
        tree.links.new(tex.outputs["Alpha"], overlay.inputs[f"Alpha {slot}"])
    return mat


def gag():
    """Gag: one template for every Game's gag eyes (ADR 0019). The material holds a frame counter,
    the expression choice and the output; `templates.apply` adds one `.Gag UV` group, image and
    `.Gag pick` group per expression the bundle gives the material."""
    _gag_uv_group()
    _gag_pick_group()
    output_group = _gag_output_group()

    mat = bpy.data.materials.new("Gag")  # a new material has its node tree already (Blender 5)
    tree = mat.node_tree
    for node in list(tree.nodes):
        tree.nodes.remove(node)
    out = tree.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    output = tree.nodes.new("ShaderNodeGroup")
    output.node_tree = output_group
    output.name = output.label = "gag.output"
    output.location = (350, 0)
    tree.links.new(output.outputs["Shader"], out.inputs["Surface"])
    frame = tree.nodes.new("ShaderNodeValue")
    frame.name = frame.label = "gag.frame"
    frame.location = (-900, 200)
    driver = frame.outputs[0].driver_add("default_value").driver
    driver.type = "SCRIPTED"
    driver.expression = "frame"
    choice = tree.nodes.new("ShaderNodeValue")
    choice.name = choice.label = "gag.choice"
    choice.outputs[0].default_value = 0.0
    choice.location = (-900, 0)
    return mat


def _new_group(name, inputs, outputs):
    if name in bpy.data.node_groups:
        bpy.data.node_groups.remove(bpy.data.node_groups[name])
    group = bpy.data.node_groups.new(name, "ShaderNodeTree")
    for socket_name, kind, default in inputs:
        item = group.interface.new_socket(name=socket_name, in_out="INPUT", socket_type=kind)
        if default is not None:
            item.default_value = default
    for socket_name, kind in outputs:
        group.interface.new_socket(name=socket_name, in_out="OUTPUT", socket_type=kind)
    group.nodes.new("NodeGroupInput").location = (-1200, 0)
    group.nodes.new("NodeGroupOutput").location = (900, 0)
    return group


def _math(group, operation, a, b, location, c=None):
    node = group.nodes.new("ShaderNodeMath")
    node.operation = operation
    node.location = location
    for socket, value in zip(node.inputs, (a, b, c)):
        if isinstance(value, (int, float)):
            socket.default_value = value
        elif value is not None:
            group.links.new(value, socket)
    return node.outputs[0]


def _gag_uv_group():
    """The animated UV of one gag expression, as the legacy SVS Gag group worked it out: spin by
    `Angle speed`, pulse by `Size speed` and `Size width`, and step through a `Tile X` x `Tile Y`
    sheet one tile per frame. Values are the game's, unscaled."""
    float_ = "NodeSocketFloat"
    group = _new_group(".Gag UV", [("Frame", float_, 0.0), ("Angle speed", float_, 0.0), ("Size speed", float_, 0.0),
                                   ("Size width", float_, 0.0), ("Tile X", float_, 1.0), ("Tile Y", float_, 1.0)],
                       [("Vector", "NodeSocketVector")])
    i = next(n for n in group.nodes if n.type == "GROUP_INPUT").outputs
    out = next(n for n in group.nodes if n.type == "GROUP_OUTPUT")
    links = group.links

    uv = group.nodes.new("ShaderNodeUVMap")
    uv.location = (-1000, 300)
    centre = group.nodes.new("ShaderNodeVectorMath")
    centre.operation = "SUBTRACT"
    centre.inputs[1].default_value = (0.5, 0.5, 0.0)
    centre.location = (-800, 300)
    links.new(uv.outputs["UV"], centre.inputs[0])

    # The legacy importer scaled the game's speeds down by 5 (angle) and 3 (size).
    angle = _math(group, "MULTIPLY", _math(group, "MULTIPLY", i["Frame"], i["Angle speed"], (-1000, 100)), 0.2,
                  (-800, 100))
    pulse = _math(group, "MULTIPLY", _math(group, "SINE", _math(group, "MULTIPLY", i["Frame"],
                                                                _math(group, "DIVIDE", i["Size speed"], 3.0,
                                                                      (-1000, -100)), (-850, -100)), None,
                                           (-700, -100)), i["Size width"], (-550, -100))
    # A pulsing pattern is drawn at half size (base 2), a still one at full size (base 1).
    still = _math(group, "COMPARE", i["Size speed"], 0.0, (-700, -250), c=1e-6)
    base = _math(group, "SUBTRACT", 2.0, still, (-550, -250))
    size = _math(group, "ADD", pulse, base, (-400, -150))

    rotation = group.nodes.new("ShaderNodeCombineXYZ")
    rotation.location = (-600, 100)
    links.new(angle, rotation.inputs["Z"])
    scale = group.nodes.new("ShaderNodeCombineXYZ")
    scale.inputs["Z"].default_value = 1.0
    scale.location = (-250, -150)
    links.new(size, scale.inputs["X"])
    links.new(size, scale.inputs["Y"])
    spin = group.nodes.new("ShaderNodeMapping")
    spin.vector_type = "VECTOR"
    spin.location = (-100, 250)
    links.new(centre.outputs["Vector"], spin.inputs["Vector"])
    links.new(rotation.outputs["Vector"], spin.inputs["Rotation"])
    links.new(scale.outputs["Vector"], spin.inputs["Scale"])
    back = group.nodes.new("ShaderNodeVectorMath")
    back.operation = "ADD"
    back.inputs[1].default_value = (0.5, 0.5, 0.0)
    back.location = (100, 250)
    links.new(spin.outputs["Vector"], back.inputs[0])

    inv_x = _math(group, "DIVIDE", 1.0, i["Tile X"], (-100, -400))
    inv_y = _math(group, "DIVIDE", 1.0, i["Tile Y"], (-100, -550))
    tile_scale = group.nodes.new("ShaderNodeCombineXYZ")
    tile_scale.inputs["Z"].default_value = 1.0
    tile_scale.location = (100, -450)
    links.new(inv_x, tile_scale.inputs["X"])
    links.new(inv_y, tile_scale.inputs["Y"])
    tiles = group.nodes.new("ShaderNodeMapping")
    tiles.vector_type = "VECTOR"
    tiles.location = (300, 250)
    links.new(back.outputs["Vector"], tiles.inputs["Vector"])
    links.new(tile_scale.outputs["Vector"], tiles.inputs["Scale"])
    step = group.nodes.new("ShaderNodeCombineXYZ")
    step.location = (300, -300)
    links.new(_math(group, "MULTIPLY", inv_x, _math(group, "MODULO", i["Frame"], i["Tile X"], (100, -650)),
                    (200, -650)), step.inputs["X"])
    links.new(_math(group, "MULTIPLY", inv_y, _math(group, "MODULO", i["Frame"], i["Tile Y"], (100, -800)),
                    (200, -800)), step.inputs["Y"])
    shifted = group.nodes.new("ShaderNodeVectorMath")
    shifted.operation = "ADD"
    shifted.location = (550, 100)
    links.new(tiles.outputs["Vector"], shifted.inputs[0])
    links.new(step.outputs["Vector"], shifted.inputs[1])
    links.new(shifted.outputs["Vector"], out.inputs["Vector"])
    return group


def _gag_pick_group():
    """Passes on this expression's colour and alpha when `Choice` equals its `Index`, else the
    previous expression's. A chain of these picks the one expression that is on."""
    color, float_ = "NodeSocketColor", "NodeSocketFloat"
    group = _new_group(".Gag pick", [("Choice", float_, 0.0), ("Index", float_, 1.0), ("Color", color, None),
                                     ("Alpha", float_, 0.0), ("Previous color", color, (1.0, 1.0, 1.0, 1.0)),
                                     ("Previous alpha", float_, 0.0)],
                       [("Color", color), ("Alpha", float_)])
    i = next(n for n in group.nodes if n.type == "GROUP_INPUT").outputs
    out = next(n for n in group.nodes if n.type == "GROUP_OUTPUT")
    picked = group.nodes.new("ShaderNodeMath")
    picked.operation = "COMPARE"
    picked.inputs[2].default_value = 0.5
    picked.location = (-600, 200)
    group.links.new(i["Choice"], picked.inputs[0])
    group.links.new(i["Index"], picked.inputs[1])
    for kind, current, previous, location in (("RGBA", "Color", "Previous color", (-200, 200)),
                                              ("FLOAT", "Alpha", "Previous alpha", (-200, -100))):
        mix = group.nodes.new("ShaderNodeMix")
        mix.data_type = kind
        mix.location = location
        suffix = "Color" if kind == "RGBA" else "Float"
        group.links.new(picked.outputs[0], _socket(mix.inputs, "Factor_Float"))
        group.links.new(i[previous], _socket(mix.inputs, f"A_{suffix}"))
        group.links.new(i[current], _socket(mix.inputs, f"B_{suffix}"))
        group.links.new(_socket(mix.outputs, f"Result_{suffix}"), out.inputs[current])
    return group


def _socket(sockets, identifier):
    return next(s for s in sockets if s.identifier == identifier)


def _gag_output_group():
    """The picked expression drawn over transparency; with no expression on, nothing shows."""
    group = _new_group(".Gag output", [("Color", "NodeSocketColor", (1.0, 1.0, 1.0, 1.0)),
                                       ("Alpha", "NodeSocketFloat", 0.0)], [("Shader", "NodeSocketShader")])
    i = next(n for n in group.nodes if n.type == "GROUP_INPUT").outputs
    out = next(n for n in group.nodes if n.type == "GROUP_OUTPUT")
    emission = group.nodes.new("ShaderNodeEmission")
    emission.location = (-300, 100)
    clear = group.nodes.new("ShaderNodeBsdfTransparent")
    clear.location = (-300, -100)
    mix = group.nodes.new("ShaderNodeMixShader")
    mix.location = (0, 0)
    group.links.new(i["Color"], emission.inputs["Color"])
    group.links.new(i["Alpha"], mix.inputs[0])
    group.links.new(clear.outputs[0], mix.inputs[1])
    group.links.new(emission.outputs[0], mix.inputs[2])
    group.links.new(mix.outputs[0], out.inputs["Shader"])
    return group


main()
