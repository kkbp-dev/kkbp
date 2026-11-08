# importer

The Blender importer. Phase 3 built its foundations: reading bundles, Character, the Mesh Loader, the pipeline with its Hooks, and Pillow. Phase 4 ported the Core Import's Steps, the Material Templates and the Game Profiles. Phase 5 adds the built-in Hooks and the tools used after an import ([hooks-and-tools.md](../docs/design/hooks-and-tools.md)).

See [docs/design/import-pipeline.md](../docs/design/import-pipeline.md) and [tests/harness/README.md](tests/harness/README.md).

| Path | Contents |
|---|---|
| `kkbp/` | The extension. `kkbp/bundle/` never imports `bpy`. |
| `kkbp/pipeline/steps.py` | The Step list with Game lists, and the built-in Hook order |
| `kkbp/steps/` | The Steps, by topic: `mesh`, `armature`, `materials` |
| `kkbp/profiles/` | The Game Profiles (`kk`, `kks`, `svs`); never imports `bpy` |
| `kkbp/library/` | The Material Template library (`library.blend`), its Template Descriptions and Template Sets, and the built-in Hooks' asset files with their descriptions (`hook_assets.py`); never imports `bpy` |
| `kkbp/builtin/` | The built-in Hooks, one module each |
| `kkbp/tools/` | The tools used after an import (Tools panel): export prep, Merge Weights, Run Hook, Bulk Import, Import Animation, and Edit Material with its bake (`edit_material.py`, `bake.py`) and Link Hair |
| `kkbp/atlas/` | The export atlas's layout and compositing; Pillow, never `bpy` |
| `kkbp/shading/` | The edit materials' colour maths (LUT saturation, light and dark colours); numpy, never `bpy` |
| `kkbp/appending.py` | Appending from the library and the asset files, with shared node groups and images |
| `kkbp/templates.py` | `apply`, `param`, `texture`, `swap`: Material Templates in the user's file |
| `templates-src/` | The legacy `KK Shader V9.blend` the library is built from, unchanged, and the game's colour grade `Lut_TimeDay.png` |
| `tools/rework_templates.py` | Builds `library.blend` from it (`scripts/rework-templates.sh`) |
| `tools/build_hook_assets.py` | Builds the Hooks' asset files from it (`scripts/build-hook-assets.sh`) |
| `kkbp/api.py` | The public API hook scripts get as `kkbp` |
| `tests/host/` | pytest tests that run without Blender |
| `tests/blender/` | pytest tests that run inside headless Blender, on every harness build, in an isolated profile |
| `tests/bundle_builder.py` | Writes small valid bundles for tests |
| `tests/harness/` | The headless Blender harness |
| `tools/gen_contract.py` | Copies the contract's closed sets into `kkbp/bundle/_contract.py` |

Set up once, and again after a Blender update (it builds `importer/.venv` from Blender's own Python, [ADR 0015](../docs/adr/0015-tests-run-on-blenders-python.md)):

```bash
scripts/setup-importer-dev.sh
```

Run the tests:

```bash
scripts/test-importer.sh
```

After changing `tools/rework_templates.py`, rebuild the template library:

```bash
scripts/rework-templates.sh
```

After changing `tools/build_hook_assets.py`, rebuild the Hooks' asset files:

```bash
scripts/build-hook-assets.sh
```

After changing a schema in `contract/schema/`:

```bash
scripts/gen-importer-contract.sh
```

## Blender quirks

Traps met while writing the importer and its tests. The rules they led to are in [CLAUDE.md](../CLAUDE.md).

### Scene and data

- Newly linked objects don't show up in `view_layer.objects` straight away: neither `in` nor iterating finds them until something syncs the view layer, and `obj.visible_get()` does. A removed object leaves a `None` there.
- `bpy.data.materials`, `.objects` and the other collections are sorted by name: compare sets, not orders.
- A PropertyGroup already has `name` and `rna_type`, so those can't be Import Option names.
- `ShaderNodeMix` has duplicate socket names: look its sockets up by identifier.
- `Material.use_nodes` is deprecated in 5.x; new materials already have a node tree.
- Appending from the library makes `.001` copies of node groups and images the file already has; `templates.py` and `appending.py` remap them.
- Driver expressions are capped at 256 characters, and in background runs drivers only evaluate after `scene.frame_set(...)`.
- Blender's glTF importer copies vertices per primitive when primitives share an accessor (KK's and KKS's eyeline get 364 extra, an approved difference). Welding them would also merge the eyeline's doubled faces.
- Moving an armature with `rig.data.transform()` leaves the pose stale until a mode change. Move the bones as edit bones inside `editing()`, reading every position before assigning any: setting a bone's tail moves its connected children's heads, so they would move twice (`builtin/rigify/legacy.py`, `move_rig`).

### Running Blender

- Blender ignores `PYTHONPATH`; the in-Blender runner adds the venv's site-packages to `sys.path` itself. It also needs `--python-exit-code 1`, or a failing script still exits 0.
- `bpy.ops.ed.undo` works in `--background`, so undo tests can run headless.
- `bpy.ops` raises `RuntimeError` when an operator reports an ERROR; a refused import's `CANCELLED` shows up that way in tests.
- `addon_utils.extensions_refresh()` installs a newly listed wheel without a restart.

### Looking at the panel by hand

Headless tests can't draw panels. Start Blender with `BLENDER_USER_RESOURCES` pointing at a throwaway profile under `importer/tests/.work/`, with a copy of `importer/kkbp` (never a link, because the Pillow installer rewrites the manifest) in its `extensions/user_default/`, and import a copy of a sample.
