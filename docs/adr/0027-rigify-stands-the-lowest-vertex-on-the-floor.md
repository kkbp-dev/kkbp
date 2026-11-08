# The Rigify Hook stands the lowest visible vertex on the floor

The legacy Rigify script put the feet on the ground by putting the root bone 4 cm under the left ankle IK bone and moving the whole rig, with the meshes on it, so the root sat at the world origin. The 4 cm is a guess at the ankle's height above the sole, and it doesn't hold: measured on the KK golden sample, the legacy import and the port both left Body's lowest vertex 6 mm under the floor and the shoes 19 mm under it. Before the Hook runs, the shoes already stand on z = 0 (+0.2 mm), because the export uses the game's floor. The user chose to ground the Character by its geometry instead: the rig moves so that the lowest vertex of the visible meshes on it is at z = 0, and the root bone goes there too.

## Considered Options

- **Legacy's ankle rule (rejected)**: sinks the Character by however far its sole is from 4 cm under the ankle; 1.9 cm on the KK sample.
- **Keep the export's height (rejected)**: no move at all, as the game places the Character, but it relies on every export using the game's floor at 0.
- **Lowest visible vertex at 0 (chosen)**: whatever the Character stands on (shoes or bare feet) touches the floor, whatever the export's floor is.

## Consequences

- Only meshes parented to the rig and visible count, so the Outfits in hidden collections don't decide the height; a pose or accessory that reaches below the feet does.
- Every rig bone sits a constant height away from the legacy rig's; the legacy comparison's `grounded` cause covers it.
- The rig's widgets aren't moved, as in legacy.
