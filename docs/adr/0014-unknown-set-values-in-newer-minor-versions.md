# Unknown set values are errors in a known minor version and warnings in a newer one

A value outside a closed set (a Bone Role, Material Role, Expression Name, …) in a bundle whose minor Schema Version this importer knows is a contract violation, so `open_bundle` reports it as an error. In a bundle with a newer minor version it is a warning, given once per value, and the value is kept as a plain string. The importer's own code compares roles with the values it knows, so an unknown one simply matches nothing.

## Considered Options

- **Always an error**: strict, but adding a member to a set is a minor bump by the Schema Version rules (adding AC adds a Game; a new expression adds an Expression Name), and the importer must accept every minor version of its major.
- **Always a warning**: lets exporter mistakes in today's version through to the scene.
- **Drop unknown values (treat them as no role)**: Bone Group is required on every bone, so there is nothing to drop it to, and Hooks written for a newer contract couldn't see the value.

## Consequences

- Hooks may see role and group strings that aren't in this importer's sets, but only in bundles from a newer exporter.
- An unknown Game is never accepted: without a Game Profile nothing can be imported, so it is always "This importer doesn't support <Game>. Update KKBP."
