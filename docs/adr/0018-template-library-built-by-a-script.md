# The template library is built by a script from the unchanged legacy file

Superseded by [ADR 0040](0040-the-library-is-built-from-code.md): the library is now built from code, and the legacy file is gone.

`importer/kkbp/library/library.blend` is not edited in Blender. `scripts/rework-templates.sh` runs `importer/tools/rework_templates.py` on `importer/templates-src/KK Shader V9.blend`, the legacy library copied unchanged, and writes the library. The script makes every change the design asks for ([material-template.md](../design/material-template.md#the-library)): it keeps only the templates, names image nodes by role, gives the shader groups one socket naming scheme and a `Hidden` input, moves per-material images onto the materials, builds the Gag template and stamps `kkbp_template_version`.

## Considered Options

- **Rework the file by hand in Blender and commit the result**: the usual way to edit templates, but a `.blend` diff can't be reviewed, and nobody could tell later which of the hundreds of node edits were intended.
- **A script, run once, then the result edited by hand from then on**: reviewable once, then the same problem.
- **A script that always rebuilds the library from the legacy source (chosen)**: every change is code in review, and the library can be rebuilt after a fix to the script.

## Consequences

- A template change is a change to the script, followed by `scripts/rework-templates.sh`; the harness test then checks every Template Description against the new file.
- Both `.blend` files are in Git LFS: the 24.9 MB source and the 3.1 MB library (saved compressed).
- The source also holds the assets the Phase 5 Hooks need (Rigify widgets, face cards, outlines); each Hook's asset file will be made from it the same way.
- Editing templates visually is still possible, but the edit has to be written back into the script.
