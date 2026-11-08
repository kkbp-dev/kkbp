# Each Hook's assets are one file built by a script, the mouth atlas as WebP

The Rigify widgets, the face cards and the outline images each live in their own file next to the template library: `rigify.blend` (0.2 MB), `face_cards.blend` (3.5 MB) and `outlines.blend` (0.1 MB). `scripts/build-hook-assets.sh` builds all three from the unchanged legacy `KK Shader V9.blend`, the way [ADR 0018](0018-template-library-built-by-a-script.md) builds the library. Every name a Hook uses from its file is in `library/hook_assets.py`, which has no `bpy`, and a harness test checks each name against the file. Everything appended from these files is shared once per Blender file, as the templates' node groups and images are.

The face cards' 8192 × 4480 mouth atlas is stored as WebP at quality 95 instead of PNG: 3.3 MB instead of 12.4 MB. Optimising the PNG saved nothing. Lossless WebP was 8.4 MB. At quality 95, about 0.04% of the pixels differ by more than 8/255, at transparent edges, and a side-by-side check shows no difference. Blender's `Image.save` ignores the quality for WebP, so the script saves through the scene's output settings.

## Considered Options

- **The assets in `library.blend`**: one file to build, but every import would carry the face cards and widgets whether or not their Hooks run, and the material-template design keeps non-template assets out of it.
- **Assets edited by hand in Blender**: the same review problem ADR 0018 rejected.
- **One file per Hook, built by a script (chosen)**: each Hook brings only its own assets, and every change to them is code in review.
- **PNG or lossless WebP for the atlas**: no quality change, at 12.4 or 8.4 MB.

## Consequences

- A change to a Hook's assets is a change to `tools/build_hook_assets.py`, then `scripts/build-hook-assets.sh`.
- The face cards' mouth is a slightly lossy copy of the legacy atlas. The `defaults` comparison lists it as `MouthAtlas.webp`.
