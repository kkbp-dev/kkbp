# Bone rest poses carry no scale

Each bone is written with the world position and rotation it has when the Pass is captured, and a scale of 1. Any scale on the game's transforms, from the character maker's sliders or KKABMX, is already in the mesh: the adapter takes vertex positions from the game's own skinning at the capture pose, and the Core computes the inverse bind matrices from the unscaled bones, so the skin reproduces those positions exactly.

## Considered Options

- **Keep Unity's local scale on every bone**: faithful to the game, but Blender's edit bones can't hold scale, so its glTF importer moves the scale into the pose. The imported rest pose would then differ from the game's, and every Pass would need its scales to agree.
- **Positions and rotations only (chosen)**: what the legacy PMX export amounted to, and what Blender can represent as a rest pose.

## Consequences

- A bone scaled in the game shows its effect in the mesh, not as bone scale. Scaling bones in Blender doesn't reproduce the game's sliders.
- Translations in `skeleton.json` and the `.glb` files are world offsets expressed in the parent bone's rotated frame, without the parent's scale.
- Bone rotations are the game's real ones, so animations and retargeting see Unity's bone axes.
