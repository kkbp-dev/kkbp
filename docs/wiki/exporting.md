# Exporting

The exporter saves the character in the game's maker to a folder, which the importer reads.

## Exporting a character

1. Start the game, open the character maker and load the character. What you see in the maker is what is exported, so change the hair or outfit first if you want to.
2. Open the exporter window:
   - Koikatsu and Koikatsu Sunshine: tick "Show KKBP Exporter" in the maker's sidebar.
   - Summer Vacation Scramble: press Ctrl+Tab. Press it again to hide the window.
3. Set the options.
4. Click Export Model for KKBP. The game freezes while it works, for up to a few minutes.

> **Picture to come:** `images/exporting/window.jpg`, the exporter window in the Koikatsu maker.

## Options

All five are off to begin with.

| Option | What it does | When to use it |
|---|---|---|
| Export All Outfits | Exports every outfit on the card. Off, only the outfit being worn is exported | Most of the time |
| Export Variations | Also exports the half-off versions of the clothes, such as an unbuttoned shirt. The export is larger | When you want those states in Blender |
| Freeze Current Pose | Keeps the pose the character is in. Off, the character is exported in a T-pose | Only for a fixed pose. Leave it off to pose or animate in Blender |
| Freeze Shape Keys | Bakes the current facial expression into the mesh | Only for one fixed expression |
| Disable Physics | Exports the hair and skirt in their neutral shape. Off, the exporter waits two seconds for them to settle under gravity | When settled hair or skirts get in the way |

## Exporting a folder of cards

1. Click "Export every card in a folder…". A folder browser opens in the window, starting at the game's `UserData/chara` folder, or at the folder you last exported.
2. Go to the folder and click Export them.

Each `.png` directly in the folder is loaded into the maker in name order and exported with the window's options, one export each. A file that isn't a character card (an outfit card, a plain picture) is skipped. The window shows the progress ("Card 3 of 12"), and Stop after this card ends the batch early. At the end it shows how many exported and how many failed; the BepInEx log names each failure. The last card stays loaded in the maker.

> **Picture to come:** `images/exporting/batch.jpg`, the folder browser with the Export them button.

## What an export holds

Exports go to `KKBP Exports` in the game's main folder. Each is a folder named with the date, the time and the character's name, such as `20261030154424_Haruno Chika`:

| File or folder | Contents |
|---|---|
| `manifest.json` | Identifies the export. This is the file Blender asks for |
| `.glb` files, `outfits/` | The body's meshes, and each outfit's |
| `textures/` | The textures |
| `kkbp_cache/` | Made by the importer, not the exporter: its log and the images it generates. Deleting it is always safe |

To export somewhere else, set "Output folder" in the plugin's BepInEx settings.

Keep the export folder after importing: [Edit Material](edit-material.md) and [Export Prep](export-prep.md) read it again.

## Per game

| | Koikatsu | Koikatsu Sunshine | Summer Vacation Scramble |
|---|---|---|---|
| Opening the window | Sidebar toggle | Sidebar toggle | Ctrl+Tab |
