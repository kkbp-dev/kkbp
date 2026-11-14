# contract

The Export Bundle contract shared by the exporters and the importer. The design is [docs/design/export-bundle.md](../docs/design/export-bundle.md); terms are in [CONTEXT.md](../CONTEXT.md).

| Path | Contents |
|---|---|
| `schema/*.schema.json` | One JSON Schema (draft 2020-12) per bundle file |
| `schema/sets/*.schema.json` | The closed sets: Bone Role, Bone Group, Material Role, Blend Mode, Texture Role, Texture Variant, Expression Name, expression category |
| `expressions/<game>.json` | Each Game's expression translation table, embedded into its exporter |
| `sample-cards/<game>.png` | The Sample Cards: the three sample Characters' Cards, in Git LFS. |
| `samples/<game>/` | The Golden Samples, ignored by git: each developer exports their own from the Sample Cards (Outfit 00, physics on, no other options). |

| Bundle file | Schema |
|---|---|
| `manifest.json` | `manifest.schema.json` |
| `character.json` | `character.schema.json` |
| `skeleton.json` | `skeleton.schema.json` |
| `materials.json` | `materials.schema.json` |
| `expressions.json` | `expressions.schema.json` |
| `physics.json` | `physics.schema.json` |
| `body.json`, `outfits/NN/outfit.json` | `pass.schema.json` |

The schemas are strict (`additionalProperties: false`) so that exporter mistakes fail the contract tests. The importer still ignores unknown fields at runtime, as the Schema Version rules require. A Game-only field is added only when a Step or Hook reads it. The only one so far is a material's `extensions.kk.create`, its Create Material, which the edit material tool reads; every other Game Extension must be empty.

Every schema has an `$id` under `https://schemas.kkbp.invalid/1.2/`. The host doesn't exist; validators load the files from this folder and resolve the relative `$ref`s.

## Rules the schemas can't express

The contract tests check these in code.

- **Unique roles.** A set's `x-unique` keyword lists the members that may appear at most once:
  - Bone Roles: once per bundle (`skeleton.json`).
  - Material Roles: once per bundle (`materials.json`).
  - Texture Roles: once per material for each `(variant, pattern)`. `overlay` may repeat.
- **Unique keys.** Ids are unique within their kind across the bundle. `(raw, variant, pattern)` is unique within a material. `(mesh, target)` is unique in `expressions.json`, and an Expression Name appears on at most one target per mesh.
- **Passes.** The Manifest lists exactly one Body Pass, first, and each Outfit index at most once. An Outfit Pass's files are in its own `outfits/NN/` folder, `NN` being its index with two digits. A data file's `kind` and `outfit` match its Manifest entry.
- **References.** Every bone `parent`, mesh material, physics bone and expression mesh names an Id that exists. Each `effects` entry names the target of at least one expression record, and no target has two entries. Its `shows` and `hides` name meshes in the Pass of that expression's records, and each shown mesh has a showing key: a `tears` or `gag` shape key with no game name. A `material_changes` texture names a pattern its material has for that Raw Property.
- **Body textures.** A Pass's `body_textures` name materials that Body Pass meshes use, in slots that material doesn't fill itself, each slot once per Pass. Every texture `file` exists. Every Pass in the Manifest has its `.glb` and data file.
- **Create materials.** A material's `extensions.kk.create` follows the rules for a material's own textures: `(raw, variant, pattern)` is unique within the `create`, and so is `(role, variant, pattern)`, except `overlay`. Every `create` texture `file` exists. A material with a `create` is used by meshes of exactly one Pass, the Pass whose objects it colours: the Body Pass if the material has a Material Role (body, face, eyes), an Outfit Pass if it has none (clothes).
- **Expression categories.** A named expression's category is its name's prefix: `Eye` → `eye`, `Mouth` → `mouth`, `Eyebrow` → `eyebrow`, `Gag` → `gag`, `Tears` → `tears`.
- **Bakes without eyeshadow.** The Texture Variants `light_no_eyeshadow` and `dark_no_eyeshadow` (Schema Version 1.2) are the `light` and `dark` bakes of a face material drawn without its eyeshadow. An exporter writes both or neither, beside the `light` and `dark` of the same texture, and only when the face has eyeshadow it can leave out.
- **Game scale.** A bone's `game_scale` (Schema Version 1.1) is the scale the game had on it at capture, parents included, which the rest pose leaves out ([ADR 0008](../docs/adr/0008-bone-rest-poses-carry-no-scale.md)). Each component is above 0, and a bone at scale 1 has no `game_scale`. The `.glb` nodes don't carry it.
- **glTF.** Every `.glb` passes the Khronos glTF Validator with no errors and no warnings (`contract/tools/validate-gltf.mjs` fails on either). Every node, mesh and material has `extras.id` equal to its `name`. A bone that appears in several `.glb` files has the same rest pose in each.

## Expression tables

`expressions/<game>.json` follows `schema/expression-table.schema.json` ([ADR 0004](../docs/adr/0004-expression-names-are-display-names.md)).

- `patterns` name the game's expression patterns by list (`eye`, `eyebrow`, `mouth`) and 0-based position in the game's list. `game_name` is what the game showed when the table was written; it is never used for matching. An eye pattern that shows the gag eyes is named with the `Gag` prefix.
- `closed_name` names the pattern baked with the eyes or mouth closed. The exporter skips it when it is identical to the open one.
- `recipes` are expressions that aren't game patterns, baked from game shape keys at the given weights (0 to 1). A mesh that lacks one of the shapes skips it.
- A pattern that isn't in the table keeps its game name and has no Expression Name.
- Every name in a table must be in the Expression Name set and appear once per table.

The tables were first written from the legacy samples in Phase 1. Phase 2 checked their positions against the games: the legacy KK and KKS exporters inserted an extra mouth entry, "Open" (the default mouth opened), after pattern 0, so every later mouth position was one too high. That entry is gone; its look is `Mouth Default`, the open version of pattern 0. The exporter also makes the tear and gag-mesh keys (`Tears small`, `Tears med`, `Tears big`, `Gag eye 00` to `Gag eye 02`), which are in the set but not in any table.

## Texture Roles

Adapters map the game's slots to Roles. Phase 1 starts from:

| Role | Raw Properties |
|---|---|
| `main` | `_MainTex`, `_Main_texture` |
| `color_mask` | `_ColorMask`, `_Main_color_mask`, `_Hair_color_mask` |
| `normal` | `_NormalMap`, `_Normal_map` |
| `detail_normal` | `_NormalMapDetail`, `_DetailNormal` |
| `alpha_mask` | `_AlphaMask`, `_Cloth_alpha` |
| `line_mask` | `_LineMask`, `_Line_mask` |
| `detail_mask` | `_DetailMask`, `_Detail_mask` |
| `overlay` | `_overtex1`, `_overtex2`, `_overtex3` |

Everything else, including `_liquidmask`, is known by its Raw Property only.

## Golden Samples

`samples/kk`, `samples/kks` and `samples/svs` are the Golden Samples: the Sample Cards in `sample-cards/`, the same three Characters as the legacy samples, exported by the new exporters. They are game content, so they are not in the repository (ADR 0031); each developer makes their own from the games they have:

```bash
scripts/export-sample.sh        # every installed game
scripts/export-sample.sh kk     # one
```

It needs the game installed (see [exporters/README.md](../exporters/README.md)). It checks each sample against the schemas, the rules above and the glTF Validator, writes `samples/<game>.stamp` with the exporter and contract it came from, and then checks the imports against the importer's committed snapshots. The Core's tests check every Golden Sample present; tests of a Game without one are skipped. Each sample's `exported_at`, texture contents and physics-settled bones change with every remake.

