# Bone tails and roll come from the game's rotation, except for bones the rules make upright

glTF has no bone tails or roll ([ADR 0001](0001-gltf-instead-of-pmx.md)), so the importer sets them. Most bones are aimed along the game bone's local −Z axis, with its local +Y as the Blender bone's Z axis, which is the game's rotation turned −90° about its own X axis. That is what the legacy importer's bones amounted to: 485 of KK's 736 legacy bones are exactly this. The Game Profile lists the bones that point straight up instead, with roll 0, by Bone Role (the limbs, spine, head, fingers and IK helpers) and by Bone Group (eye, eyebrow, mouth outside the tongue, face under the face root, nsfw, hair, accessory). Skirt chains point at their next bone. No rule names a Game's bones.

## Considered Options

- **Keep the legacy importer's name lists** (about 40 `cf_d_`/`cf_s_` arm, leg and waist bones it turned upright, in each Game's profile): the baseline's bone directions would match, but the profile would hold the game knowledge [ADR 0002](0002-exporters-write-game-meaning.md) moves to the exporters.
- **Blender's own bone heuristics** (the glTF importer's Temperance or Fortune): no rules to keep, but the bones' axes would no longer be the game's, and animations and retargeting rely on them ([ADR 0008](0008-bone-rest-poses-carry-no-scale.md)).
- **The game's rotation, with role and group rules (chosen)**: the bones keep the game's axes, and the rules need only the bundle's tags.

## Consequences

- About 85% of the legacy bone directions are matched; the rest follow the rules and are listed in the baseline comparison.
- Aimed bones are the profile's `aim_length` long; the legacy lengths came from the PMX and can't be rebuilt.
- The Rigify Hook re-aimed the bones its legacy joint-correction drivers acted on, because those drivers were written for upright bones. Since [ADR 0038](0038-joint-corrections-copy-the-games-rules.md) the joint corrections work on the bones as this ADR aims them, and nothing re-aims them.
