# Expressions hide meshes through their materials

An expression's `hides` effect (such as the pupils and eyelines behind gag eyes) is carried out in the materials of the hidden meshes: every shader group in the template library has a `Hidden` input that fades it to transparent, and the material-changes Step drives it from the expressions that hide the mesh. The meshes themselves don't move.

## Considered Options

- **Move the hidden vertices back inside the head in each hiding expression's shape key**, as the legacy importer did: works with any material, but the importer would invent geometry the exporter didn't bake, and every hiding expression would need the right depth.
- **Hide the objects**: Blender can drive object visibility, but the hidden meshes are joined into Body.
- **A `Hidden` template parameter (chosen)**: the effect stays a material change, like the gag-eye textures, and Body stays one object.

## Consequences

- A material used by both a hidden and a visible mesh would hide both; no sample has one, and the Step would hide it only where the bundle says.
- Templates without a `Hidden` input (Transparent, Gag) can't be hidden; nothing hides them.
- Replacement templates brought by a Hook need a `Hidden` input for hiding to keep working.
