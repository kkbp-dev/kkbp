# Edit materials copy their edit template's texture group

The edit material tool swaps a material for an editable copy of a legacy edit template (KK Body, KK General, KK Hair, …), which rebuilds the game's colouring from the raw textures and the material's colours so they can be changed and baked again. These templates keep their image nodes inside one texture group per template (`.Tex Body`, `.Tex General`, …). Each edit material gets its own copy of that group, as in the legacy importer, so its images can differ from another's. Every other node group stays shared. Saving bakes the edit material into new light and dark textures and puts them into the original Light Dark material, which keeps following [material-template.md](../design/material-template.md).

## Considered Options

- **Restructure the edit templates so their image nodes sit on the material** and feed group inputs, as the rework did for the Light Dark templates: follows the design, but each texture group holds 10 to 20 image nodes wired through positioning and parsing sub-groups, and edit materials are temporary.
- **A copy of the texture group per edit material (chosen)**: the legacy templates work unchanged, at the cost of one group copy for each material being edited.

## Consequences

- The edit templates' Template Descriptions name their image nodes inside the texture group, and `templates` finds them through it.
- An edited material's texture group copy goes when the edit is cancelled, or when it is saved and baked.
- "No group copies per material" ([material-template.md](../design/material-template.md#appending-and-sharing)) holds for every material a Character uses after the import, but not while one is being edited.
