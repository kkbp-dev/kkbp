# Character

How the importer and its tools find an imported Character's Blender objects. Terms are defined in [CONTEXT.md](../../CONTEXT.md).

## Identity

- Each imported Character gets a **Character Key**: a unique id generated at import and stored on every Part.
- The Key is the only thing that decides membership. Names and Collections don't count.
- The import still creates a Collection for the Character, for tidiness only. It is an asset, tagged with the Game, with the Card's picture as its preview (issue 131); the Card's data after the picture isn't kept. Each Collection the import and the Hooks make has an Outliner colour by what it holds, from the table in `collection_colors.py` (issue 130).
- Blender object names are for display only (for example "Chika Body"). Nothing looks an object up by name, and users can rename freely. Material and bone names are still bundle Ids.

## Part Roles

- Each Part carries exactly one Part Role from a closed set: `body`, `hair`, `outfit`, `alt_outfit`, `tears`, `gag_eyes`, `armature`, `rig`, `face_card`, `eyes`, `eyebrows` (the last two only after the Separate Eyes Hook), `low_poly` (only after the Low poly Hook).
- Outfit, alternate clothes and low poly Parts also carry their Outfit index.
- `ch.add_part` is the only way to tag an object, so the tagging rules live in one place.

## Interface

```python
Character.of(obj)            # the Character obj belongs to, or None
Character.all(scene)
ch.key / ch.name / ch.game
ch.body / ch.armature / ch.rig / ch.tears / ch.gag_eyes   # one each, or None
ch.control                   # ch.rig if there is one, else ch.armature
ch.bone(id)                  # the name of the bone in ch.control that follows bundle bone id
ch.hairs / ch.outfits / ch.alt_outfits                  # lists
ch.outfit(index)             # that Outfit's Parts
ch.parts(roles=...)          # filtered list
ch.add_part(obj, role, outfit=None)
ch.bundle()                  # reopens the Export Bundle this Character came from
```

- `ch.armature` is always the deform armature from the import. `ch.rig` is the Rigify control rig, or None. `ch.control` is for animation and posing tools.
- `ch.bone(id)` finds a bundle bone in `ch.control` by the `id` custom property every bone carries, preferring Rigify's `ORG-` copy, so a Hook can aim at or pose a bone with Rigify's rig or without it ([ADR 0054](../adr/0054-ch-bone-finds-the-rigs-org-copy.md)).
- Character only looks things up and tags Parts. Operations such as separating hair stay in Steps and Hooks.
- In the pipeline, `ctx.character` is the Character being imported.

## Materials and images

- Materials and images carry the Character Key and their bundle Id as custom properties.
- `ch.material(id)` and `ch.materials(...)` find them through those properties, never by name. Blender renames clashing materials (`cf_m_body.001`) when a second Character, or the same one again, is imported.

## Importing again

- Every import creates a new Character with a new Key, even if the same Character is already in the scene. The two exist side by side.
- Replacing an earlier import is a possible later tool, built on Character.

## Which Character a tool works on

- The Character of the active object.
- If the scene has exactly one Character, that one.
- Otherwise the tool asks the user to select an object of the Character they mean.
- Several Characters in one scene are supported. There is no hidden "current Character" setting.

## Lookup

- A Character holds only its Key. Parts are looked up on every access, because Blender undo invalidates any Python references being held to its data.
- Getters for single Parts raise a clear error naming every match if more than one object has that role (for example, after Shift+D on the body).
- A "Duplicate Character" tool that gives the copy a new Key is a later feature.

## Link to the bundle

- The Character stores its Export Bundle's path.
- `ch.bundle()` reopens the bundle for tools used after the import (edit material, bake, export prep). Nothing about the bundle's place is kept on the scene.
- If the folder has moved, `ch.bundle()` raises a clear error, and the panel offers to locate it again.

## Testing

- Character needs Blender, so its tests run in the headless Blender harness, not plain pytest.
- They use small hand-built scenes: tagged cubes, a duplicated body, two Characters with clashing material names, and an undo in the middle of a lookup.
- The full sample imports remain the regression check.
