# Exporters write down what game data means; the importer doesn't work it out

The exporters tag bones with Bone Roles and Bone Groups, tag materials with Material Roles, and give expression shape keys canonical Expression Names. The importer finds what it needs only through these tags, never through a Game's own bone, material or shape-key names. The exporter reads the game's own structures and knows these things for certain. The importer could only reverse-engineer them, and that is how today's 66 game branches built up.

## Considered Options

- **Name tables in the importer's Game Profile**: fixes ship with an importer update alone, but every Game's naming quirks stay in the importer, and Hooks would need the profile to understand a bundle.
- **Tags written by the exporters (chosen)**: bundles describe themselves to the importer and to Hooks alike. Most importer code needs no game knowledge.

## Consequences

- Fixing a role or an Expression Name table needs an exporter release, not just an importer update.
- The role sets and Expression Names are part of the contract, so changing them follows Schema Version rules.
- The translation tables live as data files in `contract/expressions/` and are embedded into the exporters when they're built, so they can be reviewed without reading C#.
