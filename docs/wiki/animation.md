# Animations

Import Animation puts a Koikatsu animation on the character's Rigify rig, with no other add-on.

> **Picture to come:** `images/animation/walk.jpg`, frames of an imported animation.

## What you need

- A character imported with [Use Rigify armature](rig.md) on.
- A Koikatsu animation as an `.fbx` file, with the game's own bone names.

Animations from other sources, such as Mixamo, aren't supported.

## Using it

1. Select any part of the character.
2. In the KKBP tab, open Tools and click Import Animation.
3. Pick the `.fbx` file.

The animation becomes a new action on the rig. The rig's controls are matched to the animation's bones by what each bone is for, so the same animations go onto Koikatsu Sunshine and Summer Vacation Scramble characters; only Koikatsu characters are covered by KKBP's tests so far.

| Option | Default | What it does |
|---|---|---|
| Lengthen arms | on | Makes the arms 5% longer, which looks closer to the game in some poses |

The animation is on the rig's FK controls. To carry on from a frame in IK, click [Snap IKs](rig.md#snap-iks).
