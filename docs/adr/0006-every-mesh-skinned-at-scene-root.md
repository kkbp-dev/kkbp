# Every mesh is skinned and sits at the glTF scene root

In each Pass's `.glb`, the bones form the node tree, and every mesh is a skinned mesh whose node sits at the scene root with no transform. A Pass has one skin listing all of its bones. A game mesh that isn't skinned in the game (a rigid accessory under a bone) is written skinned to that one bone with weight 1. The Exporter Core computes the inverse bind matrices from the bones' rest pose, and the adapter gives vertex positions already at that rest pose.

## Considered Options

- **Keep Unity's object tree, with rigid meshes under their bones**: closer to the game, but glTF clients ignore the transforms of skinned mesh nodes, the Khronos validator warns about skinned meshes that aren't at the root, and the importer would have to handle bone-parented and skinned meshes separately.
- **One skin per mesh, using that mesh's own bind pose**: Unity gives each mesh its own bind poses, so this needs no rebaking, but Blender would create one armature per skin and the importer would have to merge them.

## Consequences

- "The object tree" in a `.glb` is the bone tree; meshes are a flat list beside it.
- Blender's glTF importer builds one armature per Pass, and the importer joins Passes by bone Id.
- The adapter, not the Core, bakes meshes into the rest pose, because only it can read the game's bind poses.
