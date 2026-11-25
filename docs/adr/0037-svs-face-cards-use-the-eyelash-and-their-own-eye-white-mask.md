# SVS face cards use the eyelash and an eye white mask of their own

The face cards show the Character's eye textures whole on flat card meshes. Each card's UVs cover the texture as KK lays it out, and the Eyewhite card cuts the eye white out of its texture with `Eye_White_Alpha`, the outline of KK's eye white UV island. On SVS the cards drew two opaque black boxes over the eyes:

- SVS has no `eyeline_upper`, `eyeline_shadow` or `eyeline_lower` materials. Its eye lines are an `eyelash` and an `eyelid`. The Eyeline card's three image nodes stayed empty, and an empty image node draws opaque black.
- SVS's eye white texture is laid out by SVS's eye mesh, so KK's mask cut the wrong shape out of it.

The fix:

- Each card image node lists Material Roles to try in order (`hook_assets.FACE_CARDS.textures`). The upper eyeline falls back to `eyelash`. A node that none of them fills is unlinked, so that layer draws nothing.
- The mask follows the eye white material's template (`eye_white_masks`): `KK Light Dark` keeps `Eye_White_Alpha`, and `SVS Light Dark` gets `SVS Eye_White_Alpha`. This is how the Outlines Hook picks its face mask, so the Hook never checks the Game.
- `SVS Eye_White_Alpha` isn't in the legacy V9 file, the source of every other Hook asset ([ADR 0024](0024-one-asset-file-per-hook-built-by-a-script.md)). `importer/tools/make_svs_eye_white_mask.py` draws it once from an SVS bundle's eye white UVs: the first `eye_white` material, the left eye, the one the Hook puts on the card. The output is committed as `importer/templates-src/SVS Eye_White_Alpha.png`, beside V9, and `build_hook_assets.py` packs it into `face_cards.blend`, as `rework_templates.py` packs `Lut_TimeDay.png`. The game's eye mesh is the same for every SVS Character, so one mask serves them all.

## Considered Options

- **Leave the Eyeline card empty on SVS**: the cards show the eye whites and pupils with no lines at all.
- **Put the eyelid on the Eyeline card too, as the shadow or the lower line**: each layer draws its texture where the game puts it in that texture. SVS's eyelid line sits in the middle of its texture, so it lands across the iris.
- **Remap the card's UVs for SVS**: more work, and the eyelash already sits in a usable place. Not needed.
- **Draw the mask at import time from the Character's own UVs**: it would follow modded eye meshes, but every import would make an image, and the game's own mesh doesn't change.

## Consequences

- SVS face cards show the eye white, the pupils and the eyelash. They have no lower line or shadow, and the eyelash sits where SVS's texture puts it, not where KK's eyeline would.
- The Eyewhite card shows a little less of the texture's bottom than SVS's island covers, so the SVS eye white is cut slightly flat at the bottom.
- If SVS's eye mesh UVs ever change, rerun the tool on a new Golden Sample, then `scripts/build-library.sh` (ADR 0040).
- Any bundle missing a card's roles now gets an empty layer instead of a black one.
