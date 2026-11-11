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


def light_dark(t, node, light="Light", dark="Dark"):
    """Feeds a shader group's light and dark outputs to the grade."""
    t.link(node, light, "graded.light", "Color")
    t.link(node, dark, "graded.dark", "Color")
