# Material Template source

`KK Shader V9.blend` is the legacy importer's template library, copied unchanged. It is never edited.
`scripts/rework-templates.sh` builds the importer's library, `importer/kkbp/library/library.blend`, from it
([ADR 0018](../../docs/adr/0018-template-library-built-by-a-script.md)), so every change to the templates is
code that can be reviewed and run again.

The Hooks that need its other assets (Rigify widgets, face cards, outlines) take them from this file in Phase 5.
