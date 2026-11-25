# The atlas copy has plain Principled materials

Export prep's atlas copy used to keep each material as a copy of its KK shader material, with the atlases in its image nodes. Blender's FBX exporter then wrote no textures at all: it reads a material's textures through `PrincipledBSDFWrapper`, which sees only a Principled BSDF in the material's own node tree, wired to the output, with Image Texture nodes plugged straight into it (the normal map through a Normal Map node). The KK shader's textures are inside node groups.

So an atlas material is now a new material holding only that: a Principled BSDF with the light atlas as its Base Color and Alpha and the normal atlas as its normal map. The collection's FBX exporter has `embed_textures` on, so the FBX holds both atlases and can be moved without its folder.

The materials of one atlas then differ only in their render method, so each atlas has one material for its dithered materials (`<object> Atlas`) and one for its blended ones (`<object> Atlas Blended`), each with that render method; an object whose atlas is split has a pair per atlas. Its `kkbp_atlas_of` lists the bundle Ids of the materials it stands in for, one a line (`atlas.sources`). The copy has no outlines: its Solidify modifiers and outline material slots are removed before the atlas is made, so the outline materials don't take room in it, and each material is left with one slot.

- The BSDF is matte (Roughness 1, Specular 0): the light atlas is a bake of the game's shading, not a surface colour to be lit again.
- The alpha is plugged in because the atlas has each material's alpha mask folded into it, and without it the eyelines, eyelashes and hair tips are opaque rectangles in Blender. The FBX then names the light atlas as its transparency texture too.
- The dark atlas, and with "Atlas of every texture" the detail, alpha and colour masks, are PNG files in the bundle's `kkbp_cache/atlas/` only. No material shows them, so they aren't loaded into Blender or put in the FBX.
- A material without a normal map gets a flat normal (128, 128, 255) in the normal atlas, where it used to get transparent black, which a Normal Map node reads as a normal pointing backwards.
- With "Atlas without the eyes", each eye gets the same kind of material with its own light texture, named `<material> Simple`, so the FBX holds it too. These aren't merged: each has its own texture.
- A material with no light texture keeps the material it had.

## Considered Options

- **Keep the KK shader and add an unconnected Principled BSDF**: the wrapper only finds a BSDF that is wired to the output, so the copy would have to stop showing the KK shader anyway.
- **The `.Principled` shader variant** (Convert shaders): its BSDF is inside a node group, which the wrapper doesn't look into.
- **Replace the materials without an atlas too**: with "No atlas" export prep works on the Character itself, not a copy, and the Character would lose its shaders. That FBX still has no textures.
- **Plain materials (chosen)**.

## Consequences

- The atlas copy in Blender looks like the light bake under flat lighting: no dark side, no outlines, none of the KK shader's parameters. It is for exporting, and the Character itself is untouched.
- An atlas material has no Material Template, so `templates` functions raise on it. `atlas.shown(material, slot)` gives the image it shows.
- An FBX with an 8192 px light atlas and its normal atlas embedded is as large as the two PNGs together.
