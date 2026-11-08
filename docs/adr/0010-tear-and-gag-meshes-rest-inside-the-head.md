# Tear and gag-eye meshes rest hidden inside the head

The tear meshes (`cf_O_namida_L`, `_M`, `_S`) and the gag-eye meshes (`cf_O_gag_eye_00` to `_02`) are written with their basis pushed back inside the head, by half the depth of the face mesh, so they rest in the middle of the head. (At first the push was the whole depth, which left them poking out through the back of the head.) Each gets one exporter-made shape key, `Tears big`, `Tears med`, `Tears small` or `Gag eye 00` to `Gag eye 02`, that moves it forward to where the game shows it. Raising the key shows the mesh; at 0 it is out of sight. The expression keys on these meshes are baked from that hidden basis, so they add to it.

## Considered Options

- **Write the meshes where the game shows them and let the importer hide them**: every mesh stays at its game position, but the importer has to know which meshes these are and invent the keys, which is the game knowledge [ADR 0002](0002-exporters-write-game-meaning.md) keeps out of it.
- **Hidden basis plus a showing key, made by the exporter (chosen)**: it is what the legacy importer built, so the result matches the Phase 0 baseline, and the importer only loads shape keys.

## Consequences

- These meshes are the one exception to "vertex positions are the capture pose" ([ADR 0006](0006-every-mesh-skinned-at-scene-root.md)).
- The keys are in `expressions.json` like any other, with categories `tears` and `gag` and no game name.
- A gag-eye expression names the gag mesh it needs, and the importer drives that mesh's key from it.
