# Golden Samples are made locally, from tracked Sample Cards

The three golden samples were committed Export Bundles: 165 MB of meshes and textures captured from the games, in Git LFS. They are no longer distributed. `contract/samples/` is ignored by git, and each developer makes their own Golden Samples with `scripts/export-sample.sh`, which exports the three Sample Cards in `contract/sample-cards/<game>.png` (now tracked) with Outfit 00 and physics on. The importer snapshots (`importer/tests/snapshots/<sample>.<core|defaults>.json`) stay committed and reviewable, so everyone's Golden Samples are checked against the same record.

Physics settles differently on every export. Between two re-exports of the same cards, bones moved up to 5.7 mm on KK's skirt, 21.8 mm on SVS's hair and 13.1 mm on SVS's buttocks, where the snapshot comparison allowed 1 mm. The Rigify rig carries these on: on the re-export that set the tolerance, an SVS hair bone's IK tail moved 32.3 mm. So the comparison gives bones that physics moves a tolerance of 3.5 cm (`importer/tests/harness/physics.py`) and keeps 1 mm everywhere else. A physics bone is one in the `skirt`, `hair` or `breast` Bone Group, one under `cf_j_siri_L` or `cf_j_siri_R`, or a descendant of either. In the Core Import plus built-in Hooks it is also a Rigify bone or widget made from one of those, or one of the Rigify Hook's breast and buttock handles. The buttock bones are named because no Bone Group or physics chain marks them: SVS's `physics.json` has no chains (its MagicaCloth isn't captured), and its buttock bones are in the `deform` and `helper` groups.

## Considered Options

- **Keep committing the samples (rejected)**: they were game content, and they made the repository large.
- **Local snapshots recorded from each developer's own samples (rejected)**: exact comparison, but scene changes would no longer be reviewable in commits.
- **Golden Samples exported with physics off, so bones reset to the same pose each time (rejected)**: no tolerance needed, but the samples would stop matching what users export by default.
- **Committed snapshots with a physics tolerance (chosen)**.

## Consequences

- History was rewritten: old samples are no longer available in Git LFS.
- A Game with no Golden Sample, for a developer without that game, has its sample tests skipped with a notice; the builder's synthetic bundles still cover the code.
- `export-sample.sh` writes `contract/samples/<game>.stamp`: one hash of the files under `exporters/`, `contract/schema/` and `contract/expressions/` it was made from, Markdown docs left out, so an edit to a README doesn't make a sample stale. `test-importer.sh`, `check-core.sh` and `check-bundle.sh` warn, without failing, when a stamp is missing or differs from the working tree.
- A real change under 3.5 cm to a physics bone goes unnoticed by the snapshot comparison. The headroom is small (32.3 mm seen), so a sample that settles further needs the tolerance raised, not the rule widened silently.
- The Koikatsu FBX walk the animation test used was game content too; the test now writes a synthetic walk at run time.
- A re-export after an exporter change is no longer committed. If it changes the imported scene on purpose, re-record the snapshots and commit those.
