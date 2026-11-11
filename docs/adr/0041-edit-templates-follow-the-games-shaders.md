# Edit templates follow the games' own shaders, and grade their light and dark as the maker camera does

Updates [ADR 0026](0026-edit-materials-dont-saturate-by-default.md) as issue 30 asks. In progress: both Games' eye whites, eyebrows, eyelines and nose line are done; the other Material Roles still use the legacy edit templates.

An edit template is rebuilt from the game's own shaders instead of the legacy templates' approximations. The shaders were read from the installed games (`importer/tools/game_shaders/dump.py` disassembles their compiled D3D11 programs; the output is the games' code and stays in `importer/tests/.work/`), and each one used is written as a numpy model in `importer/tools/game_shaders/models.py`. `host/test_shader_models.py` checks every model against the Golden Samples' own bakes, and the node groups follow the models.

Comparing the models with the samples found three things the legacy importer and ADR 0026 didn't know:

- **Bundle textures hold linear values.** The exporter copies each texture through a linear render target, so a PNG holds what the shader sampled; only the `light` and `dark` bakes are sRGB-encoded. The templates re-encode each texture after Blender's sRGB decode (`.KK srgb`), which gives back the stored value without touching images other materials share.
- **The shaders see colours linear**, as Unity's linear colour space gives them: `lerp(lin(_Color2), lin(_Color), main.r)` is the eye white's composited texture to within 8-bit rounding.
- **Both games' `light` and `dark` bakes are colour graded by the maker camera** (AmplifyColor with `Lut_TimeDay.png`) after the shader. No per-channel factor fits the bakes without the grade; with it, the eye white's light factor is 1.0 in every channel. So a template grades its light and dark colours last, in nodes (`.KK grade`, `.KK graded`), and never saturates its input textures. ADR 0026 found the legacy hair and eyebrows closer saturated because saturating their colours stood in for this grade.

KK's maker light, found by fitting: the light term 1.0, `_ambientshadowG` 0.15 (ambient shadow 0.2775, legacy's constant), the ramp 1 for `light` and 0 for `dark`.

KKS's shaders (`Koikano/*`) add light probes, `_KanoVerShift`, a 0.67 / 0.33 light term and a desaturated shadow, but under the bake they reduce to KK's formula with other constants. Its `light` bakes match KK's to within 0.017 for the same card; only `dark` differs. The bake's flat quad sees the probes as one ambient colour, and a light of 1.0 makes both light terms 1. What is left is the ambient colour, its strength and how much lit colour the shadow keeps (`saturate(ramp + _ambientshadowG.a)`, 0 in KK). Fitted on the KKS eye-white family, they are 0.225 / 0.216 / 0.203, 0.175 and 0.2. So KKS uses KK's templates, and its Game Profile sets these three values (`models.KKS`).

Measured by `blender/test_edit_accuracy.py` (mean absolute difference per channel, light / dark, sRGB values over pixels opaque in both). KK Golden Sample:

| Material | Legacy template | From the game's shader |
|---|---|---|
| `cf_m_sirome_00` (eye white) | 0.170 / 0.103 | 0.004 / 0.003 |
| `cf_m_mayuge_00` (eyebrow) | 0.019 / 0.000 | 0.003 / 0.000 |
| `cf_m_eyeline_00_up` | 0.155 / 0.002 | 0.020 / 0.015 |
| `cf_m_eyeline_kage` | 0.562 / 0.056 | 0.006 / 0.011 |
| `cf_m_eyeline_down` | 0.135 / 0.000 | 0.023 / 0.015 |
| `cf_m_noseline_00` | 0.000 / 0.000 | 0.000 / 0.000 |

KKS Golden Sample, with KKS's maker light:

| Material | Legacy template | From the game's shader |
|---|---|---|
| `cf_m_sirome_00` (eye white) | 0.169 / 0.114 | 0.003 / 0.003 |
| `cf_m_mayuge_00` (eyebrow) | 0.019 / 0.000 | 0.003 / 0.000 |
| `cf_m_eyeline_00_up` | 0.155 / 0.034 | 0.020 / 0.020 |
| `cf_m_eyeline_kage` | 0.563 / 0.259 | 0.005 / 0.004 |
| `cf_m_eyeline_down` | 0.135 / 0.010 | 0.023 / 0.018 |
| `cf_m_noseline_00` | 0.000 / 0.000 | 0.000 / 0.000 |

With KK's constants, KKS's shadow eyeline's dark would be 0.198: the shadow keeping a fifth of the lit colour is what matters, not the probes.

The eyelines' dark is a little further than legacy's, whose black happened to match their nearly black dark bake: what remains is at their semi-transparent edges, where Blender filters a texture with premultiplied alpha and the game with straight alpha. The numpy models, which filter as the game does, are within 0.001 to 0.008 there.

## Considered Options

- **Keep the legacy templates and tune their saturation (ADR 0026)**: the errors of 0.03 to 0.56 come from the templates' own formulas, which no saturation choice fixes.
- **Saturate the input textures through the LUT, as legacy did**: the grade happens after the shader, on its encoded output; saturating the inputs and then shading gives other colours.
- **Rebuild each template from the game's shader, with the grade last (chosen)**.

## Consequences

- A template made this way is named after the game's shaders (`KK toon_eyew`, `KK create_eyewhite`, `KK toon_nose`), keeps its image nodes at the top level (no texture group copied per material, so [ADR 0025](0025-edit-materials-copy-their-texture-group.md) doesn't apply to it), takes the game's own colours linear (`plain`), and is `graded` in its Template Description: the edit tool never saturates it, whatever Saturate says.
- The Game Profile picks a template per Material Role (`LEGACY_EDIT_TEMPLATES` for the Roles not modelled yet), and sets its maker light through `values`. The templates' defaults are KK's, and KKS's profile sets its own ambient colour, strength and shadow floor. Both Games' `saturated_roles` is now the hair alone.
- `Lut_TimeDay.png` stays in `library.blend`, Non-Color, read by `.KK grade` (and still by the legacy saturation).
- `importer/tests/data/edit_accuracy.json` records each material's numbers; the test fails when a material moves further from the game. Re-record it when a template brings a material closer.
- Each further shader is the same work: dump it, model it, fit any constants against the samples, write its node group and template, point the profile at it, re-record. The legacy templates, the Saturate option and `kkbp/shading/` go when no Role uses them.
