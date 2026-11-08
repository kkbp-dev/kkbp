# Blender Compatibility and Testing

How the importer keeps up with new Blender releases, and how changes are checked. Terms are defined in [CONTEXT.md](../../CONTEXT.md).

Status: agreed design, not yet implemented.

## Supported Blender versions

- The minimum starts at **Blender 5.2 LTS**, because this is a new plugin. Every newer release is supported.
- After that, the minimum follows Blender's normal LTS timeline: an LTS stays supported until Blender ends its support, and then the minimum moves to the oldest LTS that is still maintained.
- Code for versions below the minimum is deleted. That includes today's Blender 2.x/3.x branches, the 5.1 rendering workaround, and the 5.2 checks (`use_transparent_shadow`, Geometry Nodes modifier inputs), which become unconditional.
- So the Compat module starts empty. It exists so that the next API change has one obvious home.

## Compat module

- All code that depends on the Blender version lives in `compat/`, as functions named for what they do (for example `compat.set_transparent_shadow(mat)`).
- `bpy.app.version` appears only there, and only as a tuple comparison (`bpy.app.version >= (5, 3)`).
- Each branch records the Blender version, a link to the release notes, and "remove when the minimum is X or later".
- A test fails if `bpy.app.version` appears outside `compat/`.
- Feature detection (`hasattr(...)`) is preferred. Version checks are used only for behaviour changes with nothing to detect.

## Data API over operators

- Steps use the data API (`bpy.data`, `bmesh`, `edit_bones.new`, …) wherever one exists.
- Operators remain only where there is no equivalent. They go through small helpers in Compat that set an explicit context with `bpy.context.temp_override`.
- This is done as each Step is ported, not as a separate pass.
- Mode switching uses one context manager, `with editing(obj, "EDIT"):`, which always restores the previous state, even if an error is raised. It replaces the 63 `mode_set` calls and `c.switch()`.

## Third-party code

- The bundled third-party code is removed: shotariya's `material_combiner` (MIT, about 3,000 lines, used for the export atlas) and the CATS scripts (MIT, used only for Merge Weights).
- The features KKBP uses from them are rewritten as KKBP's own code, using the originals as a reference.
- Scope: only what KKBP's panel offers today. That is the export atlas, with its current size and material options, and Merge Weights. The rest of material_combiner's general-purpose UI is not carried over.
- The atlas is split in two:
  - a part with no `bpy` that works out the rectangle layout and UV remapping and composites the images with Pillow, tested with pytest (Pillow installed in the development environment);
  - a thin Blender part that only loads and saves images and applies the UVs, tested in the harness.
- shotariya's Material Combiner and CATS are credited in a `NOTICE` file and in the README.
- The Rigify scripts are KKBP's own code and become a built-in Hook.

## Pillow

- The atlas uses Pillow, installed as a wheel through the extension's `blender_manifest.toml`.
- **Pillow is mandatory.** Importing is not possible until it is installed.
- The existing installer is reused (today's `InstallPIL` in `exporting/material_combiner/get_pillow.py`, which moves out of the removed folder). It:
  1. downloads Pillow from PyPI with Blender's own pip into `<add-on>/wheels`;
  2. replaces `#wheel_placeholder` in `blender_manifest.toml` with the `wheels = [...]` entry;
  3. calls `addon_utils.extensions_refresh()`, Blender's call for "an extension changed on disk", which installs the wheel without a restart (disabling and re-enabling the add-on is the fallback if Pillow still doesn't load);
  4. asks for confirmation first if Blender's online access is turned off.
- Two fixes to the installer:
  - the Pillow version is pinned and only raised on purpose, so the harness tests what users get;
  - the `wheels/` folder is emptied first and the file pip just downloaded is used, not `os.listdir(...)[0]`.
- Offline install: the panel also accepts a wheel file the user downloaded elsewhere, installed through steps 2–3 above. The file must be a Pillow wheel whose tags match the running Python and platform (worked out from the interpreter, never a fixed `cp313`), because Blender will move to newer Python versions.
- Enforcement: until Pillow loads, the panel shows only an **Install Pillow** button and the import operator's `poll()` returns False. `kkbp.import_bundle()` raises "Pillow is required. Install it from the KKBP panel."

## Mesh Loader

- It is the only caller of `bpy.ops.import_scene.gltf` and sets every option explicitly.
- When the add-on starts, it checks that every option it sets still exists. If one doesn't, it reports "glTF importer option X no longer exists in Blender Y".

## Test harness

- Headless Blender (`blender --background`) runs on two builds: the minimum (5.2 LTS) and the latest stable release.
- Each sample import produces a JSON scene summary: Parts and roles, materials with their template and texture images, shape keys, bone count and rounded positions, vertex counts.
- Summaries are stored in `importer/tests/snapshots/`. They change only through an explicit "update snapshots" command, and the diff is reviewed.
- The same summaries do the old-vs-new comparison described in [export-bundle.md](export-bundle.md#testing).

## Other candidates

- Candidate 6 (Exporter Naming) is dropped. Assigning Ids is part of the shared exporter writer ([export-bundle.md](export-bundle.md#ids)).
