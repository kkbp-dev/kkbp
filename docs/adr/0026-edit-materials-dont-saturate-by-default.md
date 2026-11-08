# Edit materials don't saturate by default, except hair and eyebrows

The legacy importer ran every edit material's main textures and colours through the game's colour grade (`Lut_TimeDay.png`) to match the in-game look, because the textures it imported were the game's unlit inputs. The exporters now bake each material's light and dark textures with the game's own shader, and an edited material is saved by baking it back into those slots, so the edit material should reproduce them. Measured on the KK and KKS golden samples by baking each unedited edit material and comparing it with the bundle's own light and dark textures (mean absolute difference per channel over opaque pixels), the bake without saturation was closer for 22 of the 26 materials (light and dark differences added). Examples for the light texture: KK body 0.051 without, 0.107 with; KK jacket 0.082 against 0.218; KKS trousers 0.155 against 0.304. The four exceptions are the hair and the eyebrows of both samples. Once the edit templates drew them as the game does (the hair's colour mask switched on, the eyebrows multiplying their texture and shaded as `toon_eyew`), they came out much closer saturated: hair 0.30 without against 0.14 with, eyebrows 0.31 against 0.02. Their templates draw from colours alone, with no composited main texture to start from. So saturation is off, except for the hair and eyebrows (below), and Edit Material keeps a Saturate option to choose either way.

## Considered Options

- **Saturate, as legacy (rejected)**: the colours come out darker and more saturated than the game's own bake, so saving an untouched edit would change the material.
- **No saturation, with an option (chosen)**: closest to the bundle; the LUT code (`kkbp/shading/`) stays for the option.
- **By Material Role, by measurement (chosen for hair and eyebrows)**: they come out clearly closer saturated, so the profile's `saturated_roles` names them.

## Consequences

- `tools/edit_material.saturates` is true only for the profile's `saturated_roles` (KK and KKS: hair, eyebrow); the operator's Saturate option is Default, On or Off. The material panel shows it as a Saturate dropdown beside the Edit Material button (`scene.kkbp_edit_saturate`), and Reset keeps the choice the edit was made with (issue #13).
- The saturated hair's dark bake is redder than the game's, which is a darker brown.
- Even without saturation an unedited edit material isn't an exact copy of the game's bake (differences of 0.03 to 0.17 remain), since the legacy templates approximate the game's shaders; editing a material means accepting that approximation, as in legacy.
