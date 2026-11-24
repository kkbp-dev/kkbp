# Troubleshooting

## The log

Each import writes a log to `kkbp_cache/log/log.txt` in the export folder, replacing the last one. After an import, the summary in the KKBP panel has an Open KKBP Log button. Attach this file when you report a problem.

The exporter writes to the game's BepInEx log (`BepInEx/LogOutput.log`, or `output_log.txt` in the game's main folder for Koikatsu Sunshine).

## In the game

| Problem | What to do |
|---|---|
| There is no "Show KKBP Exporter" toggle, or Ctrl+Tab does nothing | Check that `BepInEx/plugins/KKBP/` exists in the game's main folder and holds a `.dll`: the `BepInEx` folder from the zip must be merged into the game's own, not placed inside it. Check that BepInEx itself works (HF Patch installs it). You must be in the character maker |
| The game freezes after clicking Export | That is normal while it exports, for up to a few minutes with all outfits |
| A card was skipped in a folder export | It isn't a character card (an outfit card or a plain picture), or it is a card for another game. The BepInEx log names it |
| The exporter says the export failed | Look in the BepInEx log for the reason and report it with the card if you can |

## In Blender

| Problem | What to do |
|---|---|
| The zip won't install | Blender must be 5.2 or newer. Install the zip itself with Install from Disk; don't unzip it |
| "Pillow is required. Install it with the buttons below." | Click Download Pillow in the KKBP tab. It needs an internet connection; without one, use Install Pillow from local file |
| The panel asks for Pillow again after an update | Click Download Pillow again |
| The file browser shows no files | It shows only `manifest.json`. Open the export's own folder, the one named with the date and the character |
| The import is refused | The export is incomplete (no `manifest.json` means the export didn't finish), or it was made by a newer exporter than the importer supports. The message says which |
| Export Prep says the character has a Rigify rig | Import the character again with Use Rigify armature off |
| There is no Edit Material button | It shows in Object Mode, in the Material tab, for an imported character's material. Tears, gag eyes, face cards, glasses and Summer Vacation Scramble's eyelids have none |
| Edit Material or Export Prep can't find the export | They read the export folder again: put it back where it was imported from |
| There are no outlines | Outlines are left out for the Cycles and Principled shaders |
| A seam shows around the neck or down the chest | Report it with the card: every import welds the face and body together, so a seam is a bug |
| The face controls or other rig controls aren't showing | Show them in Rig Layers, in the sidebar's Item tab; the face controls are the Emotions and Eyes rows |
| Colours look washed out or too strong | Set the scene's View Transform to Standard (the import does this for you) |

Deleting an export's `kkbp_cache/` folder is always safe; the importer makes it again.

## Reporting a bug

Open an issue with:

- the game and its version, the Blender version and the KKBP version
- what you did and what happened
- the log (`kkbp_cache/log/log.txt`), and for exporter problems the BepInEx log
- the card, if you are able to share it
