# Export Prep

Export Prep readies a character for another program: it renames and simplifies the skeleton for the target and packs the textures into an atlas.

> **Picture to come:** `images/export-prep/atlas.jpg`, a character beside its light atlas.

## Before you start

Import the character with **Use Rigify armature off**. Export Prep refuses a character with a Rigify rig. It also needs the character's export folder to still be where it was imported from.

## Using it

1. Select any part of the character.
2. In the KKBP tab, open Tools and click Export Prep.
3. Choose the options and confirm.
4. Export with Blender's own exporters. Export Prep sets up an FBX exporter on the character's collection for you (Collection properties > Exporters), which embeds the textures in the `.fbx`; for VRM, use a VRM add-on.

> **Picture to come:** `images/export-prep/dialog.jpg`, the Export Prep options.

## Options

| Option | Choices |
|---|---|
| Target | VRM, VRChat, Unreal, Koikatsu, No change. Adjusts the skeleton and bone names to suit the target |
| Bones | **Very simple** merges the deform details, the face and the tongue into their parents. **Simple** merges the helper bones only. **No change** keeps every bone |
| Atlas | **Atlas** makes one atlas each for the light, dark and normal textures. **Atlas without the eyes** leaves the eyes their own textures. **Atlas of every texture** includes the detail, alpha and colour masks. **No atlas** leaves the textures as they are |
| Largest atlas | 2048, 4096, 8192 (default) or 16384 px. An object whose atlas would be larger gets several atlases; nothing is scaled down |

With an atlas, the result is a copy of the character in a `<name> atlas` collection, and the original is left as it was. The copy has no outlines, and its materials are plain, matte Principled BSDFs showing the light atlas and the normal atlas, which other programs read: one material per atlas, and a second, `<object> Atlas Blended`, for the materials that blend their transparency.

Every atlas image is saved in the export folder's `kkbp_cache/atlas/`. The dark atlas, and with Atlas of every texture the masks, are only there: no material uses them, so they aren't in the `.fbx`.

## Merge Weights

Merge Weights gives the selected bones' weights to their parents and deletes the bones, for trimming a skeleton by hand. It isn't on the panel: select the bones, press F3 and search for Merge Weights.
