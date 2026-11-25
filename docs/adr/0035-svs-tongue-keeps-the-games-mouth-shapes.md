# The SVS tongue keeps the game's mouth shapes, even where it doesn't follow the mouth

In an imported SVS Character, most mouth expressions move the lips and teeth but leave the tongue where it is. In KK and KKS every mouth pattern moves the tongue by its own amount. This was reported as a capture bug. It isn't: the game does the same.

A probe in SVS's maker (2026-11-08, Sample Card) found:

- The head's tongue, `o_tango`, has 8 blend shapes: `tang.f00_kuwae`, `def_op`, `def_cl`, `pero`, `peroL`, `peroR`, `name` and `sinken_op`. It is weighted to `cf_J_MouthCavity` alone.
- For 18 of the 28 mouth patterns, the mouth controller gives the tongue `tang.f00_def_op`, the Mouth Default shape, while the teeth move up to 1.2 cm. The tongue changes only for the serious, playful, hold-in-mouth, kiss, tongue-out and eating patterns.
- No bone moves with any mouth pattern, so nothing outside the blend shapes moves the tongue either.
- The patterns that move the game's baked tongue (`SkinnedMeshRenderer.BakeMesh`) are the ones whose exported tongue keys differ from Mouth Default, grouped the same way.

The exporter keeps what the game shows. The table's recipes (Mouth A, I, U, E, O, Hate and Cartoony Smile) also give the tongue `tang.f00_def_op`, the shape most of the game's own patterns use, while the teeth of Mouth A, I, U and Hate use `tooth.f00_no_dw_op`, which drops the lower teeth 2.2 cm.

## Considered Options

- **Make the tongue follow the lower teeth**: an importer Step, or the exporter, would add the lower teeth's movement to each mouth key on the tongue, fading from the tip to the root. The tongue would look more like KK's, but it would move in ways the game never does.
- **Keep the game's shapes (chosen)**: the export stays faithful to the game. Nothing changes in the exporter, the importer or the table.

## Consequences

- In Blender, most SVS mouth keys leave the tongue still. That is correct, not a bug.
- With the recipes that drop the lower teeth, a gap can show between the tongue and the lower teeth.
- Mouth A, I, U, E, O and Cartoony Smile have since become the game's own mouth patterns 19 to 23 and 26, not recipes: their lips were identical to the recipes', and their teeth and tongue are now the game's too. Only Mouth Hate is still a recipe.
