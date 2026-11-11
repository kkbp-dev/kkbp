# Library sources

What `scripts/build-library.sh` builds the Material Template library and the built-in Hooks' asset files from, besides the node modules in `importer/tools/library/groups/` and `materials/` ([ADR 0040](../../docs/adr/0040-the-library-is-built-from-code.md)). They came from the legacy importer's `KK Shader V9.blend` (credited in NOTICE).

- `images/`: the images, as they were packed (Git LFS). `images.json` gives each image's name in the `.blend`, its file, colour space and alpha mode; generated blanks have generator settings and no file. Two aren't from V9:
  - `Lut_TimeDay.png`: the game's colour grade, for the edit materials.
  - `SVS Eye_White_Alpha.png`: the face cards' SVS eye white mask, drawn from an SVS bundle by `importer/tools/make_svs_eye_white_mask.py` ([ADR 0037](../../docs/adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)).
- `meshes/`: one JSON file per mesh, by the mesh data API's own arrays, so a rebuild keeps every vertex, edge and loop in its order.
- `scenes/`: per asset file, its collections, objects (modifiers, constraints, vertex groups and weights) and armatures (bones, bone collections, pose bones).

Edit these files, or the modules, then run `scripts/build-library.sh`.
