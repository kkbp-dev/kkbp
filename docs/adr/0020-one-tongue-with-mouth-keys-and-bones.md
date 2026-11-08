# One tongue carries the mouth keys and the tongue bones

The games have two copies of one tongue mesh: the head's, which the mouth expressions move, and the body's rigged one, weighted to the bones under the `tongue_root` Bone Role and normally hidden. The exporters capture both. The importer's `merge_rigged_tongue` Step keeps one: the head tongue takes the rigged tongue's weights by vertex index (the two have the same vertices in the same order), the tongue bones move by the mean offset between the two copies so they bend the head tongue from the right place, and the rigged copy is deleted. The result is the visible `tongue` Part, parented to Body, with its mouth keys driven from Body's.

## Considered Options

- **Two tongues, as the legacy importer had**: the head tongue inside Body and a hidden rigged copy for Rigify. Nothing to merge, but users see one tongue and pose another, and the rigged one doesn't follow the mouth expressions.
- **No rigged tongue**: the simplest import, but the Rigify Hook would lose its tongue controls.
- **One tongue (chosen)**: a Blender mesh applies shape keys before its armature, so the mouth expressions and the tongue bones work together on one mesh.

## Consequences

- The tongue bones' rest positions are the head tongue's, not the game's rigged tongue's (about 1.5 cm apart in KK, 1.5 cm in SVS).
- The rigged tongue's weights replace the head tongue's `cf_J_MouthCavity` weights, so the tongue follows the tongue bones rather than the mouth cavity bone.
- If the two copies don't match vertex for vertex, the head tongue is kept as it is and the rigged one is left out, with a warning.
- Body no longer holds a tongue, and the tongue Part is visible; the baseline comparison lists both.
