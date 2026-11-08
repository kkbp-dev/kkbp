# SVS's eye bones are its eye movers, cf_J_Eye_tx

The SVS adapter gives the `left_eye` and `right_eye` Bone Roles to `cf_J_Eye_tx_L` and `cf_J_Eye_tx_R`, which the game moves to turn the eyes; SVS has no `cf_J_hitomi_tx` bones, which carry the roles in KK and KKS. The Rigify Hook names the bones with those roles Left Eye and Right Eye (D23), so in an SVS rig `cf_J_Eye_rz` and the eyelid bones hang below Left Eye, where in KK Left Eye has no children. The legacy importer instead renamed SVS's eye-look targets, `EyeTargetL` and `EyeTargetR`, which nothing is weighted to, to Left Eye and Right Eye. The Phase 6 comparison showed the difference; the user checked the SVS rig in Blender and kept it as it is.

## Considered Options

- **Roles on the eye-look targets, as legacy (rejected)**: the same shape as KK's rig, but the roles would name bones the game doesn't move the eyes with, and it needs the SVS adapter changed and the sample re-exported.
- **Roles on the eye movers (chosen)**: the bundle says what the game does (ADR 0002).

## Consequences

- An SVS rig's Left Eye and Right Eye are `cf_J_Eye_tx_L` and `_R`; `EyeTargetL` and `EyeTargetR` stay ordinary bones in the metarig's Junk collection.
- The legacy comparison's `svs-eyes` cause covers the differences.
