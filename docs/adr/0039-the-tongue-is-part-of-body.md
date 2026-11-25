# The tongue is part of Body

[ADR 0020](0020-one-tongue-with-mouth-keys-and-bones.md) kept one tongue, the head's, weighted to the tongue bones, and made it a Part of its own: `tongue`, parented to Body, with its mouth keys driven from Body's. The user wants the tongue in Body, as the legacy importer had the head's tongue. The merge of the two game tongues stays as ADR 0020 describes it; only where the result goes changes.

- The importer no longer gives a mesh the `tongue` Part Role. A mesh with a `tongue` material is a `body` Part in the Body Pass, so `build_parts` joins it into Body with the rest of the head.
- `merge_rigged_tongue` finds the two tongues by their `tongue` Material Role instead of their Part Role, before `build_parts` joins them.
- Joining keeps the tongue's mouth keys: Blender merges shape keys by name, so each of Body's mouth keys moves the mouth and the tongue together, with no drivers.
- The `tongue` Part Role and `ch.tongue` are gone from the hook interface. Removing them is a breaking change, so the hook interface's major version goes up.
- The Rigify Hook's tongue rig reads the tongue bones' vertex groups on Body, and its mouth grid drives Body's keys alone.

## Considered Options

- **Keep ADR 0020's separate tongue Part**: a Hook could find the tongue by its Part Role, but the user wants one object, as in the legacy importer.
- **Join the tongue into Body but keep the `tongue` Part Role, with `ch.tongue` always None**: no hook interface major version, but a role that no Part ever has is misleading.
- **Remove the role (chosen)**: the Part Roles say what the import makes. The tongue's faces are still found by the `tongue` Material Role.

## Consequences

- The tongue's material is one of Body's, so the Hooks that work on Body's materials work on it too. Convert shaders converts it with Body's, and Outlines gives it Body's outline, as the legacy importer did with the head's tongue.
- A Hook that used `ch.tongue` or the `tongue` Part Role must find the tongue in Body by its `tongue` Material Role. A Hook that declares the old major version is skipped, with a warning.
- A `.blend` imported before this change still has its tongue Part, tagged with a role the importer no longer knows. Lookups by other roles ignore it.
- The ADR 0020 consequences about the tongue bones' rest positions, the weights and a mismatched rigged tongue still hold.
