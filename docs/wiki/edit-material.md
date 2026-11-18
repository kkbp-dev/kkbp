# Edit Material

Edit Material lets you change a material's colours, then bakes the result back into fast textures.

> **Picture to come:** `images/edit-material/before-after.jpg`, a character before and after a hair and clothes recolour.

An imported material is a pair of finished textures, light and dark, which is fast but fixed. Edit Material swaps it for a version built from the game's original layers and colours, following the game's own shaders, so the colours can be changed and still look like the game.

Edit Material works in all three games. It needs the character's export folder to still be where it was imported from.

## Changing a colour

1. In Object Mode, select the object and open the Material tab of the Properties editor.
2. Select the material in the list and click Edit Material under it.
3. Change the colours in the material's settings.
4. Click Save. The colours are baked into the material's light and dark textures.

> **Picture to come:** `images/edit-material/buttons.jpg`, the Material tab with Edit Material, then with Reset, Cancel and Save.

| Button | What it does |
|---|---|
| Edit Material | Swaps the material for the editable one |
| Save | Bakes the edited colours into the original material and ends the edit |
| Cancel | Puts the original material back and drops the changes |
| Reset | Starts the edit again from the export |
| Link Hair | Shown on hair: puts every hair material of the object into edit with this one's settings |

## Hair

Hair is usually several materials. Edit one, click Link Hair to copy its light and dark settings to the others, then save.

## What can be edited

| Game | What can be edited |
|---|---|
| Koikatsu, Koikatsu Sunshine | The body, face, hair, eyes, eye whites, eyebrows, eyelines, nose line, teeth, tongue and clothes. For the eyes, the highlight colours and the pupil and highlight positions can be changed too |
| Summer Vacation Scramble | The body, face, hair, eyes, eye whites, eyebrows, eyelashes, nails, teeth, tongue, clothes, socks and accessories |

Tears, gag eyes, face cards and glasses can't be edited in any game, nor Summer Vacation Scramble's eyelids. A material from a modded shader may not be editable.

In Summer Vacation Scramble, saving the face also bakes its version without eyeshadow.

## The Saturate choice

Beside the Edit Material button, Saturate decides whether the colours go through the game's colour grade. Leave it at Default: KKBP then does what matches the game for each material. On and Off are there for materials from modded shaders that come out too pale or too strong.

## Where the files go

The baked textures are saved in the export folder's `kkbp_cache/` and packed into the `.blend`.

## Per game

| | Koikatsu | Koikatsu Sunshine | Summer Vacation Scramble |
|---|---|---|---|
| Edit Material | Yes | Yes. Clothes, teeth, tongue and skin are close but approximated | Yes, except the eyelids |
