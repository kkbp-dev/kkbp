# Ids are assigned per kind, from keys the adapter supplies

Meshes, materials and bones each have their own Id namespace. A mesh and a bone may share an Id, but two bones never do. The Game Adapter gives every object a source key that is stable within one export, such as its transform path. The Exporter Core turns each new key into an Id, and the same key always gets the same Id. That is how a bone that appears in several Passes keeps one Id.

The Id is built from the game name. Characters outside `A–Z a–z 0–9 _ . -` become `_`, runs of `_` collapse to one, and leading and trailing `_` are dropped. Case is kept. If nothing is left, the Id is the kind's prefix: `mesh`, `mat` or `bone`. On a clash the Core appends `_2`, `_3`, … in the order keys arrive, so the Ids are deterministic when the adapter's order is. The name part is shortened so that the whole Id, counter included, is at most 63 bytes.

## Considered Options

- **One namespace for the whole bundle**: Blender keeps objects, materials and bones apart anyway, so a shared namespace would only add counters for clashes that can never cause a problem.
- **Ids from names alone, without keys**: two different game objects with the same name in two Passes could not be told apart from one object seen twice.

## Consequences

- CONTEXT.md's "unique within one Export Bundle" means unique within its kind.
- Shape keys have no Id. They are addressed by their mesh's Id and their target name.
- Re-exporting the same Character gives the same Ids only while the adapter visits objects in the same order. Adapters must walk game objects in a fixed order.
