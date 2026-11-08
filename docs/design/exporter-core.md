# Exporter Core

How the exporters are structured: one shared Exporter Core and one Game Adapter per game. It replaces the forked `PmxBuilder.cs` files (2,882 lines in KK, 2,396 in SVS) and the duplicated PmxLib. Terms are defined in [CONTEXT.md](../../CONTEXT.md).

Status: agreed design, not yet implemented.

## Split

- **Exporter Core**, shared by every exporter:
  - the Export Bundle writer: folder layout, Manifest written last, Ids, glTF and JSON, texture file names ([export-bundle.md](export-bundle.md));
  - running the Passes in order;
  - plain C# model types (mesh, material, bone, expression, …);
  - material sections: shader data an adapter attaches to a material for its Game Extension, such as KK's create material. The Core writes a section like the material's own shader data, under the extension key and field name the adapter gives (`kk`, `create`), with its textures numbered right after the material's own;
  - the list of export options, which is the same list the Manifest records.
- **Game Adapter**, one per game. It does everything that touches the game: reading the Character, switching Outfits, capturing meshes into plain arrays, baking textures, and assigning Bone Roles, Bone Groups, Material Roles, Blend Modes and Expression Names.

## Sharing across runtimes

- The Core is a shared source project (`.shproj`/`.projitems`) compiled into each plugin: KK (.NET 3.5), KKS (.NET 4.6), SVS (.NET 6 IL2CPP).
- The Core uses only base-library APIs that exist in .NET 3.5: no `Task`, no `Span`, no `System.Text.Json`. CI builds the Core on its own for `net35` to enforce this.
- The Core references no UnityEngine. It has its own small `Vec3`/`Quat`/`Color` structs and takes arrays.
- Adapters convert Unity and IL2CPP types at the seam. IL2CPP wrapper types never leave the SVS adapter.
- The Core converts from Unity's coordinate space to glTF's, in exactly one place.

## Passes

- `adapter.Passes()` returns the Body Pass and one Pass per Outfit.
- The Core runs them in order as a Unity coroutine (`IEnumerator`), because switching Outfits needs game frames in between.
- For each Pass, the Core calls `adapter.Capture(pass)`, which can yield while it waits.
- There is no static state, and no "which pass is this" check such as `nowCoordinate == maxCoord`.
- The Core steps the adapter's enumerators itself and passes on each yielded value, so Unity is never handed a nested coroutine. This matters for SVS's IL2CPP coroutine wrapper.
- Each Pass's bones form one tree. A bone that appears in several Passes has the same key, parent and rest pose in each.

## Textures

- The adapter renders and bakes textures, including the light/dark Texture Variants, because that needs the game's shaders.
- It passes the Core PNG bytes, each with its Texture Role, Raw Property and Texture Variant.
- The Core names and writes the files. It never decodes an image.

## Games

- **KK and KKS:** one adapter project with two build configurations (NET35 for KK, NET46 for KKS). All KKS differences are in one file under `#if KKS`.
- **SVS:** its own adapter.
- **AC:** out of scope for now.

## What the adapters capture

Agreed at the start of Phase 2. Each point applies to both adapters unless it names a Game.

- **Passes.** The Body Pass holds the body and head meshes: body, face, eyes, eyebrows, eyelines, nose, teeth, tongue, tears and gag eyes. Each adapter also captures the body's rigged tongue, even when its object is inactive: in KK and KKS `n_tang/o_tang` (`ChaReference.S_TongueB`), which the game shows in place of the head's tongue only at tongue state 1, and in SVS `n_body/o_tang` (`HumanBody.rendTongueBody`; the head's is `o_tango`). It is weighted to the `cf_j_tang_*` chain, has Material Role `tongue`, and has no expressions and no light and dark bake. Its vertices are the head tongue's in the same order, so the importer can copy its weights onto the head tongue and drop it. Each Outfit Pass holds that Outfit's clothes, hair and accessories, as the legacy `Outfit NN` folders did.
- **Meshes.** One mesh per enabled renderer whose GameObject is active; one primitive per material slot. Extra materials beyond the submesh count re-render the last submesh, as in Unity. Mosaic and male-part stand-ins (`o_mnpa`, `o_dankon`, …), the ChaAlphaMask plugin's `o_Mask` quad in KK and KKS, SVS's hair outline shells (`hair_*_line`, shader `LIF/lif_main_hair_outline`) and hit meshes are never captured. `alternate` meshes, those shown only in a non-default clothing state, are captured only with `all_variations`. Normals and tangents are written at unit length, as glTF requires; one the game gives zero-length or not finite, as some clothes and accessories do, takes the average of the good ones of the vertices it shares a triangle with, or failing that any direction that fits (a tangent perpendicular to the normal).
- **Bones.** Every active transform under the body bone root, except hit transforms (`cf_hit_*`, `cf_d_hit_*`); a transform under a skipped one is re-parented to the nearest exported ancestor. Every Pass carries the whole body skeleton plus its own Outfit-owned bones.
- **Keys.** Body bones by transform path from the Character's root; meshes, materials and Outfit-owned bones with the Pass in front ([ADR 0009](../adr/0009-outfit-owned-objects-keyed-per-pass.md)). Walks are depth-first by child index, materials in slot order.
- **One body pose for every Pass.** The adapter records the body skeleton's pose once, at the start of the Body Pass, and skins every Pass's meshes against that record itself. Physics moving bones between Passes, or the game replacing body transforms when the Outfit changes, can't give a bone two rest poses. Later Passes find body bones again by key.
- **Rest pose.** The capture pose: the game's T-pose, or the frozen current pose with `current_pose`. KK and KKS find the T-pose by name in the maker's pose list. SVS's maker has none, so the adapter loads one of the game's craft-mode animator controllers and plays its `tpose_M` clip in place of the current one; the clip is humanoid, so it fits any body. The export fails if no T-pose is found. Bones carry world position and rotation without scale ([ADR 0008](../adr/0008-bone-rest-poses-carry-no-scale.md)).
- **Hit objects.** Released before capture. A collider on a hit transform moves to the nearest exported ancestor, its center re-expressed in that bone's space.
- **Bone Roles.** From the game's Humanoid Avatar (`Animator.GetBoneTransform`) where the body has one, otherwise from a name table in the adapter; the KKBP extras always come from the table.
- **Bone Groups.** Body bones by name rules, first match wins: `skirt` (`cf_j_sk_*`, `cf_d_sk_*`), `breast` (`bust`, `bnip`), `nsfw` (Better Penetration's `cf_J_Vagina_*`, `cf_j_kokan`, `cf_j_ana` and their `cf_d_`/`cf_s_` forms, the male-part `dan` bones), then under the face root `eye` (`cf_J_Eye*`, `cf_J_hitomi_tx*`, eye-look targets), `eyebrow` (`cf_J_Mayu*`), `mouth` (`cf_J_Mouth*`, `cf_j_tang_*`) and `face` for the rest, then `deform` (`cf_j_`, `cf_s_`, `cf_d_`) and `helper`. Bones of hair, clothes and accessories are `hair` or `accessory`, or `helper` when nothing weights them ([ADR 0011](../adr/0011-unweighted-outfit-bones-are-helpers.md)). Whichever rule made a bone a `helper`, the Core makes it `face` or `deform` when a mesh of any Pass weights it or a bone below it, or physics uses one, so every helper is safe to delete ([ADR 0029](../adr/0029-the-core-keeps-helpers-safe-to-delete.md)).
- **Material Roles.** From the renderer fields `ChaControl` exposes (body, face, eye, tooth, tear and gag-eye renderers, the hair objects), with names only where the game exposes no field. SVS draws each eye white and pupil with one material, so the SVS adapter gives each eye a copy, 1 mm behind it, as its `eye_white` mesh and bakes the white on the copy and the pupil on the eye ([ADR 0034](../adr/0034-svs-eye-whites-are-copies-of-the-eyes.md)).
- **Blend Modes.** A per-game table of shader names (`glasses`, `alpha`), then the render queue: 2450–2999 or alpha clipping is `cutout`, 3000 and above `alpha`, the rest `opaque`.
- **Expressions.** For each pattern in the game's eye, eyebrow and mouth lists, the adapter sets the pattern without blending, runs only that controller's blend-shape calculation, and sums the weighted frame deltas of the blend shapes that controller drives, converted into the rest pose. Eyes and eyebrows are baked fully open; mouths at open rate 1, and their closed version at 0 when the table names one and it differs. Recipes bake full-weight game keys. Meshes no controller drives keep their own blend shapes as category `other`. Tear and gag-eye meshes get their showing keys ([ADR 0010](../adr/0010-tear-and-gag-meshes-rest-inside-the-head.md)).
- **Textures.** Every texture slot the material holds at capture, by Raw Property, plus the baked `light` and `dark` variants made by rendering the material with the game's shader. Normal maps are unpacked from Unity's format first. Textures that depend on the Outfit but sit on a body material, such as the body alpha masks, are written by each Outfit Pass, not the Body Pass.
- **Create materials (KK, KKS).** The game colours the body, face, eyes and most clothes by compositing their main texture in a separate create material ([contract-change-create-materials.md](contract-change-create-materials.md)). The adapter captures each one with the same property walk as a material's, plus `CustomTextureCreate.texMain`, the uncoloured base, as `_MainTex` with role `main` and the create material's `_MainTex` placement, in place of the create material's own `_MainTex`. It becomes the material section `kk.create` on the first material slot of each captured renderer the game gives that texture:
  - Body Pass: `customTexCtrlBody` on the body, `customTexCtrlFace` on the face, `ctCreateEyeW` on both eye whites, `ctCreateEyeL` and `ctCreateEyeR` on `rendEye[0]` and `[1]`.
  - Outfit Passes, for the clothes worn there: `ctCreateClothes[kind, i]` and `ctCreateClothesSub[kind, i]` as the game's `ChangeCustomClothes` gives them out, `i` = 0 to `rendNormal01`, `rendAlpha01` and `rendAccessory`, 1 to `rendNormal02`, 2 to `rendNormal03`.
  A create whose renderers weren't captured is left out. KK's create shaders are in `shader-properties.json` from KK's own `chara/mm_base.unity3d`, dumped through KKS with `dump_bundles`.
- **Physics.** SVS moves hair, clothes and breasts with MagicaCloth, which `physics.json` doesn't hold, so SVS bundles carry colliders only, as legacy SVS bundles did. MagicaCloth stays out of the contract until a Step or Hook reads physics; adding it then is a minor Schema Version change. In KK and KKS, `DynamicBone`, `DynamicBone_Ver01` and `DynamicBone_Ver02` all become chains, with distribution curves and `Ver02`'s active pattern applied per bone. With `physics` the bones settle for two seconds before capture; without it they are reset. `physics.json` is always written.
- **Card.** The Character's card as the game saves it, `card.png`.

Unity-free helpers that both adapters need (normal-map unpacking on RGBA buffers, morph delta sums, the hidden tear and gag basis, the helper-bone rule) live in the Core's `AdapterKit` folder, so the fake adapter's tests cover them.

## Building

- Adapters reference the game, Unity and BepInEx assemblies from a local install ([ADR 0007](../adr/0007-game-assemblies-from-local-install.md)).
- `scripts/build-exporters.sh` builds KK (`NET35`), KKS (`NET46`) and SVS (`net6.0`). `scripts/deploy-exporter.sh <game>` copies a build into that game's `BepInEx/plugins/KKBP/`.
- `scripts/export-sample.sh [game]` makes the Golden Samples from the Sample Cards through the auto-export request ([ADR 0012](../adr/0012-file-triggered-auto-export.md)).

## Export options

- The "Export hit boxes" option is removed. Exporters always release the game's hit objects before capturing, so hit box meshes and bones never reach a bundle.
- As a result, the importer has no hit box Step (today's KK-only `separate_hitboxes`), no `hitbox` Part Role and no `hitbox` Bone Group.

## In-game UI

- Each adapter has a thin IMGUI window and BepInEx config. They can't be shared, because BepInEx 5 (KK) and 6 (SVS) differ.

## Failure

- If any Pass fails, the export stops and no Manifest is written, so the importer reports the bundle as an unfinished export.
- The Core also fails the export when the captured data breaks the contract (see [exporters/README.md](../../exporters/README.md)), rather than writing a bundle the importer would reject.
- The error appears in the game window and in the BepInEx log.

## Testing

- A fake adapter builds an in-memory Character, run with `dotnet test`.
- Its output is checked against the JSON Schemas and with the Khronos glTF Validator.
- The test project targets current .NET. The Core itself also builds for `net35`.
- With the KK and SVS adapters plus the fake, the seam has three adapters.
