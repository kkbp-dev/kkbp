# Headless Blender test harness

Runs imports in `blender --background` on every configured Blender build and checks the resulting scene summaries against reviewed snapshots. Design: [docs/design/blender-compat-and-testing.md](../../../docs/design/blender-compat-and-testing.md#test-harness).

All commands run from the repository root and need Python 3.11 or later on the host.

## Blender builds

[harness.toml](harness.toml) lists the builds. Check them with:

```bash
python3 importer/tests/harness/run.py builds
```

- `min` is the minimum supported release, 5.2 LTS: on the development machine, the release tarball in `~/.local/opt/blender-5.2.2/`.
- `latest` is the latest stable release: the snap at `/snap/bin/blender`, 5.3.0 as of 2026-11-12.

Builds that resolve to the same binary and version are imported once.

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

Each import gets its own profile with a copy of `importer/kkbp` and Pillow installed from the pinned wheel, and its own copy of the sample, so the samples stay untouched. The copy's files are hard links to the sample's ([bundle_copy.py](../bundle_copy.py)): an import writes only into `kkbp_cache/`, which the copy leaves out.

Import every Golden Sample with the Core Import followed by every built-in Hook, with the Import Options' defaults, and fail if an import or a Hook fails or the summary differs from `<sample>.defaults.json`:

```bash
python3 importer/tests/harness/run.py hooks
```

Run each built-in Hook on its own (`hooks=[that one]`, its switch on, once per choice for a choice switch) and check that it changes only what it owns, by the rules in [hook_owns.py](hook_owns.py). The reports are `importer/tests/.work/hooks/<build>.<sample>.<run>.md`:

```bash
python3 importer/tests/harness/run.py hooks --each [--hook "Outlines"]
```

All three at once, with every import in one queue (the Core Import once per sample and build, not twice) and then the three checks; `scripts/test-importer.sh` runs this after the in-Blender tests:

```bash
python3 importer/tests/harness/run.py all
```

## Rig fingerprint

The snapshots record bone positions and only the *counts* of drivers and constraints, so they can't
tell whether a constraint's settings or a driver's expression changed. For a change to the Rigify
Hook that must leave the rig as it was, compare a rig fingerprint instead: [blender/rig_fingerprint.py](blender/rig_fingerprint.py)
imports a Golden Sample with the Rigify Hook alone and records the metarig as the Hook hands it to
Rigify and the finished rig: every bone collection in order, every bone's and pose bone's
properties, custom properties with their UI data, Rigify types and the Rigify parameters that are
set, every constraint in stack order with all its settings, every driver, the Character's modifiers,
vertex groups (with a hash of their weights) and shape keys (with a hash of their positions), the
widgets, Rigify's UI script, and the Hook's log lines. The names that change on every import (the
Character's name and key, Rigify's `rig_id`, the metarig's random id bone, the order of Rigify's
set literals) are replaced ([blender/fingerprint_names.py](blender/fingerprint_names.py)).

Record the baseline on the commit before the change, then compare after each commit:

```bash
python3 importer/tests/harness/run.py fingerprint --record   # the baseline, in .work/fingerprint/base/
python3 importer/tests/harness/run.py fingerprint            # fails if anything differs
```

Each build and Golden Sample is compared with its own baseline; the differences go to
`importer/tests/.work/runs/<build>/<sample>.fingerprint/differences.txt`. The baseline is local, like
the Golden Samples it comes from (ADR 0031), and is void once they or a Blender build change:
record it again from the base commit, in a `git worktree` if the work has moved on. `--baseline NAME`
keeps another one beside it. A fingerprint takes about 25 s per sample and build.

A value a driver sets is recorded as the driver leaves it, so changing the stored value under a
driver shows no difference; the driver itself is compared.

`--jobs` sets how many Blender processes import at once (every command but `builds`). Each keeps about three CPU threads busy and needs up to about 1.3 GB, so the default is a quarter of the machine's threads, and at least 2.

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
