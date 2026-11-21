# The body takes the shown Outfit's textures, swapped in by the add-on

Each Outfit sets textures on body materials. The one that matters is the alpha mask that hides the skin under that Outfit's clothes: `_AlphaMask` on KK and KKS, `_Cloth_alpha` and `_Cloth_alpha_bot` on SVS (an Outfit Pass's `body_textures`). The importer used to put only the first Outfit's into the body, so with Export All Outfits, showing another Outfit's Collection kept the first Outfit's mask, and skin stayed hidden wherever the first Outfit's clothes had covered it (issue 119).

Now, when a Character has more than one Outfit, every body material an Outfit sets a texture on stores each Outfit's texture for that slot, as the custom property `kkbp_outfit_textures` (an image pointer per Outfit, with its offset and scale). An Outfit that sets nothing in a slot stores the template's own image there. The first Outfit's textures go into the image nodes, as before. Each `Outfit NN` Collection carries its Outfit number (`kkbp_outfit`). While the add-on is enabled, a `depsgraph_update_post` handler (`outfit_textures.py`) looks at which Outfit Collections are visible in the view layer. When that changes and exactly one Outfit is shown, it puts that Outfit's textures into the image nodes of every material that stores them. That includes the body's outline, which the Outlines Hook copies from the body material. Showing several Outfits, or none, leaves the textures as they are.

## Considered Options

- **An image node per Outfit in the body material, picked by a number** read from the body object through an Attribute node, as the gag eyes' expressions are (ADR 0042). It can be keyframed, and it works without the add-on. But each Outfit adds one image to the body's shader on KK and two on SVS. A card with seven Outfits gives the body up to 14 more textures, which makes shader compiles slower and gets close to the number of textures EEVEE can bind in one material.
- **A driver on the body material reading the Collections' visibility**: Blender can't drive from a Collection's eye icon (it is view layer data), and ADR 0042 shows that a material with a driver whose input is animated is re-evaluated on every frame, which costs most of the frame rate.
- **A button in the KKBP panel**: one more thing to remember, when the wiki already says to change clothes by hiding one Collection and showing another.
- **The add-on swaps the image in the existing node (chosen)**: the shader stays as it is, and playback does no extra work. Blender calls the handler after edits, not on frame changes. It only does work when the set of shown Outfits changes.

## Consequences

- Switching Outfits can't be keyframed. The eye icon can't be keyframed either, so an animation that changes clothes was already beyond what the Outfit Collections offer.
- Without the add-on enabled, a file keeps the textures of the Outfit shown last; showing another Outfit doesn't change the body.
- A bundle with one Outfit stores nothing, and its scene is the same as before.
- Export Prep's atlas, and the alpha folding in `atlas/alpha.py`, read the image node, so they use the shown Outfit's mask.
- An Outfit's alternate clothes (`Alts NN`) are meshes of that Outfit's Pass, which has one set of body textures, so they use their Outfit's. Showing an `Alts` Collection changes nothing.
- The body's edit materials (`KK create_body`, `SVS lif_main_skin_body`) have no alpha mask slot, so they don't store the textures. The original material, which keeps them, follows while it is being edited.
- Every Character in a file is followed separately, by its Character Key. The view layer the handler is given decides what counts as shown.
