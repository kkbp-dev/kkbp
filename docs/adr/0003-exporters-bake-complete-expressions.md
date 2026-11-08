# Exporters bake complete expressions into shape keys

The exporters write each expression as a finished shape key: one game expression pattern (eyes, mouth or eyebrows) evaluated by the game, plus its closed-eyes or closed-mouth version where the game blends between the two. The game's partial shape keys (`eye_face.f00_def_cl`, `face.kuti_f00_egao_op`, …) are not exported. Expressions the importer builds today that are not game patterns (KK's chewing `mogu` and eating `tabe` keys, SVS's vowel, hate and cartoony-smile mouths) come from a recipe of partial keys in the translation table, and the exporter bakes those too. The tear and gag-eye shape keys are made by the exporter as well. The importer combines nothing.

## Considered Options

- **Export the partial keys and the pattern recipes; the importer combines them**: it keeps the exporter simple, but the combining rules are game knowledge (which keys a mouth pattern skips, which teeth and tongue keys a mouth needs, how `_op` and `_cl` pair up), and that knowledge is exactly what grew today's importer branches.
- **Bake complete expressions in the exporter (chosen)**: the game evaluates its own patterns, so the result matches the game, and the importer only names and loads shape keys.

## Consequences

- An expression includes only the shape keys its own game controller drives, so one Eye, one Mouth and one Eyebrow expression can be mixed in Blender without counting a key twice.
- A closed version is written only when it differs from the open one.
- Bundles carry more morph targets than partial keys would, all on the small face meshes.
- The importer Steps `combine_shapekeys`, `combine_mouth_shapekeys`, `create_gag_and_tear_shapekeys`, `create_svs_tear_shapekeys` and `delete_remaining_partial_shapekeys` have no replacement.
- Adding a missing expression means adding a recipe to `contract/expressions/<game>.json` and releasing the exporter.
