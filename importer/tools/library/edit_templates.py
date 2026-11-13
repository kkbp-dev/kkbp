"""The layout every edit template made from a game's shaders shares (issue 30), for the modules in
`materials/` to call. Not a module of its own datablock: build.py's registry skips it.

    texture slots           tex.<slot> image nodes, each re-encoded by `.KK srgb` (encode.<slot>)
    the game's shaders      group nodes the module adds and wires, by name
    light, dark             `.KK graded` (graded.light, graded.dark): the bake's colour grade
    shade, combine, out     `.Toon shading` for the viewport, `.Combine colors` (whose Toon shading
                            input the bake sets: the `toon_shading` param), the Material Output

The image nodes' stored-value convention and the grade are in game_shaders/models.py.
"""

RENDER = {  # the legacy edit templates' settings, kept
    "surface_render_method": "BLENDED", "blend_method": "BLEND", "use_transparency_overlap": False,
    "show_transparent_back": False, "use_backface_culling_lightprobe_volume": False,
    "diffuse_color": (1.0, 1.0, 1.0, 1.0), "specular_color": (0.0, 0.0, 0.0), "roughness": 1.0,
}


def begin(lib, name, slots, *, force_visibility=0.0, props=None):
    """A new edit template with an image node per texture slot, and its light, dark, shade, combine
    and output nodes. Returns the Tree; the module wires its shader groups between them."""
    t = lib.new_material(name, props={**RENDER, **(props or {})})
    for row, slot in enumerate(slots):
        y = 300 - row * 320
        t.make("ShaderNodeTexImage", f"tex.{slot}", (-1400, y), {"label": slot})
        t.make("ShaderNodeGroup", f"encode.{slot}", (-1100, y), {"node_tree": lib.group(".KK srgb")},
               {"Color": (f"tex.{slot}", "Color")})
    t.make("ShaderNodeGroup", "graded.light", (300, 200), {"node_tree": lib.group(".KK graded")})
    t.make("ShaderNodeGroup", "graded.dark", (300, 0), {"node_tree": lib.group(".KK graded")})
    t.make("ShaderNodeGroup", "shade", (300, -250), {"node_tree": lib.group(".Toon shading"), "width": 240.0})
    t.make("ShaderNodeGroup", "combine", (650, 0), {"node_tree": lib.group(".Combine colors"), "width": 300.0},
           {"Alpha mask": (1.0, 1.0, 1.0, 1.0), "Alpha mask (alpha)": 1.0, "Alpha mask (custom)": (1.0, 1.0, 1.0, 1.0),
            "Main texture (alpha)": 1.0, "Force visibility": force_visibility,
            "Light colors": ("graded.light", "Color"), "Dark colors": ("graded.dark", "Color"),
            "Toon shading": ("shade", "Toon shading")})
    t.make("ShaderNodeOutputMaterial", "out", (1050, 0), ins={"Surface": ("combine", "Result")})
    return t


def toon_through(t, node):
    """Routes the toon value to `.Combine colors` through `node` (a group with a Toon shading input and
    output), whose input is then the `toon_shading` param the bake sets."""
    toon = t.tree.nodes["combine"].inputs["Toon shading"]
    for link in [l for l in t.tree.links if l.to_socket == toon]:
        t.tree.links.remove(link)
    t.link("shade", "Toon shading", node, "Toon shading")
    t.link(node, "Toon shading", "combine", "Toon shading")


def clamp(t, *slots):
    """The game clamps its overlays' sampler: outside the texture, its edge (transparent) shows, not a
    repeat of it."""
    for slot in slots:
        t.tree.nodes[f"tex.{slot}"].extension = "EXTEND"


def clip(t, *slots):
    """Nothing is drawn outside the texture (transparent), where `clamp` carries its edge pixels outward:
    for a texture whose edge isn't transparent, like an emblem's."""
    for slot in slots:
        t.tree.nodes[f"tex.{slot}"].extension = "CLIP"


def light_dark(t, node, light="Light", dark="Dark"):
    """Feeds a shader group's light and dark outputs to the grade."""
    t.link(node, light, "graded.light", "Color")
    t.link(node, dark, "graded.dark", "Color")


CLOTHES_SLOTS = ["plain", "color_mask", "pattern_mask1", "pattern_mask2", "pattern_mask3", "detail_mask", "line_mask"]


def clothes(lib, name, lit, ins):
    """A clothes template: create_topN composited in nodes (the colour mask, the patterns at
    `.KK pattern uv`), then the lit group `lit` with its inputs `ins` plus Main, into the grade."""
    t = begin(lib, name, CLOTHES_SLOTS)
    create = {"Main": ("encode.plain", "Color"), "Main alpha": ("tex.plain", "Alpha"),
              "Color mask": ("encode.color_mask", "Color")}
    for k in (1, 2, 3):
        t.make("ShaderNodeGroup", f"pattern{k}", (-1700, 300 - (k + 1) * 320), {"node_tree": lib.group(".KK pattern uv")})
        t.link(f"pattern{k}", "Vector", f"tex.pattern_mask{k}", "Vector")
        create[f"Pattern {k}"] = (f"encode.pattern_mask{k}", "Color")
    t.make("ShaderNodeGroup", "create", (-800, 400), {"node_tree": lib.group(".KK create_topN"), "width": 240.0}, create)
    t.make("ShaderNodeGroup", "lit", (-450, 100), {"node_tree": lib.group(lit), "width": 240.0},
           {"Main": ("create", "Color"), **ins})
    t.link("create", "Alpha", "combine", "Main texture (alpha)")
    light_dark(t, "lit")
    return t


SKIN_SLOTS = ["detail_mask", "line_mask", "overlay1", "overlay2", "overlay3"]


def skin(t, lib, create):
    """main_skin's half of a body or face template: the overlays (on their UV maps) over the create
    group `create`'s colour, shaded by `.KK main_skin`, into the grade."""
    clamp(t, "overlay1", "overlay2", "overlay3")
    t.make("ShaderNodeGroup", "overlay uv", (-1700, -2300), {"node_tree": lib.group(".KK skin overlay uv"), "width": 200.0})
    t.link("overlay uv", "Nipple", "tex.overlay1", "Vector")
    t.link("overlay uv", "Underhair", "tex.overlay2", "Vector")
    t.make("ShaderNodeUVMap", "uv.eyeshadow", (-1700, -2700), {"uv_map": "uv_eyeshadow"})
    t.link("uv.eyeshadow", "UV", "tex.overlay3", "Vector")
    ins = {"Color": (create, "Color")}
    for k in (1, 2, 3):
        ins[f"Overlay {k}"] = (f"encode.overlay{k}", "Color")
        ins[f"Overlay {k} alpha"] = (f"tex.overlay{k}", "Alpha")
    t.make("ShaderNodeGroup", "overlays", (-450, 400), {"node_tree": lib.group(".KK skin overlays"), "width": 240.0}, ins)
    t.make("ShaderNodeGroup", "lit", (-150, 100), {"node_tree": lib.group(".KK main_skin"), "width": 240.0},
           {"Color": ("overlays", "Color"), "Detail mask": ("encode.detail_mask", "Color"),
            "Line mask": ("encode.line_mask", "Color")})
    light_dark(t, "lit")
