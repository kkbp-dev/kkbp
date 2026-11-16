# The importer snaps mirror partners and lifts the upper eyeline

The exporter writes the Body Pass as an exact mirror image across X = 0 (ADRs [0047](0047-the-exporter-makes-vertex-copies-one-and-mirrors-the-body.md) and [0048](0048-the-body-is-skinned-with-mirrored-skin-matrices.md)), but Blender's Select Mirror still found no partner for about 580 KK and 620 KKS Body vertices after an import (issue 106). Two things were in the way:

- **The glTF importer's rounding.** Blender's glTF importer skins every vertex into its bind pose through matrices that are the identity but for float rounding, which leaves mirror partners up to a micrometre apart. Where the face, its lower eyeline and the eye whites lie within a micrometre of each other in Body, that is enough for X Mirror to take a vertex of one for the partner of another.
- **The upper eyeline's shadow.** KK and KKS draw the eyeline's shadow (`eyeline_shadow`) as a second copy of the upper eyeline (`eyeline_upper`), at exactly the same place. X Mirror pairs a place with one vertex, so one of the two copies never has a partner.

So the Core Import has two more Steps:

1. `snap_to_symmetry` (`steps/symmetry.py`), after `weld_copies` and before `build_parts`: in each mesh as it was loaded, each position is paired with the position nearest its mirror image, within 1 µm and when each is the other's nearest, and both become exact mirror images; a position that is its own nearest goes onto X = 0. Then, across the Body Pass's meshes, the positions with no partner in their own mesh are paired the same way (the left and right eyes are separate meshes). Positions, not vertices, so coincident copies move together; shape keys move by as much. Before the join, an eyeline can't be taken for the face it lies on.
2. `move_upper_eyeline_forward` (`steps/mesh.py`), beside SVS's `move_eyelids_forward`: in a mesh with both an `eyeline_upper` and an `eyeline_shadow` material, the vertices the upper eyeline alone uses move 0.1 mm forward (Blender -Y), shape keys too. Every Game runs it; only KK's and KKS's meshes have both roles.

## Results

Select Mirror on the imported Body of each Golden Sample finds a partner for every vertex but KK's 3 and SVS's 2 on the tongue, and on KKS also the 13 on the crotch's middle line the game's mesh has no partner for (ADR 0048), with 2 more.

## Considered Options

- **Skip the glTF importer's skinning into the bind pose**: a glTF import extension can turn it off, and the positions would then be the bundle's to the bit. But it changes how Blender's own importer works, for something the importer can put right after it.
- **Blender's Snap to Symmetry on the joined Body**: it does the same thing after the join, where the face and its eyelines are one mesh, and it took some of their vertices for each other's partners; with the eyeline moved it still left 25 KK and 41 KKS vertices.
- **Move the shadow back instead of the eyeline forward**: either clears them; the eyeline is drawn on top, so it moves towards the camera.

## Consequences

- The upper eyeline sits 0.1 mm in front of its shadow, which doesn't show.
- An import moves vertices by under a micrometre where they had a partner that close; nothing else moves.
