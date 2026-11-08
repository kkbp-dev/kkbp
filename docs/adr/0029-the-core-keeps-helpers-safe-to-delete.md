# The Core keeps every helper safe to delete

The contract says a `helper` bone is safe to delete: nothing weights it or anything below it, and no physics chain uses it (export-bundle.md, ADR 0011). The body rules gave Bone Groups by name, so any body bone outside the `cf_j_`, `cf_s_` and `cf_d_` names and the face root was a helper, including bones with the whole skeleton or the face below them. In the three golden samples seven broke the rule: `BodyTop`, `p_cf_body_bone` (SVS `p_cf_sv_body_bone_00(Clone)`), `cf_n_height` (the `body_root`), `p_cf_head_bone` (SVS `p_cf_sv_head_bone_00(Clone)`), `cf_J_N_FaceRoot`, and SVS's `cf_n_siri01_L` and `_R`. Export prep's simplification drops helpers, and the Rigify Hook left `p_cf_head_bone` and `cf_J_N_FaceRoot` out of the rig, which the legacy rig had (the Phase 6 comparison).

The Core now checks the rule when it writes `skeleton.json`, after every Pass, because a body bone can have an Outfit's weighted bones below it. A bone a rule made a helper, but that a mesh weights, that has a weighted bone below it, or that physics uses at or below it, becomes `face` if every such bone is at or below the bone with the `face_root` Bone Role, and `deform` otherwise. The face root, not the face Bone Groups, decides, because the hair's weighted bones hang below the face root too.

## Considered Options

- **Name rules for the bones above the face root (rejected)**: it fixes these samples, but any other name the rule misses breaks the contract again.
- **The importer works around it (rejected)**: the Rigify Hook could pull Junk bones above face bones into Face (MCH), but the bundle would still call them safe to delete.
- **The Core enforces the rule for every adapter (chosen)**.

## Consequences

- `p_cf_head_bone` and `cf_J_N_FaceRoot` are `face`, so the Rigify Hook rigs them as legacy did; the root chain and `cf_n_siri01` are `deform`.
- The KK_Colliders plug-in's bones, which physics.json's colliders use, are `deform` instead of `helper` (13 in each KK and KKS sample).
- A Game Adapter's group for a bone can still change in the bundle, but only from `helper`.
