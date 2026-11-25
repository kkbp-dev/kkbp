# Tear and gag-eye meshes rest hidden inside the head

The tear meshes (`cf_O_namida_L`, `_M`, `_S`) and the gag-eye meshes (`cf_O_gag_eye_00` to `_02`) are written with their basis pushed back inside the head, by half the depth of the face mesh, so they rest in the middle of the head. (At first the push was the whole depth, which left them poking out through the back of the head.) Each gets one exporter-made shape key, `Tears big`, `Tears med`, `Tears small` or `Gag eye 00` to `Gag eye 02`, that moves it forward to where the game shows it.

The basis is also half as wide, narrowed towards the middle of the face from left to right, and the showing key widens it again. The head narrows towards its back, so at full width the meshes came out through its sides there: on the SVS Sample Card 68 of the gag eyes' 248 vertices and about half of each tear mesh's were outside the head mesh, by up to 13.5 mm, and on KK and KKS 6 of each gag mesh's 240 by 2.3 mm. At half width none is, and the nearest is 4 mm inside.

Raising the key shows the mesh; at 0 it is out of sight. The expression keys on these meshes are baked from that hidden basis, so they add to it.

## Considered Options

- **Write the meshes where the game shows them and let the importer hide them**: every mesh stays at its game position, but the importer has to know which meshes these are and invent the keys, which is the game knowledge [ADR 0002](0002-exporters-write-game-meaning.md) keeps out of it.
- **Hidden basis plus a showing key, made by the exporter (chosen)**: it is what the legacy importer built, so the result matches the Phase 0 baseline, and the importer only loads shape keys.

## Consequences

- These meshes are the one exception to "vertex positions are the capture pose" ([ADR 0006](0006-every-mesh-skinned-at-scene-root.md)).
- The keys are in `expressions.json` like any other, with categories `tears` and `gag` and no game name.
- A gag-eye expression names the gag mesh it needs, and the importer drives that mesh's key from it.
- No expression shows the tear meshes, so the user moves them. The importer gives Body the tears' showing keys (`Tears big`, `Tears med`, `Tears small`), which move nothing on Body and drive the tears Part's keys of the same name, so the tears are keyed with the rest of the face. A showing key Body has gets no driver from an expression.
