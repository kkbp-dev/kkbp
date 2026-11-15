# Expressions

Every eye and mouth expression of the game comes into Blender as a shape key with an English name, and the rig has a grid of controls for them.

> **Picture to come:** `images/expressions/grid.jpg`, a few expressions made with the emotion grid.

## Shape keys

The body's shape keys are named by what they do, with their category first: `Eye Closed`, `Eye Happy`, `Mouth Big A`. They are the game's complete expressions, so one key at full gives the expression as the game shows it. The names are the same in all three games.

## The emotion grid

With the [Rigify rig](rig.md), the face has controls for the mouth, the eyes and custom keys. Show them with the Emotions row of Rig Layers, then drag a control to blend between expressions.

> **Picture to come:** `images/expressions/controls.jpg`, the emotion grid's controls beside the face.

## Gag eyes

The game's gag eyes (spirals, hearts, fiery eyes and so on) are one shape key, `Gag eyes`, and a dropdown:

1. Select the gag eyes object and open its first material.
2. Pick the expression in the `Gag expression` dropdown.
3. Raise the `Gag eyes` shape key on the body.

To change the gag expression during an animation, keyframe the `Number` value beside the dropdown.

> **Picture to come:** `images/expressions/gag-eyes.jpg`, three gag expressions and the dropdown.

The gag eyes and the tears are hidden until an expression shows them, and the normal eyes hide while the gag eyes show.

## Face cards

Face cards (on by default) adds flat 2D eye and mouth cards in front of the face, with the character's eye textures, for a drawn look. They are in a collection that starts hidden: show it in the Outliner to use them.

> **Picture to come:** `images/expressions/face-cards.jpg`, the face cards in use.

## Separate eyes

Separate eyes (off by default) moves the eyes and eyebrows out of the body into their own objects, in an `Eyes and Eyebrows` collection. Their shape keys follow the body's. Use it to draw the eyes and eyebrows over the hair with the compositor.

To do this on a character already imported, use Run Hook in the Tools panel and pick Separate Eyes.

## Per game

| | Koikatsu | Koikatsu Sunshine | Summer Vacation Scramble |
|---|---|---|---|
| Expression shape keys, emotion grid | Yes | Yes | Yes |
| Tongue during mouth expressions | Moves with the mouth | Moves with the mouth | Stays still in most, as in the game |
