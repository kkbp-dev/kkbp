# The library from code, and edit templates from the games' shaders

How `library.blend` and the Hooks' asset files are built ([ADR 0040](../adr/0040-the-library-is-built-from-code.md), D66), and how the edit templates follow the games' own shaders ([ADR 0041](../adr/0041-edit-templates-follow-the-games-shaders.md), D67). Terms are in [CONTEXT.md](../../CONTEXT.md); what a template is and how materials use one is in [material-template.md](material-template.md).

## The library from code

`library.blend`, `rigify.blend`, `face_cards.blend` and `outlines.blend` in `importer/kkbp/library/` are build output. Nobody edits them in Blender; `scripts/build-library.sh` builds all four from tracked text and image files.

### Layout

```
importer/library-src/
  images/  images.json     the images (Git LFS), and each one's name, colour space and alpha mode
  meshes/*.json            one file per mesh: widgets, card meshes, bone shapes
  scenes/*.json            per asset file: collections, objects, armatures
importer/tools/library/
  nodes.py                 the builder helper the modules are written with
  groups/<name>.py         one module per node group
  materials/<name>.py      one module per template material
  edit_templates.py        builds the edit templates that follow the games' shaders
  decals.py                the skin templates' decal and overlay nodes
  build.py                 builds the four files
  export_nodes.py          the decompiler: writes a group or material in a .blend back as a module
  export_assets.py         writes meshes and scenes in a .blend back as JSON
  fingerprint.py           a structural dump of a .blend
  compare.py               compares two fingerprints
  introspect.py            shared reading of nodes, sockets and properties
```

`build.py` starts from `--factory-startup` with an emptied file, never from a `.blend`, and runs on the harness's `min` Blender build, so the files open in every supported version.

### Writing a group

A module reads like the graph it builds, through `nodes.py`:

- A group's interface sockets are declared with type, subtype, default, limits and panel. Their order matters: code reads sockets by name, and users see the order.
- Node sockets are addressed by identifier, not by name or index: `ShaderNodeMix` has `A_Color`, `B_Color`, `Factor_Float` and `Result_Color`, and several nodes repeat socket names.
- A node's properties are set before its sockets and links, because `data_type`, `operation`, `blend_type` and `mode` change which sockets exist.
- A group comes after the groups it contains.

A group edited visually in Blender goes back into its module with `scripts/export-library-nodes.sh <file.blend> [name ...]`. The decompiler writes every node property that differs from a fresh node of the same type, every unlinked input's value, links by socket identifier, drivers, custom properties and, for materials, the settings that differ from a new material.

### Checking a build

`fingerprint.py` dumps a `.blend` as sorted JSON: nodes and links, images (name, size, colour space, alpha mode, a hash of the pixels), meshes (vertices, edges, faces, UVs, shape keys, vertex groups, material slots) and objects (parents, transforms, modifiers, constraints, custom shapes, bone collections), with floats rounded to 6 places.

`scripts/check-library.sh` rebuilds the four files and compares their fingerprints with the committed ones. In the test suite, a harness test checks every Template Description and Hook asset description against the built files.

Every template and group carries `kkbp_template_version` (`TEMPLATE_VERSION` in `kkbp/library/__init__.py`), and every Hook asset `kkbp_asset_version` (`ASSET_VERSION` in `kkbp/library/hook_assets.py`).

## Edit templates from the games' shaders

An edit template rebuilds a material's colouring in nodes, from the textures and colours the bundle carries, so the colours can be changed and baked again. Each one copies the game's own shaders. SVS has no edit templates (issue 62).

### How the games shade

Each KK and KKS material is drawn in two stages, and an edit template copies both:

1. **Create shader** (`Shader Forge/create_body`, `create_head`, `create_topN`, `create_eye`, `create_eyewhite`, `create_hair`; KKS `Koikano/create_skinbody`, `create_skinface`, `create_topN`, `create_eye`, `create_eyew`): composites the uncoloured base texture, masks and the Character's colours into the material's `_MainTex`. The bundle carries its inputs as `extensions.kk.create` and its output as the material's `main` texture.
2. **Lit shader** (`main_skin`, `main_opaque`/`main_item`/`main_alpha`, `main_hair`/`main_hair_front`, `toon_eye_lod0`, `toon_eyew_lod0`, `toon_nose_lod0`; KKS `Koikano/main_skin`, `main_clothes_opaque`, `main_clothes_item`, `hair_main_sun`, `hair_main_sun_front`, `main_eye`, `main_eyew`, `main_nose`): shades `_MainTex` with overlays, the detail and line masks, `_ShadowColor` and global light values. The bundle carries its output as `main.light` and `main.dark`.

The exporter's bake (`exporters/kk/src/Bake.cs`) fixes the lit shader's other inputs, which makes it a per-pixel function nodes can copy:

- The material is drawn on a flat quad (and, for mesh-dependent shaders, the mesh flattened into UV space) through an orthographic camera facing it, so `dot(normal, view) = 1` and rim light is 0.
- `_AlphaMask`, `_NormalMap`, `_NormalMapDetail` and `_NormalMask` are cleared, and `_SpecularPower`, `_SpecularPowerNail` and `_nip_specular` are 0: no specular, a flat normal.
- Light comes from the front for `light` (ramp at its lit end) and from behind for `dark` (ramp at its dark end). There is no shadow map.
- Outline and shadow-caster passes are off.

So `light` and `dark` are the forward pass with `ramp = 1` and `ramp = 0`, and nothing else varies.

### Colour spaces and the grade

Measured against the kk and kks Golden Samples, pixel by pixel:

- **Every bundle PNG except `light` and `dark` holds the linear values the shader samples.** The exporter copies each texture through a linear render target, which decodes an sRGB texture as it reads it and writes the result unencoded. So `main`, the masks and the create inputs are data: they go into Blender as Non-Color and are used as they are.
- **Colours are linearised**: the shader sees `lin(colour)` of the bundle's sRGB-encoded colours.
- **The `light` and `dark` bakes are sRGB-encoded and then colour graded** by the maker camera's LUT, `Lut_TimeDay.png`, in both KK and KKS. So the grade is the last step of every edit template, done in nodes (`.KK grade`), and a template that follows the game's shaders is never saturated ([ADR 0026](../adr/0026-edit-materials-dont-saturate-by-default.md) covers the older templates).
- `.KK grade` reads its LUT with Closest and filters by hand: Eevee mipmaps a Linear image by the coordinate's change between pixels, and a LUT's coordinate is the colour, so sharp texture edges would read a blurred LUT.
- **KK's light**: `_LightColor0` term 1.0, `_ambientshadowG` 0.15 in every channel and alpha, ramp 1 lit and 0 dark.
- **KKS's light**: under the bake, KKS's shaders reduce to KK's with other constants, so KKS shares KK's templates and its Game Profile sets `ambient`, `ambient_strength` and `shadow_floor`.
- Global values the lit shaders read that the bundle doesn't carry (`_ambientshadowG`, `_LineColorG`, `_linewidthG`, `_LightColor0`, the `_RampG` texture) are constants in `models.py` and the Game Profiles, fitted to the samples: `_LineColorG.a` 0.065 and `_linewidthG` 0.32.

### The shaders

The create shaders, decoded from the disassembly (`lerp(a, b, t) = a + t*(b - a)`; every texture is
sampled at `uv * X_ST.xy + X_ST.zw` unless a UV is given; `rot(p, turns)` rotates by `turns * 2π`:
`x' = x*cos + y*sin`, `y' = -x*sin + y*cos`):

```
create_topN (clothes)                     out.a = Main.a
  uvK   = uv * (20 - 19 * (PatternScaleKu, PatternScaleKv))          K = 1, 2, 3
  pK    = max(PatternMaskK(uvK).r, 1 - ColorK_2.a)
  c1    = lerp(Color1_2, Color,  p1);  c2 = lerp(Color2_2, Color2, p2);  c3 = lerp(Color3_2, Color3, p3)
  col   = lerp(1, c1, CM.r);  col = lerp(col, c2, CM.g);  col = lerp(col, c3, CM.b)
  out   = col * saturate(Main.rgb)
  KKS's version adds _PatternOffsetKu/v and _PatternRotatorK; read its disassembly.

create_body                               out.a = 1
  skin  = lerp(Color4, Color, max(Texture4.r, 1 - Color4.a))         Texture4: tan lines
  base  = skin * Main.rgb * lerp(1, Color2, CM.g * Color2.a)
  paint(uvp, s) = rot(((uv + p.xy) * 2s + (0.5 - s)) - 0.5, p.z) + 0.5,   s = 2 - 2 * p.w
  base  = lerp(base, Texture3(paint1).rgb * Color3, Texture3.a * Color3.a * paintmask.r)
  base  = lerp(base, Texture6(paint2).rgb * Color6, Texture6.a * Color6.a * paintmask.r)
  out   = lerp(base, Color5 * base, CM.b)                            nails

create_head                               out.a = 1
  base  = max(CM.b, lerp(1, Color, CM.r) * lerp(1, Color2, CM.g)) * Main.rgb
  uvN   = (uv + texNuv.xy) * s - s + 0.5,  s = 1 - texNuv.zw         N = 4, 5
  base  = lerp(base, Texture4(uv4).rgb * Color4, Texture4.a * Color4.a)
  base  = lerp(base, Texture5(uv5).rgb * Color5, Texture5.a * Color5.a)
  base  = lerp(base, Texture3(paint1).rgb * Color3, Texture3.a * Color3.a * paintmask.r)
  base  = lerp(base, Texture7(paint2).rgb * Color7, Texture7.a * Color7.a * paintmask.r)
  uv6   = (uv + hokuro.xy) * 2s + (0.5 - s),  s = 2 - 2 * hokuro.w   mole, no rotation
  out   = lerp(base, Texture6(uv6).rgb * Color6, Texture6.a * Color6.a)

create_eye                                out.a = Main.a * Color.a
  uvg   = (uv + grad.xy) * 2s + (0.5 - s),  s = 1 - grad.w
  c     = lerp(Color2, Color, CM(uvg).r);   m = Main.r
  vivid = saturate(m > 0.5 ? c / (2 * (1 - m)) : 1 - (1 - c) * 0.5 / m)
  out   = lerp(c * m, vivid, Blend)

create_eyewhite   out = lerp(Color2, Color, Main.r), a = 1
create_hair       col = lerp(1, Color, CM.r); col = lerp(col, Color2, CM.g); col = lerp(col, Color3, CM.b)
                  out = col * Main.rgb, a = 1
```

Two small lit shaders, as a model for the rest (`A = _ambientshadowG`):

```
toon_eyew_lod0 (eye whites, eyebrows, eyelines)        clip Main.a < 0.5;  out.a = Main.a
  S     = saturate(A.w * 0.5 + 0.5 > 0.5 ? 1 - (1 - A.w) * (1 - A.rgb) : (A.w + 1) * A.rgb)
  shade = saturate(_shadowcolor > 0.5 ? 1 - (2 - 2 * _shadowcolor) * (1 - S) : 2 * S * _shadowcolor)
  base  = Main.rgb * _Color.rgb
  out   = lerp(shade * base, base, ramp) * max(_LightColor0.rgb * 0.6 + 0.4, A.rgb)

toon_nose_lod0    out.rgb = _Color.rgb * (1 - Main.r) + Main.g;  out.a = Main.a * _Color.a
```

`main_item`, `main_opaque` and `main_skin` are long. With the bake's fixed inputs every term multiplied by specular or rim drops out. Their models are in `models.py`.

### The models, groups and templates

- `importer/tools/game_shaders/models.py` holds each shader as a numpy function (`create_eyewhite`, `toon_eyew`, `toon_nose`, `main_hair`, `create_topN`, `main_opaque`, `main_item`, `main_alpha`, `main_emblem`, `toon_eye`, `create_eye`, `create_body`, `create_head`, `main_skin`), with `lin`, `srgb`, `grade` and the KK and KKS lights. `importer/tests/host/test_shader_models.py` checks them against the Golden Samples.
- Each model has a node group named after its shader (`.KK toon_eyew`, `.KK main_hair`, `.KK create_topN`, `.KK main_skin`), with shared helpers (`.KK srgb`, `.KK linear`, `.KK grade`, `.KK graded`, `.KK shadow tint`, `.KK pattern uv`, `.KK paint uv`, `.KK eye uv`).
- The templates are built by `importer/tools/library/edit_templates.py`: `KK create_eyewhite`, `KK toon_eyew`, `KK toon_nose`, `KK main_hair`, `KK main_opaque`, `KK main_item`, `KK main_alpha`, `KK main_emblem`, `KK toon_eye`, `KK create_body`, `KK create_head`.
- The KK profile's `EDIT` tables pick a template by shader first (`shader_templates`), then by Material Role, and map bundle colours and values onto the template's params.
- `importer/tests/blender/test_edit_accuracy.py` bakes an unedited edit material of each kind and compares it with the bundle's `light` and `dark`, against the limits in `importer/tests/data/edit_accuracy.json`.

What each template covers, and what it leaves out:

| Materials | Template | Left out |
|---|---|---|
| Eye whites, eyebrows, eyelines | `KK create_eyewhite`, `KK toon_eyew` | nothing |
| Nose line | `KK toon_nose` | nothing |
| Hair (KKS's `hair_main_sun` bakes as KK's) | `KK main_hair` | the gloss's second read, the rim, the bitangent term of `_SpeclarHeight` |
| Clothes | `KK main_opaque`, `KK main_alpha`, `KK main_emblem` | the nail specular |
| Teeth, tongue, items | `KK main_item` | `_LineColorG`'s colour (taken as white) |
| Eyes (KKS's `main_eye` bakes as KK's) | `KK toon_eye` | recolouring the iris through `create_eye` (modelled and tested, not built); the expression texture |
| Body and face | `KK create_body`, `KK create_head` | `_FaceShadowG` (taken as at most 1), `_LineColorG`'s colour, the liquid |
| KKS clothes and skin | KK's templates with KKS's values | approximated: the physically based half of `Koikano/main_skin` and `main_clothes_*` (light probes, cubemaps, the ramp's other channels) |

A material whose shader no template models (a modded shader) takes the older general templates (`KK General` and the others picked by Material Role), with the Saturate option and the numpy code in `kkbp/shading/`.

### Reading a game's shaders

`importer/tools/game_shaders/dump.py` reads Unity shader assets with UnityPy (pinned in `importer/requirements-dev.txt`, in the dev venv only), cuts out each compiled program and disassembles it with `dxdis.py`, naming every constant and texture:

```
importer/.venv/bin/python -I importer/tools/game_shaders/dump.py "<name filter or *>" <output folder> <asset files...>
```

`dump.py --find FOLDER` lists which asset file holds each shader. The disassembly is the games' code and is never committed: its output goes under `importer/tests/.work/`.

- KK: `Koikatu_Data/globalgamemanagers.assets` (`toon_*`, `create_*` except `create_topN`), `abdata/chara/mm_base.unity3d` (`create_topN`), `abdata/chara/54/chara_data_00.unity3d` (`main_opaque`, `main_item`, `main_hair`), `54/chara_mat_00.unity3d` (`main_skin`), `co_bot_13.unity3d` (`main_alpha`), `bo_hair_b_13.unity3d` (`main_hair_front`).
- KKS: `abdata/chara/mm_base.unity3d` (`create_*`), `bo_head_00.unity3d` (`main_skin`, `main_eye`, `main_eyew`, `main_nose`), `co_bot_00.unity3d` (`main_clothes_opaque`, `main_clothes_alpha`), `ao_arm_00.unity3d` (`main_clothes_item`), `bo_hair_b_00.unity3d` and `ao_head_00.unity3d` (`hair_main_sun_front`, `hair_main_sun`).
- The program to read is the fragment one (type 17) whose keywords are `DIRECTIONAL` alone (KK) or the fewest (KKS).

### Adding a shader

1. Dump and read the shader.
2. Write its model in `models.py`, with a host test against a Golden Sample, and fit any constants the bundle doesn't carry.
3. Write the node group and the template (`edit_templates.py`), and its Template Description with `graded=True`.
4. Add the profile's template row, colours and values.
5. Record its accuracy in `importer/tests/data/edit_accuracy.json`.

Notes for writing the groups:

- Texture UV transforms (`_ST`) are the image node's own mapping. The create shaders' extra UV maths (`paint`, `tex4uv`, `hokuro`, `grad`, pattern scale) goes in a group, fed by vector inputs.
- HSV steps are per-channel arithmetic built from Math nodes, not Blender's Hue/Saturation node, which rounds differently.
- `saturate` is a clamped Math node; a conditional move is a Mix with a 0-or-1 factor from a Greater Than.
- The render target clamps at 1, so the group output is clamped.
- Pattern masks repeat (scale up to 20); overlays clamp. Missing decals and overlays are switched off by their colour's alpha.
- `main_skin` reads the mesh's vertex colour for its overlays; the bake copies it to its flat mesh.
