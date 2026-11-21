# SVS's alpha masks are merged and read KK's way by the KK variants

SVS's alpha masks and KK's mean opposite things. The `.SVS` shader group shows a texel where a mask's red is black: min((1 − top red) × top alpha, (1 − bottom red) × bottom alpha), with the top mask `_Cloth_alpha` and the bottom one `_Cloth_alpha_bot`. The `.KK alphamask parser`, which Eevee Mod and the three Cycles variants use, reads one mask and shows a texel where its red is white (red × alpha at Force visibility 2, the larger of red and green at 1). SVS Light Dark gets KK's variants (D18), and `templates.swap` used to move the links across as they were. So a converted SVS material read its mask backwards. A material with no mask holds the black `Template: BlackWithAlpha`, which hides nothing for `.SVS` and everything for the parser: an SVS Character converted to Eevee Mod or Cycles had an invisible face, hair and clothes. The bottom mask was dropped, with a warning.

Now a template's description can say its masks are inverted (`InvertedMasks`, on SVS Light Dark and SVS Light Dark Face), and for which variants. When `swap` puts one of those variants in, it adds a few nodes to the material, in a frame "SVS alpha masks, read KK's way" and named `kkbp.masks.*`. They work out the `.SVS` formula from both image nodes and feed the result to the variant's `Alpha mask` input as red, green and blue, with `Alpha mask alpha` set to 1. The nodes are removed and rebuilt on every swap. A variant not on the list, Principled, gets the image nodes linked straight to its inputs again.

## Considered Options

- **A library group that reads SVS's masks**, replacing the parser inside each variant group, or a second set of variant groups for SVS: library.blend changes, and the variants stop being KK's (D18).
- **Inverting the images** when the variant is swapped in: the Outfit textures the body swaps (ADR 0055) and the outline masks would need inverting too, and a mask on disk would no longer be the game's.
- **Nodes in the material between the image nodes and the shader (chosen)**: the images stay the game's, every image node keeps working as a texture slot, and the variants stay KK's.

## Consequences

- The bottom mask now counts for the KK variants, so `swap` no longer reports it lost. `variant_drops` still names it, since the variants lack the input.
- The Outlines Hook gives a shared outline the mask that hides nothing for its template: black for an inverted one, white for KK's. A white mask hid every SVS shared outline, converted or not.
- The face outline mask (`SVS OutlineMask.png`) is drawn SVS's way, and reads the same through the conversion.
- Export Prep folds a material's top alpha mask into its atlased textures (`atlas/alpha.py`) inverted for an inverted template, so SVS textures no longer go transparent wherever their mask is black. The bottom mask isn't folded in.
