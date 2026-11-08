# Expression Names are display names, matched by pattern position

An Expression Name is the shape key name a user sees in Blender, such as `Eye Happy`, `Mouth Happy (Broad), Closed` or `Gag Heart Eyes`, not a machine id. The name starts with its category: `Eye`, `Mouth`, `Eyebrow`, `Gag` for gag-eye expressions, or `Tears`. A closed version adds `, Closed`. One look has one name across every Game; where KK and SVS name the same look differently, KK's spelling wins.

The per-Game translation tables find a pattern by its category and its position in the game's pattern list, not by the name the game shows. KK reads pattern names from its list data, and translation mods change them: the KK sample shows `デフォルト` next to English names.

## Considered Options

- **Machine ids (`eye.happy.closed`) with a separate display label**: easy for code, but every shape key then needs a second lookup to get a readable name, and Hooks and users would see two names for one thing.
- **Display names (chosen)**: the importer uses them directly as shape key names, and they read the same in the contract, in Blender and in Hooks.
- **Keying tables on the game's displayed name**: breaks as soon as a translation mod or a game update changes the text.

## Consequences

- The closed set of Expression Names is a list of English display strings, and renaming one is a contract change.
- Table entries record the game's own name for reference only; it is never used for matching.
- Some names change from today's importer (SVS `Fire Eyes` becomes `Gag Fiery Eyes`, `Cat` becomes `Catlike`). Phase 6 approves these as differences.
- A pattern a table doesn't name keeps its game name and has no Expression Name.
