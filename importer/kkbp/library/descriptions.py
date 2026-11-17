"""Template Descriptions: what each Material Template in library.blend accepts and where it goes.

- `textures`: texture slot -> image node. A slot is a Texture Role with its Variant (`main.light`,
  `normal`), or a Raw Property's slot from the Game Profile (`alpha_mask_bottom`).
- `params`: parameter name -> (node, socket). The socket is the node's input of that name, or its
  output for a Value node.
- `patterns`: a slot whose patterns an expression picks between (eye overlays, gag eyes).
- `shader`: the group node `templates.swap` replaces with a variant group from `variants`.
- `variant_params`: parameters only a variant's group has, such as Eevee Mod's fresnel, by variant.
- `variant_drops`: the shader group's inputs the variants lack; their links go when a variant is
  swapped in, and `swap` says so.
- `requires`: slots a material must have for this template; without them it gets the Set's fallback.
- `copies`: group nodes each material gets its own copy of (the edit templates' texture groups,
  ADR 0025), outermost first.
- `positions`: a slot whose placement is a `Scale Vector` group node in place of the image node's own
  mapping (the edit eyes' pupil and highlights, D41).
- `graded`: an edit template made from a game's shaders, which grades its light and dark itself as
  the game's bake did; the edit tool never saturates its textures (issue 30).

A node is named by its path: `textures/_CM.png` is the node `_CM.png` in the group of the material's
node `textures`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

_EMPTY: Mapping = MappingProxyType({})


@dataclass(frozen=True)
class Chain:
    """Pattern image nodes built per material, one link of the chain per pattern: a `uv_group`
    node animated by `pattern_params`, the image node, and a `pick_group` node that passes on that
    pattern's colour when the choice picks it. The last pick feeds `output`."""

    uv_group: str
    pick_group: str
    output: str
    frame: str  # the param the uv groups' frame input comes from
    pattern_params: Mapping[str, str]  # param name -> uv group input
    # The object property the frame param reads (an Attribute node), which the importer drives by
    # the frame on every object with the material: a driver in the material would update it, and
    # every driver reading its dropdown, on every frame (ADR 0042).
    frame_property: str | None = None
    # The groups' own sockets, by what they are for.
    sockets: Mapping[str, str] = MappingProxyType({
        "frame": "Frame", "vector": "Vector",  # uv group
        "choice": "Choice", "index": "Index", "color": "Color", "alpha": "Alpha",  # pick group, in
        "previous_color": "Previous color", "previous_alpha": "Previous alpha",
        "picked_color": "Color", "picked_alpha": "Alpha",  # pick group, out
        "output_color": "Color", "output_alpha": "Alpha",  # output node
        "output_picked": "Expression",  # output node: the material's dropdown (Picker), for the panel
    })


@dataclass(frozen=True)
class Picker:
    """A dropdown `templates.add_picker` makes in one material of a chained slot, as a group node of
    its own listing the Character's expressions: its `output` is the picked item's place from 1, or
    the `number` input while that is above 0, since Blender can't keyframe a dropdown (ADR 0042)."""

    node: str
    group: str  # the group's name, followed by the Character's
    menu: str  # input: the dropdown
    number: str  # input: an integer
    output: str


@dataclass(frozen=True)
class Patterns:
    """A slot whose patterns an expression picks between. The `choice` param is set to
    `first + n` to show the n-th pattern (in the bundle's order) and to `off` to show none."""

    slot: str
    choice: str
    first: int
    off: int
    nodes: tuple[str, ...] = ()  # fixed image nodes, or empty when `chain` builds them
    chain: Chain | None = None
    picker: Picker | None = None


@dataclass(frozen=True)
class Template:
    name: str
    textures: Mapping[str, str] = _EMPTY
    params: Mapping[str, tuple[str, str]] = _EMPTY
    patterns: Patterns | None = None
    shader: str | None = None
    variants: Mapping[str, str] = _EMPTY
    variant_params: Mapping[str, Mapping[str, tuple[str, str]]] = _EMPTY
    variant_drops: tuple[str, ...] = ()
    requires: tuple[str, ...] = ()
    groups: tuple[str, ...] = field(default=())  # groups apply() needs beyond those the material holds
    copies: tuple[str, ...] = ()
    positions: Mapping[str, str] = _EMPTY
    graded: bool = False  # an edit template that grades its light and dark as the game's bake (issue 30)


_LIGHT_DARK_TEXTURES = {
    "main.light": "tex.main.light",
    "main.dark": "tex.main.dark",
    "normal": "tex.normal",
    "detail_normal": "tex.detail_normal",
    "alpha_mask": "tex.alpha_mask",
    "permalight_mask": "tex.permalight_mask",
}
_LIGHT_DARK_PARAMS = {
    "force_visibility": ("shader", "Force visibility"),
    "hidden": ("shader", "Hidden"),
    "light": ("shader", "Light"),
    "dark": ("shader", "Dark"),
    "light_alpha": ("shader", "Light alpha"),
    "permalight_mask": ("shader", "Permalight mask"),
}
# KK's shader variants, which SVS Light Dark uses too (D18).
_KK_VARIANTS = {
    "cycles": ".Cycles",
    "cycles_classic": ".Cycles Classic",
    "cycles_no_shadows": ".Cycles no shadows",
    "eevee_mod": ".Eevee Mod",
    "principled": ".Principled",
}
_KK_VARIANT_PARAMS = MappingProxyType({
    "eevee_mod": MappingProxyType({
        "fresnel": ("shader", "Enable fresnel"),
        "disable_permalight_mask": ("shader", "Disable permalight mask"),
    }),
})

# --- the edit templates (D38) -------------------------------------------------------------
# The legacy templates as they are: each keeps its image nodes in a texture group (ADR 0025), and
# most have a `light` and a `dark` group with the same inputs, whose params end `.light` and `.dark`.

# The `Scale Vector` group's inputs a position sets.
POSITION_SOCKETS = MappingProxyType({"scale_x": "Scale X", "scale_y": "Scale Y",
                                     "position_x": "Position X", "position_y": "Position Y"})


def _pair(**sockets):
    """`name.light` and `name.dark` params for inputs the light and dark groups share."""
    return {f"{name}.{node}": (node, socket) for name, socket in sockets.items() for node in ("light", "dark")}


def _in(group, **slots):
    return {slot: f"{group}/{node}" for slot, node in slots.items()}


# Every edit template bakes through these: the combine group's light-dark mix, and the texture
# group's toon shading normals.
_BAKE = {"toon_shading": ("combine", "Toon shading"), "use_normals": ("textures/shade", "Use Normals?")}
# The templates made from the games' shaders bake the same way, through their own nodes.
_GAME_BAKE = {"toon_shading": ("combine", "Toon shading"), "use_normals": ("shade", "Use Normals?")}
# The Game's Maker Light as toon_eyew and Koikano/main_eyew shade with it; the defaults are KK's.
_EYEW_LIGHT = {"ambient": ("lit", "Ambient"), "ambient_strength": ("lit", "Ambient strength"),
               "shadow_floor": ("lit", "Shadow floor")}
# SVS's maker light as the LIF templates see it (models.SVS_LIGHT, SVS_DARK); the defaults are the
# Sample Card's probe.
_SVS_LIGHT = {"light_color": ("lit", "Light color"), "ndl_light": ("lit", "N.L light"), "ndl_dark": ("lit", "N.L dark"),
              "ambient": ("lit", "Ambient")}


def _svs_colors(*names, alpha_from=0):
    """`name` and (from the `alpha_from`th on) `name_alpha` params on the lit group's `Name` sockets:
    `color1` is `Color 1`, `line_color` is `Line color`."""
    out = {}
    for i, name in enumerate(names):
        socket = name.replace("_", " ").capitalize()
        socket = socket[:-1] + " " + socket[-1] if socket[-1].isdigit() else socket
        out[name] = ("lit", socket)
        if i >= alpha_from:
            out[f"{name}_alpha"] = ("lit", f"{socket} alpha")
    return out


# lif_main_eye's texture slots and the `.SVS eye` sockets they feed.
_SVS_EYE_SLOTS = {"shadow_mask": "Shadow mask", "iris_mask": "Iris", "pupil": "Pupil", "grade": "Grade",
                  "highlight1": "Highlight 1", "highlight2": "Highlight 2", "highlight3": "Highlight 3"}
_SVS_EYE_COLORS = {"eye_white1": "Eye white 1", "eye_white2": "Eye white 2", "eye1": "Eye 1", "eye2": "Eye 2",
                   "eye3": "Eye 3", "pupil1": "Pupil 1", "pupil2": "Pupil 2", "pupil3": "Pupil 3",
                   "line_color": "Line color", "grade_color": "Grade color", "highlight_color1": "Highlight color 1",
                   "highlight_color2": "Highlight color 2", "highlight_color3": "Highlight color 3"}
_SVS_EYE_UV = {"eye_position": "Eye position", "eye_position_w": "Eye position w",
               "eye_position_add": "Eye position add", "eye_position_add_w": "Eye position add w",
               "pupil_size": "Pupil size", "rotation": "Rotation", "mirror": "Mirror", "eye_open": "Eye open",
               "grade_position": "Grade position", "grade_size": "Grade size", "parallax": "Parallax",
               **{f"highlight{k}_position": f"Highlight {k} position" for k in (1, 2, 3)},
               **{f"highlight{k}_position_w": f"Highlight {k} position w" for k in (1, 2, 3)},
               **{f"highlight{k}_rotation": f"Highlight {k} rotation" for k in (1, 2, 3)}}
_SVS_HAIR_COLORS = {"main_color": "Main color", "sub_color1": "Sub color 1", "sub_color2": "Sub color 2",
                    "add_skin_color": "Add skin color", "ex_hair_color": "Ex hair color", "ex_hair_color2": "Ex hair color 2",
                    "shadow_color": "Shadow color", "shadow_color2": "Shadow color 2"}
# What main_opaque and main_item share: the shadow colour and extends, the line switches, the
# maker's ambient and line colour.
_ITEM_LIGHT = {"shadow_color": ("lit", "Shadow color"), "shadow_extend": ("lit", "Shadow extend"),
               "shadow_extend_another": ("lit", "Shadow extend another"),
               "detail_r_line_r": ("lit", "Detail R line R"), "detail_b_line_g": ("lit", "Detail B line G"),
               "line_color_alpha": ("lit", "Line color alpha"),
               "ambient": ("lit", "Ambient"), "ambient_strength": ("lit", "Ambient strength")}
_SKIN_LIT = {"detail_normal_map_scale": ("lit", "Detail normal map scale"), "shadow_extend": ("lit", "Shadow extend"),
             "line_tex_on": ("lit", "Line tex on"), "line_color_alpha": ("lit", "Line color alpha"),
             "line_width": ("lit", "Line width"), "ambient": ("lit", "Ambient"), "ambient_strength": ("lit", "Ambient strength"),
             "shadow_floor": ("lit", "Shadow floor"),
             **{f"overlay_color{k}": ("overlays", f"Overlay color {k}") for k in (1, 2, 3)},
             **{f"overlay_color{k}_alpha": ("overlays", f"Overlay color {k} alpha") for k in (1, 2, 3)},
             "nip_specular": ("overlays", "Nip specular"), "tex1_mask": ("overlays", "Tex1 mask"),
             "nip": ("overlay uv", "Nip"), "nip_size": ("overlay uv", "Nip size")}
_SKIN_TEXTURES = {"plain": "tex.plain", "color_mask": "tex.color_mask", "paint_mask": "tex.paint_mask",
                  "detail_mask": "tex.detail_mask", "line_mask": "tex.line_mask",
                  **{f"overlay{k}": f"tex.overlay{k}" for k in (1, 2, 3)}}
# create_topN's half of a clothes template (edit_templates.clothes).
_CLOTHES_TEXTURES = {"plain": "tex.plain", "color_mask": "tex.color_mask", "pattern_mask1": "tex.pattern_mask1",
                     "pattern_mask2": "tex.pattern_mask2", "pattern_mask3": "tex.pattern_mask3",
                     "detail_mask": "tex.detail_mask", "line_mask": "tex.line_mask"}
_CLOTHES_CREATE = {"color": ("create", "Color"), "color2": ("create", "Color 2"), "color3": ("create", "Color 3"),
                     **{f"pattern_color{k}": ("create", f"Pattern color {k}") for k in (1, 2, 3)},
                     **{f"pattern_color{k}_alpha": ("create", f"Pattern color {k} alpha") for k in (1, 2, 3)},
                     **{f"pattern{k}_present": ("create", f"Pattern {k} present") for k in (1, 2, 3)},
                     **{f"pattern_scale{k}{a}": (f"pattern{k}", f"Scale {a}") for k in (1, 2, 3) for a in "uv"}}
_MISC = Template("", textures=_in("textures", main="_ST_CT.png"), params=_BAKE, copies=("textures",))
_GENERAL_TEXTURES = _in(
    "textures", main="_ST_CT.png", **{"main.dark": "_ST_DT.png", "color_mask.plain": "_CM.pngopaque"},
    plain="_ST.png", color_mask="_CM.png", detail_mask="_DM.png", normal="_NMP.png",
    detail_normal="_NMPD_CNV.png", alpha_mask="_AM.png", pattern_mask1="_PM1.png", pattern_mask2="_PM2.png",
    pattern_mask3="_PM3.png", hair_gloss="_HGLS.png")
_EYE = Template(
    "",
    textures=_in("textures", main="_ST_CT.png", overlay1="_ot1.png", overlay2="_ot2.png",
                 **{"main.dark": "_ST_DT.png", "expression.0": "_cf_t_expression_00_EXPR.png",
                    "expression.1": "_cf_t_expression_01_EXPR.png"}),
    params={**_BAKE, **_pair(highlight_up_color="Eye highlight up color",
                             highlight_down_color="Eye highlight down color",
                             highlight_up_intensity="Eye highlight up intensity",
                             highlight_down_intensity="Eye highlight down intensity")},
    copies=("textures", "textures/Eyepos"),
    positions={"main": "textures/Eyepos/eye_scale", "overlay1": "textures/Eyepos/Group",
               "overlay2": "textures/Eyepos/Group.001"},
)

_EDIT_TEMPLATES = (
    Template(
        "KK Body",
        textures={**_in("textures", main="_ST_CT.png", color_mask="_CM.png", detail_mask="_DM.png",
                        line_mask="_LM.png", normal="_NMP_CNV.png", detail_normal="_NMPD_CNV.png",
                        alpha_mask="_AM.png", texture3="_T3.png", texture6="_T6.png", **{"main.dark": "_ST_DT.png"}),
                  **_in("texturesnsfw", plain="_ST.png", overlay1="_ot1.png", overlay2="_ot2.png",
                        **{"overlay1.left": "_ot1.pngleft"})},
        params={**_BAKE, **_pair(skin_color="Skin color", detail_color="Detail color", line_mask_color="Line mask color",
                                 nail_color="Nail color (multiplied)", use_main_texture="Use main texture?")},
        copies=("textures", "texturesnsfw"),
    ),
    Template(
        "KK Face",
        textures=_in("textures", main="_ST_CT.png", plain="_ST.png", color_mask="_CM.png", detail_mask="_DM.png",
                     line_mask="_LM.png", texture3="_T3.png", texture4="_T4.png", texture5="_T5.png",
                     texture7="_T7.png", overlay1="_ot1.png", overlay2="_ot2.png", overlay3="_ot3.png",
                     **{"main.dark": "_ST_DT.png"}),
        params={**_BAKE, **_pair(skin_color="Skin color", detail_color="Detail color",
                                 light_blush_color="Light blush color", lipstick_multiplier="Lipstick multiplier",
                                 use_main_texture="Use main texture?")},
        copies=("textures",),
    ),
    Template(
        "KK General",
        textures=_GENERAL_TEXTURES,
        params={**_BAKE, **_pair(
            color_mask_base="Color mask (base)", color_mask_red="Color mask (red)",
            color_mask_green="Color mask (green)", color_mask_blue="Color mask (blue)",
            pattern_color_red="Pattern color (red)", pattern_color_green="Pattern color (green)",
            pattern_color_blue="Pattern color (blue)", maintex_saturation="Maintex Saturation",
            detail_intensity_green="Detail intensity (green)", detail_intensity_shine="Detail intensity (shine)",
            use_plain_main_texture="Use plain main texture?")},
        copies=("textures", "textures/pospattern"),
    ),
    Template(
        "KK Hair",
        textures=_GENERAL_TEXTURES,
        params={**_BAKE, **_pair(hair_color="Hair color", color_mask_root="Color mask (root)",
                                 color_mask_tip="Color mask (tip)", use_color_mask="Use color mask?")},
        copies=("textures", "textures/pospattern"),
    ),
    Template("KK EyeL (hitomi)", textures=_EYE.textures, params=_EYE.params, copies=_EYE.copies,
             positions=_EYE.positions),
    Template("KK EyeR (hitomi)", textures=_EYE.textures, params=_EYE.params, copies=_EYE.copies,
             positions=_EYE.positions),
    Template("KK Eyewhites (sirome)", textures=_MISC.textures, params=_MISC.params, copies=_MISC.copies),
    Template("KK Eyebrows (mayuge)", textures=_MISC.textures, copies=_MISC.copies,
             params={**_BAKE, "eyebrow_color": ("light", "Eyebrow color"),
                     "eyebrow_color_dark": ("light", "Eyebrow color dark"),
                     "use_main_texture_color": ("light", "Use main texture color?")}),
    Template("KK Nose", textures=_MISC.textures, params=_MISC.params, copies=_MISC.copies),
    Template("KK Eyeline up", textures=_MISC.textures, copies=_MISC.copies,
             params={**_BAKE, "eyeline_fade_color": ("light", "Eyeline fade color"),
                     "use_kage_texture": ("light", "Use kage texture color?"),
                     "use_down_texture": ("light", "Use down texture color?")}),
    Template("KK Teeth (tooth)", textures=_MISC.textures, params=_MISC.params, copies=_MISC.copies),
    # The edit templates made from the games' shaders (issue 30, importer/tools/game_shaders/models.py):
    # each slot's image node by name at the top level, shared groups, and the game's colours linear.
    Template("KK toon_eyew", graded=True, textures={"main": "tex.main"},
             params={**_GAME_BAKE, **_EYEW_LIGHT, "color": ("lit", "Color"), "shadow_color": ("lit", "Shadow color")}),
    Template("KK create_eyewhite", graded=True, textures={"create_main": "tex.create_main"},
             params={**_GAME_BAKE, **_EYEW_LIGHT, "color": ("lit", "Color"), "shadow_color": ("lit", "Shadow color"),
                     "create_color": ("create", "Color"), "create_color2": ("create", "Color 2")}),
    Template("KK main_hair", graded=True,
             textures={"main": "tex.main", "color_mask": "tex.color_mask", "detail_mask": "tex.detail_mask",
                       "hair_gloss": "tex.hair_gloss"},
             params={**_GAME_BAKE, "toon_shading": ("gloss", "Toon shading"), "front": ("gloss", "Front"),
                     "ambient": ("lit", "Ambient"), "ambient_strength": ("lit", "Ambient strength"),
                     "use_main_texture": ("lit", "Use main texture"), "color": ("lit", "Color"),
                     "color2": ("lit", "Color 2"), "color3": ("lit", "Color 3"),
                     "shadow_color": ("lit", "Shadow color"), "shadow_extend": ("lit", "Shadow extend")}),
    Template("KK main_opaque", graded=True, textures=_CLOTHES_TEXTURES,
             params={**_GAME_BAKE, **_ITEM_LIGHT, **_CLOTHES_CREATE, "line_width": ("lit", "Line width")}),
    Template("KK main_alpha", graded=True, textures=_CLOTHES_TEXTURES,
             params={**_GAME_BAKE, **_CLOTHES_CREATE, "shadow_color": ("lit", "Shadow color"),
                     "shadow_extend": ("lit", "Shadow extend"), "specular_color": ("lit", "Specular color"),
                     "detail_b_line_ga": ("lit", "Detail B line GA"), "line_color_alpha": ("lit", "Line color alpha"),
                     "line_width": ("lit", "Line width"), "ambient": ("lit", "Ambient"),
                     "ambient_strength": ("lit", "Ambient strength")}),
    Template("KK main_emblem", graded=True, textures={"main": "tex.main"}, params=_GAME_BAKE),
    Template("KK main_item", graded=True,
             textures={"main": "tex.main", "color_mask": "tex.color_mask", "detail_mask": "tex.detail_mask",
                       "line_mask": "tex.line_mask", "another_ramp": "tex.another_ramp"},
             params={**_GAME_BAKE, **_ITEM_LIGHT, "toon_shading": ("ramp", "Toon shading"),
                     "use_another_ramp": ("lit", "Use another ramp"), "use_main_texture": ("lit", "Use main texture"),
                     "color": ("lit", "Color"), "color2": ("lit", "Color 2"), "color3": ("lit", "Color 3"),
                     "another_ramp_full": ("lit", "Another ramp full"), "line_blue": ("lit", "Line blue"),
                     "not_use_tex_specular": ("lit", "Not use tex specular")}),
    Template("KK toon_eye", graded=True,
             textures={"main": "tex.main", "overlay1": "tex.overlay1", "overlay2": "tex.overlay2"},
             params={**_GAME_BAKE, "rotation": ("iris", "Rotation"), "highlight": ("lit", "Highlight"),
                     "overlay_color1": ("lit", "Overlay color 1"), "overlay_color1_alpha": ("lit", "Overlay color 1 alpha"),
                     "overlay_color2": ("lit", "Overlay color 2"), "overlay_color2_alpha": ("lit", "Overlay color 2 alpha"),
                     "shadow_color": ("lit", "Shadow color"), "ambient": ("lit", "Ambient"),
                     "ambient_strength": ("lit", "Ambient strength")}),
    Template("KK create_body", graded=True,
             textures={**_SKIN_TEXTURES, "texture4": "tex.texture4", "texture3": "tex.texture3", "texture6": "tex.texture6"},
             params={**_GAME_BAKE, **_SKIN_LIT, "tan_present": ("create", "Tan present"),
                     **{("color" if k == 1 else f"color{k}"): ("create", "Color" if k == 1 else f"Color {k}") for k in range(1, 7)},
                     **{f"color{k}_alpha": ("create", f"Color {k} alpha") for k in (2, 3, 4, 6)},
                     "paint1": ("paint1", "Paint"), "paint1_w": ("paint1", "Paint w"),
                     "paint2": ("paint2", "Paint"), "paint2_w": ("paint2", "Paint w")}),
    Template("KK create_head", graded=True,
             textures={**_SKIN_TEXTURES, "texture4": "tex.texture4", "texture5": "tex.texture5", "texture3": "tex.texture3",
                       "texture7": "tex.texture7", "texture6": "tex.texture6"},
             params={**_GAME_BAKE, **_SKIN_LIT,
                     **{("color" if k == 1 else f"color{k}"): ("create", "Color" if k == 1 else f"Color {k}") for k in range(1, 8)},
                     **{f"color{k}_alpha": ("create", f"Color {k} alpha") for k in range(3, 8)},
                     "tex4uv": ("place4", "Place"), "tex4uv_w": ("place4", "Place w"),
                     "tex5uv": ("place5", "Place"), "tex5uv_w": ("place5", "Place w"),
                     "paint1": ("paint1", "Paint"), "paint1_w": ("paint1", "Paint w"),
                     "paint2": ("paint2", "Paint"), "paint2_w": ("paint2", "Paint w"),
                     "hokuro": ("mole", "Paint"), "hokuro_w": ("mole", "Paint w")}),
    Template("KK toon_nose", graded=True, textures={"main": "tex.main"},
             params={**_GAME_BAKE, "color": ("lit", "Color"), "color_alpha": ("lit", "Color alpha")}),
    # SVS's (issue 62): each follows a LIF shader under the maker's bake light (models.SVS_LIGHT), with
    # no grade, as SVS's bake has none. `graded` keeps the edit tool from saturating them.
    Template("SVS lif_main_eyebrow", graded=True, textures={"eyebrow": "tex.eyebrow"},
             params={**_GAME_BAKE, **_SVS_LIGHT, "length": ("uv", "Length"), "width": ("uv", "Width"),
                     **_svs_colors("color1", "color2", "color3", "line_color", alpha_from=1),
                     "light_influence": ("lit", "Light influence"), "shadow_power": ("lit", "Shadow power")}),
    Template("SVS lif_main_eyelash_up", graded=True,
             textures={"eyelash_up": "tex.eyelash_up", "eyelash_down": "tex.eyelash_down"},
             params={**_GAME_BAKE, **_SVS_LIGHT, **_svs_colors("color1", "color2", "color3", "line_color", alpha_from=1),
                     "shadow_power": ("lit", "Shadow power")}),
    Template("SVS lif_main_eye", graded=True, textures={k: f"tex.{k}" for k in _SVS_EYE_SLOTS},
             params={**_GAME_BAKE, **_SVS_LIGHT, "eye_white_only": ("lit", "Eye white only"),
                     "shadow_power": ("lit", "Shadow power"), "highlight_power": ("lit", "Highlight power"),
                     **{f"{k}_present": ("lit", f"{socket} present") for k, socket in _SVS_EYE_SLOTS.items()},
                     **{name: ("lit", socket) for name, socket in _SVS_EYE_COLORS.items()},
                     **{f"{name}_alpha": ("lit", f"{socket} alpha") for name, socket in _SVS_EYE_COLORS.items()
                        if name not in ("eye_white1", "eye1")},
                     **{name: ("uv", socket) for name, socket in _SVS_EYE_UV.items()}}),
    Template("SVS lif_main_hair", graded=True,
             textures={k: f"tex.{k}" for k in ("color_mask", "detail1", "detail2", "ramp", "ramp2")},
             params={**_GAME_BAKE, "toon_shading": ("ndl", "Toon shading"), "ndl_light": ("ndl", "N.L light"),
                     "ndl_dark": ("ndl", "N.L dark"), "light_color": ("lit", "Light color"), "ambient": ("lit", "Ambient"),
                     **{name: ("lit", socket) for name, socket in _SVS_HAIR_COLORS.items()},
                     **{f"{name}_alpha": ("lit", f"{socket} alpha") for name, socket in _SVS_HAIR_COLORS.items()
                        if name not in ("main_color", "shadow_color", "shadow_color2")},
                     "ex_hair_color_on": ("lit", "Ex hair color on"), "ex_hair_color2_on": ("lit", "Ex hair color 2 on"),
                     "shadow_power": ("lit", "Shadow power"), "shadow_color_on": ("lit", "Shadow color on")}),
)
EDIT_TEMPLATES = tuple(t.name for t in _EDIT_TEMPLATES)

TEMPLATES: Mapping[str, Template] = MappingProxyType({t.name: t for t in (
    Template(
        "KK Light Dark",
        textures=_LIGHT_DARK_TEXTURES,
        params={**_LIGHT_DARK_PARAMS, "disable_permalight_mask": ("shader", "Disable permalight mask")},
        shader="shader", variants=_KK_VARIANTS, variant_params=_KK_VARIANT_PARAMS, requires=("main.light",),
    ),
    # The face when the bundle has its bakes without eyeshadow (issue 38, ADR 0046).
    Template(
        "KK Light Dark Face",
        textures={**_LIGHT_DARK_TEXTURES, "main.light_no_eyeshadow": "tex.main.light_no_eyeshadow",
                  "main.dark_no_eyeshadow": "tex.main.dark_no_eyeshadow"},
        params={**_LIGHT_DARK_PARAMS, "disable_permalight_mask": ("shader", "Disable permalight mask"),
                "eyeshadow": ("eyeshadow", "Eyeshadow"),
                "eyeshadow_hidden": ("eyeshadow", "Hide with gag eyes")},
        shader="shader", variants=_KK_VARIANTS, variant_params=_KK_VARIANT_PARAMS, requires=("main.light",),
    ),
    Template(
        "SVS Light Dark Face",
        textures={**_LIGHT_DARK_TEXTURES, "alpha_mask_bottom": "tex.alpha_mask_bottom",
                  "main.light_no_eyeshadow": "tex.main.light_no_eyeshadow",
                  "main.dark_no_eyeshadow": "tex.main.dark_no_eyeshadow"},
        params={**_LIGHT_DARK_PARAMS, "eyeshadow": ("eyeshadow", "Eyeshadow"),
                "eyeshadow_hidden": ("eyeshadow", "Hide with gag eyes")},
        shader="shader", variants=_KK_VARIANTS, variant_params=_KK_VARIANT_PARAMS, requires=("main.light",),
        variant_drops=("Alpha mask bottom", "Alpha mask bottom alpha"),
    ),
    Template(
        "KK Eye",
        textures=_LIGHT_DARK_TEXTURES,
        params={**_LIGHT_DARK_PARAMS, "disable_permalight_mask": ("shader", "Disable permalight mask"),
                "expression": ("expression", "Choice")},
        patterns=Patterns("expression", choice="expression", first=0, off=2,
                          nodes=("tex.expression.0", "tex.expression.1")),
        shader="shader", variants=_KK_VARIANTS, variant_params=_KK_VARIANT_PARAMS, requires=("main.light",),
    ),
    Template(
        "SVS Light Dark",
        textures={**_LIGHT_DARK_TEXTURES, "alpha_mask_bottom": "tex.alpha_mask_bottom"},
        params=_LIGHT_DARK_PARAMS,
        shader="shader", variants=_KK_VARIANTS, variant_params=_KK_VARIANT_PARAMS, requires=("main.light",),
        # KK's variants have no bottom alpha mask; Principled does.
        variant_drops=("Alpha mask bottom", "Alpha mask bottom alpha"),
    ),
    Template(
        "KK Tears",
        textures={"main": "tex.main"},
        params={"hidden": ("shader", "Hidden"), "game_look": ("shader", "Game look"),
                "use_hdri": ("shader", "Use HDRI"), "tear_color": ("shader", "Tear color")},
    ),
    Template(
        "Gag",
        params={"choice": ("gag.choice", "Value"), "frame": ("gag.frame", "Fac")},
        patterns=Patterns("main", choice="choice", first=1, off=0, chain=Chain(
            uv_group=".Gag UV", pick_group=".Gag pick", output="gag.output", frame="frame",
            frame_property="kkbp_gag_frame",
            pattern_params={"angle_speed": "Angle speed", "size_speed": "Size speed", "size_width": "Size width",
                            "tile_x": "Tile X", "tile_y": "Tile Y"}),
            picker=Picker("gag.expression", "Gag expression", menu="Gag expression", number="Number",
                          output="Expression")),
        groups=(".Gag UV", ".Gag pick"),
    ),
    Template("Transparent"),
    *_EDIT_TEMPLATES,
)})
