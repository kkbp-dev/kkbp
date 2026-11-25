# SVS's edit templates follow its LIF shaders under the maker's bake light, with no grade

SVS needed edit templates made as KK's and KKS's are ([ADR 0041](0041-edit-templates-follow-the-games-shaders.md)): each game shader read from the installed game, written as a numpy model that gives back the Golden Sample's bakes, then as nodes. SVS is Unity 2021 with URP, and three things differ from KK.

- **The shaders had to be read anew.** Unity 2021 keeps a program's constants in the pass and in a parameter blob per variant, not after its bytecode, so `importer/tools/game_shaders/dump.py` reads that layout too (KK's and KKS's dumps are byte-identical). Each shader has up to 192 keyword variants; the exporter's `probe_bake` request records which keywords every light and dark bake had.
- **The bake isn't graded.** SVS's exporter bakes through a camera of its own, so the maker camera's post-processing never runs: a bake is the shader's output, sRGB-encoded. The templates have no `.KK grade` (`edit_templates.begin(grade=False)`), and are still `graded` in their Template Description, which keeps the edit tool from saturating them.
- **The light is the maker's own, not a ramp end.** The exporter turns the maker's directional light to two rotations; on the bake quad, whose normal is +z, N.L is 0.828 for `light` and -0.944 for `dark`. The shaders read the light colour (1, 1, 1), the light probe's ambient (the maker's trilight ambient, no light probes in the scene, `models.SVS_AMBIENT_PROBE`, whose stored coefficients URP reads as they are), additional lights (none) and a reflection cubemap (`unity_SpecCube0_HDR` is 0, so every reflection term vanishes). The probe read these from the game; nothing is fitted. A template lights at the N.L its bake's toon value picks (`.SVS toon ndl`), or lights twice where the shader's output isn't linear in its inputs.

The models found more than the shaders' names suggest:

- **The shadow is a colour of its own.** Where KK multiplies by a shadow colour, the LIF shaders blend between a lit colour (the light plus half the ambient) and a shadow colour: an overlay of the ambient and a tint made from the material's own colour in HSV (the face parts' `svs_shadow_tint`, the items' `svs_item_shadow_tint`), or a constant red for `_TypeSelect` 3 (the teeth). How far into it comes from the ramp `_Lamp`, read at N.L and weighted by `_ShadowSetting` and the detail mask.
- **The eyes bake in layers.** `lif_main_eye` draws the eye white and the pupil together, and the exporter bakes the eye white copies alone and the eyes as the pupil over transparency (ADR 0034), measuring its coverage from two more renders with the eye white black and white. The eye template lights its eye that way too: the eye over its eye white is affine in the eye white (`.SVS eye layers`), so it lights it over the real one and over black and white. Taking the coverage as the shader composites it instead was 0.016 off in the dark.
- **SVS's masks keep data of their own in their alpha.** The hair's colour mask holds its second extra colour there, half of it transparent. Blender associates a straight-alpha image's colour with its alpha, so a profile's `EDIT` now lists `channel_packed` slots, whose images are loaded Channel Packed (SVS's masks; KK and KKS list none).
- **The skin is lit as the items are, with a tint of its own.** The nails, body and face share the items' light (`svs_item_t`, `svs_item_mix`), their shadow colour the base colour's hue at saturation sqrt(s) + 0.1 and value 0.8 - 0.1 sqrt(v) (`svs_skin_shadow_tint`). The shade matcap (`_shadematcap`, the nails' `_Mat_cap`), which the bake doesn't clear, is read at the bake's view normal, the texture's centre. The body adds a highlight from `_Detail_mask_01`'s blue, moved toward the light by `_SpeclarHeight`, and the nails a gloss from their matcap.
- **The skin's layers are placed by the mesh.** The exporter bakes the body and face from their mesh flattened into UV space, every normal toward the camera as on the quad, so the nipples and under-hair (the body's second UV map, picked by the vertex colour's red) and the cheek blush, lips and nose (the face's second to fourth UV maps) land where the game draws them; the quad's render under it has them cleared. The templates read the same UV maps on the importer's flattened mesh and scale those layers by the vertex colour's alpha, which the bake's plane lacks.
- **A texture the bundle lacks reads its shader's default** (`m_PropInfo`'s default texture names: black for the LIF masks and the skin's layers, white for `lif_main_acs`'s main texture and the face create's `_Facetype_texture`). An empty image node reads black and opaque, so templates have `present` switches that a missing slot turns off.

Measured by `blender/test_edit_accuracy.py`, mean absolute difference per channel (light / dark) on the SVS Golden Sample:

| Material | Shader | From the shader |
|---|---|---|
| `cf_m_mayuge_00` (eyebrow) | `lif_main_eyebrow` | 0.0012 / 0.0009 |
| `cf_m_eyelash_up_00` | `lif_main_eyelash_up` | 0.0010 / 0.0010 |
| `cf_m_hitomi_00_L`, `_R` (pupil layer) | `lif_main_eye` | 0.0019 / 0.0018 |
| `cf_m_hitomi_00_L_white`, `_R_white` | `lif_main_eye` | 0.0011 / 0.0011 |
| `cf_hair_b_m_o_12_00` | `lif_main_hair` | 0.0015 / 0.0011 |
| `cf_hair_f_m_o_03_00` | `lif_main_hair` | 0.0011 / 0.0011 |
| `cf_m_tooth` | `lif_main_acs` (skin-face variant) | 0.0014 / 0.0012 |
| `cf_m_tango` | `lif_main_acs` | 0.0007 / 0.0007 |
| `m_cloth_cf_top_tshirt00` | `lif_main_cloth` | 0.0022 / 0.0014 |
| `m_cloth_cf_bot_denim00` | `lif_main_cloth` | 0.0024 / 0.0020 |
| `m_cloth_cf_bra_base00_03` | `lif_main_cloth` | 0.0080 / 0.0022 |
| `m_cm_shoes_01` | `lif_main_cloth` | 0.0075 / 0.0043 |
| `m_cloths_cm_socks_00` | `lif_main_cloth_socks` (the clothes' template) | 0.0024 / 0.0020 |
| `cf_m_nail_def_00`, `_01` | `lif_main_nail` | 0.0014 / 0.0013, 0.0009 / 0.0009 |
| `cf_m_body_00` | `lif_main_skin_body` (with its create) | 0.0049 / 0.0044 |
| `cf_m_head_00` | `lif_main_skin_head` (with its create) | 0.0020 / 0.0019 |

## Considered Options

- **Fit constants to KK's templates, as KKS did**: SVS's shaders aren't KK's with other constants; the shadow colour, the ramp and the eye's layers have no KK counterpart.
- **Fit the light from the bakes**: the probe reads it from the game, so the models have no free constants.
- **Rebuild each shader from its disassembly, by hand, with the bake's fixed inputs (chosen)**.

## Consequences

- The SVS Game Profile has its own `EDIT` tables (`profiles/svs.py`), picked by shader for the accessories, clothes and socks (no Role), by Role for the rest. SVS's materials carry their textures by Raw Property, so every source is `own:`. `EDIT` colours gain `vector_z`.
- **The create materials (Schema Version 1.3).** The SVS exporter writes each body, face and clothing material's create material as `extensions.svs.create` (`exporters/svs/src/Creates.cs`). The templates composite it in nodes (`.SVS create cloth`, `.SVS create skin body`, `.SVS create skin head`, from `models.create_main_cloth`, `create_main_skin_body` and `create_main_skin_head`, which give back the composited textures within 0.0024, 0.0013 and 0.0017), so the clothes' colours, patterns and paints, the skin colour, sunburn and paints, and the face's mouth colour, mole and eyeshadow can be edited. A material without one (an older bundle) takes the composited texture (`_Create_main_texture`, `_Create_jm_main_skin_head`) as it is (`use_create`). The edit tool's `values` rules gain `create:S`, true when the material's create shader is S.
- **Save keeps the face's bakes without eyeshadow in step** ([ADR 0046](0046-the-face-is-also-baked-without-its-eyeshadow.md)). The face's create shader draws the eyeshadow last, so the face template has an `eyeshadow` param, and Save bakes the face a second time at 0 into the Light Dark Face's no-eyeshadow pair, as the exporter's second bake sets the eyeshadow colour's alpha to 0. A face without its create material can't leave the eyeshadow out; Save then keeps that pair as it was and says so in the log.
- Not editable: the eyelid (its bake shows only its outline; the coloured pass fades out with the camera's distance), and the shaders no sample shows (`_alpha` and `_low` copies, modded shaders).
- The skin models leave out what a maker Character has off or the bundle doesn't carry: the liquid and sweat, the body's dents and bust shadow, the face's blush expression (`_HohoakaIntensity`), specular map and lip line, the line textures (`_linetexon`, `_Line_textureonoff`), the rim (`_RimMask` 1) and the reflection (no cubemap). The body's highlight leaves out the view's share of its parallax, under a camera 10 away. The body's template is 0.005 from its bakes where its model is 0.001; the rest wasn't chased.
- The clothes' models leave out their liquid effects (off on a maker Character) and the shoes' small `_Hight` parallax (0.006 of their 0.008); `lif_main_acs` leaves out its outline widening of the main texture's alpha.
- The probe's numbers are the Sample Card's maker scene. A game update that moves the maker light or its ambient needs `probe_bake` again.
