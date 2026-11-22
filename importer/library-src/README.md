# Library sources

What `scripts/build-library.sh` builds the Material Template library and the built-in Hooks' asset files from, besides the node modules in `importer/tools/library/groups/` and `materials/` ([ADR 0040](../../docs/adr/0040-the-library-is-built-from-code.md)). NOTICE credits where they came from.

- `images/`: the images, as they were packed (Git LFS). `images.json` gives each image's name in the `.blend`, its file, colour space and alpha mode; generated blanks have generator settings and no file. Some were added since:
  - `Lut_TimeDay.png`: the game's colour grade, for the edit materials.
  - `SVS Eye_White_Alpha.png`: the face cards' SVS eye white mask, drawn from an SVS bundle by `importer/tools/make_svs_eye_white_mask.py` ([ADR 0037](../../docs/adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)).
  - `Face SDF KK.png` and `Face SDF SVS.png`: the Eevee Mod face's SDF in KK's and SVS's face UV layouts, in place of the legacy `sdf 5.png`. Each was baked from its Game's face mesh: the light order follows the head's smoothed shape, the front of the face is shaded by its width at each height so every shadow edge is one smooth line, and the underside of the jaw and the neck are always in shadow. They keep the legacy encoding (sRGB grey = order / 12 × 140 / 255, as 16-bit), so the group's Minimum, Middle and Maximum values still fit. The baking scripts aren't in the repository.
  - `SVS hair contact shadows mask.png`: the legacy KK mask (`SDF hair contact shadows mask 2.png`) carried onto SVS's face UV layout by `importer/tools/make_svs_hair_contact_mask.py`.
- `meshes/`: one JSON file per mesh, by the mesh data API's own arrays, so a rebuild keeps every vertex, edge and loop in its order.
- `scenes/`: per asset file, its collections, objects (modifiers, constraints, vertex groups and weights) and armatures (bones, bone collections, pose bones).

Edit these files, or the modules, then run `scripts/build-library.sh`.
