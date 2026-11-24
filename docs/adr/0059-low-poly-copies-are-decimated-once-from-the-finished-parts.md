# Low poly copies are decimated once, from the finished Parts

The Low poly Hook (issue 129) gives each Outfit's clothes and hair a copy with fewer faces, so that animation plays back faster on slow computers. The user picks how many faces the copies keep from one Import Option, `low_poly`: Off (the default), Light (50%), Medium (25%) or Strong (10%). The copies go in a hidden `Low poly NN` Collection for each Outfit, and have no outline.

Each copy is made from the finished Part. The Hook runs after every Hook that changes the clothes and hair: Separate meshes, Outlines, SFW and Rigify. Only Delete default scene runs after it. The copy's faces are cut by a Collapse Decimate modifier evaluated alone, with the Part's other modifiers off, so it works on the rest pose. That result becomes the copy's mesh, and the modifier is removed. The copy keeps its vertex weights and the Part's other modifiers. It loses the Outline modifier and the outline materials' slots. It shares the Part's materials. It is a Part with Part Role `low_poly` and its Outfit number.

## Considered Options

- **A Decimate modifier left on the copy**: it could be changed after the import. But a modifier after the armature runs again on every frame, on the posed mesh, and that is the work the copy is there to save. A modifier before the armature still runs on every frame, because Blender evaluates the whole stack again when the pose changes.
- **Copies made before Outlines, so that Outlines skips them by their Part Role**: the copies would have no outline with nothing to remove. But SFW, Rigify and Separate Eyes would then work on them too. Rigify stands the lowest visible vertex on the floor (ADR 0027), and the rig fingerprint records every mesh's vertex groups, so the copies could change the rig.
- **Copies of the finished Parts, decimated once (chosen)**: no other Hook sees the copies, and the rig is the same with the Hook on or off.

## Consequences

- The amount can't be changed on the copies. Running the Hook again with Run Hook removes the Character's `low_poly` Parts and makes new ones at the preset chosen then.
- Shape keys don't survive the decimation. The sample Characters' clothes and hair have none. A copy made from a Part that has some has none, and the log says so.
- Each `Low poly NN` Collection carries its Outfit's number, as `Outfit NN` does (ADR 0055). Showing it in place of the Outfit's Collection still gives the body that Outfit's Body Textures.
- Bake leaves the copies out: they share the materials, and their faces would draw over the original's in the bake. Export Prep's atlas copy leaves them out too.
- The hook interface is 2.2, for the new Part Role.
