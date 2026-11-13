# KKBP redesign

Agreed architecture for the new KKBP exporters and importer. These are new plugins with no backwards compatibility. Terms are defined in [CONTEXT.md](../../CONTEXT.md). Decisions that would be surprising without context are in [docs/adr/](../adr/).

Status: Phases 0 to 6 implemented; released as importer 10.0.0 and exporters 6.0.0. Later decisions are under "After the release".

## Designs

| Area | Doc | Replaces |
|---|---|---|
| Export Bundle (the contract) | [export-bundle.md](export-bundle.md) | 21 prefixed JSON files, PMX, name decoding, `JsonFileManager` |
| Exporter Core and Game Adapters | [exporter-core.md](exporter-core.md) | forked `PmxBuilder.cs`, duplicated PmxLib, static state |
| Import pipeline and Hooks | [import-pipeline.md](import-pipeline.md) | four chained operators, ignored failures, options declared three times |
| Character | [character.md](character.md) | 14 `get_*` scanners, `scene.kkbp.character_name` |
| Game Profile | [game-profile.md](game-profile.md) | 66 `is_kk()` / `get_prefix()` branches |
| Material Template | [material-template.md](material-template.md) | 120+ node and socket lookups by name, per-Character group copies |
| Blender compatibility and testing | [blender-compat-and-testing.md](blender-compat-and-testing.md) | scattered version checks, bundled third-party code, no regression tests |
| Built-in Hooks and tools | [hooks-and-tools.md](hooks-and-tools.md) | `postoperations.py`, the Rigify scripts, the extras that look things up by name |

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

Folded or dropped from the original review: candidate 6 (Exporter Naming) is replaced by Ids; candidate 9 (import options declared once) is part of the import pipeline.

Supported Games: KK, KKS, SVS. AC is out of scope for now.

Option changes: the "Export hit boxes" export option is removed. "Fix body seams" and "Separation type" move out of the Core Import into built-in Hooks that run at the end of the import.

## Roadmap

Each phase lists what it delivers and what it needs first.

```
Phase 0  baseline ─┐
Phase 1  contract + Exporter Core ─┬─> Phase 2  Game Adapters + new samples ─┐
                                   └─> Phase 3  importer foundations ────────┴─> Phase 4  port Steps ─> Phase 5  Hooks + tools ─> Phase 6  match and release
```

### Phase 0: baseline

- Set up the single repository (`contract/`, `exporters/`, `importer/`, `docs/`, `CONTEXT.md`).
- Build the headless Blender harness on 5.2 LTS and the latest stable release.
- Run the **current** importer on the three current samples and save their scene summaries. They are the target the new plugins must match.

### Phase 1: contract and Exporter Core

- JSON Schemas for every bundle file, including the Bone Role, Bone Group, Material Role, Blend Mode and Expression Name sets, and `contract/expressions/<game>.json`.
- The Exporter Core: glTF and JSON writer, Ids, layout, Manifest written last, Pass sequencing. It is built for `net35` in CI.
- A fake adapter, with its output checked by the schemas and the Khronos glTF Validator.

### Phase 2: Game Adapters (needs Phase 1)

- KK/KKS adapter (one project, NET35/NET46 configurations) and SVS adapter.
- Re-export the same three Characters as the new golden samples in `contract/` (made locally since D55).
- Can run in parallel with Phase 3.
- Not done in Phase 2: batch export (the legacy KK exporter's "Bulk export all cards in folder"). It moves to Phase 6.

### Phase 3: importer foundations (needs Phase 1)

- `bundle/` package with no `bpy`, tested with pytest against the test-bundle builder.
- Character, Compat (empty to start), the `editing()` context manager, the Mesh Loader with its startup option check.
- Pipeline skeleton: `import_bundle`, the Step list with Game lists, declared Import Options, Hook registration, the hooks folder, ImportResult.
- The Pillow installer and the Pillow-required check.

### Phase 4: port Steps (needs Phases 2 and 3)

- Port today's mesh, armature and material Steps onto `ctx`, the data API and the role tags, with no `ctx.game` checks.
- Rework the template `.blend` (role-named nodes, shared groups) and write the Template Descriptions and Template Sets.
- Game Profiles for KK, KKS and SVS.

Decisions agreed at the start of Phase 4 (the baseline comparison's causes cite them by number):

- **D1** The Step list in `pipeline/steps.py`, in running order: load the Passes, join the armatures, name UV maps, merge the tongues, build the Parts, order material slots and shape keys, link and drive the face keys, SVS's eyelids, trim the skeleton, bone tails and roll, IK bends, KK/KKS's fingers and legs, bone collections, templates, the Outfit's body textures, material changes, viewport colours, Collections, view transform.
- **D2** Bone tails and roll from Bone Roles and Groups only, with no bone names in the profiles ([ADR 0017](../adr/0017-bone-tails-from-the-game-rotation.md)). The Rigify Hook re-aims the bones its drivers need.
- **D3** One Gag template for every Game ([ADR 0019](../adr/0019-one-gag-template-built-per-material.md)).
- **D4** One tongue ([ADR 0020](../adr/0020-one-tongue-with-mouth-keys-and-bones.md)), part of Body since D65.
- **D5** `hides` through a `Hidden` template input ([ADR 0021](../adr/0021-expressions-hide-meshes-through-their-materials.md)).
- **D6** The Template Sets pick by (Material Role, Blend Mode) and set parameters and render methods; a material without its baked texture gets Transparent.
- **D7** Bone collections from Bone Roles and Groups; the legacy name-based splits (Charamaker, Toes, Face MCH) go.
- **D8** Steps get `ctx.profile`; Hooks don't. `import_bundle` refuses a Game without a profile before building anything.
- **D9** Objects keep the legacy display names; materials and bones are named by Id; every armature modifier is "Armature modifier".
- **D10** Images are packed; the view transform is set to Standard; the default scene is never deleted; each alternate clothing mesh is its own hidden Part.
- **D11** The template library is built by a script from the unchanged V9 source ([ADR 0018](../adr/0018-template-library-built-by-a-script.md)); since D66, from code.
- **D12** `templates.swap` is in place, with the KK shader variants; the convert-shaders Hook uses it in Phase 5.
- **D13** The harness imports the golden samples on every build (`run.py core`) and reports every difference from the baseline by cause (`run.py compare`). The comparison with the baseline is retired (D56).

Differences from the baseline approved after the Phase 4 comparison (`causes.py` marks them expected):

- SVS's rest pose is the game's own T-pose, so most SVS bones differ from the legacy export's pose.
- KK's and KKS's eyeline keeps a copy of its vertices for each of its two materials, as Blender's glTF importer makes them (+364 vertices).
- SVS hair is its own hair Part.
- Expressions that move nothing aren't exported (KK's Eyebrow Default, the body's vagina.open).
- Game patterns the translation tables don't name keep the game's name (KK and KKS mouths 40 to 42, six SVS mouths).
- A mesh has only the UV sets it has in the game.
- A mesh without expressions has no shape keys, not a lone Basis.
- Every active transform under the body root is a bone, so the samples have bones the legacy exports lacked (KKS's ClothCyclerCollision, SVS's o_tango).

The snapshots aren't updated in Phase 4; Phase 6 updates them once every difference is fixed or approved.

### Phase 5: Hooks and tools (needs Phase 4)

Status: implemented. With every built-in Hook, `run.py compare --profile defaults` leaves 62 (KK), 63 (KKS) and 216 (SVS) differences that no cause explains, nearly all in the Rigify rig, its metarig and its widgets; the Core Import alone leaves none. They are left for Phase 6 to fix or approve.

- Built-in Hooks: fix body seams, convert shaders, separate meshes (with Separation type), outlines, face cards, SFW, Rigify. Each Hook that needs assets has its own asset file.
- Tools used after an import: edit material, bake, export prep with the rewritten atlas (Pillow), Merge Weights. All of them go through Character, `ch.bundle()` and the Material Template module.
- The legacy panel's other extras, which no later phase has: import animation and IK snap, link shape keys, link hair, bulk import (the animation library and Mixamo import are dropped, D34).

Decisions agreed at the start of Phase 5. [hooks-and-tools.md](hooks-and-tools.md) lists every legacy piece and every legacy name lookup they replace.

- **D14** `BUILTIN_HOOKS`: Fix body seams → Convert shaders → Separate meshes → Outlines → Face cards → SFW → Rigify → Separate Eyes (→ Delete default scene). Switches, with the legacy panel's defaults: `fix_seams` on; `convert_shaders` (`off`, `eevee_mod`, `cycles`, `cycles_classic`, `principled`) off; `separation_type` (`off` "One object per outfit", `by_material` "Separate all clothing") off; `use_outlines` on; `use_face_cards` on; `sfw_mode` off; `use_rigify` on. Built-ins pass their switch to `kkbp.hook`. Outlines skips itself for the Cycles and Principled variants, as legacy did.
- **D15** The Hooks live in `importer/kkbp/builtin/`. Each asset file has a description with no `bpy`, checked against the file by a harness test, and is built from code by `scripts/build-library.sh` (D66; first from the unchanged V9 source): `rigify.blend` (widgets), `face_cards.blend` (its mouth atlas stored as WebP at quality 95), `outlines.blend`.
- **D16** Fix body seams merges by distance with bmesh on Body faces of Material Roles `face` and `body`: as Merge by Distance at 0.00001 (legacy's distance) with Centroid Merge, keeping each face corner's custom normal.
- **D17** Separate meshes splits each `outfit` Part into one Part per material, named by material Id, through a Compat helper.
- **D18** Convert shaders goes through `templates.swap` and the legacy rules by Material Role; the Eevee Mod inputs are per-variant template params; Principled is a `.Principled` variant group. SVS Light Dark gets the KK variants, with a warning that its bottom alpha mask is lost.
- **D19** Outlines: the legacy Solidify modifier and black material copies, found through templates; the face outline mask is chosen by the face material's template. The unused `outline` Part Role goes.
- **D20** Face cards take their images from Material Roles; the card meshes and card rig get a new Part Role, `face_card`.
- **D21** SFW deletes the vertices and bones of Bone Group `nsfw` and, by exact name, the KK nipple bones, whether or not Rigify is on.
- **D22** Rigify: the armature becomes the hidden metarig (still `ch.armature`), the generated rig is Part Role `rig`, Rigify is enabled for the session only (preferences are never saved), and each Character gets its own widgets.
- **D23** Rigify renames the Role bones to the legacy names from a Bone Role table before generating, so the rig's names are human-readable and match the baseline and the legacy retargeting lists.
- **D24** The KK/KKS-only Rigify branches (joint corrections, palms, finger rolls, nipple widgets) run when the skeleton has every joint-correction bone the legacy drivers name; the SVS-only hand IK widget branch runs when it doesn't ([ADR 0022](../adr/0022-kk-rigify-extras-gated-on-their-bones.md)).
- **D25** Rigify re-aims the joint-correction bones upright before driving them (ADR 0017), builds the eye controller and the Left and Right Eye vertex groups from Bone and Material Roles, rigs the single tongue (ADR 0020), on Body since D65, and builds the emotion grid from the Expression Names present.
- **D26** Tools go through Character, `ch.bundle()` and templates, and write into the Cache. Export prep refuses a Character with a rig.
- **D27** The legacy edit templates move into `library.blend` with descriptions and "edit" rows chosen by Material Role; a profile field `EDIT_COLORS` maps colours; the dark-texture code has no `bpy`. SVS has no edit rows yet. Bake renders with Eevee through an orthographic camera.
- **D28** Export prep: one module per prep type (VRM, VRC, Unreal, Koikatsu, no change), rebuilt by Bone Role; simplification by Bone Group; the atlas's layout and Pillow compositing have no `bpy` and are tested with pytest (Pillow pinned in the dev venv). Merge Weights is the CATS logic on the data API.
- **D29** `join_armatures` tags each bone added from an Outfit Pass with its Outfit, so Rigify can put later Outfits' hair and accessory bones in their own collections.
- **D30** A "Run Hook on this Character" tool replaces legacy "Convert for Rigify".
- **D31** The legacy extras no later phase has come into Phase 5.
- **D32** The harness imports the samples with every built-in Hook (`run.py hooks`) and compares them with `<sample>.defaults.json` by cause (`run.py compare --profile defaults`); `run.py hooks --each` runs each Hook alone and fails if it changes anything it doesn't own. The comparison by cause is retired (D56).
- **D33** ADRs from 0022; one commit per Hook and tool.
- **D34** Animation import retargets Koikatsu FBX animations onto the Rigify rig with KKBP's own retargeting, mapped by Bone Role (the FBX bones carry the game's names, which are the bundle's Ids); no Rokoko add-on. Mixamo animations and the animation library are dropped. One FBX sample is committed as the test file; since D55 the test writes a synthetic walk instead.
- **D35** Link shape keys moves the eye and eyebrow materials into new Parts with Part Roles `eyes` and `eyebrows`, parented to Body with their keys driven from Body's; the Rigify eye UV-warp modifiers move with them.
- **D36** Bulk import runs one background Blender per bundle folder and saves `<folder>.blend` (or `Error - <folder>.blend`) beside it.
- **D37** Edit material copies its edit template's texture group for each material being edited, as the legacy importer did, an exception to shared groups ([ADR 0025](../adr/0025-edit-materials-copy-their-texture-group.md)); the edited material is baked back into its Light Dark material. For KK and KKS face, body, eyes and clothes it needs the game's create materials, which the bundle doesn't carry yet: [contract-change-create-materials.md](contract-change-create-materials.md) proposes them for Phases 1 and 2.
- **D38** Edit templates are the legacy ones, picked by Material Role (body, face, hair, eyes, eye whites, eyebrow, nose line, eyelines, teeth; tongue and Role-less materials take KK General) or, for glasses shaders, by a KK profile list. Tears, gag eyes, face cards and glasses aren't editable; legacy's transparent dummy templates for glasses and the lower eyeline are left out, and every eyeline takes KK Eyeline up.
- **D39** Each legacy image slot is filled from one bundle texture, the create material's first and the material's own otherwise, with its offset and scale; `_ST_DT` is made from `_ST_CT` by the dark-texture code.
- **D40** `EDIT_COLORS` (KK profile, shared by KKS) maps template inputs to the legacy colours: create colours for face, body and clothes, the material's own for hair, eyebrows, eyelines, the tongue and clothes without a create; dark colours use `_ShadowColor`. A create colour legacy left unused is mapped only where a test shows it rebuilds the game's composited `main`.
- **D41** Eye highlight colours and strengths come from `_overcolor1`/`_overcolor2`, and pupil and highlight positions from the offsets and scales of `_MainTex`, `_overtex1` and `_overtex2`.
- **D42** The LUT saturation and the dark-texture code are ported with no `bpy`. Whether edit materials saturate is decided by measurement: an unedited edit material baked with and without it, against the bundle's `light` texture. Measured, only hair and eyebrows saturate by default ([ADR 0026](../adr/0026-edit-materials-dont-saturate-by-default.md)).
- **D43** numpy, pinned to Blender's own version, is in the dev venv for the host tests.
- **D44** Edit material, Cancel, Reset and Save. Save bakes light and dark with Eevee through an orthographic camera onto the mesh flattened into UV space, at the size of the largest texture, into the original Light Dark material; the edit copy goes; the bake is never smaller than the light texture it replaces, and the alpha mask stays the Light Dark material's. No Backup material and no normal bake. Generated images go into the Cache (`kkbp_cache/edit/`, `kkbp_cache/baked/`).
- **D45** Link hair puts every hair material of the object into edit and copies the active one's light and dark settings to them (for a template made from the game's shaders, its colours; each hair keeps its own shader's values, ADR 0041).
- **D46** Edit material isn't available for SVS yet; KKS uses the KK templates.
- **D47** A built-in Hook, Delete default scene (`delete_default_scene`, on), runs last of the built-in Hooks and deletes Blender's startup cube, camera and light when every other object in the file belongs to an imported Character, as legacy's import button deleted them from a file holding only them.

### Phase 6: match and release

Status: implemented and released as importer 10.0.0 and exporters 6.0.0 (git tag `v10.0.0`). No difference from the Phase 0 baseline is unexplained (D48, D49, ADR 0029), and the new importer's snapshots are the regression target (D50); the baseline is retired since (D56).

- The new importer's summaries for the new samples must match the Phase 0 baseline within tolerance (done; retired by D56). Each difference is fixed or approved, then snapshots are updated.
- Write the hook interface documentation (version 1.0) and the NOTICE credits.
- Add batch export to the exporters: pick a folder and export every card in it, one bundle each, with the window's options. It only loops the existing export over the cards, so no contract change is needed. It goes here because nothing before release needs it.

Decisions agreed at the start of Phase 6:

- **D48** The comparison applies ADR 0005's Id rules to legacy names no Id can be in the defaults profile too (`(Clone)`, `__2`, `cf_j_armsk_L_0_1 1`), finds a rig bone's metarig bone by the longest start of its name (side suffix kept, case ignored), and lets rig bones follow their whole metarig chain.
- **D49** Approved differences in the Rigify rig: the Junk collection holds the widgets and the metarig; the metarig and rig counts follow; legacy's snapped `cf_j_spinesk_00` head; face widgets sorted by weights; no accessory controls on the breast bones; the emotion grid's copied keys; SVS's eye bones are `cf_J_Eye_tx` ([ADR 0028](../adr/0028-svs-eye-bones-are-the-eye-movers.md)).
- **D50** New-importer snapshots, `importer/tests/snapshots/<sample>.<core|defaults>.json`, become the regression target once every difference is fixed or approved; `snapshots/baseline/` stays as the Phase 0 record (until D56 deletes it).
- **D51** The hook interface 1.0 is documented in [../hook-interface.md](../hook-interface.md); the public API adds `editing`, `templates` (apply, param, params, texture, slots, swap, variant) and `TemplateError`.
- **D52** NOTICE credits the legacy KKBP importer (the Rigify scripts and `KK Shader V9.blend`) and names the legacy exporters as reference only; the repository is MIT (LICENSE); both ship in the importer zip and the exporter deploy folder.
- **D53** Batch export: a folder browser in the window, every `.png` directly in the folder by name, a card that doesn't load skipped and logged, progress and Stop after this card, the auto-export's `"folder"` request for testing. The card list, the browser's navigation and the card mark (`【SVChara】`, which SVS needs because its `LoadFileLimited` returns false for good cards) are in the AdapterKit.
- **D54** The helper groups are fixed in the exporter: the Core keeps every helper safe to delete ([ADR 0029](../adr/0029-the-core-keeps-helpers-safe-to-delete.md)), and the samples are re-exported. The saturated hair's redder dark bake stays, as ADR 0026 records.

### After the release

- **D55** The Golden Samples are made locally ([ADR 0031](../adr/0031-golden-samples-are-made-locally.md)). `contract/samples/` is ignored by git; `scripts/export-sample.sh` exports the tracked Sample Cards in `contract/sample-cards/` and stamps each sample with the exporter and contract it came from. The importer snapshots stay committed, with a 3.5 cm tolerance on the bones physics moves. Tests of a Game with no Golden Sample are skipped with a notice. The animation test writes a synthetic walk FBX.
- **D56** The legacy baseline and its comparison are deleted ([ADR 0032](../adr/0032-the-legacy-baseline-is-retired.md)).
- **D57** The SVS adapter closes the half-millimetre seam the game's gag shape leaves between each eye socket's disc and rim, and the Outlines Hook gives Body's modifier no thickness where the face mask hides the outline ([ADR 0033](../adr/0033-svs-gag-keys-close-the-eye-seam.md)).
- **D58** The SVS adapter gives each eye a separate eye white, as KK's: a copy of the eye mesh 1 mm behind it with an `eye_white` material, hidden with the eye. The bakes draw the eye white alone on the copy and only the pupil, over a transparent background, on the eye, so moving the pupils in Blender leaves the eye whites in place (issue 19, [ADR 0034](../adr/0034-svs-eye-whites-are-copies-of-the-eyes.md)).
- **D59** SVS's tongue keeps the game's mouth shapes: most SVS mouth patterns leave the tongue still while the teeth move, as in the game, and the exporter and importer don't add movement of their own (issue 2, [ADR 0035](../adr/0035-svs-tongue-keeps-the-games-mouth-shapes.md)).
- **D60** Link shape keys is now the built-in Hook Separate Eyes (`separate_eyes`, off), which runs after Rigify and puts the new `eyes` and `eyebrows` Parts in an `Eyes and Eyebrows <name>` Collection; its panel button is gone, and Run Hook runs it on an imported Character (issue 16).
- **D61** The Import Export Bundle button's file browser shows only `manifest.json`: choose a bundle's `manifest.json`, or open its folder and import with no file chosen. Any other file is refused with a message; scripts may still pass `directory` alone. The browser's button reads "Import manifest.json"; the panel's button keeps "Import Export Bundle" (issue 21).
- **D62** The light and dark bakes render through the full viewport: the maker camera's rect (`x 0.33`, room for the maker's menus) resampled every bake sideways and blurred it. KK and KKS reset the maker camera's rect while baking; SVS sets it on its own copy. No supersampling: baking at 2× and downscaling blurs texture detail (issue 17, [ADR 0036](../adr/0036-bakes-render-through-a-full-viewport.md)).
- **D63** The face cards try each image node's Material Roles in order: SVS's `eyelash` takes the upper eyeline's place, and a node none of them fills is unlinked, so it draws nothing instead of black. The Eyewhite card's mask follows the eye white's template: SVS's, `SVS Eye_White_Alpha`, is drawn from an SVS bundle's eye white UVs by `importer/tools/make_svs_eye_white_mask.py`, committed in `importer/library-src/images/` and packed by `scripts/build-library.sh` (issue 23, [ADR 0037](../adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)).
- **D64** The joint corrections are the games' own: the rules of KK's `ExpressionBone` and SVS's `HumanIndirectCorrection` are data in the Game Profiles, checked against what each game does in 801 recorded poses, and a Core Import Step (Import Option `joint_corrections`) rebuilds them as helper bones and simple-expression drivers that match Studio. Schema Version 1.1 adds each bone's `game_scale`. The Rigify Hook drops the legacy drivers and puts the corrections back on the generated rig (issue 10, [ADR 0038](../adr/0038-joint-corrections-copy-the-games-rules.md)).
- **D65** The tongue is part of Body: the importer finds the two game tongues by their `tongue` Material Role, merges them as D4 says, and joins the result into Body with the rest of the head, so Body's mouth keys move it. The `tongue` Part Role and `ch.tongue` are removed, which makes the hook interface 2.0; the Rigify Hook's tongue rig reads Body (issue 31, [ADR 0039](../adr/0039-the-tongue-is-part-of-body.md)).
- **D66** The template library and the Hooks' asset files are built from code: one Python module per node group and material in `importer/tools/library/`, and the images, meshes and scenes in `importer/library-src/`. The legacy `KK Shader V9.blend` is deleted. A rebuild was shown to match the files it replaced by a structural fingerprint and a decompile round trip; `scripts/check-library.sh` repeats the check (issue 29, [ADR 0040](../adr/0040-the-library-is-built-from-code.md)).
- **D67** Edit templates are rebuilt from the games' own shaders, read from the installed games and written as numpy models checked against the Golden Samples. Bundle textures hold linear values, colours are linear in the shader, and both games' light and dark bakes are graded by the maker camera's `Lut_TimeDay.png`, so each template grades last, in nodes, and is never saturated. KKS shares KK's templates, its Game Profile setting its own maker light (ambient colour, strength, shadow floor). Done for both Games' eye whites, eyebrows, eyelines, nose line and hair (KKS's hair shader bakes as KK's), both Games' irises (KKS's eye shader bakes as KK's), KK's clothes, teeth, tongue (picked by shader), body and face, KK's `main_emblem` and `main_alpha`, and KKS's clothes, teeth, tongue and skin through KK's templates (approximated); shaders no template models (modded ones) keep the legacy templates until their shaders are modelled (issue 30, [ADR 0041](../adr/0041-edit-templates-follow-the-games-shaders.md)).
- **D68** The gag expressions' shape keys become one key, `Gag eyes`, on every Part they moved, and the gag eyes' first material gets a `Gag expression` dropdown that picks which one it shows, with an integer `Number` beside it for keyframes. Expressions whose shape differs from the shared one (Fiery Eyes) get a driven correction key each, `Gag eyes (Fiery Eyes)`. The other gag materials, the gag meshes' showing keys, the correction keys and the hidden pupils follow the dropdown through drivers, and the add-on's message bus subscription re-evaluates them when it changes (issue 35, [ADR 0042](../adr/0042-one-gag-eyes-key-with-a-dropdown.md)).
