# The face is also baked without its eyeshadow

The light and dark bakes of the face have the eyeshadow drawn into them, so its colour around the eyes can't be faded or removed in Blender (issue 38). When a face has eyeshadow, the exporter bakes it a second time without it and writes the results as two more Texture Variants of the face's `_MainTex`: `light_no_eyeshadow` and `dark_no_eyeshadow` (Schema Version 1.2). The importer gives such a face the `KK Light Dark Face` template (`SVS Light Dark Face` on SVS), whose **Eyeshadow** parameter fades between the two pairs: 1, the default, is the game's own bake, and 0 is the face without eyeshadow.

The template has a second parameter, **Hide with gag eyes**, which takes the eyeshadow away as it rises whatever Eyeshadow is. The importer drives it from the `Gag eyes` shape key, because the eyeshadow is painted around eyes the gag expressions close or cover; like the other things expressions change on a material it is driven on the objects, not the material (issue 70). Its own value on the material still hides the eyeshadow by hand: the material shows the larger of the two.

## What the exporter leaves out

KK and KKS: the eyeshadow is the face material's third overlay, `_overtex3`; the other two overlays are the cheeks and the lips and stay in both bakes. The overlays are drawn in the bake's mesh pass, so the second bake is that pass again with `_overtex3` cleared, laid over the same quad pass. A face with no eyeshadow texture gets no second bake, and neither does a tessellated face shader, whose bake has no quad pass to share.

SVS: the head shader has no eyeshadow layer of its own. The game draws the eyeshadow into the head's texture (`_Create_jm_main_skin_head`) with the face's create material (`HumanFace.customTexCtrlFace`), whose eyeshadow texture and colour are the properties `ChaShader.Face.CreateShader` names. For the second bake the adapter sets that colour's alpha to 0, has the game draw the head's texture again (`SetNewCreateTexture`), bakes the face, and then puts the colour back and draws the texture once more. A face whose create material has no eyeshadow texture, or a clear eyeshadow colour, gets no second bake.

## Considered Options

- **A new Texture Role**: a Role says what a texture is for in the shader, and these are the same bake as `light` and `dark` with one layer missing. They are Variants.
- **Two new Texture Variants (chosen)**: a new set value is a minor Schema Version change ([ADR 0014](0014-unknown-set-values-in-newer-minor-versions.md)), and an importer that doesn't know them keeps them with a warning and imports as before.
- **Leave out every overlay**: the issue asks for the eyeshadow only, and the cheeks and lips don't sit on skin the eyelids move.
- **An Import Option that picks one pair**: the user would have to import again to compare. A parameter on the material can be changed, and keyed, afterwards.
- **Add the slots to `KK Light Dark`**: every material uses that template, and all but the face would carry two unused image nodes and a parameter that does nothing. A Template Set row can now name the texture slots a material `needs`; the face's row with the new template needs both Variants, and a face without them falls through to the `KK Light Dark` row, so a bundle from an older exporter imports exactly as before.

## Consequences

- The contract says the two come as a pair, beside the `light` and `dark` of the same texture. The Exporter Core fails an export that breaks this, and the importer's bundle check reports it.
- A bundle with eyeshadow has two more 4096² PNGs.
- The SVS adapter changes the Character's face texture for the length of one bake. It is put back in a `finally`, so a bake that fails leaves the Character as it was.
- Each face template has the same shader node and shader variants as the template it adds to, so Convert shaders, the outlines' face mask and the other Hooks treat it the same.
