# The Rigify Hook is rewritten in the importer's style, and a rig fingerprint shows the rig is unchanged

ADR 0023 ported the legacy importer's Rigify scripts with as few changes as possible: `before.py`, `after.py` and `commons.py`, about 4,000 lines bound to the Character through a module-level `legacy.py`. They have since been rewritten to the rest of the importer's standard: the Hook hands a `RigBuild` (`build.py`) to each phase of `metarig/` (the metarig, before Rigify generates the rig) and `finish/` (the generated rig), every name the rig uses is in `names.py`, the left and right eyes, limbs and fingers are written once with their real differences as data, constraints and drivers go through keyword helpers (`constraints.py`, `drivers.py`), bone collections through `bone_collections.py`, and modes change only in `editing()` blocks. `before.py`, `after.py`, `commons.py` and `legacy.py` are gone.

The user decided the rewrite must leave the rig as it was: every bone, constraint, custom property, driver and name the legacy rig had, which animators and saved actions use. The importer snapshots can't show that, as they record bone positions and only the counts of drivers and constraints. So the harness gained a rig fingerprint (`run.py fingerprint`): the metarig as handed to Rigify and the finished rig, with every collection, bone and pose bone setting, Rigify type and parameter, constraint setting in stack order, driver (expression and variables), the meshes' vertex groups and shape keys (hashed), the widgets and the Hook's log. Its baseline was recorded from the commit before the rewrite on both Blender builds and all three Golden Samples, and every commit of the rewrite was compared with it exactly.

## Considered Options

- **Keep the port (ADR 0023) and only tidy it**: least risk, but the code stays a legacy script with module state, positional helpers of up to 30 arguments and every eye written twice.
- **Rewrite on Bone Roles with new rig names**: what ADR 0023 turned down for breaking the names animators use; still turned down.
- **Rewrite in the importer's style, same rig, checked by a fingerprint (chosen)**: the code reads like the rest of the importer, and the fingerprint makes "same rig" a check rather than a hope.

## Consequences

- One log line changed: on a Body without one of the eye keys the emotion grid stops where it always did, but says which key is missing instead of passing on Blender's error (SVS's Golden Sample). A later change made the grid whole on such a Body: a missing key is skipped and logged, and the rest is made.
- The bone-name tables can't be changed: the legacy scripts removed names from them for a Character without a tongue or Better Penetration bones, and the next Character imported in the same session got a different rig. Each Character now works on its own copies; a first import's rig is unchanged.
- What looked wrong but was kept, so the rig stays the same, for later changes:
  1. SVS's emotion grid stopped partway, because the eye drivers assumed all four eye keys. Since fixed (above).
  2. The skirt is found by the game's indexed names, `cf_d_sk_top` and all 48 of `cf_d_sk_00_00`…`cf_j_sk_07_05`, so a skirt with another bone count gets no skirt rig. The design doc said Bone Group `skirt` and the bone tree; it now says what the code does.
  3. Only the left elbow's front and back joint-correction bones get a 180° roll (`metarig/limbs.py`, `_arm`); every other limb edit is mirrored. Seen by reading; not checked in the UI.
  4. The driver variable `headdDistX_R` kept its typo, since renaming it would break an animator's driver that copied it. It went with the emotion grid, which the face rig replaced (ADR 0058).
  5. A test that was never true, `bone.parent == targetToChange`, compared a pose bone with a name, so raw-copy bones parented to a limb bone never got `relink_constraints` or `parent_bone`. It was removed as dead code; if its intent holds, the fix changes those bones' parents on the rig.
  6. `cf_s_siri_L` and `_R` were set to deform on `data.bones` while in Edit Mode, which leaving Edit Mode overwrote. They deform anyway because the meshes are weighted to them, so the line was removed as dead code.
- A later change to the Rigify Hook that must keep the rig records a fingerprint baseline first ("Rig fingerprint" in the harness README); one that changes the rig on purpose re-records the importer snapshots as usual.
- ADR 0023 still holds for the names: the rig keeps the legacy importer's bone names, by Bone Role through `bone_names.py` and by exact name in `names.py`.
