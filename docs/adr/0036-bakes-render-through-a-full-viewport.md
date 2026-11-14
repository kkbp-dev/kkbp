# Light and dark bakes render through a full viewport, without supersampling

Issue 17 reported that the light and dark bakes looked softer in Blender than the game draws them, and proposed baking at double resolution and downscaling. Measured on a KK card with patterned clothes (2026-11-09), the bakes of the jacket, skirt and bra were visibly smeared: the jacket pattern's one-pixel swirls came out blocky, though the pattern kept its tiling (period 51 px in both).

The bake renders the material onto a quad that covers UV space, through the maker camera into a render texture of the bake's size. Each pixel then lands on a texel centre and gets that texel back. A diagnostic export found the cause:

- An `Unlit/Texture` render of the same main texture, through the same path, was as smeared as the bake. So the game's shader wasn't the cause.
- The maker's camera keeps a viewport rect of `x 0.33, width 1` to leave room for the maker's menus. A camera rendering into a texture keeps its rect, so the bake was resampled sideways. With the rect set to the full viewport, the unlit render matched the texture pixel for pixel (apart from AmplifyColor's colour grade). The fit residual against the raw texture dropped from 1373 to 446 (bra), 1180 to 559 (jacket) and 595 to 421 (skirt).
- A −2 mip bias on the texture changed nothing, so mip selection wasn't the cause.
- The only image effect enabled on the KK maker camera is AmplifyColor, which the bakes keep (ADR 0026 measured their colours with it). Switching the other effects off changed nothing.

So the KK and KKS bake sets the camera's rect to the full viewport while it runs and restores it afterwards. SVS's bake camera is a `CopyFrom` copy of the maker camera, which copies the rect too, so it sets the full viewport as well.

## Considered Options

- **Supersample: bake at 2× and downscale (rejected)**: at 2× the GPU samples the texture a quarter-texel either side of each texel centre, and averaging those is a fixed 1/8, 3/4, 1/8 blur. Simulated on the Golden Samples, edge sharpness dropped to 83–95% of the source. It only antialiases edges the shader computes itself, and it would hide this cause rather than fix it.
- **Switch off the maker camera's image effects (rejected)**: none but AmplifyColor is enabled in the maker, and the re-export with them off was unchanged.
- **Render through a full viewport (chosen)**: the bake samples each texel once, as the game's own texture has it.

## Consequences

- KK and KKS bakes of patterned and detailed textures are as sharp as their main texture, so their light and dark Variants change and the Golden Samples were remade. The SVS bakes that could be measured were already sharp; the SVS line is a safeguard.
- Bakes are still square at the larger side of the main texture, and the face is still baked at 4096. A rectangular texture is stretched along its short side, which costs a little vertical sharpness in Blender. This is left for a separate decision. (Decided in [ADR 0044](0044-bakes-keep-the-main-textures-shape-and-skin-stays-4096.md): bakes follow the main texture's shape, and the body and face stay 4096.)
