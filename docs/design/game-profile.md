# Game Profile

How the importer handles differences between Games. Terms are defined in [CONTEXT.md](../../CONTEXT.md).

The decision to tag meaning in the exporters is [ADR 0002](../adr/0002-exporters-write-game-meaning.md).

## Where game knowledge lives

- **The exporters tag meaning in the bundle**, because they read the game's own structures and know it for certain:
  - bones may carry a Bone Role, and every bone carries a Bone Group, in `skeleton.json`;
  - materials may carry a Material Role in `materials.json`;
  - expression shape keys carry an Expression Name, with the game's own name alongside.
- The sets themselves are listed in [export-bundle.md](export-bundle.md#roles-and-canonical-names).
- The importer finds what it needs through those roles and names, never through a Game's own bone or material names. Most importer code therefore needs no game knowledge.
- Trade-off accepted: a fix to these tables needs an exporter release.

See [export-bundle.md](export-bundle.md#roles-and-canonical-names).

## What a Game Profile is

- A **data-only** module per Game: tables and settings, no behaviour.
- A profile can **extend** another and override only what differs: KKS extends KK.
- The profile names its Template Set (`TEMPLATE_SET = "KK"` or `"SVS"`). Template Sets are described in [material-template.md](material-template.md).
- It maps the Raw Properties a template has a slot for (`RAW_TEXTURES`) and the per-pattern values an expression sets (`PATTERN_VALUES`).
- It maps the Rigify Hook's Face Key Roles to Expression Names (`FACE_KEYS`, [ADR 0058](../adr/0058-the-face-rig-drives-the-expression-keys-through-face-key-roles.md)): the same name can mean another expression in another Game.
- It holds the bone tail and roll rules (`BONES`), by Bone Role and Bone Group ([ADR 0017](../adr/0017-bone-tails-from-the-game-rotation.md)). No exact bone names turned out to be needed.
- A field a profile sets replaces its base profile's; a field it leaves out is inherited.
- Profiles live in `importer/kkbp/profiles/`, which never imports bpy. Steps get the bundle's profile as `ctx.profile`.

## Parts from Material Roles

- The importer separates hair, tears and gag eyes into their own Parts by Material Role (`hair` → `hair` Part, `tears` → `tears` Part, and so on). The tongue stays in Body ([ADR 0039](../adr/0039-the-tongue-is-part-of-body.md)).
- That mapping is one table, the same for every Game, so these Steps need no game data.

## Behaviour differences

- Behaviour that differs between Games is a separate Step with a Game list, as in [import-pipeline.md](import-pipeline.md#steps-per-game). An empty list runs on every Game. A non-empty list runs only on the Games it names.
- Game lists name exact Games (`["KK", "KKS"]`). Profile inheritance never widens them.
- Built-in Steps and built-in Hooks (including Rigify) never compare `ctx.game`. A test scans the built-in code for `ctx.game ==`. User Hooks may check `ctx.game` freely.

## Hooks

- Hooks do not get `ctx.profile` in v1. What a Hook needs is in the bundle, so profiles can change freely without affecting the hook interface. Where a built-in Hook needs profile data, a Step writes it into the scene: the Face Key Roles go onto Body's shape keys (`record_face_keys`).

## Unknown Games

- `open_bundle` rejects a bundle whose Game has no profile: "This importer doesn't support <Game>. Update KKBP."

## Adding a Game

- An exporter, a profile module (which may extend an existing one), a Sample Card in `contract/sample-cards/`, and a Game list on any Step specific to the new Game.
- Shared Steps don't change unless the Game really behaves differently.
- The contract tests check that every Game in the schema has a profile and a Sample Card.
