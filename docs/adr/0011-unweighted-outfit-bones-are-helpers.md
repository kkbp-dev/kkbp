# Unweighted hair and accessory bones are helpers

Body bones get their Bone Group from name rules. Bones that come with an Outfit's hair, clothes or accessories get theirs from the Pass's weights instead. Such a bone is a `helper` when no mesh in its Pass weights it, no bone below it is weighted, and no physics chain or collider uses it. Otherwise it is `hair` or `accessory`. The importer can then delete every `helper` bone without breaking the bone tree or a physics chain, as the legacy importer did with its "Junk" collection.

## Considered Options

- **Name rules for every bone**: stable, but hair and accessory items name their bones freely, so no rule can tell a bone that deforms the mesh from one left over in the item's prefab.
- **Weights for every bone**: the body skeleton is shared by every Pass and each Outfit weights it differently, so a body bone's group would change from Pass to Pass.
- **Weights for Outfit-owned bones only (chosen)**: these bones exist in exactly one Pass ([ADR 0009](0009-outfit-owned-objects-keyed-per-pass.md)), so their weights are known when they are captured.

## Consequences

- `helper` means "safe to delete" for every bone, whichever rule assigned it.
- Re-exporting with a different Outfit can change whether a hair bone is a helper, because the group follows that Outfit's meshes.
