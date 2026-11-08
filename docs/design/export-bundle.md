# Export Bundle

The Export Bundle is the versioned contract between the exporters and the importer: the folder an exporter writes for one Character, and the only thing the importer reads. Terms are defined in [CONTEXT.md](../../CONTEXT.md). The mesh format decision is [ADR 0001](../adr/0001-gltf-instead-of-pmx.md).

Status: agreed design, not yet implemented. These are new plugins; no backwards compatibility with today's export folders.

## Repository and contract

- One repository: `contract/` (JSON Schemas, written spec, Sample Cards; the Golden Samples are made locally, ADR 0031), `exporters/core`, `exporters/kk`, `exporters/svs`, `importer/`, plus `CONTEXT.md` and `docs/`.
- The JSON Schemas are the contract. Each side writes its own types by hand. Contract tests check every exporter's sample output, and every test bundle the importer uses, against the schemas.
- The exporters write the canonical shape directly and the schemas enforce it. The importer does not convert between Games.

## Layout

```
manifest.json
character.json
skeleton.json
materials.json
expressions.json
physics.json
body.glb
body.json
outfits/NN/outfit.glb
outfits/NN/outfit.json
textures/
card.png
kkbp_cache/<kind>/
```

- `kkbp_cache/` is written only by the importer and never by an exporter. Deleting it is always safe. It has no leading dot, so file browsers show it (ADR 0030).
- Texture file names are short, ASCII and carry no meaning (`textures/0001.png`, numbered in write order). Lookup goes through `materials.json`, never through file names.
- The bundle folder is named `<yyyyMMddHHmmss>_<Character name>`, with characters that aren't valid in paths replaced. `NN` is the two-digit Outfit index.
- `body.json` and each `outfit.json` are a Pass's data file: its meshes (Id, game name, material Ids in primitive order, and whether the mesh shows only in the game's alternate clothing state) and its Game Extension. An Outfit's data file also lists the textures that Outfit puts on body materials, such as the body alpha mask that hides skin under its clothes; the Body Pass leaves those slots out. `materials.json` holds the materials of every Pass.
- All JSON is UTF-8 without a BOM. The schemas in `contract/schema/` give every field.

## Manifest

- Game: one of `KK`, `KKS`, `SVS`. AC is out of scope for now; adding it later is a minor Schema Version bump with its own exporter, profile and golden sample.
- Schema Version: `major.minor`. The importer accepts any bundle with its major version, whatever the minor, and ignores unknown fields.
- Exporter name and Exporter Version: informational, never used to accept or reject a bundle.
- Export time (RFC 3339, UTC), Character name, Card file (`card.png`, or null).
- Export options used (replaces `KKBPExporterConfig.json`): `all_outfits`, `all_variations`, `physics`, `enabled_shape_keys`, `current_pose`, plus Game-only options under `extensions`. The batch-export switch is UI state and isn't recorded.
- Passes: for each, kind (`body` or `outfit`), Outfit index (null for the body), `.glb` path, data-file path.
- The first Schema Version is `1.0`, released with importer 10.0.0 and exporters 6.0.0. From then on, a change that only adds (an optional field, a set value) raises the minor version (`1.1`), and any other change raises the major version (`2.0`), which also forces a hook interface major version.
- No file hashes.
- The exporter writes the Manifest last. A bundle without one is an unfinished export, and the importer reports it as such.

## Shared core and Game Extensions

- Data every Game has lives in the shared core.
- Data only one Game has lives in its Game Extension (`extensions.kk`, `extensions.svs`, …). The accessor returns `None` for other Games.
- A Game-only field is added only when a Step or Hook reads it. The first is a material's `extensions.kk.create`: the KK and KKS Create Material that composites its main texture, with the shape of a material's shader data (shader, colours, floats, vectors, textures). The edit material tool reads it ([contract-change-create-materials.md](contract-change-create-materials.md)). Every other Game Extension is empty.
- KK and KKS both write `extensions.kk`. A field only KKS has would go in `extensions.kks`.

## Ids

- Every mesh, material and bone record carries an `id` and the original game `name`.
- Ids are short ASCII strings built from the game name, with a counter only when two would clash (`cf_m_body`, `cf_m_hair_b_2`).
- Meshes, materials and bones each have their own namespace. A name that simplifies to nothing gets the kind's prefix: `mesh`, `mat_2`, `bone_3`. The rules are in [ADR 0005](../adr/0005-ids-per-kind-from-adapter-keys.md).
- Deterministic: re-exporting the same Character gives the same Ids.
- At most 63 bytes, to fit Blender name limits.
- All matching between files, and between files and Blender data, uses Ids. The importer never parses a name.

## Roles and canonical names

The exporters write down what things mean, so that the importer needs no Game's own names ([game-profile.md](game-profile.md)).

The decision is [ADR 0002](../adr/0002-exporters-write-game-meaning.md).

- **Bone Roles:** a bone in `skeleton.json` may carry one. The set is Unity's 55 `HumanBodyBones` in snake_case (`hips`, `left_upper_arm`, …) plus KKBP extras: `body_root`, `face_root`, `left_breast`, `right_breast`, `tongue_root`, and the IK helpers `left_hand_ik`, `right_hand_ik`, `left_foot_ik`, `right_foot_ik`, `left_elbow_pole`, `right_elbow_pole`, `left_knee_pole`, `right_knee_pole`. Every Bone Role is unique.
- **Bone Groups:** every bone carries exactly one, from `deform`, `helper`, `skirt`, `breast`, `hair`, `accessory`, `face`, `eye`, `eyebrow`, `mouth`, `nsfw`. `face` is the face bones that aren't `eye`, `eyebrow` or `mouth`; `nsfw` is the genital and Better Penetration bones. A `helper` bone is safe to delete: nothing weights it or anything below it, and no physics chain uses it. Hit boxes are never exported ([exporter-core.md](exporter-core.md#export-options)).
- **Material Roles:** a material in `materials.json` may carry one, from `body`, `face`, `eyebrow`, `eyelash`, `eyelid`, `eyeline_upper`, `eyeline_lower`, `eyeline_shadow`, `nose_line`, `eye_white`, `eye_l`, `eye_r`, `gag_eyes`, `tongue`, `teeth`, `tears`, `hair`. Outfit and accessory materials have no role.
- **Blend Mode:** every material in `materials.json` carries one, from `opaque`, `cutout`, `alpha`, `glasses`. The importer uses it to choose a Material Template ([material-template.md](material-template.md)).
- **Uniqueness:** the contract marks each role as unique (such as `body_root`, `face`, `eye_l`) or repeatable (such as `hair`). `open_bundle` reports a unique role that appears twice as an error. Most bones and materials have no role. The repeatable Material Roles are `hair`, `eye_white`, `gag_eyes`, `tongue`, `teeth` and `tears`, because the games split these across several materials.
- **Expression Names:** a closed list in the contract. Each expression shape key carries its Expression Name and the game's own name. A shape key with no translation keeps its game name and has no Expression Name. Names are display strings with a category prefix (`Eye`, `Mouth`, `Eyebrow`, `Gag` for gag-eye expressions, `Tears`) and `, Closed` for a closed version ([ADR 0004](../adr/0004-expression-names-are-display-names.md)).
- **Translation tables:** the per-Game tables are data files (`contract/expressions/kk.json`, `kks.json`, `svs.json`), embedded into each exporter when it's built. A table names patterns by category and position in the game's list, and adds recipes for expressions that aren't game patterns (such as KK's chewing and eating mouths).
- The role sets, Bone Groups and Expression Names are part of the contract and follow Schema Version rules.

## Encoding

- Numbers are plain JSON numbers, written the same way on every PC locale.
- Colours are `[r, g, b, a]` floats exactly as set on the game's material, declared sRGB-encoded. Any linear conversion happens in the importer.
- Vectors are `[x, y, z, w]`.
- Empty lists are `[]`, never empty files.

## Textures

`materials.json` lists each material's textures. Each entry has:

- a Texture Role from the shared set, if it has one: `main`, `color_mask`, `normal`, `detail_normal`, `alpha_mask`, `line_mask`, `detail_mask`, `overlay`;
- its Raw Property name (always present);
- its Texture Variant, if any: `light` or `dark`, the baked versions;
- its pattern, if the slot holds several textures the game swaps at runtime (gag-eye frames, eye expression textures): the game's texture name;
- the file path under `textures/`, plus offset and scale.

The shared importer steps use Roles only. Game profiles use Raw Properties for everything else.

- `(Raw Property, Variant, pattern)` is unique within a material. So is `(Role, Variant, pattern)`, except `overlay`, which may repeat in the game's order.
- `_liquidmask` has no Role; nothing in the importer reads it, so it is known by its Raw Property only.
- Normal maps are written as standard tangent-space maps, already converted from Unity's packed format. There is no separate converted variant.
- Offset and scale use Unity's UV convention (origin bottom left), which is also Blender's. The `.glb` UVs are flipped to glTF's convention by the Core, and Blender's glTF importer flips them back.
- Material shader values are keyed by Raw Property: `colors` (`[r, g, b, a]`), `floats` and `vectors` (`[x, y, z, w]`), alongside the game's shader name.

## Meshes (glTF)

- One `.glb` per Pass, with no textures embedded.
- Contents: geometry, normals, UV sets, skin weights, the skeleton's rest pose, shape keys (morph targets named via `targetNames`) and the object tree.
- `extras.id` on every node, mesh and material. Blender's glTF importer turns `extras` into custom properties, which gives the Blender → Id mapping. The glTF `name` of each node, mesh and material is also its Id, so Blender names bones and materials by Id.
- glTF materials are placeholders (name and Id only). Shader data lives in `materials.json`.
- No custom glTF extension.
- The bones form the node tree. Every mesh is skinned, and its node sits at the scene root with no transform; a Pass has one skin with all its bones ([ADR 0006](../adr/0006-every-mesh-skinned-at-scene-root.md)).
- Vertex data: `POSITION`, `NORMAL`, `TANGENT` and `COLOR_0` when the game has them, every UV set, and as many `JOINTS_n`/`WEIGHTS_n` sets as the mesh needs, with weights normalised. Morph targets hold `POSITION` and `NORMAL` deltas.
- All Passes use the same bone Ids. The importer joins them onto one armature by Id. `skeleton.json` lists every bone of every Pass; a bone in two `.glb` files has the same rest pose in both.
- Coordinate space is glTF's (right-handed, +Y up, metres). The exporter converts from Unity in exactly one place by negating X, and every transform in the JSON files uses the same space.
- glTF has no bone tails or roll. The importer sets them from game-profile rules. `skeleton.json` contains no Blender concepts.

## Expressions

- Each expression is a finished shape key baked by the exporter: a game pattern, its closed version where the game has one, or a recipe from the translation table ([ADR 0003](../adr/0003-exporters-bake-complete-expressions.md)). The game's partial shape keys are not exported.
- An expression is a morph target on every mesh it moves, with the same target name on each. The target name is the Expression Name if it has one, otherwise the game name.
- `expressions.json` lists each one: mesh Id, target name, category (`eye`, `mouth`, `eyebrow`, `gag`, `tears` or `other`), Expression Name or null, and the game's own name.
- An expression can also record what else the game does while it is on, in one `effects` entry named by its target name that applies to all of its records: the meshes it `shows` (each a tear or gag-eye mesh with its showing key, [ADR 0010](../adr/0010-tear-and-gag-meshes-rest-inside-the-head.md)), the meshes it `hides` (such as the pupils behind gag eyes), and its `material_changes`: texture patterns, floats and vectors it sets on a material, keyed by Raw Property. Gag-eye textures and their animation values (`_TileAnimation`, `_SizeSpeed`, …) are material changes, so both Games use the shared core for them.

## Exporter side

- One shared C# module, with no dependencies, writes glTF 2.0 and JSON. Its interface takes plain arrays, not Unity types. It is compiled into all exporters: KK (.NET 3.5, Unity 5.6), KKS (.NET 4.6, Unity 2019.4), SVS (.NET 6 IL2CPP, Unity 2021.3).
- It replaces PmxLib, the KK string-patching JSON writers and SVS's `CustomJsonSerializer`.
- Its output is checked with the Khronos glTF Validator in the contract tests.

## Importer side

`bundle/` is its own package inside the add-on. It never imports `bpy` and uses relative imports only within itself. Tests import it directly, and one test checks that `bpy` never loads.

```python
bundle = open_bundle(path)  # raises BundleError listing every problem found
bundle.manifest
bundle.character
bundle.skeleton
bundle.passes               # each: kind, outfit, mesh_path, meshes, materials
bundle.material(id)         # shader values + textures by Role / Raw Property / Variant
bundle.expressions
bundle.physics
bundle.extension("kk")      # None for other Games
bundle.cache_dir("baked")   # path inside kkbp_cache/
bundle.warnings
```

- Sections are frozen standard-library dataclasses, built when the bundle opens.
- The bundle checks everything on open: required files present and parseable, Game identified, Schema Version accepted. It gives one error listing every problem, or a list of warnings.
- All JSON is read on open. `.glb` files and textures are only handed out as paths.
- Every current reader moves to the bundle, including `extras/editmaterial.py`. `JsonFileManager` is deleted.
- The Mesh Loader is the only caller of `bpy.ops.import_scene.gltf` and sets every option explicitly.
- Post-import hooks receive the opened Bundle (read-only) and the imported Character. The bundle's interface is therefore part of what hook authors depend on.

## Testing

- A small builder writes valid bundles into a temporary folder, so tests go through the real open-and-validate path.
- The Golden Samples, exported locally from the Sample Cards in `contract/sample-cards/` (ADR 0031), are the full regression set.
- To check the rewrite: Phase 0 records a scene summary from the current importer for each of the three current samples (objects, materials, shape keys, bone count and positions, vertex counts, textures used). The new exporters re-export the same three Characters, and the new importer must produce matching summaries within a tolerance, comparing names through Ids. Each difference is either a bug or an approved fix. (Done in Phase 6; the baseline is retired, ADR 0032.)

## Effect on the architecture plan

- Candidate 5's PMX Loader becomes the Mesh Loader.
- Part of candidate 7 (the shared glTF and JSON writer) moves into Phase 1.
- The Phase 0 harness becomes the old-vs-new comparison above.
