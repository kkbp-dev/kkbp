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
| `tools/library/` | Builds `library.blend` and the Hooks' asset files from code (`scripts/build-library.sh`, [ADR 0040](../docs/adr/0040-the-library-is-built-from-code.md)): `build.py`, the builder `nodes.py`, one module per node group in `groups/` and per material in `materials/`, and the decompiler, fingerprint and comparison tools |
| `library-src/` | The images, meshes and scenes the library and asset files are built from |
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

After changing a module in `tools/library/` or a file in `library-src/`, rebuild the template library and the Hooks' asset files, and check them:

```bash
scripts/build-library.sh
```

```bash
scripts/check-library.sh
```

To edit a node group visually, open the built `kkbp/library/library.blend` (or a copy), edit and save, then write the groups back to their modules and review the diff:

```bash
scripts/export-library-nodes.sh importer/kkbp/library/library.blend ".Group name"
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
- A driver doesn't run again when a node socket it reads is edited, from the UI or from Python; a keyframed socket does drive it as the frame changes. `node_tree.update_tag()` makes it run, which `kkbp.dropdowns` does on the message bus for the gag dropdown (ADR 0042). Tests, which have no event loop, call `dropdowns.refresh()` themselves.
- `obj.shape_key_add()` gives the new key a value of 1.
- A Menu Switch node comes with two items. Drivers read a menu socket as its item's number, given in the order the items were made, so renaming the two and adding the rest numbers them from 0 in order.
- A material whose node tree changes with the frame (a `frame` driver in it, or an Attribute node in View Layer mode) is updated on every frame, and so is every driver that reads any socket of it, and whatever those drivers drive. Ten materials re-evaluated per frame took EEVEE's Material Preview from 29 to 11 fps. An Attribute node in Object mode reading a property the object's own driver sets keeps the material still; EEVEE reads the new value each frame. `test_a_frame_change_updates_no_material` checks it.
- A new driver curve on a bone's location (`driver_add`) carries two keyframes, (0, 0) and (1, 1), with an ease between: a driven value between 0 and 1 comes out squashed, so 0.0002 becomes about 0. Shape-key value drivers get a linear curve and aren't affected. The joint corrections remove the keyframes, and then the driver's value is used as it is.
- A driver variable reading a bone's transform in `LOCAL_SPACE` includes its constraints; `TRANSFORM_SPACE` reads the channels as they are. The joint corrections keep each value in a register bone's X location and read it back in `TRANSFORM_SPACE`.
- Blender 5.2's file browser matches an operator's `filter_glob` against each file's full path (`filelist_readjob_common.cc`), later versions against its name alone, so a bare file name such as `manifest.json` shows nothing on 5.2. `*manifest.json` matches both; each pattern is cut at 15 characters.
- Blender's glTF importer copies vertices per primitive when primitives share an accessor (KK's and KKS's eyeline get 364 extra, an approved difference). Welding them would also merge the eyeline's doubled faces.
- Moving an armature with `rig.data.transform()` leaves the pose stale until a mode change. Move the bones as edit bones inside `editing()`, reading every position before assigning any: setting a bone's tail moves its connected children's heads, so they would move twice (`builtin/rigify/legacy.py`, `move_rig`).

### Running Blender

- Blender ignores `PYTHONPATH`; the in-Blender runner adds the venv's site-packages to `sys.path` itself. It also needs `--python-exit-code 1`, or a failing script still exits 0.
- `bpy.ops.ed.undo` works in `--background`, so undo tests can run headless.
- `bpy.ops` raises `RuntimeError` when an operator reports an ERROR; a refused import's `CANCELLED` shows up that way in tests.
- `addon_utils.extensions_refresh()` installs a newly listed wheel without a restart.

### Looking at the panel by hand

Headless tests can't draw panels. Start Blender with `BLENDER_USER_RESOURCES` pointing at a throwaway profile under `importer/tests/.work/`, with a copy of `importer/kkbp` (never a link, because the Pillow installer rewrites the manifest) in its `extensions/user_default/`, and import a copy of a sample.
