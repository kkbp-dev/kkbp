# The library and the Hook asset files are built from code, not from the legacy file

Supersedes [ADR 0018](0018-template-library-built-by-a-script.md) and the "built from the legacy file" part of [ADR 0024](0024-one-asset-file-per-hook-built-by-a-script.md). Issue 29.

`library.blend`, `rigify.blend`, `face_cards.blend` and `outlines.blend` are built from an empty file by `importer/tools/library/build.py` (`scripts/build-library.sh`). The legacy `KK Shader V9.blend` is gone. What the files hold is source in git:

- each node group is a Python module in `importer/tools/library/groups/`, and each material one in `materials/`: one line per interface socket, node and link, through the small builder in `nodes.py`;
- the meshes are JSON in `importer/library-src/meshes/`, and the objects, collections and the face-card rig are JSON in `scenes/`;
- the images are the files in `importer/library-src/images/` (in Git LFS), with their settings in `images.json`. Blank placeholder images are generated, not stored.

The modules were written once by `importer/tools/library/export_nodes.py` from the built files, which already had every change `rework_templates.py` and `build_hook_assets.py` made to V9; the meshes, scenes and images by `export_assets.py`. A rebuild was proved the same as the files it replaces in two ways: a structural fingerprint of each file (`fingerprint.py`, `compare.py`: every node property, socket value, link, interface item, driver, image pixel, mesh element, object, modifier, constraint and bone) showed no difference, and decompiling the rebuilt files gave back the same modules. The importer's tests then passed with no snapshot re-recorded. The differences allowed, all listed in `compare.py`:

- `Template: Black` is a 4 x 4 black image; V9's was 0 x 0 with no pixels.
- Packed images' file paths are `//<file>`; V9 held placeholder text.
- Empty custom property groups other add-ons (Cycles, MMD tools, flip fluids) left on V9's datablocks are gone.
- Interface socket identifiers (`Socket_3` for `Input_3`) and Menu Switch item ids renumber; Blender sets them and nothing reads them, so sockets of group-like nodes are compared by position.
- Older files named a float socket with a factor subtype `NodeSocketFloat`; Blender now names it `NodeSocketFloatFactor`.
- UI and runtime state isn't compared: the node editor's view, reroute widths (reroutes draw at a fixed size), the Menu Switch's selected row, an image user's current frame, and stale values on Group Input and Output nodes' own sockets.

## Considered Options

- **Keep rebuilding from the unchanged V9 file (ADR 0018)**: every change was reviewable as a change to a script, but the shaders themselves stayed in a 24.9 MB binary nobody could read in git, and a new group had to be written as edits to legacy content.
- **JSON per node group and one generic builder**: less code, but harder to read in review and to write a new group in by hand.
- **One Python module per group and material, written once by a decompiler and kept by hand (chosen)**: a group's whole graph is readable and diffable, and new groups are written the same way.

## Consequences

- A template or asset change is a change to a module or a source file, then `scripts/build-library.sh`. The harness tests that check every Template Description and Hook asset name against the files still apply.
- A group can still be edited visually: build, edit in Blender, then `scripts/export-library-nodes.sh` writes the edited groups back to their modules, and the module diff shows the edit.
- The library is built on the harness's minimum Blender build. A module names node and socket properties as that Blender has them; a Blender that renames one makes the build fail rather than drift.
- NOTICE still credits the legacy importer: the node groups, edit templates, widgets, face cards and their images come from its V9 file.
