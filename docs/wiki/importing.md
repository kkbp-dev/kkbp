# Importing

The importer rebuilds a character in Blender from an export folder.

## Importing a character

1. Press N in the 3D viewport and open the KKBP tab.
2. Set the Import Options, if you want something other than the defaults.
3. Click Import Export Bundle.
4. Browse to the export's folder. The file browser shows only `manifest.json`: select it and click Import manifest.json. (Opening the folder and confirming with no file chosen works too.)

When the import ends, the panel shows a summary. If something went wrong, a button there opens the log.

> **Picture to come:** `images/importing/panel.jpg`, the KKBP tab with Import Options open and the summary of a finished import.

A new file's default cube, camera and light are removed for you. Several characters can be imported into one file.

## Import Options

The options apply to the next import, so set them before clicking the button.

| Option | Default | What it does | More |
|---|---|---|---|
| Fix body seams | on | Merges the face and body vertices that sit on top of each other. It can change the weights around the neck; without it, seams may show around the neck and down the chest when outlines are on | |
| Shader | Eevee | Which shaders the materials use: Eevee, Eevee+, Cycles (toon), Cycles (classic) or Principled BSDF | [Shaders](shaders.md) |
| Separation type | One object per outfit | "Separate all clothing" makes each piece of clothing its own object | [Outfits](outfits.md#separate-all-clothing) |
| Use outlines | on | Gives the body, hair and clothes an outline | [Shaders](shaders.md#outlines) |
| Face cards | on | Adds 2D eye and mouth cards in front of the face, in a hidden collection | [Expressions](expressions.md#face-cards) |
| SFW mode | off | Attempts to cover up some NSFW things | [Outfits](outfits.md#sfw-mode) |
| Use Rigify armature | on | Generates a Rigify control rig for posing and animating in Blender. Off, the character keeps the plain armature, which is easier to export | [The rig](rig.md) |
| Separate eyes | off | Moves the eyes and eyebrows into their own objects, so they can show through the hair with the compositor | [Expressions](expressions.md#separate-eyes) |
| Delete default scene | on | Deletes the startup file's cube, camera and light, if the file holds nothing else but imported characters | |

Your own [Hooks](hooks.md) can add options to this list.

### Which options for what

| You want to | Use |
|---|---|
| Pose and animate in Blender | The defaults |
| Render in Cycles | Shader: Cycles (toon) or Cycles (classic). Outlines are left out for these |
| Send the character to VRM, VRChat or Unreal | Use Rigify armature off, then [Export Prep](export-prep.md) |
| Hide or swap single pieces of clothing | Separation type: Separate all clothing |
| Share the file or show your screen | SFW mode on |

### Saving your defaults

Click Save as Defaults under the options to keep the current settings for every new file. To go back, open KKBP in Preferences > Add-ons and click "Use the built-in defaults".

## Bulk Import

Bulk Import imports every export in a folder while you do something else.

1. In the KKBP tab, open Tools and click Bulk Import.
2. Choose the folder that holds the export folders, for example `KKBP Exports`.

Each export is imported by its own Blender in the background and saved as `<export folder>.blend` beside the export folder. One that fails is saved as `Error - <export folder>.blend`.

Together with the exporter's [folder export](exporting.md#exporting-a-folder-of-cards), this turns a folder of cards into a folder of `.blend` files.

## Languages

The panel follows Blender's interface language (Preferences > Interface > Language). It is translated into Chinese (Simplified), French, German, Indonesian, Japanese, Portuguese, Russian, Spanish and Thai.

## After importing

- [Pose the character](rig.md) and [change its expression](expressions.md)
- [Change outfits](outfits.md)
- [Change a colour](edit-material.md)
- [Put an animation on it](animation.md)
