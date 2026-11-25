# Bakes have their main texture's size and shape; the body and face stay 4096 square

The light and dark bakes were a square at the longer side of the material's main texture, and 4096 square for the body and the face (ADR 0036 left this open). Two things were asked for: bake at the main texture's own width and height, and decide the body and face size by measuring rather than keeping the legacy exporter's 4096.

A material's bake now has its main texture's width and height (2048 square with no main texture). On the Sample Cards, KK's skirt, bra, shorts and jacket trim go from 1024 × 1024 to 1024 × 512 (512 × 256 for the trim), its socks to 512 × 1024, and KKS's bra and shorts to 1024 × 512. The quad covering UV space is rendered with the camera's aspect set to 1, so it fills a render texture of any shape and each pixel still lands on one texel.

The body and the face keep 4096 × 4096. Measured on the Golden Samples (2026-11-14), baking them at the largest of their own textures (KK and KKS: face 1024, body 2048; SVS: both 2048):

- **SVS body:** the pubic hair, a 512 px texture the shader places with its own UV set, covers only a few hundred pixels of the 4096 bake. At 2048 its strands blur into a grey patch. A layer placed by another UV set is finer than its own size suggests, and finer than the main texture.
- **KK and KKS face and body, SVS face:** no visible loss on the Sample Cards (under 0.3% of pixels differ by more than 8 of 255 from the smaller bake enlarged). The Sample Cards have no tattoos or face paint, which the same overlays draw.

## Considered Options

- **The largest of the material's own textures, up to 4096 (rejected)**: the plan before measuring. It loses the layers placed by other UV sets, as above, and every body has at least the nipple layer.
- **4096 only when such a layer is set (rejected)**: the KK body and face always have overlays set and the SVS skin shaders always place their layers, so it would be 4096 for every Character anyway, with one more rule.
- **Keep 4096 for the body and the face (chosen)**.

## Consequences

- Rectangular textures are no longer stretched, and their bakes are half the size.
- The body and face bakes are unchanged. A skin main texture larger than 4096 is still baked at 4096, as before.
- The importer needed no change: it reads each image's width and height. Export prep's atlas pieces follow the bakes' new shapes.
