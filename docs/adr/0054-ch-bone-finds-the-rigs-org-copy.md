# `ch.bone(id)` finds a bundle bone in the rig by its Id, and prefers Rigify's ORG- copy

The first example in the hook interface aimed a camera at `ch.armature.pose.bones[bone.id]`. With Rigify on, which is the default, that raised `KeyError`: `ch.armature` is then the metarig, whose Role bones the Rigify Hook has renamed (`cf_j_neck` is `Neck`, D23), and the rig has no bone named by the Id either. The interface said only that the rig has "readable names", so a Hook had no documented way to get from a bundle bone to the bone it should pose or aim at.

Every bone already carries its bundle Id as the custom property `id` (glTF extras), and the Rigify Hook copies it onto the rig bones it made from each ORG- bone. One bundle bone can be several rig bones: on the KK Golden Sample `cf_j_hips` is `ORG-Hips`, `DEF-Hips` and `MCH-Hips`, and a tongue bone up to seven, three of them deforming. Hair and accessory bones are copied unchanged and keep the Id as their name.

Hook interface 2.1 adds `ch.bone(id)`: the name of the bone in `ch.control` that follows bundle bone `id`. It is, in this order:

1. `ORG-<id>`, or else the one `ORG-` bone carrying the Id (`ORG-Head`, a renamed one);
2. the bone named `id`: every bone without Rigify, and the bones Rigify copied unchanged;
3. the only bone carrying the Id (`Center`, `Left Eye`).

It returns None when no bone carries the Id (bones the import leaves out), and raises `CharacterError` if several do and none of the rules picks one, which no Golden Sample has.

The ORG- copy is chosen over the DEF- bone, which is what deforms the meshes, because ORG- has the bone's own rest pose and follows the pose: a DEF- bone of a B-Bone chain (`DEF-Left arm`, `DEF-Left arm.001`) is only one segment of it. On every KK and SVS Golden Sample bone that becomes more than one rig bone, one of them is an ORG- bone.

`ch.bone` returns a name, not a bone, like the rest of Character it looks up again on each call and so is safe across undo. The doc's example uses it, and its test imports a Golden Sample with Rigify on and off.
