# The face is also baked without its eyeshadow

The light and dark bakes of the face have the eyeshadow drawn into them, so its colour around the eyes can't be faded or removed in Blender (issue 38). When a KK or KKS face has eyeshadow, the exporter bakes it a second time without it and writes the results as two more Texture Variants of the face's `_MainTex`: `light_no_eyeshadow` and `dark_no_eyeshadow` (Schema Version 1.2). The importer gives such a face the `KK Light Dark Face` template, whose **Eyeshadow** parameter fades between the two pairs: 1, the default, is the game's own bake, and 0 is the face without eyeshadow.

## What the exporter leaves out

The eyeshadow is the face material's third overlay, `_overtex3`; the other two overlays are the cheeks and the lips and stay in both bakes. The overlays are drawn in the bake's mesh pass, so the second bake is that pass again with `_overtex3` cleared, laid over the same quad pass. A face with no eyeshadow texture gets no second bake, and neither does a tessellated face shader, whose bake has no quad pass to share.

## Considered Options

- **A new Texture Role**: a Role says what a texture is for in the shader, and these are the same bake as `light` and `dark` with one layer missing. They are Variants.
- **Two new Texture Variants (chosen)**: a new set value is a minor Schema Version change ([ADR 0014](0014-unknown-set-values-in-newer-minor-versions.md)), and an importer that doesn't know them keeps them with a warning and imports as before.
- **Leave out every overlay**: the issue asks for the eyeshadow only, and the cheeks and lips don't sit on skin the eyelids move.
- **An Import Option that picks one pair**: the user would have to import again to compare. A parameter on the material can be changed, and keyed, afterwards.
- **Add the slots to `KK Light Dark`**: every material uses that template, and all but the face would carry two unused image nodes and a parameter that does nothing. A Template Set row can now name the texture slots a material `needs`; the face's row with the new template needs both Variants, and a face without them falls through to the `KK Light Dark` row, so a bundle from an older exporter imports exactly as before.

## Consequences

- The contract says the two come as a pair, beside the `light` and `dark` of the same texture. The Exporter Core fails an export that breaks this, and the importer's bundle check reports it.
- A bundle with eyeshadow has two more 4096² PNGs.
- SVS writes neither: its head shader (`lif_main_skin_head`) has no eyeshadow layer of its own among the textures and colours the exporter captures, so there is nothing to leave out of its bake. The game has eyeshadow settings, so it is drawn somewhere else; finding where is its own piece of work.
- `KK Light Dark Face` has the same shader node and shader variants as `KK Light Dark`, so Convert shaders, the outlines' face mask and the other Hooks treat it the same.
