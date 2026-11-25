# Working on KKBP

Instructions for an AI agent (or anyone) changing this repository. Read this first, then the docs it points to.

KKBP has three parts: exporters (BepInEx plugins for KK, KKS and SVS) write an **Export Bundle**, the **contract** defines that bundle, and a Blender **importer** rebuilds the Character from it. The importer and the exporters are released together under one KKBP Version, the release date `YYYY.MM.DD` in `VERSION` (ADR 0060).

## Read before changing anything

- [CONTEXT.md](CONTEXT.md): the glossary. Use its terms, not the ones it lists under "Avoid".
- [docs/design/README.md](docs/design/README.md): the design docs and every numbered decision (D1 onwards), each saying what holds now.
- [docs/adr/](docs/adr/): decisions that look wrong without context. Check them before "fixing" something that seems odd (for example SVS's eye bones, ADR 0028; edit materials not saturating, ADR 0026; Expression Names as display strings, ADR 0004).
- [docs/hook-interface.md](docs/hook-interface.md): the public Hook API, version 2.1.
- The README in [exporters/](exporters/README.md) (with "Working with the games"), [importer/](importer/README.md) (with "Blender quirks") and [the test harness](importer/tests/harness/README.md).

## First-time setup on a new computer

A fresh clone can't run the tests yet: the Golden Samples the tests import are made on each computer from the games (ADR 0031). In this order:

1. `git lfs install --local`, then `git lfs pull`: the Sample Cards, template library and Hook assets are LFS files.
2. Blender 5.2 or later, with `importer/tests/harness/harness.toml` (or `KKBP_BLENDER_<NAME>`) pointing at it; then `scripts/setup-importer-dev.sh`. It must come before step 5, which ends with a Blender import.
3. The .NET SDK 10 or later and Node.js; `scripts/check-core.sh` checks them.
4. The games, HF Patched with BepInEx, in `games/` (or `KKBP_GAMES_DIR`), SVS started once, and a launcher at `games/play.sh`: copy `scripts/play.example.sh` and adapt it ("The game launcher" in [exporters/README.md](exporters/README.md)). Ask the user for anything here you can't find.
5. `scripts/export-sample.sh` (in the background; a few minutes per game): it builds and deploys each exporter, exports each Sample Card, and checks the imports against the committed snapshots. A Game that isn't installed is skipped, and its tests then skip too.
6. `scripts/test-importer.sh` and `scripts/check-core.sh`.

## How to work

- Before writing code, list every undecided point with a proposal and wait for the user's OK.
- Record a surprising decision as a new ADR (next number after the latest in `docs/adr/`), list it in `docs/design/README.md`, and add new terms to `CONTEXT.md`.
- Work in small commits. Stage files by path; never `git add -A`. End every commit message with the `Co-Authored-By:` trailer of the model that wrote it.
- Never commit the files and folders listed in `.gitignore`.
- The git author is a placeholder from the global `~/.gitconfig`; leave it alone.
- The remote is `origin` on GitHub (`kkbp-dev/kkbp`); a change goes on its own branch and into `main` through a pull request. There is no CI: build, test and check steps are local scripts under `scripts/`.
- Nothing gets installed into Blender's own Python or the user's Blender profile without their OK, and each OK covers that one install.
- Long runs (the full test suite, `export-sample.sh`, game exports) take minutes: run them in the background and wait for them.
- Run the full test suite once, after a change. Don't run it before the change for a baseline: the committed snapshots are the baseline, and `scripts/test-importer.sh` stops at once on a tree that already passed (the green stamp). To see whether a failure predates the change, run that one test (`launch.py -k <name>`, or `run.py core --sample <game>`) on the base commit, not the whole suite.

## Rules the code follows

- **Contract:** don't change `contract/` without the user's OK. If the contract looks wrong or incomplete, stop and say so. A Schema Version major change also forces a hook interface major change. A contract change touches several places; see "Common changes".
- **The earlier importer and exporters aren't in the repository**, and the docs and code describe KKBP as it is, not by comparison with them. A copy kept beside the repository (`.gitignore` lists `Blender addons/`, `kkbp_exporter/`, `svs_exporter/` and `Sample exporter output files/`) is read-only reference. `games/` is ignored by git too. Files copied out of any of them can arrive with mode 755; check before committing.
- **Golden Samples are local** (ADR 0031): `contract/samples/` is ignored by git and never committed. Each developer makes them from the tracked Sample Cards in `contract/sample-cards/` with `scripts/export-sample.sh`. The importer snapshots stay committed; their comparison allows 3.5 cm on the bones physics moves (`importer/tests/harness/physics.py`).
- **Importer:**
  - `bundle/`, `profiles/` and `library/` never import `bpy` (a host test checks).
  - Version checks (`bpy.app.version`) live only in `compat/` (a test checks); `bpy.app.version_string` for messages is fine anywhere.
  - There is no `import kkbp` and nothing goes into `sys.modules` under that name: the hooks-folder loader hands scripts `kkbp`, other add-ons look KKBP up by its id, and tests import `bl_ext.user_default.kkbp`.
  - Steps get `ctx.profile`; Hooks don't. Built-in Steps and Hooks never check `ctx.game`; Game differences go in the Game Profiles.
  - Use the data API where one exists; operators only through small helpers in `compat/`; mode changes only through `editing()`.
  - Find things by Character, Part Roles, Material Roles, Bone Roles and Bone Groups, never by object or node names. The exception is bones the Rigify and SFW Hooks need by exact name (their joint-correction, nipple and other game bones with no Role, in the Rigify Hook's `names.py` and listed in `docs/design/hooks-and-tools.md`): they are written in the Hook with a note saying why. They aren't violations.
  - The Mesh Loader (`mesh_loader.py`) is the only caller of Blender's glTF importer and sets every option in `GLTF_OPTIONS` explicitly; change one only when an import shows it is wrong.
  - Never edit `library.blend` or the Hook asset files by hand: change a node module in `importer/tools/library/groups/` or `materials/`, or a source file in `importer/library-src/`, and rebuild with `scripts/build-library.sh` (ADR 0040). A group edited visually in Blender goes back into its module with `scripts/export-library-nodes.sh`.
  - The KKBP log goes to the bundle's `kkbp_cache/log/log.txt`, replaced by each import, never into the `.blend`.
  - Pillow is pinned (`PILLOW_VERSION` in `kkbp/pillow.py`) and raised only on purpose. A wheel must match the running Python and platform; never hard-code a tag such as `cp313`.
  - The Pillow installer rewrites the `blender_manifest.toml` of the add-on it runs from and fills its `wheels/`. Never link `importer/kkbp` itself into a Blender profile; profiles get a copy.
  - Anything added to the public API (`kkbp/api.py`) must be in `docs/hook-interface.md` (a test checks), and raises the hook interface's minor version; changing or removing something raises the major version.
- **Exporters:**
  - Game-independent code goes in the Exporter Core (`exporters/core/`, .NET 3.5 APIs, no UnityEngine, no mutable static fields). Every `.cs` file in `core/src` must be listed in `KKBP.Exporter.Core.projitems`. Unity-free helpers both adapters need go in `core/src/AdapterKit/`, where the Core tests cover them.
  - The Core fails an export, with no Manifest, on captured data that breaks the contract. A new contract rule needs a Core check as well as a contract test.
  - A Game-only field (a Game Extension) is added only when a Step or Hook reads it; KK and KKS both write `kk`.
  - KK/KKS differences live in `exporters/kk/src/Kks.cs`. SVS is IL2CPP, with rules of its own ("Working with the games" in [exporters/README.md](exporters/README.md)).
- **Tests and manual imports** use copies of the Golden Samples, never `contract/samples/` itself: every import writes `kkbp_cache/` into the folder it imports. A test of a Game with no Golden Sample skips (`golden()` in the test conftests).

## Running the games safely

The user plays these games. Details are in "Working with the games" in [exporters/README.md](exporters/README.md).

- Check that a game isn't running before launching or deploying to it. `scripts/auto-export.sh` refuses to start while the game runs; a running game also keeps the plugin it loaded, so a deploy only takes effect after a restart.
- Stop a game by its exact process name, which Linux cuts to 15 characters: `pkill -x Koikatu.exe`, `pkill -x KoikatsuSunshin`, `pkill -x SamabakeScrambl`. Never use `pgrep -f` or `pkill -f`: they match any command line that mentions the game, your own shell included.
- Under GNOME Wayland, synthetic keys (xdotool) don't reach the game windows, and X11 screenshots come out black. Ask the user to press keys or look. The SVS request `"stay": true` leaves the maker open for that.
- KK sometimes hangs at startup while BepInEx loads plugins (its log stops at XUnity hook warnings). Stop it, delete `games/Koikatsu/BepinEx/config/kkbp-autoexport.json`, and try again.

## Commands

| What | Command |
|---|---|
| Set up the importer's dev venv (once, and after the `min` build changes) | `scripts/setup-importer-dev.sh` |
| All importer tests: host, harness, in-Blender, sample imports, each Hook, snapshots. A tree that already passed (same files, Golden Samples and Blender builds) isn't run again; `--force` runs it anyway | `scripts/test-importer.sh` (no arguments) |
| Only one half, or a filter | `scripts/test-importer.sh --host-only` / `--blender-only`; with pytest arguments (`-k name`) it runs only the pytest tests, not the sample imports, Hook runs or snapshot checks |
| Only some in-Blender tests | `python3 importer/tests/blender/launch.py -k <name>` (a file path doesn't narrow it) |
| Keep an imported scene as a `.blend` in `importer/tests/.work/runs/` | add `--keep-blend` to `run.py core` or `hooks` |
| Check that a Rigify Hook change leaves the rig as it was: record the baseline on the base commit, then compare | `python3 importer/tests/harness/run.py fingerprint --record`, then `... fingerprint` |
| Re-record the importer snapshots after an intended scene change (review the diff) | `python3 importer/tests/harness/run.py core --update` and `... hooks --update` |
| Exporter Core build (net35) and tests | `scripts/check-core.sh` |
| Build or deploy an exporter | `scripts/build-exporters.sh [kk\|kks\|svs]`, `scripts/deploy-exporter.sh <game>` |
| Export in a game from a script (card or folder) | `scripts/auto-export.sh <game> <card.png\|folder> <out>` |
| Make the Golden Samples (first time, and after an exporter change), or one of them | `scripts/export-sample.sh` / `scripts/export-sample.sh <game>` |
| Record a game's joint corrections for the tests (after a game update or a rule change; ADR 0038) | `scripts/probe-corrections.sh <game>` |
| Check any bundle | `scripts/check-bundle.sh <bundle>` |
| Set the KKBP Version for a release (both parts) | `scripts/set-version.sh [YYYY.MM.DD]` |
| Package the importer zip | `scripts/package-importer.sh` |
| Package the exporter release zip (all three Games) | `scripts/package-exporters.sh` |
| Rebuild the template library and Hook assets, or check the committed ones match their sources | `scripts/build-library.sh`, `scripts/check-library.sh` |
| Write node groups edited in Blender back to their modules | `scripts/export-library-nodes.sh <file.blend> [name ...]` |
| Redraw the face cards' SVS eye white mask (then `scripts/build-library.sh`) | `importer/.venv/bin/python importer/tools/make_svs_eye_white_mask.py contract/samples/svs` |
| Regenerate the importer's copy of the contract sets | `scripts/gen-importer-contract.sh` |

Run the importer's host tests and pytest only on `importer/.venv/bin/python` (Blender's own Python, ADR 0015), never the system `python3`. `run.py` and `launch.py` run on the system `python3` (3.11 or later).

## Common changes

- **A change that alters the imported scene:** run `scripts/test-importer.sh`; if the snapshots differ on purpose, re-record them and say what changed in the commit.
- **An exporter change that alters bundles:** `scripts/check-core.sh`, then remake the Golden Samples with `scripts/export-sample.sh` (it ends with the snapshot check), then run the importer tests. If the imported scene changes on purpose, re-record the snapshots and commit those; the samples themselves are never committed. Re-exports differ every time even with no code change: KK and KKS physics (skirts, hair, breasts, `skeleton.json`, `physics.json`) and SVS's MagicaCloth settle differently, which the physics tolerance absorbs; SVS's light and dark bakes vary slightly, and texture files renumber whenever a material or texture is added or removed. To compare bundles before and after, copy `contract/samples/` before exporting.
- **A contract change** (with the user's OK) touches:
  1. the schema in `contract/schema/` (every object needs `additionalProperties`; a test checks);
  2. the rule text in `contract/README.md`;
  3. the C# contract checker, `exporters/core/tests/Support/ContractChecker.cs`;
  4. the Core's own check in `exporters/core/src/BundleWriter.cs`, with a failure test and a line in the `exporters/README.md` list;
  5. the importer's `importer/kkbp/bundle/` (`rules.py`, the reader, `_contract.py` through `scripts/gen-importer-contract.sh`) and `importer/tests/bundle_builder.py`.
- **A new Hook:** a module in `importer/kkbp/builtin/`, its place in `BUILTIN_HOOKS` (`importer/kkbp/pipeline/steps.py`), its own asset file if it needs one (a table entry in `importer/tools/library/build.py`, built by `scripts/build-library.sh`), and a rule in `importer/tests/harness/hook_owns.py` for what it may change.
- **A new shader in KK:** KK's Unity 5.6 can't list a shader's properties, so every shader KK captures needs an entry in `exporters/kk/shader-properties.json`, made by the KKS `dump_shaders` request ([exporters/README.md](exporters/README.md)).
- **A new Blender release:**
  - Add or point a build in `importer/tests/harness/harness.toml`. Today `min` is the 5.2.2 tarball in `~/.local/opt/blender-5.2.2/` and `latest` the snap at `/snap/bin/blender` (5.3.0), and every check runs on both.
  - Fetching a build: download.blender.org refuses `curl`, and snap installs one version at a time; two side by side need snap's `experimental.parallel-instances`, which only the user can turn on. Ask the user.
  - Run the tests on it. The Mesh Loader test fails if the glTF importer gained an option `GLTF_OPTIONS` doesn't set; give it a deliberate value.
  - Put version-specific code in `compat/`.
- **Installing the importer into the user's Blender profile** (with their OK): `scripts/package-importer.sh` leaves Pillow out, and a reinstall deletes any wheel no extension lists, so a plain "Install from Disk" loses the installed Pillow. Instead:
  1. Stage the package with the pinned wheel from `importer/tests/.work/wheels/` in `kkbp/wheels/`.
  2. Replace the manifest's `#wheel_placeholder` line with `wheels = ["./wheels/<file>.whl"]`.
  3. Run `blender --command extension install-file --repo user_default --enable <zip>`, then restart Blender. The profile copy is in `~/.config/blender/5.2/extensions/user_default/kkbp`.
- **A release:** set the date with `scripts/set-version.sh` (today by default; it writes `VERSION` and the manifest's unpadded copy, ADR 0060), re-record the snapshots, package both (`scripts/package-importer.sh`, `scripts/package-exporters.sh`), deploy, and tag `v<YYYY.MM.DD>`. At most one release a day.

## The machine

The computer this repository is developed on. On another computer, follow "First-time setup" and adapt the paths below.

- **Git LFS is required.** `.gitattributes` sends `png`, `jpg`, `glb`, `bin`, `blend`, `whl`, `dll` and `fbx` to LFS (set up with `git lfs install --local`). Without git-lfs a checkout gets pointer files and the tests fail. A new binary file type needs its own line in `.gitattributes`.
- **Blender:** the builds in `importer/tests/harness/harness.toml`: `min` is 5.2.2 LTS, the release tarball in `~/.local/opt/blender-5.2.2/`; `latest` is the snap at `/snap/bin/blender` (5.3.0, and it refreshes silently). Override either with `KKBP_BLENDER_<NAME>`. A process with `NoNewPrivs` set (`/proc/self/status`; the Claude desktop app sets it on everything it starts) can't start the snap, whose `snap-confine` needs file capabilities: set `KKBP_BLENDER_LATEST=/snap/blender/current/blender`, the same build without the snap's launcher. The venv is built from `min`'s Python; rerun `scripts/setup-importer-dev.sh` if `min` moves.
- **The first in-Blender test run needs the network**, to download the pinned Pillow wheel from PyPI into `importer/tests/.work/wheels/`.
- **.NET and Node:** .NET SDK 10 or later and Node.js, on `PATH` or in `~/.dotnet` and `~/.local/node/bin`. `scripts/check-core.sh` installs the glTF Validator. `ilspycmd` (in `~/.dotnet/tools`) decompiles the games.
- **The games** are in `games/` (ignored by git; `KKBP_GAMES_DIR` overrides): Koikatsu, Koikatsu Sunshine and Summer Vacation Scramble, HF Patched with BepInEx, under GE-Proton through `games/play.sh <koikatsu|kks|svs>` (on this computer, a copy of `scripts/play.example.sh`). Prefixes are in `~/Games/prefixes/`, launch logs in `~/Games/logs/`. The adapters build against these installs' assemblies (ADR 0007).
- **Game logs:** KK `games/Koikatsu/BepinEx/LogOutput.log`, KKS `games/Koikatsu Sunshine/output_log.txt`, SVS `games/Summer Vacation Scramble/BepInEx/LogOutput.log`.
- **Run times:** one headless import of a Golden Sample takes 5–15 s (Rigify the longest); the full test suite about 9 minutes (host 45 s, the in-Blender tests 4.5 min on both builds at once, the 84 harness imports 3.5 min), or under a second when the tree is already green; a game export takes one to a few minutes per card.
- **Sample Cards** are tracked in `contract/sample-cards/<game>.png`; `batch_exporter_testing/` (ignored by git) holds more cards per game for batch tests. A fresh checkout has no Golden Samples until `scripts/export-sample.sh` makes them; the stamp beside each (`contract/samples/<game>.stamp`) makes the test scripts warn when the working tree's exporters or contract differ from the ones that made it.
