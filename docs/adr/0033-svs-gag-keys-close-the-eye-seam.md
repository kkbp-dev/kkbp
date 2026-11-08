# SVS gag keys close the eye seam the game leaves open

SVS's face has a separate disc in each eye socket. Its open edge pairs vertex for vertex, with matching UVs, with the open edge of the socket's rim. The game's gag shape (`face.eye_f00_gag`, used by every gag pattern but Fiery Eyes) moves the disc 3.47 mm straight forward, but the disc's edge sits about 0.4 mm sideways of the rim's, so it stops 0.5 to 0.6 mm off the rim: 0.58 mm in the game's unskinned mesh, 0.51 mm skinned, for the Sample Card. The exporter baked exactly that. In Blender the crack shows at an angle, and with the Outlines Hook on it shows from the front as a dark line around each eye (issue 28). So the SVS adapter closes it: in each gag shape key of the face, every open-edge vertex the key moves that ends within 1 mm of an open-edge vertex it doesn't move is put exactly on that vertex (`SeamClosing` in the AdapterKit). A key that leaves any of them farther off is left as the game made it.

The Outlines Hook's modifier on Body pushes the face out by half its thickness along the normals, which pulls the two edges, now at one place but still separate vertices, apart again. So the Hook also gives the modifier no thickness where SVS's face outline mask already hides the outline (the `Outline thickness` vertex group).

## Considered Options

- **Leave the game's geometry and hide the crack in the importer only**: the outline change alone removes the dark line, but the crack still shows at an angle.
- **Weld the disc to the rim**: they are 3 mm apart in the basis and in every other expression, so they can't be one vertex.
- **Close it in the importer**: it would need to know which of the face's open edges pair up, which is SVS knowledge ADR 0002 keeps in the exporter.
- **Close it in the SVS adapter (chosen)**: like the hidden basis of ADR 0010, the exporter changes the game's geometry on purpose, and says so here.

## Consequences

- The face's gag keys are no longer exactly the game's: the disc's edge vertices move up to about 0.7 mm more than the game moves them.
- Fiery Eyes uses another shape (`face.eye_f00_ikari_op`), which also moves the rim and leaves its edge about 2.7 mm off, so it is left alone (issue 15).
- Shape keys added on top of a gag key, such as an Eye expression, can open the seam again; the game doesn't combine them either.
- KK and KKS faces have no such disc and don't call `SeamClosing`, and their outline keeps the whole thickness: the Hook thins only around the masks in `thinning_masks`, which lists SVS's alone. At first it thinned around every Game's mask, which hid KK's face outline, because KK's mask is white where the outline shows, the opposite of SVS's; and even read the right way, thinning moved KK's eyelines, which sit on the face, behind it. SVS's eyelids and eyelashes clear the push because the importer moves them forward (`move_eyelids_forward`).
