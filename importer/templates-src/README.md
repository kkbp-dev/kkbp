# Material Template source

`KK Shader V9.blend` is the legacy importer's template library, copied unchanged. It is never edited.
`scripts/rework-templates.sh` builds the importer's library, `importer/kkbp/library/library.blend`, from it
([ADR 0018](../../docs/adr/0018-template-library-built-by-a-script.md)), so every change to the templates is
code that can be reviewed and run again.

The Hooks that need its other assets (Rigify widgets, face cards, outlines) take them from this file in Phase 5.

The images beside it aren't in the legacy file. Each is packed by the build script that names it:

- `Lut_TimeDay.png`: the game's colour grade, packed into `library.blend` with the edit templates.
- `SVS Eye_White_Alpha.png`: the face cards' SVS eye white mask, packed into `face_cards.blend`. `importer/tools/make_svs_eye_white_mask.py` draws it from an SVS bundle ([ADR 0037](../../docs/adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)).
