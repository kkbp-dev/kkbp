# The Rigify Hook ports the legacy scripts and keeps their bone names

Partly superseded by [ADR 0043](0043-rigify-rewritten-and-checked-by-a-rig-fingerprint.md): the scripts are rewritten in the importer's style, with the same rig. The names below still hold.

The Rigify Hook is the legacy importer's own Rigify scripts (`rigify_before`, `rigify_after`, `commons`, about 4,000 lines), copied into `builtin/rigify/` and changed only where the new importer's rules require it. Their legacy `common` module becomes `legacy.py`, which answers through Character. Mode switches go through `editing`, and widget shaping uses the data API instead of transform operators. Rigify's own operators become property assignments, or Compat helpers where Rigify has no function to call. Before the scripts run, `prepare.py` gives the bones with a Bone Role the legacy importer's readable names (`Left arm`, `Thumb0_L`, `Center`; D23), as the legacy armature Step did. The names come from a table keyed by Bone Role in `bone_names.py`, shared with export prep.

## Considered Options

- **Rewrite the rig set-up on Bone Roles, with rig names from Ids** (`DEF-cf_j_arm00_L`): no legacy names anywhere, but weeks of work on thousands of hand-tuned constraints and drivers, and the generated rig would no longer match the baseline, the legacy documentation or the animation retargeting lists.
- **Port the scripts with as few changes as possible, keeping the legacy names (chosen)**: the rig's drivers and constraints match the legacy rig almost one for one (KK: 340 drivers against 340, 797 constraints against 806). Its controls keep names people animate with.

## Consequences

- The Core Import still names bones by Id (D9); only the rig and its metarig carry the readable names. Each bone keeps its Id in its `id` property, and its Outfit in `kkbp_outfit` (D29).
- The scripts still name the bones without a Bone Role (joint corrections, butt, breasts, skirt, tongue) by their game names. Each such name is in the Hook, as the user rule for legacy names asks.
- Where the D7 bone collections differ from the legacy armature's, `prepare.py` sorts bones back the legacy way by what they do (weighted, moving weighted bones, or neither). This covers Face, Face (MCH), Junk and the hair roots.
- Later Rigify work can replace the copied code piece by piece, against the `defaults` comparison.
