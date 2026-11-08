# Meshes are exported as glTF, not PMX

The exporters write each Pass's mesh as a binary glTF 2.0 file (`.glb`) instead of PMX. glTF has an open, well-documented specification and Blender imports it natively, which removes the importer's dependency on the mmd_tools add-on and its PMX-specific quirks. PMX is an MMD format with sparse documentation and no native Blender support.

## Considered Options

- **Keep PMX and import it through mmd_tools**: the exporters already have a working PMX writer, but every Blender release risks breaking a third-party add-on we don't control, and PMX limits (name lengths, MMD conventions) leak into the importer.
- **glTF (chosen)**: needs a new mesh writer in every exporter, since no off-the-shelf glTF library supports all of KK (.NET 3.5, Unity 5.6), KKS (.NET 4.6, Unity 2019.4) and SVS (.NET 6 IL2CPP, Unity 2021.3).

## Consequences

- The exporters share one dependency-free glTF and JSON writer, checked against the Khronos glTF Validator.
- glTF has no bone tails or roll, so the importer owns bone direction rather than taking it from the file.
- An Export Bundle no longer contains a PMX that MMD users could open directly.
