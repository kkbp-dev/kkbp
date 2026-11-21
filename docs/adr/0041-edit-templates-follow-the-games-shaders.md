# Edit templates follow the games' own shaders, and grade their light and dark as the maker camera does

Updated by [ADR 0056](0056-the-graded-templates-take-shown-colours.md): these templates' textures are still never saturated, but KK's and KKS's take their drawn colours as Shown Colours, unless Edit Material's menu is Off, and ungrade them in nodes.

Updates [ADR 0026](0026-edit-materials-dont-saturate-by-default.md) as issue 30 asks. Every material of both Golden Samples now has a template made from the game's shaders, and so does KK's `main_alpha` (checked on a second KK card with see-through clothes and accessories, exported into `importer/tests/.work/extra/`). The legacy edit templates remain the fallback for shaders no template models (modded shaders such as xukmi's, and any not seen yet). KKS's clothes, teeth, tongue and skin are approximations (below).

An edit template is rebuilt from the game's own shaders instead of the legacy templates' approximations. The shaders were read from the installed games (`importer/tools/game_shaders/dump.py` disassembles their compiled D3D11 programs; the output is the games' code and stays in `importer/tests/.work/`), and each one used is written as a numpy model in `importer/tools/game_shaders/models.py`. `host/test_shader_models.py` checks every model against the Golden Samples' own bakes, and the node groups follow the models.

Comparing the models with the samples found three things the legacy importer and ADR 0026 didn't know:

- **Bundle textures hold linear values.** The exporter copies each texture through a linear render target, so a PNG holds what the shader sampled; only the `light` and `dark` bakes are sRGB-encoded. The templates re-encode each texture after Blender's sRGB decode (`.KK srgb`), which gives back the stored value without touching images other materials share.
- **The shaders see colours linear**, as Unity's linear colour space gives them: `lerp(lin(_Color2), lin(_Color), main.r)` is the eye white's composited texture to within 8-bit rounding.
- **Both games' `light` and `dark` bakes are colour graded by the maker camera** (AmplifyColor with `Lut_TimeDay.png`) after the shader. No per-channel factor fits the bakes without the grade; with it, the eye white's light factor is 1.0 in every channel. So a template grades its light and dark colours last, in nodes (`.KK grade`, `.KK graded`), and never saturates its input textures. ADR 0026 found the legacy hair and eyebrows closer saturated because saturating their colours stood in for this grade.

KK's maker light, found by fitting: the light term 1.0, `_ambientshadowG` 0.15 (ambient shadow 0.2775, legacy's constant), the ramp 1 for `light` and 0 for `dark`.

KKS's shaders (`Koikano/*`) add light probes, `_KanoVerShift`, a 0.67 / 0.33 light term and a desaturated shadow, but under the bake they reduce to KK's formula with other constants. Its `light` bakes match KK's to within 0.017 for the same card; only `dark` differs. The bake's flat quad sees the probes as one ambient colour, and a light of 1.0 makes both light terms 1. What is left is the ambient colour, its strength and how much lit colour the shadow keeps (`saturate(ramp + _ambientshadowG.a)`, 0 in KK). Fitted on the KKS eye-white family, they are 0.225 / 0.216 / 0.203, 0.175 and 0.2. So KKS uses KK's templates, and its Game Profile sets these three values on its `Koikano/main_eyew` materials (`models.KKS`).

The constants belong to a shader, not to a Game. KKS's hair shaders (`Koikano/hair_main_sun`, `hair_main_sun_front`) are two and a half times the size of KK's `main_hair`, with keyword switches (`_OLDHAIR`, `_REVERSECOLOR01`, `_GLOSSINSHADOWONOFF`). Even so, the KKS sample's hair bakes within 0.004 of the KK sample's, and KK's hair model with KK's own constants gives them back within 0.010. With `main_eyew`'s KKS constants it would be 0.028 in the dark. So KKS's hair uses KK's hair template with KK's values. The same holds for KKS's irises (`Koikano/main_eye` against KK's `toon_eye_lod0`). Both are measured on one card, not modelled: a hair or eye whose keywords differ may not match.

Measured by `blender/test_edit_accuracy.py` (mean absolute difference per channel, light / dark, sRGB values over pixels opaque in both). KK Golden Sample:

| Material | Legacy template | From the game's shader |
|---|---|---|
| `cf_m_sirome_00` (eye white) | 0.170 / 0.103 | 0.003 / 0.002 |
| `cf_m_mayuge_00` (eyebrow) | 0.019 / 0.000 | 0.003 / 0.000 |
| `cf_m_eyeline_00_up` | 0.155 / 0.002 | 0.005 / 0.001 |
| `cf_m_eyeline_kage` | 0.562 / 0.056 | 0.006 / 0.011 |
| `cf_m_eyeline_down` | 0.135 / 0.000 | 0.012 / 0.000 |
| `cf_m_noseline_00` | 0.000 / 0.000 | 0.000 / 0.000 |
| `cf_m_hair_b_08_00` (main_hair) | 0.049 / 0.092 | 0.005 / 0.005 |
| `cf_m_hair_f_14_00_i` (main_hair_front) | 0.035 / 0.089 | 0.005 / 0.004 |
| `cf_m_top_inner01` (main_opaque) | 0.113 / 0.062 | 0.003 / 0.004 |
| `cf_m_top_jacket06` | 0.082 / 0.096 | 0.007 / 0.001 |
| `cf_m_top_deco01` | 0.100 / 0.096 | 0.001 / 0.001 |
| `cf_m_bot_skirt01` (a pattern) | 0.043 / 0.037 | 0.003 / 0.003 |
| `cf_m_bra_01` | 0.089 / 0.062 | 0.011 / 0.005 |
| `cf_m_shorts_01` | 0.087 / 0.059 | 0.010 / 0.004 |
| `cf_m_socks_high01` | 0.102 / 0.086 | 0.011 / 0.003 |
| `cf_m_shoes_roafer01` | 0.092 / 0.082 | 0.004 / 0.002 |
| `cf_m_tooth` (main_item) | 0.073 / 0.053 | 0.001 / 0.001 |
| `cf_m_body` (create_body, main_skin) | 0.049 / 0.088 | 0.004 / 0.008 |
| `cf_m_face_00` (create_head, main_skin) | 0.094 / 0.130 | 0.004 / 0.017 |
| `cf_m_hitomi_00` (toon_eye) | 0.106 / 0.073 | 0.002 / 0.004 |
| `cf_m_hitomi_00_2` | 0.106 / 0.074 | 0.003 / 0.004 |
| `cf_m_emblem` (main_emblem) | 0.108 / 0.108 | 0.021 / 0.002 |
| `cf_m_tang` (main_item) | 0.081 / 0.128 | 0.001 / 0.011 |

KKS Golden Sample (KK's templates, with KKS's Maker Light where it has one):

| Material | Legacy template | From the game's shader |
|---|---|---|
| `cf_m_sirome_00` (eye white) | 0.169 / 0.114 | 0.002 / 0.002 |
| `cf_m_mayuge_00` (eyebrow) | 0.019 / 0.000 | 0.003 / 0.000 |
| `cf_m_eyeline_00_up` | 0.155 / 0.034 | 0.005 / 0.004 |
| `cf_m_eyeline_kage` | 0.563 / 0.259 | 0.005 / 0.004 |
| `cf_m_eyeline_down` | 0.135 / 0.010 | 0.012 / 0.004 |
| `cf_m_noseline_00` | 0.000 / 0.000 | 0.000 / 0.000 |
| `cf_m_hair_b_08_00` (hair_main_sun, KK's template) | 0.049 / 0.092 | 0.007 / 0.005 |
| `cf_m_hitomi_00` (main_eye, KK's template) | 0.105 / 0.074 | 0.006 / 0.008 |
| `cf_m_hitomi_00_2` | 0.106 / 0.076 | 0.007 / 0.008 |
| `cf_m_body` (create_body + main_skin, KK's templates) | 0.051 / 0.028 | 0.009 / 0.024 |
| `cf_m_face_00` (create_head + main_skin) | 0.094 / 0.059 | 0.006 / 0.031 |
| `cf_top_defshirt_m` (main_clothes_opaque, KK main_opaque) | 0.073 / 0.038 | 0.021 / 0.036 |
| `cf_bot_defpants_m` | 0.155 / 0.082 | 0.012 / 0.049 |
| `cf_m_bra_01` | 0.080 / 0.059 | 0.014 / 0.022 |
| `cf_m_shorts_01` | 0.082 / 0.062 | 0.015 / 0.025 |
| `cf_m_socks_crewori` | 0.053 / 0.040 | 0.034 / 0.009 |
| `cf_m_shoes_tennis` | 0.106 / 0.050 | 0.005 / 0.026 |
| `cf_m_tooth` (main_clothes_item, KK main_item) | 0.073 / 0.051 | 0.002 / 0.011 |
| `cf_m_tang` | 0.081 / 0.076 | 0.001 / 0.047 |
| `cf_m_hair_f_14_00_i` (hair_main_sun_front, KK's template) | 0.035 / 0.089 | 0.011 / 0.008 |

With KK's constants, KKS's shadow eyeline's dark would be 0.198: the shadow keeping a fifth of the lit colour is what matters, not the probes.

`.KK grade` reads its LUT with Closest sampling and does the bilinear filter in nodes. Eevee samples a Linear image through mipmaps, picked by how fast the texture coordinate changes between neighbouring pixels, and a LUT's coordinate is the colour itself. Along a texture's sharp edges (the clothes' seams and lines, the eyelines' outline), that read a blurred LUT, averaged across slices. Before the change, the clothes' lines came out blue (0.065 on the bra) and the eyelines 0.020 / 0.015 off.

## Considered Options

- **Keep the legacy templates and tune their saturation (ADR 0026)**: the errors of 0.03 to 0.56 come from the templates' own formulas, which no saturation choice fixes.
- **Saturate the input textures through the LUT, as legacy did**: the grade happens after the shader, on its encoded output; saturating the inputs and then shading gives other colours.
- **Rebuild each template from the game's shader, with the grade last (chosen)**.

## Consequences

- A template made this way is named after the game's shaders (`KK toon_eyew`, `KK create_eyewhite`, `KK toon_nose`, `KK main_hair`, `KK main_opaque`, `KK main_item`, `KK toon_eye`, `KK create_body`, `KK create_head`), keeps its image nodes at the top level (no texture group copied per material, so [ADR 0025](0025-edit-materials-copy-their-texture-group.md) doesn't apply to it), takes the game's own colours linear (`plain`), and is `graded` in its Template Description: the edit tool never saturates it, whatever Saturate says.
- The Game Profile picks a template per Material Role (`LEGACY_EDIT_TEMPLATES` for the Roles not modelled yet), and sets a shader's Maker Light through `values` (the `shader:` condition). The templates' defaults are KK's; KKS's profile sets `main_eyew`'s ambient colour, strength and shadow floor. No Role of either Game saturates by default now (`saturated_roles` is empty).
- The hair's template reads `_HairGloss` through the second UV map, moved along u by the light as the game does (`.KK hair gloss uv`). The toon value reaches `.Combine colors` through that group, so the bake's fixed value moves the gloss, and the viewport slides it with the shading. Off the mesh, the game's bake shows its quad, whose second UV map is its first; the importer's bake plane has the same.
- Link hair copies a template's colours (the profile's colour table, floats left out), so each hair keeps its own shadow extend and gloss placement.
- KK's clothes are picked by shader, not Role (`EDIT["shader_templates"]`: `main_opaque`, `main_item`), since one Role draws with several. `KK main_opaque` composites `create_topN` in nodes, so an edit can change the colours and patterns; `KK main_item` (teeth, tongue, items) applies its colour mask in the lit stage, as the game does. The maker's line globals, which no material carries, are fitted (`_LineColorG.a` 0.065, `_linewidthG` 0.32).
- The irises shade the game's composited iris (the material's own main texture), as the legacy template did, turned by `_rotation` and placed by its texture transform in place of the legacy `Eyepos` groups; recolouring the iris through `create_eye` (modelled as `models.create_eye`) is left for later. The highlights read the second and third UV maps; only their alpha shows, in their colours. The expression texture is left out (`_exppower` is 0 outside expressions).
- The body and face composite create_body and create_head in nodes (the colour mask, tan lines, paints placed and turned by `_paint1`/`_paint2`, the face decals by `_tex4uv`/`_tex5uv`, the mole by `_hokuro`), put main_skin's three overlays on the mesh's second to fourth UV maps (the nipples and underhair scaled by the vertex colour, which the bake now copies to its flat mesh), and shade as main_skin bakes. Its tint takes the colour's own hue at 0.66 of its saturation, with no shadow colour; the line mask is weighted by `_DetailNormalMapScale`. The face's dark side stays a little further off (0.017) than the model (0.011).
- `main_emblem` reads `_ambientshadow`, which the game leaves unset (0); its light side is 0.021 off at the emblem's sharp edges. `main_alpha` adds the detail mask's red squared in the specular colour (half in shadow) and draws its lines by the detail mask's blue (inverted) times `_DetailBLineGA`. On the second KK card its five materials bake 0.003 to 0.019 from the game.
- `main_item`'s highlight from the detail mask's red is the lit side's only: the bake clears `_SpecularPower`, and from behind n·h is 0, so the shader's log(0) times 0 is a NaN the GPU saturates to 0. Where the red line says, an item's `_AnotherRamp` stands in for the main ramp; the template reads it at the toon value (`.KK ramp uv`). The second card's handbag, red everywhere, went from 0.57 to 0.004 in the dark with both.
- An image node without an image reads black and opaque in Eevee, where the game reads a missing texture as transparent (or, for create_body's tan lines, white). So a profile value rule switches a decal or overlay off by its colour's alpha when its slot is missing, and the tan lines have a "present" switch.
- The game clamps its overlays' samplers; the templates' overlay image nodes use Extend, so a face overlay doesn't repeat across the texture.
- KKS's clothes and skin shaders (`Koikano/main_clothes_opaque`, `main_skin`) add to KK's toon formula a matcap ramp, a saturation boost and shadow colour driven by the ramp texture's other channels, a desaturated shadow, other line maths, and then blend in a physically based term (light probes, reflection cubemaps) by `_KanoVerShift`. Modelling them needs the game's global ramp texture and the maker scene's probes, which the bundle doesn't carry. Fitting constants to KK's formula barely helps the clothes (0.021 to 0.020), but KK's formulas already bake every KKS opaque clothing item and skin material closer than the legacy templates, so KKS uses them: the clothes with KK's values, the skin with its own fitted Maker Light (`models.KKS_SKIN`: ambient 0.145, strength 0.07, shadow floor 0.28), set on `main_skin` materials. KKS's create shaders composite as KK's (within 0.003). KKS's `main_clothes_item` (teeth, tongue) doesn't darken by the line mask's blue, as KK's `main_item` does; with that switched off (`line_blue`, a `shader:main_clothes_item` value rule) KK's template draws them closer than legacy. The tests of legacy behaviour (texture groups, saturation) use a built bundle with a modded shader.
- `Lut_TimeDay.png` stays in `library.blend`, Non-Color, read by `.KK grade` (and still by the legacy saturation).
- `importer/tests/data/edit_accuracy.json` records each material's numbers; the test fails when a material moves further from the game. Re-record it when a template brings a material closer.
- Each further shader is the same work: dump it, model it, fit any constants against the samples, write its node group and template, point the profile at it, re-record. The legacy templates, the Saturate option and `kkbp/shading/` stay, for now, as the fallback for shaders no template models (decided 2026-11-12): removing them would leave modded shaders' materials uneditable.
