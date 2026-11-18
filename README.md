# KKBP

<!-- Badges: replace OWNER/REPO in both places it appears on each line, then remove this comment's first and last lines.
[![Downloads](https://img.shields.io/github/downloads/OWNER/REPO/total)](https://github.com/OWNER/REPO/releases)
[![Latest release](https://img.shields.io/github/v/release/OWNER/REPO)](https://github.com/OWNER/REPO/releases/latest)
![Blender 5.2+](https://img.shields.io/badge/Blender-5.2%2B-orange?logo=blender&logoColor=white)
-->

KKBP brings a character from Koikatsu, Koikatsu Sunshine or Summer Vacation Scramble into Blender, shaded, rigged and ready to pose.

<!-- Hero image: the character in the maker beside the same character in Blender.
<p align="center"><img src="docs/wiki/images/readme/hero.jpg" alt="A character in the game's maker and the same character in Blender" width="900"></p>
-->

It has two halves. An **exporter** runs inside the game and saves the character in the maker to a folder. An **importer** runs inside Blender and rebuilds the character from that folder.

**[Download the latest release](../../releases/latest)** · [Install](#install) · [Usage](#usage) · [Documentation](docs/wiki/README.md)

## Features

<!-- Each cell takes a thumbnail above its caption once the pictures exist:
     <img src="docs/wiki/images/readme/shaders.jpg" width="210"><br> -->
<table>
<tr>
<td width="25%" valign="top"><b><a href="docs/wiki/shaders.md">Looks like the game</a></b><br>Shaders for Eevee and Cycles, a plain Principled setup, and the game's outlines.</td>
<td width="25%" valign="top"><b><a href="docs/wiki/rig.md">A rig that bends like the game</a></b><br>A Rigify control rig, with elbows, knees and shoulders corrected by the game's own rules.</td>
<td width="25%" valign="top"><b><a href="docs/wiki/expressions.md">Every expression</a></b><br>All the game's eye and mouth expressions with English names, an emotion grid, gag eyes and tears.</td>
<td width="25%" valign="top"><b><a href="docs/wiki/outfits.md">Every outfit</a></b><br>All of a card's outfits in one import, with their half-off variations if you want them.</td>
</tr>
<tr>
<td valign="top"><b><a href="docs/wiki/edit-material.md">Recolour anything</a></b><br>Edit Material rebuilds a material from the game's layers and colours, then bakes your changes.</td>
<td valign="top"><b><a href="docs/wiki/export-prep.md">On to other programs</a></b><br>Export Prep readies the character for VRM, VRChat or Unreal, with a texture atlas.</td>
<td valign="top"><b><a href="docs/wiki/animation.md">Koikatsu animations</a></b><br>Put a Koikatsu <code>.fbx</code> animation on the rig, with no other add-on.</td>
<td valign="top"><b><a href="docs/wiki/importing.md">Built for batches</a></b><br>Export a folder of cards, import a folder of exports, and run <a href="docs/wiki/hooks.md">your own scripts</a> after each import.</td>
</tr>
</table>

The Blender panel is in English, Chinese (Simplified), French, German, Indonesian, Japanese, Portuguese, Russian, Spanish and Thai.

## Supported games

| Game | What the game needs | The exporter window opens with | Not supported |
|---|---|---|---|
| Koikatsu | BepInEx (HF Patch installs it) | the "Show KKBP Exporter" toggle in the maker's sidebar | |
| Koikatsu Sunshine | BepInEx (HF Patch installs it) | the "Show KKBP Exporter" toggle in the maker's sidebar | |
| Summer Vacation Scramble | BepInEx (HF Patch installs it) | Ctrl+Tab in the maker | |

Blender 5.2 or newer. The differences between the games are listed in [Game support](docs/wiki/game-support.md).

## Install

Download two files from the [latest release](../../releases/latest): `kkbp-exporters-<version>.zip` and `kkbp-<version>.zip`.

**The exporter, in the game:**

1. Open `kkbp-exporters-<version>.zip`. It has one folder per game.
2. Open your game's folder in the zip and copy the `BepInEx` folder inside it.
3. Paste it into the game's main folder, the one with the game's `.exe`. It merges with the `BepInEx` folder already there.

| Game | Folder in the zip | The game's main folder has |
|---|---|---|
| Koikatsu | `Koikatsu` | `Koikatu.exe` |
| Koikatsu Sunshine | `Koikatsu Sunshine` | `KoikatsuSunshine.exe` |
| Summer Vacation Scramble | `Summer Vacation Scramble` | `SamabakeScramble.exe` |

**The importer, in Blender:**

1. Open Edit > Preferences > Get Extensions, open the menu at the top right and choose Install from Disk.
2. Pick `kkbp-<version>.zip`. Don't unzip it.
3. Press N in the 3D viewport and open the KKBP tab.
4. Click Download Pillow. This is needed once, and needs an internet connection.

[Installing](docs/wiki/installing.md) has the same steps with pictures, and how to update.

## Usage

**Export, in the game:**

1. Open the character maker and load the character.
2. Open the exporter window: tick "Show KKBP Exporter" in the sidebar (Koikatsu, Koikatsu Sunshine) or press Ctrl+Tab (Summer Vacation Scramble).
3. Tick Export All Outfits if you want more than the outfit being worn.
4. Click Export Model for KKBP. The game freezes while it works.
5. The export is a new folder in `KKBP Exports`, in the game's main folder.

**Import, in Blender:**

1. In the KKBP tab, click Import Export Bundle.
2. Browse to the export's folder, select `manifest.json` and click Import manifest.json.
3. Select the rig and enter Pose Mode to pose the character.

The options of both halves are explained in [Exporting](docs/wiki/exporting.md) and [Importing](docs/wiki/importing.md).

## Documentation

The [wiki](docs/wiki/README.md) explains each feature with pictures.

| Page | What it covers |
|---|---|
| [Installing](docs/wiki/installing.md) | Installing, updating and removing both halves |
| [Exporting](docs/wiki/exporting.md) | The exporter window's options, and exporting a folder of cards |
| [Importing](docs/wiki/importing.md) | Every Import Option, saved defaults, Bulk Import, languages |
| [Shaders and outlines](docs/wiki/shaders.md) | The five shader choices and the outlines |
| [The rig](docs/wiki/rig.md) | The Rigify rig, Rig Layers, joint corrections, Snap IKs |
| [Expressions](docs/wiki/expressions.md) | The emotion grid, gag eyes, tears, face cards |
| [Outfits](docs/wiki/outfits.md) | Outfits, variations, separate clothing, SFW mode |
| [Edit Material](docs/wiki/edit-material.md) | Changing colours and baking them |
| [Export Prep](docs/wiki/export-prep.md) | VRM, VRChat, Unreal, atlases |
| [Animations](docs/wiki/animation.md) | Importing a Koikatsu animation |
| [Hooks](docs/wiki/hooks.md) | Running your own scripts after an import |
| [Game support](docs/wiki/game-support.md) | What works in which game |
| [Troubleshooting](docs/wiki/troubleshooting.md) | The log, common problems, reporting a bug |

## Getting help

When an import goes wrong, the KKBP panel shows a summary with a button that opens the log. Check [Troubleshooting](docs/wiki/troubleshooting.md) first; if that doesn't help, open an issue and attach the log.

## Developers

- [CONTRIBUTING.md](CONTRIBUTING.md): the repository's layout and how to build and test it
- [docs/design/](docs/design/README.md): the design, and the decisions behind it in [docs/adr/](docs/adr/)
- [docs/hook-interface.md](docs/hook-interface.md): the API for writing a Hook

## Credits

The importer's export atlas follows shotariya's [Material Combiner](https://github.com/Grim-es/material-combiner-addon) and Jake Gordon's bin packer, and its Merge Weights follows the [Cats Blender Plugin](https://github.com/michaeldegroot/cats-blender-plugin); all three are MIT-licensed. The edit materials' shadow colours follow xukmi's MIT-licensed recreations of the game's shaders (KKShadersPlus, KKShadersRecreated). None of their code is bundled. The Rigify Hook's joint corrections come mostly from a file by johnbbob_la_petite. Details are in [NOTICE](NOTICE).

KKBP is released under the [MIT licence](LICENSE).
