# KKBP design

The architecture of the KKBP exporters and importer. Terms are defined in [CONTEXT.md](../../CONTEXT.md). Decisions that would be surprising without context are in [docs/adr/](../adr/).

Released as importer 10.0.0 and exporters 6.0.0 (git tag `v10.0.0`). Supported Games: KK, KKS and SVS.

## Designs

| Area | Doc | What it covers |
|---|---|---|
| Export Bundle (the contract) | [export-bundle.md](export-bundle.md) | The bundle's files, Ids, Roles, Passes and Schema Version |
| Exporter Core and Game Adapters | [exporter-core.md](exporter-core.md) | The shared writer and what each Game's adapter captures |
| Import pipeline and Hooks | [import-pipeline.md](import-pipeline.md) | Steps, Hooks, Import Options, failures, UI languages |
| Character | [character.md](character.md) | How code finds an imported Character and its Parts |
| Game Profile | [game-profile.md](game-profile.md) | Where the differences between Games live |
| Material Template | [material-template.md](material-template.md) | Templates, their descriptions and Template Sets |
| The library and the edit templates | [library-from-code.md](library-from-code.md) | How the library is built from code, and how the edit templates follow the games' shaders |
| Joint corrections | [joint-corrections.md](joint-corrections.md) | The games' correction rules, rebuilt as bones and drivers |
| Blender compatibility and testing | [blender-compat-and-testing.md](blender-compat-and-testing.md) | Version checks, Pillow, the test harness |
| Built-in Hooks and tools | [hooks-and-tools.md](hooks-and-tools.md) | Each built-in Hook and tool, and the bones found by name |
| Create materials in the bundle | [contract-change-create-materials.md](contract-change-create-materials.md) | The `create` section of a material, which the edit materials read |

The public Hook API is documented in [../hook-interface.md](../hook-interface.md).

ADRs:

- [0001 Meshes are exported as glTF, not PMX](../adr/0001-gltf-instead-of-pmx.md)
- [0002 Exporters write down what game data means](../adr/0002-exporters-write-game-meaning.md)
- [0003 Exporters bake complete expressions into shape keys](../adr/0003-exporters-bake-complete-expressions.md)
- [0004 Expression Names are display names, matched by pattern position](../adr/0004-expression-names-are-display-names.md)
- [0005 Ids are assigned per kind, from keys the adapter supplies](../adr/0005-ids-per-kind-from-adapter-keys.md)
- [0006 Every mesh is skinned and sits at the glTF scene root](../adr/0006-every-mesh-skinned-at-scene-root.md)
- [0007 Adapters build against the local game install](../adr/0007-game-assemblies-from-local-install.md)
- [0008 Bone rest poses carry no scale](../adr/0008-bone-rest-poses-carry-no-scale.md)
- [0009 Outfit-owned objects are keyed per Pass](../adr/0009-outfit-owned-objects-keyed-per-pass.md)
- [0010 Tear and gag-eye meshes rest hidden inside the head](../adr/0010-tear-and-gag-meshes-rest-inside-the-head.md)
- [0011 Unweighted hair and accessory bones are helpers](../adr/0011-unweighted-outfit-bones-are-helpers.md)
- [0012 Exporters run an export when a request file appears](../adr/0012-file-triggered-auto-export.md)
- [0013 The importer checks bundles in its own code, not with the JSON Schemas](../adr/0013-bundle-checks-without-json-schema.md)
- [0014 Unknown set values are errors in a known minor version and warnings in a newer one](../adr/0014-unknown-set-values-in-newer-minor-versions.md)
- [0015 The importer's tests run on Blender's own Python](../adr/0015-tests-run-on-blenders-python.md)
- [0016 `import_bundle` returns a failed import instead of raising](../adr/0016-import-bundle-returns-step-failures.md)
- [0017 Bone tails and roll come from the game's rotation, except for bones the rules make upright](../adr/0017-bone-tails-from-the-game-rotation.md)
- [0018 The template library is built by a script from the unchanged legacy file](../adr/0018-template-library-built-by-a-script.md) (superseded by 0040)
- [0019 One Gag template for every Game, built per material from the bundle](../adr/0019-one-gag-template-built-per-material.md)
- [0020 One tongue carries the mouth keys and the tongue bones](../adr/0020-one-tongue-with-mouth-keys-and-bones.md)
- [0021 Expressions hide meshes through their materials](../adr/0021-expressions-hide-meshes-through-their-materials.md)
- [0022 The KK-only Rigify extras run when the skeleton has the joint-correction bones](../adr/0022-kk-rigify-extras-gated-on-their-bones.md)
- [0023 The Rigify Hook ports the legacy scripts and keeps their bone names](../adr/0023-rigify-keeps-the-legacy-scripts-and-names.md)
- [0024 Each Hook's assets are one file built by a script, the mouth atlas as WebP](../adr/0024-one-asset-file-per-hook-built-by-a-script.md)
- [0025 Edit materials copy their edit template's texture group](../adr/0025-edit-materials-copy-their-texture-group.md)
- [0026 Edit materials don't saturate by default, except hair and eyebrows](../adr/0026-edit-materials-dont-saturate-by-default.md)
- [0027 The Rigify Hook stands the lowest visible vertex on the floor](../adr/0027-rigify-stands-the-lowest-vertex-on-the-floor.md)
- [0028 SVS's eye bones are its eye movers, cf_J_Eye_tx](../adr/0028-svs-eye-bones-are-the-eye-movers.md)
- [0029 The Core keeps every helper safe to delete](../adr/0029-the-core-keeps-helpers-safe-to-delete.md)
- [0030 The Cache folder is visible, kkbp_cache](../adr/0030-the-cache-folder-is-visible.md)
- [0031 Golden Samples are made locally, from tracked Sample Cards](../adr/0031-golden-samples-are-made-locally.md)
- [0032 The legacy baseline is retired](../adr/0032-the-legacy-baseline-is-retired.md)
- [0033 SVS gag keys close the eye seam the game leaves open](../adr/0033-svs-gag-keys-close-the-eye-seam.md)
- [0034 SVS eye whites are copies of the eyes, resting 1 mm behind them](../adr/0034-svs-eye-whites-are-copies-of-the-eyes.md)
- [0035 The SVS tongue keeps the game's mouth shapes, even where it doesn't follow the mouth](../adr/0035-svs-tongue-keeps-the-games-mouth-shapes.md)
- [0036 Light and dark bakes render through a full viewport, without supersampling](../adr/0036-bakes-render-through-a-full-viewport.md)
- [0037 SVS face cards use the eyelash and an eye white mask of their own](../adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)
- [0038 Joint corrections copy the games' own rules, as Studio applies them](../adr/0038-joint-corrections-copy-the-games-rules.md)
- [0039 The tongue is part of Body](../adr/0039-the-tongue-is-part-of-body.md)
- [0040 The library and the Hook asset files are built from code, not from the legacy file](../adr/0040-the-library-is-built-from-code.md)
- [0041 Edit templates follow the games' own shaders, and grade their light and dark as the maker camera does](../adr/0041-edit-templates-follow-the-games-shaders.md)
- [0042 One Gag eyes key, with a dropdown that picks the gag expression](../adr/0042-one-gag-eyes-key-with-a-dropdown.md)
- [0043 The Rigify Hook is rewritten in the importer's style, and a rig fingerprint shows the rig is unchanged](../adr/0043-rigify-rewritten-and-checked-by-a-rig-fingerprint.md)
- [0044 Bakes have their main texture's size and shape; the body and face stay 4096 square](../adr/0044-bakes-keep-the-main-textures-shape-and-skin-stays-4096.md)
- [0045 The Rigify Hook aims the hands and makes palms on every skeleton](../adr/0045-every-skeleton-gets-aimed-hands-and-palms.md)
- [0046 The face is also baked without its eyeshadow](../adr/0046-the-face-is-also-baked-without-its-eyeshadow.md)

## Decisions

The agreed decisions, numbered in the order they were made. Code comments, ADRs and the other design docs cite them by number, so a number is never reused. Each one says what holds now; a decision that no longer applies says what replaced it.

### The Core Import

- **D1** The Step list is in `pipeline/steps.py`, in running order: load the Passes, join the armatures, name UV maps, merge the tongues, build the Parts, the tear controls, the one Gag eyes key (D68), order material slots and shape keys, link and drive the face keys, SVS's eyelids, trim the skeleton, bone tails and roll, IK bends, KK/KKS's fingers and legs, bone collections, joint corrections (D64), templates, the Outfit's body textures, the gag eyes' drivers, material changes, viewport colours, Collections, view transform.
- **D2** Bone tails and roll come from Bone Roles and Groups only, with no bone names in the profiles ([ADR 0017](../adr/0017-bone-tails-from-the-game-rotation.md)). The Rigify Hook re-aims the bones its own rig needs.
- **D3** One Gag template for every Game ([ADR 0019](../adr/0019-one-gag-template-built-per-material.md)).
- **D4** One tongue ([ADR 0020](../adr/0020-one-tongue-with-mouth-keys-and-bones.md)), part of Body (D65).
- **D5** An expression hides a mesh through a `Hidden` template input ([ADR 0021](../adr/0021-expressions-hide-meshes-through-their-materials.md)).
- **D6** The Template Sets pick a template by (Material Role, Blend Mode) and set parameters and render methods; a material without its baked texture gets Transparent.
- **D7** Bone collections come from Bone Roles and Groups, never from bone names.
- **D8** Steps get `ctx.profile`; Hooks don't. `import_bundle` refuses a Game without a profile before building anything.
- **D9** Objects get display names (`Body <name>`, `Outfit 00 <name>`); materials and bones are named by Id; every armature modifier is "Armature modifier".
- **D10** Images are packed; the view transform is set to Standard; each alternate clothing mesh is its own hidden Part. The Core Import never deletes the default scene; a Hook does (D47).
- **D11** The template library is built by a script, never edited by hand; it is built from code (D66, [ADR 0040](../adr/0040-the-library-is-built-from-code.md)).
- **D12** `templates.swap` changes a material's shader variant in place; the Convert shaders Hook uses it.
- **D13** The harness imports the Golden Samples on every build (`run.py core`) and compares each scene with its committed snapshot (D50).

### Hooks and tools

[hooks-and-tools.md](hooks-and-tools.md) describes each Hook and tool.

- **D14** `BUILTIN_HOOKS`: Fix body seams → Convert shaders → Separate meshes → Outlines → Face cards → SFW → Rigify → Separate Eyes → Delete default scene. Switches and defaults: `fix_seams` on; `convert_shaders` (`off`, `eevee_mod`, `cycles`, `cycles_classic`, `principled`) off; `separation_type` (`off` "One object per outfit", `by_material` "Separate all clothing") off; `use_outlines` on; `use_face_cards` on; `sfw_mode` off; `use_rigify` on; `separate_eyes` off; `delete_default_scene` on. Built-ins pass their switch to `kkbp.hook`. Outlines skips itself for the Cycles and Principled variants.
- **D15** The Hooks live in `importer/kkbp/builtin/`. Each asset file has a description with no `bpy`, checked against the file by a harness test, and is built from code by `scripts/build-library.sh` (D66): `rigify.blend` (widgets), `face_cards.blend` (its mouth atlas stored as WebP at quality 95), `outlines.blend`.
- **D16** Fix body seams merges by distance with bmesh on Body faces of Material Roles `face` and `body`: as Merge by Distance at 0.00001 with Centroid Merge, keeping each face corner's custom normal. A face vertex and a body vertex also merge from up to 0.0001 apart, because SVS writes most of the neck's pairs 0.010 to 0.026 mm apart (issue 85).
- **D17** Separate meshes splits each `outfit` Part into one Part per material, named by material Id, through a Compat helper.
- **D18** Convert shaders goes through `templates.swap`, with rules by Material Role; the Eevee Mod inputs are per-variant template params; Principled is a `.Principled` variant group. SVS Light Dark gets the KK variants, with a warning that its bottom alpha mask is lost.
- **D19** Outlines: a Solidify modifier and black copies of the materials, found through templates; the face outline mask is chosen by the face material's template. There is no `outline` Part Role.
- **D20** Face cards take their images from Material Roles; the card meshes and card rig have Part Role `face_card`.
- **D21** SFW deletes the vertices and bones of Bone Group `nsfw` and, by exact name, the KK nipple bones, whether or not Rigify is on. With both on, the rig has no crotch, anus or nipple controls.
- **D22** Rigify: the armature becomes the hidden metarig (still `ch.armature`), the generated rig is Part Role `rig`, Rigify is enabled for the session only (preferences are never saved), and each Character gets its own widgets.
- **D23** Rigify renames the Role bones to readable names (`Left arm`, `Hips`) from a Bone Role table before generating, so the rig's controls have readable names and Import Animation can map onto them ([ADR 0023](../adr/0023-rigify-keeps-the-legacy-scripts-and-names.md)).
- **D24** The parts of the rig only KK and KKS skeletons have (the edits to the joint-correction bones, finger rolls, nipple widgets) run when the skeleton has every joint-correction bone they name ([ADR 0022](../adr/0022-kk-rigify-extras-gated-on-their-bones.md)). The wrists are aimed and the palms made on every skeleton ([ADR 0045](../adr/0045-every-skeleton-gets-aimed-hands-and-palms.md)).
- **D25** Rigify re-aims the joint-correction bones upright (ADR 0017), builds the eye controller and the Left and Right Eye vertex groups from Bone and Material Roles, rigs the single tongue on Body (ADR 0020, D65), and builds the emotion grid from the Expression Names present.
- **D26** Tools go through Character, `ch.bundle()` and templates, and write into the Cache. Export prep refuses a Character with a rig.
- **D27** The edit templates are in `library.blend` with descriptions and "edit" rows chosen by Material Role; the profile's `EDIT` tables map colours; the dark-texture code has no `bpy`. Bake renders with Eevee through an orthographic camera.
- **D28** Export prep: one module per target (VRM, VRChat, Unreal, Koikatsu, no change), built by Bone Role; simplification by Bone Group; the atlas's layout and Pillow compositing have no `bpy` and are tested with pytest (Pillow pinned in the dev venv). Merge Weights works on the data API. The user picks the largest atlas (2048, 4096, 8192 by default, or 16384 px): an object whose atlas would be over it gets several atlases, each material going in the first it fits in, and nothing is scaled down, so a material over the limit on its own keeps an atlas of its own size (issue 12).
- **D29** `join_armatures` tags each bone added from an Outfit Pass with its Outfit, so Rigify can put later Outfits' hair and accessory bones in their own collections.
- **D30** The Run Hook tool runs any Hook on an imported Character.
- **D31** The panel's tools are bulk import, Run Hook, Export Prep, Import Animation and Snap IKs; the material panel has Edit Material and Link Hair.
- **D32** The harness imports the samples with every built-in Hook (`run.py hooks`) and compares each scene with `<sample>.defaults.json`; `run.py hooks --each` runs each Hook alone and fails if it changes anything it doesn't own.
- **D33** One commit per Hook and tool.
- **D34** Import Animation retargets Koikatsu FBX animations onto the Rigify rig with KKBP's own retargeting, mapped by Bone Role (the FBX bones carry the game's names, which are the bundle's Ids). It needs no other add-on. Mixamo animations and an animation library aren't supported. The test writes a synthetic walk FBX (D55).
- **D35** Separate Eyes moves the eye and eyebrow materials into new Parts with Part Roles `eyes` and `eyebrows`, parented to Body with their keys driven from Body's; the Rigify eye UV-warp modifiers move with them (D60).
- **D36** Bulk import runs one background Blender per bundle folder and saves `<folder>.blend` (or `Error - <folder>.blend`) beside it.
- **D37** Edit material copies its edit template's texture group for each material being edited, an exception to shared groups ([ADR 0025](../adr/0025-edit-materials-copy-their-texture-group.md)); the edited material is baked back into its Light Dark material. For KK and KKS face, body, eyes and clothes it reads the game's create materials from the bundle ([contract-change-create-materials.md](contract-change-create-materials.md)).
- **D38** Edit templates are picked by Material Role (body, face, hair, eyes, eye whites, eyebrow, nose line, eyelines, teeth; tongue and Role-less materials take KK General) or, for glasses shaders, by a KK profile list. Tears, gag eyes, face cards and glasses aren't editable. The templates follow the games' shaders (D67).
- **D39** Each image slot of an edit template is filled from one bundle texture, the create material's first and the material's own otherwise, with its offset and scale; `_ST_DT` is made from `_ST_CT` by the dark-texture code.
- **D40** The KK profile's `EDIT` colours (shared by KKS) map template inputs to bundle colours: create colours for face, body and clothes, the material's own for hair, eyebrows, eyelines, the tongue and clothes without a create; dark colours use `_ShadowColor`. A create colour is mapped only where a test shows it rebuilds the game's composited `main`.
- **D41** Eye highlight colours and strengths come from `_overcolor1`/`_overcolor2`, and pupil and highlight positions from the offsets and scales of `_MainTex`, `_overtex1` and `_overtex2`.
- **D42** The LUT saturation and the dark-texture code have no `bpy`. Whether edit materials saturate was decided by measurement: an unedited edit material baked with and without it, against the bundle's `light` texture. Only hair and eyebrows saturate by default ([ADR 0026](../adr/0026-edit-materials-dont-saturate-by-default.md)); a template made from the game's shaders never saturates (D67).
- **D43** numpy, pinned to Blender's own version, is in the dev venv for the host tests.
- **D44** Edit material, Cancel, Reset and Save. Save bakes light and dark with Eevee through an orthographic camera onto the mesh flattened into UV space, into the original Light Dark material; the edit copy goes; the alpha mask stays the Light Dark material's. The bake has its main texture's size and shape, and the body and face stay 4096 square ([ADR 0044](../adr/0044-bakes-keep-the-main-textures-shape-and-skin-stays-4096.md)). There is no backup material and no normal bake. Generated images go into the Cache (`kkbp_cache/edit/`, `kkbp_cache/baked/`).
- **D45** Link hair puts every hair material of the object into edit and copies the active one's light and dark settings to them (for a template made from the game's shaders, its colours; each hair keeps its own shader's values, ADR 0041).
- **D46** Edit material isn't available for SVS yet; KKS uses the KK templates.
- **D47** A built-in Hook, Delete default scene (`delete_default_scene`, on), runs last of the built-in Hooks and deletes Blender's startup cube, camera and light when every other object in the file belongs to an imported Character.

### Checks and the release

- **D48, D49** Retired. They set how the importer's scenes were compared with the old importer's while the two were being matched; that comparison is gone (D56, [ADR 0032](../adr/0032-the-legacy-baseline-is-retired.md)). What they approved in the Rigify rig still holds: the Junk collection holds the widgets and the metarig; face widgets are sorted by weights; the breast bones get no accessory controls; SVS's eye bones are `cf_J_Eye_tx` ([ADR 0028](../adr/0028-svs-eye-bones-are-the-eye-movers.md)).
- **D50** The importer's snapshots, `importer/tests/snapshots/<sample>.<core|defaults>.json`, are the regression target.
- **D51** The hook interface is documented in [../hook-interface.md](../hook-interface.md); the public API includes `editing`, `templates` (apply, param, params, texture, slots, swap, variant) and `TemplateError`.
- **D52** NOTICE credits the earlier KKBP importer, which the Rigify Hook and the shader templates come from; the repository is MIT (LICENSE); both ship in the importer zip and the exporter deploy folder.
- **D53** Batch export: a folder browser in the exporter window, every `.png` directly in the folder by name, a card that doesn't load skipped and logged, progress and Stop after this card, the auto-export's `"folder"` request for testing. The card list, the browser's navigation and the card mark (`【SVChara】`, which SVS needs because its `LoadFileLimited` returns false for good cards) are in the AdapterKit.
- **D54** The Core keeps every helper bone safe to delete ([ADR 0029](../adr/0029-the-core-keeps-helpers-safe-to-delete.md)). Saturated hair bakes a redder dark texture, as ADR 0026 records.

### Since the release

- **D55** The Golden Samples are made locally ([ADR 0031](../adr/0031-golden-samples-are-made-locally.md)). `contract/samples/` is ignored by git; `scripts/export-sample.sh` exports the tracked Sample Cards in `contract/sample-cards/` and stamps each sample with the exporter and contract it came from. The importer snapshots stay committed, with a 3.5 cm tolerance on the bones physics moves. Tests of a Game with no Golden Sample are skipped with a notice. The animation test writes a synthetic walk FBX.
- **D56** There is no comparison with the old importer: its recorded scenes and the code that compared them are deleted ([ADR 0032](../adr/0032-the-legacy-baseline-is-retired.md)).
- **D57** The SVS adapter closes the half-millimetre seam the game's gag shape leaves between each eye socket's disc and rim, and the Outlines Hook gives Body's modifier no thickness where the face mask hides the outline ([ADR 0033](../adr/0033-svs-gag-keys-close-the-eye-seam.md)).
- **D58** The SVS adapter gives each eye a separate eye white, as KK's: a copy of the eye mesh 1 mm behind it with an `eye_white` material, hidden with the eye. The bakes draw the eye white alone on the copy and only the pupil, over a transparent background, on the eye, so moving the pupils in Blender leaves the eye whites in place (issue 19, [ADR 0034](../adr/0034-svs-eye-whites-are-copies-of-the-eyes.md)).
- **D59** SVS's tongue keeps the game's mouth shapes: most SVS mouth patterns leave the tongue still while the teeth move, as in the game, and the exporter and importer don't add movement of their own (issue 2, [ADR 0035](../adr/0035-svs-tongue-keeps-the-games-mouth-shapes.md)).
- **D60** Separate Eyes is a built-in Hook (`separate_eyes`, off) that runs after Rigify and puts the new `eyes` and `eyebrows` Parts in an `Eyes and Eyebrows <name>` Collection; Run Hook runs it on an imported Character (issue 16). The eyes Part takes the pupils, eye whites and eye lines: KK's and KKS's eyelines, and SVS's eyelash and eyelid materials (issue 27).
- **D61** The Import Export Bundle button's file browser shows only `manifest.json`: choose a bundle's `manifest.json`, or open its folder and import with no file chosen. Any other file is refused with a message; scripts may still pass `directory` alone. The browser's button reads "Import manifest.json"; the panel's button keeps "Import Export Bundle" (issue 21).
- **D62** The light and dark bakes render through the full viewport: the maker camera's rect (`x 0.33`, room for the maker's menus) resampled every bake sideways and blurred it. KK and KKS reset the maker camera's rect while baking; SVS sets it on its own copy. No supersampling: baking at 2× and downscaling blurs texture detail (issue 17, [ADR 0036](../adr/0036-bakes-render-through-a-full-viewport.md)).
- **D63** The face cards try each image node's Material Roles in order: SVS's `eyelash` takes the upper eyeline's place, and a node none of them fills is unlinked, so it draws nothing instead of black. The Eyewhite card's mask follows the eye white's template: SVS's, `SVS Eye_White_Alpha`, is drawn from an SVS bundle's eye white UVs by `importer/tools/make_svs_eye_white_mask.py`, committed in `importer/library-src/images/` and packed by `scripts/build-library.sh` (issue 23, [ADR 0037](../adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)).
- **D64** The joint corrections are the games' own: the rules of KK's `ExpressionBone` and SVS's `HumanIndirectCorrection` are data in the Game Profiles, checked against what each game does in 801 recorded poses, and a Core Import Step (Import Option `joint_corrections`) rebuilds them as helper bones and simple-expression drivers that match Studio. Schema Version 1.1 adds each bone's `game_scale`. The Rigify Hook puts the corrections back on the generated rig (issue 10, [ADR 0038](../adr/0038-joint-corrections-copy-the-games-rules.md), [joint-corrections.md](joint-corrections.md)).
- **D65** The tongue is part of Body: the importer finds the two game tongues by their `tongue` Material Role, merges them as D4 says, and joins the result into Body with the rest of the head, so Body's mouth keys move it. There is no `tongue` Part Role and no `ch.tongue`, which made the hook interface 2.0; the Rigify Hook's tongue rig reads Body (issue 31, [ADR 0039](../adr/0039-the-tongue-is-part-of-body.md)).
- **D66** The template library and the Hooks' asset files are built from code: one Python module per node group and material in `importer/tools/library/`, and the images, meshes and scenes in `importer/library-src/`. `scripts/check-library.sh` checks that the committed files match a rebuild, by a structural fingerprint (issue 29, [ADR 0040](../adr/0040-the-library-is-built-from-code.md), [library-from-code.md](library-from-code.md)).
- **D67** Edit templates are built from the games' own shaders, read from the installed games and written as numpy models checked against the Golden Samples. Bundle textures hold linear values, colours are linear in the shader, and both games' light and dark bakes are graded by the maker camera's `Lut_TimeDay.png`, so each template grades last, in nodes, and is never saturated. KKS shares KK's templates, its Game Profile setting its own maker light (ambient colour, strength, shadow floor). Covered: both Games' eye whites, eyebrows, eyelines, nose line and hair (KKS's hair shader bakes as KK's), both Games' irises (KKS's eye shader bakes as KK's), KK's clothes, teeth, tongue (picked by shader), body and face, KK's `main_emblem` and `main_alpha`, and KKS's clothes, teeth, tongue and skin through KK's templates (approximated). A shader no template models (a modded one) takes the older general templates, which saturate as D42 says (issue 30, [ADR 0041](../adr/0041-edit-templates-follow-the-games-shaders.md)).
- **D68** The gag expressions' shape keys are one key, `Gag eyes`, on every Part they move, and the gag eyes' first material has a `Gag expression` dropdown that picks which one it shows, with an integer `Number` beside it for keyframes. Expressions whose shape differs from the shared one (Fiery Eyes) get a driven correction key each, `Gag eyes (Fiery Eyes)`. The other gag materials, the gag meshes' showing keys, the correction keys and the hidden pupils follow the dropdown through drivers, and the add-on's message bus subscription re-evaluates them when it changes (issue 35, [ADR 0042](../adr/0042-one-gag-eyes-key-with-a-dropdown.md)).
- **D69** The Rigify Hook is written in the importer's style: a RigBuild handed to the phases of `metarig/` and `finish/`, every name in `names.py`, each side written once, keyword helpers for constraints and drivers, modes only in `editing()`. A rig fingerprint (`run.py fingerprint`) shows whether a change leaves the rig as it was (issue 33, [ADR 0043](../adr/0043-rigify-rewritten-and-checked-by-a-rig-fingerprint.md)).

Later decisions are recorded as ADRs (0044 onwards) and in the design doc of the area they change, without a D number.
