# Headless Blender test harness

Runs imports in `blender --background` on every configured Blender build and checks the resulting scene summaries against reviewed snapshots. Design: [docs/design/blender-compat-and-testing.md](../../../docs/design/blender-compat-and-testing.md#test-harness).

All commands run from the repository root and need Python 3.11 or later on the host.

## Blender builds

[harness.toml](harness.toml) lists the builds. Check them with:

```bash
python3 importer/tests/harness/run.py builds
```

- `min` is the minimum supported release, 5.2 LTS.
- `latest` is the latest stable release. As of 2026-10-31 that is still 5.2 (5.3 is in beta), so both builds point at the same binary. Builds that resolve to the same binary and version are imported once.

To use another build without editing the file, set `KKBP_BLENDER_<NAME>`:

```bash
KKBP_BLENDER_LATEST=/opt/blender-5.3.0-linux-x64/blender python3 importer/tests/harness/run.py builds
```

## The Golden Samples

The imports run on the Golden Samples in `contract/samples/`, which git ignores: each developer makes their own from the Sample Cards in `contract/sample-cards/` with `scripts/export-sample.sh` (ADR 0031). A Game with a Sample Card but no Golden Sample is skipped with a notice.

Import every Golden Sample with the Core Import (no Hooks) on every build, and fail if one doesn't import or its summary differs from the reviewed snapshot, [../snapshots/](../snapshots/)`<sample>.core.json` (D50):

```bash
python3 importer/tests/harness/run.py core
```

The snapshots are committed, and every developer's Golden Samples are checked against them. Physics settles differently on every export, so the bones it moves are compared within 3.5 cm instead of 1 mm ([physics.py](physics.py)): the `skirt`, `hair` and `breast` Bone Groups, the buttock bones under `cf_j_siri_L` and `cf_j_siri_R`, everything below them, and the Rigify bones, widgets and breast and buttock handles made from them. The Bone Groups come from the Golden Sample's `skeleton.json`.

Re-record the snapshots after a change that is meant to alter the scene, and review the diff before committing:

```bash
python3 importer/tests/harness/run.py core --update
python3 importer/tests/harness/run.py hooks --update
```

`scripts/test-importer.sh` runs this after the in-Blender tests. Each import gets its own profile with a copy of `importer/kkbp` and Pillow installed from the pinned wheel, and its own copy of the sample, so the samples stay untouched.

Import every Golden Sample with the Core Import followed by every built-in Hook, with the Import Options' defaults, and fail if an import or a Hook fails or the summary differs from `<sample>.defaults.json`:

```bash
python3 importer/tests/harness/run.py hooks
```

Run each built-in Hook on its own (`hooks=[that one]`, its switch on, once per choice for a choice switch) and check that it changes only what it owns, by the rules in [hook_owns.py](hook_owns.py). The reports are `importer/tests/.work/hooks/<build>.<sample>.<run>.md`:

```bash
python3 importer/tests/harness/run.py hooks --each [--hook "Fix body seams"]
```

`scripts/test-importer.sh` runs all three after the in-Blender tests.

## Scene summary

[blender/scene_summary.py](blender/scene_summary.py) records, for one imported Character:

- the collection tree;
- every object: type, parent, role tags, `id`, visibility, location, modifiers, and for meshes the vertex, edge and face counts, UV maps, vertex group count, material slots and shape keys; for armatures the bone count, bone collections and every bone's parent and rounded head and tail;
- every used material: role tags, `id`, render method, node groups (template) and texture images;
- image file names and datablock counts;
- `run`: Blender and importer versions, options, and the importer's log warnings and errors. `run` is kept for reference and is not compared.

It reads the importer's tags: an object's or material's role is its Part Role or Material Role, a material's `id` is its bundle Id and `template` its Material Template, and an image is known by the name the importer gives it (`cf_m_body main.light`), since bundle texture files are named `textures/0001.png`.

The Character's name is replaced by `{character}`. [compare.py](compare.py) compares two summaries: counts and names exactly, positions within 1 mm, or within a tolerance per path ([physics.py](physics.py)). `hooks --each` diffs a Hook run with the Core Import of the same bundle item by item ([hook_owns.py](hook_owns.py)).

```bash
python3 -m unittest discover importer/tests/harness
```
