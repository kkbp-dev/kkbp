# exporters

The Exporter Core and the Game Adapters (KK/KKS, SVS). The design is [docs/design/exporter-core.md](../docs/design/exporter-core.md).

| Path | Contents |
|---|---|
| `core/KKBP.Exporter.Core.shproj`, `.projitems` | The Exporter Core as a shared source project. Exporters import the `.projitems` to compile it in. |
| `core/src/` | The Core's source: .NET 3.5 APIs only, no UnityEngine |
| `core/src/AdapterKit/` | Unity-free helpers both adapters use: normal-map unpacking, shape-key deltas, the hidden tear and gag basis, closing the SVS eye seam (ADR 0033), the SVS eye white copies (ADR 0034), Bone Role and Group rules, Blend Mode choice, Texture Roles, and the pixel steps of the light and dark bake |
| `core/build/` | Builds the Core alone for `net35`, so newer APIs fail the build. Nothing ships from it. |
| `core/tests/` | `dotnet test` project with a fake Game Adapter. Its bundle is checked against the JSON Schemas and the Khronos glTF Validator. |

## Checking the Core

```bash
scripts/check-core.sh
```

It builds the Core for `net35`, installs the pinned glTF Validator in `contract/tools/` with `npm ci`, and runs the tests. It needs the .NET SDK 10 or later and Node.js, found on `PATH` or in `~/.dotnet` and `~/.local/node/bin`. On Linux the `net35` reference assemblies come from the `Microsoft.NETFramework.ReferenceAssemblies.net35` package during restore. A CI job can call the script as it is.

## Building the adapters

| Path | Game | Configuration | Output |
|---|---|---|---|
| `kk/KKBP.Exporter.KK.csproj` | KK | `NET35` | `kk/bin/NET35/KKBP.Exporter.KK.dll` |
| `kk/KKBP.Exporter.KK.csproj` | KKS | `NET46` | `kk/bin/NET46/KKBP.Exporter.KKS.dll` |
| `svs/KKBP.Exporter.SVS.csproj` | SVS | `Release` | `svs/bin/Release/KKBP.Exporter.SVS.dll` |

```bash
scripts/build-exporters.sh
```

```bash
scripts/deploy-exporter.sh kk
```

The adapters compile against the game, Unity and BepInEx assemblies of a local install ([ADR 0007](../docs/adr/0007-game-assemblies-from-local-install.md)): the `games/` folder in the working copy, or the folder in `KKBP_GAMES_DIR`, holding `Koikatsu`, `Koikatsu Sunshine` and `Summer Vacation Scramble`. SVS needs BepInEx to have run once, so that its interop assemblies exist. [Exporter.props](Exporter.props) holds the shared settings and the Exporter Version. The deploy script copies a build into `<game>/BepInEx/plugins/KKBP/`.

## Packaging a release

```bash
scripts/package-exporters.sh
```

It builds all three adapters and writes `exporters/dist/kkbp-exporters-<version>.zip`, named after the Exporter Version in [Exporter.props](Exporter.props). LICENSE and NOTICE sit at the zip's root beside a folder per Game: `Koikatsu`, `Koikatsu Sunshine` and `Summer Vacation Scramble`. Each holds `BepInEx/plugins/KKBP/` with that Game's DLL, so a user installs the exporter by copying that folder's `BepInEx` into the game's root folder, the one with the game's `.exe`. It needs all three installs, since each adapter builds against its own.

## Exporting in the game

In the character maker, KK and KKS show the exporter window from the sidebar toggle "Show KKBP Exporter", and SVS shows and hides it with Ctrl+Tab. The window opens where the legacy KK exporter drew its options, and its option names are the legacy KK exporter's: Export All Outfits, Export Variations, Freeze Current Pose, Freeze Shape Keys and Disable Physics. Disable Physics is the inverse of the manifest's `physics` option.

**Export every card in a folder…** opens a folder browser in the window, starting at the folder it last exported (the game's `UserData/chara` at first). **Export them** loads each `.png` directly in that folder into the maker, in name order, and exports it with the window's options, one bundle each, into the usual output folder; it is the legacy KK exporter's "Bulk export all cards in folder". A file the game doesn't load as a character card (an outfit card, a plain picture) is skipped and logged, and the batch goes on. The window shows "Card 3 of 12", and **Stop after this card** ends the batch early. At the end it shows how many exported and how many failed; the BepInEx log names each failure. Each card replaces the Character in the maker, and the last one stays loaded.

## The game launcher

The scripts that start a game (`scripts/auto-export.sh`, and through it `scripts/export-sample.sh`) run `games/play.sh <koikatsu|kks|svs>`, or `play.sh` in `KKBP_GAMES_DIR`. It isn't in the repository, because how a Windows game starts depends on the computer: each computer brings its own. [scripts/play.example.sh](../scripts/play.example.sh) is the one this repository was developed with (umu-launcher, a pinned GE-Proton, one prefix per game); copy it to `games/play.sh`, make it executable and set its paths. Any launcher works if it:

- takes the game as its first argument: `koikatsu`, `kks` or `svs`;
- starts that game's main exe (`Koikatu.exe`, `KoikatsuSunshine.exe`, `SamabakeScramble.exe`) from the game's own folder, with BepInEx loading: under Wine, the doorstop proxy DLL must load native (`winhttp` for KK and KKS, `hid` for SVS);
- leaves the game running as a process with that exe's name, which the scripts watch and stop with `pkill -x` (Linux keeps the first 15 characters).

`auto-export.sh` refuses to start without an executable launcher. SVS needs Proton; KK and KKS also run on plain Wine. The games must be HF Patched with BepInEx, and SVS must have started once so that BepInEx has made its interop assemblies.

## Exporting from a script

Each plugin runs an export when `BepInEx/config/kkbp-autoexport.json` exists ([ADR 0012](../docs/adr/0012-file-triggered-auto-export.md)): it opens the maker, loads the card, exports and quits. `scripts/auto-export.sh` writes the request, starts the game through the launcher and prints the result:

```bash
scripts/auto-export.sh kks contract/sample-cards/kks.png /tmp/out '"outfit": 0'
```

Given a folder instead of a card, the request is `"folder"` and the plugin runs the batch export on it; the result lists `cards`, `bundles` and `failures`, and succeeds only if every card exported:

```bash
scripts/auto-export.sh kk ~/cards /tmp/out
```

`scripts/check-bundle.sh <bundle>` checks any bundle as the Golden Samples are checked, and `scripts/export-sample.sh [game]` makes the Golden Samples (ADR 0031). The request can also carry `"dump_shaders"` (KKS: writes the shader property table KK embeds as `kk/shader-properties.json`; `"dump_bundles"` adds the shaders of the asset bundles it lists, such as KK's `abdata/chara/mm_base.unity3d` for KK's create shaders), `"diagnose"` (SVS: describes the maker's Character instead of exporting) and `"stay": true` (SVS: leaves the game in the maker with the card loaded, for trying the window by hand).

## Writing a Game Adapter

An adapter implements `IGameAdapter` and runs `new BundleExport(adapter, outputDirectory).Run()` as a coroutine. The Core checks what it is given and fails the export, with no Manifest, if:

- the first Pass isn't the Body Pass, or two Passes have the same Outfit;
- a Pass's bones don't form one tree, or a bone seen in two Passes has a different parent or rest pose;
- a mesh isn't skinned, has a vertex with no weight, or uses a material or bone that wasn't captured;
- a unique Bone Role or Material Role appears twice, or a material has two textures in one slot;
- a material section repeats a texture slot or field, or its material is unused in, or used outside, the Pass that captured it;
- an Expression Name's prefix doesn't match its category, or a mesh has two shape keys with one name;
- a texture or the Card isn't PNG data, or a physics chain uses a collider no Pass captured.

Keys are the adapter's own stable names for game objects (a transform path is a good choice). Walk game objects in a fixed order so that re-exports get the same Ids ([ADR 0005](../docs/adr/0005-ids-per-kind-from-adapter-keys.md)).

## Working with the games

What the adapters' authors learned the hard way. The safety rules for running the games (check before launching, stop by exact process name, no synthetic input under Wayland) are in [CLAUDE.md](../CLAUDE.md#running-the-games-safely).

### Reading the game's code

- `ilspycmd` (in `~/.dotnet/tools`) decompiles the games. KK and KKS: `Assembly-CSharp.dll` under `<game>_Data/Managed/`. SVS: its IL2CPP interop assemblies are in `games/Summer Vacation Scramble/BepInEx/SamabakeScramble/interop/`, not `BepInEx/interop/`.
- .NET string literals are stored as UTF-16, so a plain `grep` on a DLL finds nothing; decode the file as UTF-16LE at both byte alignments.
- The game assemblies aren't publicized: protected members such as `CustomTextureCreate.matCreate` and `texMain` are read by reflection. The legacy exporters built against publicized copies, so their code doesn't port directly.

### Loading cards

- `LoadFileLimited` doesn't tell a character card from anything else. KK and KKS report no error code for an outfit card or a plain picture and keep the Character they had; SVS's returns false even for a good card. So `Cards.Load` checks the card's mark first, the string after its PNG picture (`CardFile.Mark` in the AdapterKit): KK loads `【KoiKatuChara】`; KKS also `【KoiKatuCharaS】`, `【KoiKatuCharaSP】` and `【KoiKatuCharaSun】` (`Kks.CardMarks`, read from each game's own card reader); SVS `【SVChara】`. Outfit cards are `【KoiKatuClothes】` and `【SVClothes】`.
- KK's `LoadFileLimited` doesn't keep the card's picture; `Cards.Load` always sets it from the loaded file.
- KKS's maker runs at time scale 0, so waits use `WaitForSecondsRealtime`.

### IL2CPP (SVS)

- Use `TryCast`, never `is`.
- Key dictionaries and sets by `GetInstanceID()`: two wrapper objects for one game object don't compare equal.
- Methods that fill arrays (`GetBlendShapeFrameVertices`) take `Il2CppStructArray`.
- Step coroutines yourself and pass on what they yield; the IL2CPP wrapper can't be handed a nested coroutine.
- Cast window callbacks to `GUI.WindowFunction` and pass explicit `GUILayoutOption` arrays.
- URP won't render from a disabled camera.
- Under Proton on GNOME, Ctrl and Shift reach SVS but the letter of a Ctrl+Shift shortcut doesn't; the window uses Ctrl+Tab.

### Testing in the games

- A game keeps the plugin it loaded at startup: deploy only to a closed game.
- A running-game check can't be tested with a renamed copy of `sleep` (it refuses to run under another name); doing so launched the real SVS once.
- The legacy samples can mislead: in the legacy KK sample, `cf_m_body_T3.png` is the rendered material's liquid texture, not a create texture, because the two share one file name. Legacy's shader property lists (`MaterialShaders.cs`) are handwritten and inexact (`tex4uv` typed as a colour).
