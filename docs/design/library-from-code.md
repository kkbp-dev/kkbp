# The library from code, and edit templates from the game's shaders

Status: **agreed** (2026-11-11; every proposal in "Decisions" accepted). Part A is implemented
([ADR 0040](../adr/0040-the-library-is-built-from-code.md), D66). Part B is in progress ([ADR 0041](../adr/0041-edit-templates-follow-the-games-shaders.md),
D67): KK's eye whites, eyebrows, eyelines and nose line are done; "Part B progress" at the end lists what is left. Plan for issues #29 and #30. Terms are in [CONTEXT.md](../../CONTEXT.md).

Two pieces of work, in this order:

- **Part A (issue #29):** delete `importer/templates-src/KK Shader V9.blend`. Build `library.blend`,
  `rigify.blend`, `face_cards.blend` and `outlines.blend` from Python code plus plain asset files that git tracks.
- **Part B (issue #30):** replace the legacy edit templates (the materials on V9's `Text.002` object) with
  node groups that follow the games' own shaders, and update ADR 0026.

Part A comes first because Part B's new groups are written in Part A's format.

## What the investigation found

### Issue #29: what still comes from the old .blend

No runtime code opens V9. Only two build scripts do: `importer/tools/rework_templates.py` and
`importer/tools/build_hook_assets.py`. But almost everything in the four built files is V9 content:

| Built file | From V9 | Made in code today |
|---|---|---|
| `library.blend` (17 materials, 50 node groups, 941 group nodes, 12 images) | 46 node groups, 15 of the 17 materials, 11 images | `.Principled`, `.Gag UV`, `.Gag pick`, `.Gag output`; the `Gag` material; `KK Eye` (a copy of KK Light Dark plus nodes); `Lut_TimeDay.png` (file beside V9) |
| `rigify.blend` | 28 widget meshes in `Bone Widgets` | nothing |
| `face_cards.blend` | 2 card meshes with shape keys, the 10-bone rig, 4 bone-shape meshes, 5 materials, 4 groups, the mouth atlas, `Eye_White_Alpha` | `SVS Eye_White_Alpha.png` (file beside V9), the WebP re-encode |
| `outlines.blend` | 4 images | nothing |

The shader variant groups the issue asks about (`.Cycles`, `.Cycles Classic`, `.Cycles no shadows`,
`.Eevee Mod`, `.SDF_Cel_Shader`, `.Light Rotation Catcher`) sit in V9 on the material `node easy access`
of the object `geometry nodes holder`; `rework_templates.py` keeps them with fake users
(`VARIANT_GROUPS`, `VARIANT_EXTRAS`). `.KK` and `.SVS` come from the materials on `Plane.001`.

Things in V9 worth knowing before rebuilding it:

- Node types in use: about 55, nearly all `ShaderNodeMath` (210), `ShaderNodeMix` (145), group nodes (149),
  image nodes (115), frames (262) and reroutes (55). Also 2 geometry node groups (`.Light Rotation Catcher`
  is kept; `.Geometry Nodes`/`.Flatten to UV map` are not), `ShaderNodeValToRGB` (18), one `ShaderNodeFloatCurve`,
  `GeometryNodeMenuSwitch` (4), and interface panels on `.SDF_Cel_Shader`.
- Drivers: `frame` drivers on Value nodes (legacy gag groups, not kept), and on the `Pupil L/R card`
  materials four drivers each reading the `Face card rig` transforms (kept, in `face_cards.blend`).
- Images: `Template: Black` is broken in V9 (size 0 x 0, not packed, TARGA). Three images are
  Blender-generated blanks: `Template: Placeholder` (24 x 24 white), `Template: BlackWithAlpha`
  (24 x 24 black), `Template: Normal detail placeholder` (1024 x 1024, colour 0.5, 0.5, 0.5, 0).
  `Template: orbita_1k.exr` is a 1.3 MB EXR (Linear Rec.709, premultiplied). `Eye_White_Alpha` is Non-Color.
- V9 material leftovers not used today: `KK Simple`, `KK Glasses`, `KK Eyeline down`, `KK Eyeline kage`,
  `KK Gag00/01/02`, `SVS Gag`, `Outline General`, `Outline Body`, `Misc`, and about 20 groups only they use.

### Issue #30: how the games shade

The games' real shaders can be read. I extracted and disassembled them from the installed game
(prototype in `importer/tools/game_shaders/`, output in `importer/tests/.work/game-shaders/kk/`, which
git ignores). `KKShadersRecreated-main/` beside the repository (xukmi's recreation, already credited in
NOTICE) has readable HLSL for the lit shaders (skin, item, hair, eye, eye white) but **not** the create
shaders; the disassembly has both.

Each KK/KKS material is drawn in two stages, and the edit templates must copy both:

1. **Create shader** (`Shader Forge/create_body`, `create_head`, `create_topN`, `create_eye`,
   `create_eyewhite`, `create_hair`; KKS `Koikano/create_skinbody`, `create_skinface`, `create_topN`,
   `create_eye`, `create_eyew`): composites the uncoloured base texture, masks and the Character's
   colours into the material's `_MainTex`. The bundle carries its inputs as `extensions.kk.create` and
   its output as the material's `main` texture.
2. **Lit shader** (`main_skin`, `main_opaque`/`main_item`/`main_alpha`, `main_hair`/`main_hair_front`,
   `toon_eye_lod0`, `toon_eyew_lod0`, `toon_nose_lod0`; KKS `Koikano/main_skin`, `main_clothes_opaque`,
   `main_clothes_item`, `hair_main_sun`, `hair_main_sun_front`, `main_eye`, `main_eyew`, `main_nose`):
   shades `_MainTex` with overlays, the detail and line masks, `_ShadowColor` and global light values.
   The bundle carries its output as `main.light` and `main.dark`.

What the exporter's bake fixes (`exporters/kk/src/Bake.cs`), which makes the lit shader a pure
per-pixel function the nodes can copy exactly:

- The material is drawn on a flat quad (and, for mesh-dependent shaders, the mesh flattened into UV
  space) through an orthographic camera facing it, so `dot(normal, view) = 1`: rim light is 0.
- `_AlphaMask`, `_NormalMap`, `_NormalMapDetail`, `_NormalMask` are cleared and `_SpecularPower`,
  `_SpecularPowerNail`, `_nip_specular` are 0: no specular, flat normal.
- Light from the front for `light` (lambert 1, ramp at its lit end), from behind for `dark`
  (lambert at most 0, ramp at its dark end). No shadow map.
- Outline and shadow-caster passes are off. KKS's AmplifyColor grade is off.

So `light` and `dark` are the forward pass with `ramp = 1` and `ramp = 0`, and nothing else varies.

**A likely cause of today's inaccuracy:** both games' player settings have `m_ActiveColorSpace = 1`,
linear. Textures and colours reach the shaders linear. `kkbp/shading/` (legacy's maths) applies the
shader formulas to sRGB-encoded values. Blender's nodes work in linear too, so nodes that copy the
shader maths one to one should need no colour-space conversion and no LUT. This is a hypothesis: the
accuracy test below decides it, and render-texture formats could still add an encode or decode step.

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

`main_item`/`main_opaque` and `main_skin` are long (about 290 and 400 instructions); their readable
form is `KKShadersRecreated-main/Shaders/Item/MainItem.shader` (`frag` of the Forward pass, with
`ShadeAdjustItem` in `KKItemDiffuse.cginc`) and `Skin/SkinMain.shader` (with `GetDiffuse`,
`MapValuesMain` in `KKDiffuse.cginc`). With the bake's fixed inputs they reduce a lot: every term
multiplied by specular or rim drops out, and `finalRamp` is the constant 1 or 0.

Globals the lit shaders read that the bundle doesn't carry: `_ambientshadowG`, `_LineColorG`,
`_linewidthG`, `_LightColor0`, the `_RampG` texture, `_FaceShadowG`, `_FaceNormalG`. `kkbp/shading/`
already assumes the maker's values (ambient shadow 0.15 with alpha 0.15, light term 1.0656).

## Decisions (agreed)

1. **Source format for node groups: one generated Python module per group, kept by hand afterwards.**
   A one-time decompiler reads the current built files and writes builder code; the result is committed
   and V9 is deleted. Alternative: JSON per group plus one generic builder; smaller code, but harder to
   read in review and to write new groups in by hand. Proposal: Python modules through a small builder
   helper (below).
2. **Keep the decompiler as a tool** (`scripts/export-library-nodes.sh`), so a group edited visually in
   Blender can be written back to its module. This replaces ADR 0018's "the edit has to be written
   back into the script" by hand. Proposal: yes.
3. **Meshes and rigs as JSON** (`importer/library-src/meshes/*.json`, `rigs/*.json`): 28 widgets, 2
   card meshes, 4 bone shapes, the card rig. Text, so git diffs them. Proposal: yes.
4. **Images as files in `importer/library-src/images/`**, through Git LFS like every PNG today.
   `.gitattributes` needs lines for `*.exr` and `*.webp`. The mouth atlas is stored as the WebP that
   `face_cards.blend` holds now (extracting V9's PNG and re-encoding would not be byte-identical).
   The three generated blanks and the fixed `Template: Black` are made in code, not stored.
5. **The legacy edit templates are removed, not kept beside the new ones.** `KK Body`, `KK Face`, etc.
   and the about 30 groups only they use leave `library.blend`. Alternative: keep them one release as
   a fallback option. Proposal: remove, once the accuracy test shows the new ones are closer on every
   material of the kk and kks samples.
6. **Saturation (ADR 0026) goes away** if decision 5's test passes without it: the Saturate dropdown,
   `scene.kkbp_edit_saturate`, `saturated_roles`, `Lut_TimeDay.png`, and the LUT half of `kkbp/shading/`.
   Removing an operator option the hook interface documents may be a hook-interface version change;
   check `docs/hook-interface.md`. Proposal: remove if the numbers allow, otherwise keep and say why in the ADR.
7. **Global light values stay constants in the Game Profile**, checked by the accuracy test. Alternative:
   the exporter captures them (a contract change, needs its own OK). Proposal: constants; revisit only
   if the test can't be met.
8. **The games' shader disassembly is never committed.** It is the games' code. The extraction tool is
   committed; its output goes under `importer/tests/.work/` (ignored). The node modules are our own
   implementation with comments giving the maths, as `kkbp/shading/` already does.
9. **SVS edit templates are out of scope.** SVS has none today (`profile.edit.templates` is empty); its
   shaders (`LIF/*`, Unity 2022, IL2CPP) are issue #62.
10. **Template version:** `TEMPLATE_VERSION` and `ASSET_VERSION` go to 2 with Part B (new groups);
    Part A alone changes nothing a user sees and keeps 1.
11. **Blender version.** The snap at `/snap/blender/current` is now **5.3.0** (built 2026-11-10), while
    `harness.toml` asks `min` for 5.2. Settled: the library is generated on the minimum build, as the
    build scripts already say, which on this computer is Blender 5.2.2 LTS at
    `~/.local/opt/blender-5.2.2/blender` (the dev venv already uses it), selected with
    `KKBP_BLENDER_MIN`. `harness.toml` is left as it is; pointing it at that build is a separate change.

## Part A: the library from code

### Layout

```
importer/library-src/                      replaces importer/templates-src/
  README.md
  images/                                  LFS: png, exr, webp
  meshes/*.json   rigs/face_card_rig.json
importer/tools/library/
  nodes.py            the builder helper
  export_nodes.py     the decompiler (decision 2)
  export_meshes.py    one-time: meshes and rig to JSON
  fingerprint.py      structural dump of a .blend, for the equality check
  build.py            builds all four files; replaces rework_templates.py and build_hook_assets.py
  groups/<name>.py    one module per node group
  materials/<name>.py one module per template material
scripts/build-library.sh                   replaces rework-templates.sh and build-hook-assets.sh
```

`build.py` starts from `--factory-startup` with an emptied file (remove the default cube, camera,
light, collection and world users as today's files have them), never from a `.blend`.

### The builder helper (`nodes.py`)

Thin, so modules read like the graph. Needed operations, all present in today's scripts in some form
(`_new_group`, `_math`, `_socket`):

- `group(name, kind, inputs, outputs, panels)`: interface sockets with type, subtype, default, min,
  max, `hide_value`, description, panel; order matters (code reads sockets by name, users see order).
- `node(tree, idname, name, label, location, **props)`, `link(a, b)`, `frame(...)`, `reroute(...)`.
- Sockets addressed by **identifier**, not name or index (`ShaderNodeMix` has `A_Color`, `B_Color`,
  `Factor_Float`, `Result_Color`; several nodes repeat socket names).
- Set node properties before sockets and links: `data_type`, `operation`, `blend_type`, `mode` change
  which sockets exist.

### The decompiler (`export_nodes.py`)

Reads a built `.blend` and writes one module per group and material. For every node it must emit:

- `bl_idname`, `name`, `label`, `location`, `width`, `hide`, `mute`, `parent` (frame), `use_custom_color`,
  `color`; for frames `label_size`, `shrink`; for group nodes the `node_tree` name.
- Every RNA property of the node that isn't read-only and differs from a fresh node of the same type:
  walk `node.bl_rna.properties`, skip the base `Node` ones handled above, compare with a scratch node.
  This covers `operation`, `use_clamp`, `blend_type`, `data_type`, `clamp_factor`, `clamp_result`,
  `factor_mode`, `interpolation`, `extension`, `projection`, `uv_map`, `attribute_name`, `vector_type`,
  `mode`, `space`, `invert`, and whatever a future node adds.
- Pointer and collection properties the walk can't copy generically, by hand: `image` (by name),
  `color_ramp` (interpolation, color_mode, elements' position and colour), `mapping` on the float
  curve (points, handle types, extend, clip), `texture_mapping` and `color_mapping` on image nodes,
  `image_user`, menu-switch `enum_items`, and geometry-node items collections.
- Every unlinked input's `default_value`, and outputs' for `ShaderNodeValue`/`ShaderNodeRGB`; `hide`
  and `enabled` are derived, skip them; keep socket `hide` if set.
- Links as (from node, from socket identifier, to node, to socket identifier), in `tree.links` order;
  keep `is_muted`. Multi-input order only matters for geometry nodes' join; check `.Light Rotation Catcher`.
- Drivers on the tree (`animation_data.drivers`): data path, expression, variables and their targets.
  The face-card drivers target the rig object, so they are built after the rig.
- Group and material custom properties (`kkbp_template_version`, `kkbp_asset_version`).
- For materials: `surface_render_method`, `use_transparent_shadow`, `use_backface_culling`,
  `displacement_method`, `use_fake_user`, `diffuse_color`, and the other settings that differ from a new material.

Order: emit groups so that a group comes after the groups it contains (topological; no cycles exist).

### Equality check (how Part A is proved)

`fingerprint.py` dumps everything listed above for a `.blend` as sorted JSON, with floats rounded to
6 places, images as (name, size, colourspace, alpha mode, sha1 of pixels), meshes as (vertices, edges,
faces, UVs, shape keys, vertex groups and weights, material slots), objects as (type, parent, parent
bone, transforms, modifiers and their settings, constraints, custom shapes, bone collections).

1. Before touching anything: fingerprint the four committed files into `importer/tests/.work/`.
2. Decompile them (not V9: the built files already hold `rework_templates.py`'s changes, so those
   changes are captured without porting that script).
3. Build with `build.py`, fingerprint again, diff. **Done when the diff is empty**, apart from an
   agreed list: `Template: Black` becoming a real 4 x 4 black image, `Lut_TimeDay.png`'s absolute
   file path, and image `filepath` strings (V9's are placeholder text).
4. Then `scripts/test-importer.sh` in full: the harness test that checks every Template Description
   and hook asset name against the files, and the snapshots, must pass with **no** re-record.

Only after step 4 passes: delete `importer/templates-src/KK Shader V9.blend`, the two old tool scripts
and the two old shell scripts, and move `Lut_TimeDay.png` and `SVS Eye_White_Alpha.png` into
`library-src/images/`.

### One-time extraction from V9 and the built files

- Images: save each packed image's `packed_file.data` bytes straight to a file (don't re-save through
  Blender, which re-encodes): `sdf 5.png`, `SDF hair contact shadows mask 2.png`, `Template: Body neck
  shadow`, `Template: Face shinymask`, `Template: nose mask for pinkness`, `Template: SFW alpha mask.png`,
  `Template: orbita_1k.exr`, `KK OutlineMask.png`, `SVS OutlineMask.png`, `Eye_White_Alpha`,
  `MouthAtlas.webp` (from `face_cards.blend`). The build loads each, packs it, and sets name,
  colourspace and alpha mode from a table in `build.py`.
- Meshes and the rig: `export_meshes.py` writes the JSON once. The card rig needs bone heads, tails,
  rolls, parents, `use_connect`, `use_deform`, the `Pupil Clip` bone collection, pose constraints
  (`LIMIT_LOCATION`, `LIMIT_ROTATION` with all their settings), custom shapes and their transforms,
  rotation modes, and locks. The card meshes need the Armature and Subdivision modifiers, four vertex
  groups, shape keys `Basis` and `Key 1`, and the mouth card's bone parenting to `Mouth` (with
  `matrix_parent_inverse`).

### Files to change in Part A

- `importer/tools/`: add `library/`; delete `rework_templates.py`, `build_hook_assets.py`.
  `make_svs_eye_white_mask.py`: default output path.
- `scripts/`: add `build-library.sh` (same Blender lookup as today's two); delete the two old ones.
- `importer/tests/host/test_shading.py:13`: `LUT_FILE` path.
- `importer/tests/blender/test_hook_assets.py:21`: the message naming the script.
- `importer/kkbp/library/__init__.py`, `hook_assets.py`, `importer/kkbp/templates.py:298`: comments.
- `.gitattributes`: `*.exr`, `*.webp`.
- Docs: `CLAUDE.md` (the "Never edit `library.blend`" rule, the Commands table, "A new Hook"),
  `importer/README.md` (the layout table and the two rebuild sections), `NOTICE` (still credit the
  legacy importer's V9 as the origin of the node groups and assets), `docs/design/README.md` (D15),
  `docs/design/material-template.md`, `docs/design/hooks-and-tools.md:160`, ADR 0037's rebuild note.
- A new ADR (0039) superseding ADR 0018 and ADR 0024's "built from the legacy file"; mark those two
  superseded rather than rewriting them.

## Part B: edit templates from the game's shaders

### Getting the shaders

`importer/tools/game_shaders/` holds a working prototype (untracked; review before committing):

- `dxdis.py`: a small DXBC shader-model-4 disassembler. Enough for these shaders; it prints opcodes
  with `_sat`, operands with swizzles, negation and abs, and immediates.
- `dump.py`: reads Unity shader assets with UnityPy, decompresses the LZ4 blob, cuts out each DXBC
  program, and names constants and textures from the binding records Unity stores after the bytecode.

  ```
  importer/.venv/bin/python -I importer/tools/game_shaders/dump.py \
      "<name filter or *>" <output folder> <asset files...>
  ```

  UnityPy is pinned in `importer/requirements-dev.txt`, so `scripts/setup-importer-dev.sh` puts it
  in the dev venv (never into Blender).

Where KK's shaders are: `Koikatu_Data/globalgamemanagers.assets` (the `toon_*` and `create_*` set),
`abdata/chara/mm_base.unity3d` and `oo_base.unity3d` (`create_topN`, `main_skin`, `main_item`).
`main_opaque`, `main_alpha`, `main_hair` and `main_hair_front` are in other bundles (clothes and hair);
`grep` can't find them because bundles are compressed, so load bundles with UnityPy and list shader names.

Known limits of the prototype, to fix first:

- **KKS** (Unity 2019): `offsets`, `compressedLengths` and `decompressedLengths` are lists per
  platform, so `dump.py` fails at the decompress call. Platform 4 (D3D11) is present, so the DXBC part
  is unchanged; only the blob indexing needs the newer layout.
- Float properties share a vec4 in the constant buffer. The annotation names the whole vec4 after one
  of them (`_PatternScale1u.z` is really another float). Map by byte offset: `offset // 16` is the
  register, `(offset % 16) // 4` the component.
- With more than one constant buffer, texture names can be wrong (`toon_eyew` shows `_RampG` as
  `tex:_WorldSpaceLightPos0`). Take texture names only from records whose third int's low byte is a
  texture dimension and that sit in the texture section.
- Pick the right program: fragment programs are type 17; the forward pass without a shadow map is the
  one with keywords `['DIRECTIONAL']` only, and the largest of those per shader.

Use the disassembly as the reference for the create shaders and to confirm that KKShadersRecreated
matches the game for the lit ones (it was made for KK; KKS's `Koikano/*` may differ and must be read).

### What the measurements found (2026-11-11)

Numpy models of the eye-white shaders, compared pixel by pixel with the kk and kks Golden Samples,
settled the colour-space question and found a step the plan didn't have:

- **Every bundle PNG except `light` and `dark` holds the linear values the shader samples.** The
  exporter copies each texture through a linear render target (`Materials.Read`), which decodes an
  sRGB texture as it reads it and writes the result unencoded. So `main`, the masks and the create
  inputs are data: they go into Blender as Non-Color and are used as they are. Read decoded instead,
  the eyelines' fit fails (error 0.1 to 0.2 against 0.005).
- **Colours are linearised**: the shader sees `lin(colour)` of the bundle's sRGB-encoded colours.
  `create_eyewhite` is exactly `lerp(lin(_Color2), lin(_Color), main.r)`, stored unencoded (fit
  residual 0.0001).
- **The `light` and `dark` bakes are sRGB-encoded and then colour graded** by the maker camera's
  AmplifyColor LUT, `Lut_TimeDay.png`, in **both** KK and KKS (the KKS bake clears only the grade's
  mask). Without the grade no per-channel factor fits (error 0.02 to 0.03); with it, the eye white's
  light factor is 1.0 per channel (error 0.0002 to 0.004). So the grade is the last step of every edit
  template, done in nodes, not a saturation of the input textures. This is why ADR 0026 found the
  hair and eyebrows closer saturated: the legacy templates graded the wrong thing at the wrong step.
  Decision 6's condition doesn't hold: the LUT stays, inside the templates; the Saturate option and
  the input-texture saturation go.
- **KK's light constants**: `_LightColor0` term 1.0, `_ambientshadowG` = 0.15 in every channel and
  alpha (ambient shadow S = 1 - 0.85² = 0.2775, legacy's constant), ramp 1 lit and 0 dark. With these,
  KK's `toon_eyew` gives the eye white, eyebrow and eyelines within 0.001 to 0.005 of the bundle.
- **KKS's shaders are different**, not KK's renamed: `Koikano/main_eyew` mixes `_ambientshadowG` with
  the scene's light-probe ambient (`unity_SHA*`) by `_KanoVerShift`, uses a 0.67 / 0.33 light term and
  desaturates the light by 0.75 towards its luminance on the dark side. Its constants must be fitted the
  same way (KKS eye white: light factor 1.0, dark factor about 0.8, 0.9, 1.02).

The fitting scripts used were throwaway; write the models properly as below.

### The new templates

One edit template per (create shader, lit shader) pair the profiles need, each a material with image
nodes on top and three kinds of group underneath:

- `.create <name>`: the create shader. Inputs: its textures' colour and alpha, colours and vectors.
  Output: colour and alpha, the game's composited `_MainTex`.
- `.lit <name>`: the lit shader's Forward pass with the bake's fixed inputs. Inputs: the composited
  main, the overlay, detail and line textures, colours, floats, and a `Ramp` input. Output: colour, alpha.
  Used twice per material, with `Ramp` 1 (light) and 0 (dark).
- Shared helpers, written once: `.shade adjust item` (`ShadeAdjustItem`), `.shade adjust skin`
  (`MapValuesMain`'s second output), `.ambient shadow` (the `finalAmbientShadow` block), `.line blend`
  (the `_LineColorG` blend), `.paint uv` (the offset, scale and rotation), plus the existing
  `.Combine colors` (light and dark into the Eevee toon mix the bake renders) and `.Toon shading`.

Notes for writing the groups:

- Texture UV transforms (`_ST`) are the image node's own mapping or a `Mapping` node, as
  `templates.set_position` does today; the create shaders' extra UV maths (`paint`, `tex4uv`,
  `hokuro`, `grad`, pattern scale) goes in the group, fed by vector inputs.
- `main_skin` reads `uv1`, `uv2`, `uv3` and vertex colour for the overlays. The importer's UV map names
  are in `steps/mesh.py` `UV_NAMES` (`uv_nipple_and_shine`, `uv_underhair`, `uv_eyeshadow`); check
  that the vertex colour the shader multiplies the UV by reaches Blender, or bake it into the UV maths.
- HSV steps in `ShadeAdjust*` are per-channel arithmetic; build them from Math nodes (as
  `shading._hue_tint` does in numpy), not from Blender's Hue/Saturation node, which rounds differently.
- `saturate` is a clamped Math node; `movc` is a Mix with a 0-or-1 factor from a Greater Than.
- The render target clamps at 1: the light term 1.0656 clips bright colours. Clamp the group output.
- Sampler state: check each texture's wrap mode (repeat or clamp) on the game material; pattern masks
  repeat (scale up to 20), overlays clamp.

Mapping onto the existing code, which already separates data from nodes:

- `importer/kkbp/library/descriptions.py`: replace `_EDIT_TEMPLATES` with descriptions of the new
  templates. `params` then name the game's own properties (`color`, `color2`, `color1_2`, `shadow_color`,
  `shadow_extend`, `detail_b_line_g`, ...), one param per property instead of `.light`/`.dark` pairs.
- `importer/kkbp/profiles/kk.py` `EDIT`: `templates` keyed by Material Role **and** by shader where one
  Role has several (clothes: `main_opaque`, `main_alpha`, `main_item`, and no create); `textures` and
  `colors` become near-identity maps from Raw Properties (`create:_Color` → `color`). The `how` column
  (`item`, `skin`, `eyew_dark`) disappears: the nodes do the shading. `values` shrinks to floats copied
  from the bundle. Add the constants of decision 7.
- `importer/kkbp/tools/edit_material.py`: `_set_colors` loses the dark-colour maths; `_fill_textures`
  loses `main.dark` (`shading.dark_pixels`) and, if decision 6 holds, saturation and `_derived`.
  Vectors (`_paint1`, `_grad`, ...) need a setter; today only colours and floats are set.
- `importer/kkbp/shading/`: delete what nothing calls afterwards. Keep `test_shading.py`'s shader
  hand-calculations as tests of the node groups instead, if they still apply.
- ADR 0025 (texture group copied per material) stays true only if the new templates keep image nodes
  in a copied group; simpler is image nodes at the material's top level, as Light Dark has. If so,
  `copies` and ADR 0025 go: say so in the new ADR.

### Accuracy test (how Part B is proved)

ADR 0026's measurement, as a kept test. For every editable material of the kk and kks Golden Samples
(copies, never `contract/samples/` itself):

1. **Create stage:** bake `.create` alone (emission) and compare with the bundle's `main` texture.
2. **Whole material:** `edit()` then bake light and dark as `save()` does, without saving, and compare
   with the bundle's `main.light` and `main.dark`.

Metric: mean absolute difference per channel over pixels opaque in both, on sRGB-encoded values, as
ADR 0026 used (its numbers: unsaturated legacy 0.03 to 0.17). Record before (legacy templates) and
after in the ADR. Proposed bar: every material better than legacy, and create stage under 0.01. No
existing script does this measurement (none found under `importer/tests`, `importer/tools` or
`scripts`); put it in `importer/tests/harness/` beside the snapshot checks, with thresholds per material.

Work one shader at a time, simplest first, and measure each before the next: `create_eyewhite` +
`toon_eyew` (eye whites, eyebrows, eyelines), `toon_nose`, `create_hair`/`main_hair`, `create_topN` +
`main_opaque`, `create_eye` + `toon_eye`, `create_body` and `create_head` + `main_skin`. The first one
settles the colour-space question for all of them.

### Files to change in Part B

- `importer/tools/library/groups/`, `materials/`: the new modules; remove the legacy edit ones (decision 5).
- `importer/kkbp/library/descriptions.py`, `sets.py` if needed, `__init__.py` (`EXTRAS["lut"]`, versions).
- `importer/kkbp/profiles/kk.py`, `profiles/__init__.py` (the `edit` rules' shape), `kks.py`.
- `importer/kkbp/tools/edit_material.py`, `bake.py` if the bake reads `.Combine colors` by name,
  `importer/kkbp/ui/` (the Saturate dropdown), `importer/kkbp/shading/`.
- Tests: `importer/tests/blender/test_tool_edit_material.py`, `importer/tests/host/test_shading.py`,
  the description-against-library harness test, the new accuracy test; re-record snapshots only if a
  snapshot covers edit materials.
- Docs: ADR 0026 updated as issue #30 asks (or superseded by a new ADR, with the measured numbers),
  ADR 0025, `docs/design/README.md` (D37 to D42, D44), `docs/design/hooks-and-tools.md`,
  `docs/hook-interface.md` if an option is removed, `CONTEXT.md` for new terms (create stage, lit stage),
  `NOTICE` (KKShadersRecreated is already credited).

## Order of work

1. Get the user's OK on the decisions. Settle the Blender build (decision 11).
2. Part A: `fingerprint.py` and baseline; `nodes.py`; `export_nodes.py`; `export_meshes.py` and image
   extraction; `build.py`; empty diff; full test run; delete V9; docs and ADR. Commit in those steps.
3. Part B: fix `dump.py` for KKS and dump both games; the accuracy test with the legacy numbers; then
   one shader pair at a time; remove legacy templates and saturation; docs and ADR; version 2.

## Part B progress

Done (ADR 0041, D67):

- `importer/tools/game_shaders/dump.py` and `dxdis.py`: dump and disassemble both games' shaders, with
  every constant and texture named (Unity 5.6 and 2019 layouts). `dump.py --find FOLDER` lists
  which asset file holds each shader. Where they are: KK `Koikatu_Data/globalgamemanagers.assets`
  (toon_*, create_* but topN), `abdata/chara/mm_base.unity3d` (create_topN), `abdata/chara/54/chara_data_00.unity3d`
  (main_opaque, main_item, main_hair), `54/chara_mat_00.unity3d` (main_skin), `co_bot_13.unity3d`
  (main_alpha), `bo_hair_b_13.unity3d` (main_hair_front); KKS `abdata/chara/mm_base.unity3d` (create_*),
  `bo_head_00.unity3d` (main_skin, main_eye, main_eyew, main_nose), `co_bot_00.unity3d`
  (main_clothes_opaque, main_clothes_alpha), `ao_arm_00.unity3d` (main_clothes_item),
  `bo_hair_b_00.unity3d` and `ao_head_00.unity3d` (hair_main_sun_front, hair_main_sun). The forward
  program to read is the fragment one (type 17) whose keywords are `DIRECTIONAL` alone (KK) or the
  fewest (KKS).
- `importer/tools/game_shaders/models.py`: `lin`, `srgb`, `grade`, the KK and KKS lights,
  `create_eyewhite`, `toon_eyew`, `toon_nose`; `host/test_shader_models.py` checks them on both samples.
- Groups `.KK srgb`, `.KK linear`, `.KK grade`, `.KK graded`, `.KK create_eyewhite`, `.KK toon_eyew`,
  `.KK toon_nose`, `.KK shadow tint`, `.KK main_hair`, `.KK hair gloss uv`, and the clothes' (below);
  templates `KK create_eyewhite`, `KK toon_eyew`, `KK toon_nose`, `KK main_hair`, `KK main_opaque`,
  `KK main_item`, `KK toon_eye`, `KK create_body`, `KK create_head`, built on
  `importer/tools/library/edit_templates.py`; KK's profile points eye whites, eyebrows, eyelines and
  the nose line at them, and KKS's profile inherits them with its own maker light.
- `blender/test_edit_accuracy.py`, with `importer/tests/data/edit_accuracy.json` (the legacy numbers are
  in ADR 0041).

Left, in this order (each: dump, model in models.py with a host test, fit constants, node group,
template, Template Description with `graded=True`, profile row and colours, re-record the accuracy):

1. ~~**KKS's light.**~~ Done: under the bake `Koikano/main_eyew` is KK's toon_eyew with three other
   constants (ADR 0041), so KKS shares KK's templates and its profile sets `ambient`,
   `ambient_strength` and `shadow_floor`. `Koikano/main_nose` bakes as KK's nose. Each further KKS
   shader: check first whether it reduces the same way (compare the KK and KKS bakes of the same card:
   light within 0.02 means only the shadow side differs).
2. ~~**KK hair**~~ Done: `models.main_hair`, `.KK main_hair`, `.KK hair gloss uv`, `KK main_hair`
   (ADR 0041). The gloss reads the second UV map; the host test rasterises it from the outfit's glTF
   (`_second_uv`), with the exporter's island order and the quad's own UVs in the gaps. KKS's
   `hair_main_sun` bakes as KK's with KK's constants, so KKS uses the template too. Link hair copies
   the colours. Left out: the gloss's second read, the rim, `_AnotherRamp` (white when absent; check a
   hair that has one), the bitangent term of `_SpeclarHeight`.
3. ~~**KK clothes**~~ Done: `models.create_topN`, `main_opaque`, `main_item`, `item_tint`; groups
   `.KK create_topN`, `.KK pattern uv`, `.KK item tint`, `.KK main_opaque`, `.KK main_item`; templates
   `KK main_opaque`, `KK main_item`, picked by shader (`EDIT["shader_templates"]`, before the Role).
   Fitted globals: `_LineColorG.a` 0.065 and `_linewidthG` 0.32 (`models.LINE_*`; they trade off).
   The other ramp follows the main one under the bake. `main_item` (teeth, tongue, items) differs from
   `main_opaque` in its second half: a scaled tint, the detail mask's red as a highlight, linear lines.
   Not modelled: `main_alpha` (no sample uses it; it keeps the legacy template), `_LineColorG`'s colour
   in `main_item` (white), the nail specular. **`.KK grade` reads its LUT with Closest and filters by
   hand**: Eevee mipmaps a Linear image by the coordinate's change between pixels, and a LUT's
   coordinate is the colour, so sharp texture edges read a blurred LUT (blue lines on the clothes,
   and what was left of the eyelines' error). KKS's clothes (`main_clothes_opaque`, `main_clothes_item`)
   keep the legacy templates: KK's models fit them to 0.005 to 0.055, better than legacy but not
   modelled, and KKS's tongue is 0.27 off, so `main_clothes_item` differs.
4. ~~**KK eyes**~~ Done: `models.toon_eye`, `eye_rotation`, `create_eye`; groups `.KK eye uv`,
   `.KK toon_eye`; template `KK toon_eye` on the eyes' Roles (KKS's too: `Koikano/main_eye` bakes as
   KK's, measured). It shades the material's own composited iris, as legacy did: the iris's offset
   and scale are on that texture, not on the create textures. Recolouring through `create_eye` in the
   template (the `_grad` UV, the vivid-light blend) is modelled and tested but not built. The
   expression texture (`_exppower`) is left out.
5. ~~**KK body and face**~~ Done: `models.create_body`, `create_head`, `paint_uv`, `face_uv`, `mole_uv`,
   `skin_overlays`, `nipple_uv`, `skin_tint`, `main_skin`; groups `.KK create_body`, `.KK create_head`,
   `.KK paint uv`, `.KK face uv`, `.KK skin overlay uv`, `.KK skin overlays`, `.KK main_skin` (with
   `importer/tools/library/decals.py`); templates `KK create_body`, `KK create_head`. The bake copies
   the mesh's vertex colour to its flat mesh. Missing decals and overlays are switched off by their
   colour's alpha (value rules); overlays clamp. Not modelled: `_FaceShadowG` (taken as at most 1),
   `_LineColorG`'s colour (white), the liquid. The face's dark side is 0.017 from the bake, the model 0.011.
6. **KKS** for 3 and 5 (its hair and eyes bake as KK's): `main_clothes_opaque`, `main_clothes_item`
   (its tongue is 0.27 off KK's model), `create_skinbody`, `create_skinface`, `Koikano/main_skin`.
7. When no Role uses a legacy edit template: delete them and the groups only they use, the Saturate
   option (`scene.kkbp_edit_saturate`, the operator's option; check `docs/hook-interface.md`), the
   LUT and dark-texture half of `kkbp/shading/`, `saturated`, `saturated_roles`,
   `plain_color_mask_shaders` and the `how` kinds nothing uses; update ADR 0026 and 0025 to say so.
