# The Body is skinned with mirrored skin matrices

Blender's X Mirror in Edit Mode needs every vertex of Body to have a partner at exactly (-x, y, z). [ADR 0047](0047-the-exporter-makes-vertex-copies-one-and-mirrors-the-body.md) snapped the Body Pass positions that were within 0.1 mm of their mirror image, which left 600 KK, 1004 KKS and 112 SVS vertices out, around the shoulders, hips, waist and mouth.

The exporter's symmetry probe (`"probe_symmetry"`, `SymmetryProbe` in each adapter) wrote out how the Sample Cards' Body Pass meshes are skinned. It showed that:

- **The game's meshes are symmetrical**: in their own bind space the face, eyes, eyelines, eyebrows, teeth and body pair with a vertex within 0.1 µm of their mirror image. The exceptions are the KKS body's waist and crotch (1463 vertices up to 1 mm off; KK's body is symmetrical there), KK's around the anus (25, under 0.1 mm), SVS's crotch (11, under 0.3 mm) and the head tongue (6 in KK and KKS, 1 to 5 mm).
- **The weights are mirror images** but for a few vertices (34 on the KK body).
- **The skin matrices aren't.** A skin matrix is a bone's pose times its bind pose, and the pose the Character is captured in has its left and right joint-correction and eye bones apart by up to 0.6 mm where they carry vertices: `cf_s_thigh01` 0.6 mm, `cf_s_shoulder02` 0.5 mm, `cf_s_leg02` 0.34 mm, `cf_J_Eye08_s` 0.25 mm in KK, and SVS's head 10 µm off the middle.
- **The bones' own asymmetry doesn't matter**: bones up to 8.5 mm apart (KK's forearm twist bones) have bind poses that make up for it, so their skin matrices are mirror images. Mirroring the bones instead would have made the mesh less symmetrical, not more.

So each adapter makes the skin matrices of every readable mesh mirror images before it skins it (`AdapterKit.SkinMirror`): each left and right pair, found by names that differ in one L and R, gets the mean of one and the other's mirror image, and a bone with no pair the mean of itself and its own mirror image. A pair or bone whose change would move a vertex it carries more than 1 mm is left as the game made it, so a bone that is one-sided, or a physics bone that settled well off its partner, keeps its place. Shape keys are baked with the same matrices. The bones themselves are written as the game has them: only the mesh is mirrored, and its rest shape is up to about 0.3 mm from where the game's pose would put it.

Then the Core's Symmetry snaps what the game's mesh and weights leave, now up to 1 mm (and 0.5 mm onto X = 0).

## Results on the Golden Samples

Body Pass positions with an exact mirror image: KK 13891 of 13897, KKS 14524 of 14543, SVS 18766 of 18771. What is left is the tongue's six (the head tongue, and the rigged tongue the importer drops), three on SVS's head tongue, and in KKS a cluster of 13 on the crotch's middle line, 0.05 to 0.2 mm apart, where the game's mesh has more vertices on one side than the other, so no exact partner exists.

## Considered Options

- **Snap more of the Body Pass by distance or by mesh topology**: no game data needed, but it moves vertices away from what the skinning says without knowing why they are off, and by distance alone about 5 to 65 percent of the remaining vertices had no single clear partner.
- **Mirror the rest pose's bones**: the first suggestion. The probe showed the bones' asymmetry is matched by their bind poses, and the simulation made the mesh less symmetrical.
- **Put the game into a symmetrical pose before capture**: each Game would need its own way to drive its joint corrections from mirrored joints, and the eye and correction bones would still be the game's own.
- **Mirror the skin matrices (chosen)**: one Unity-free helper both adapters use, covered by the Core tests, and it doesn't touch a mesh the game made asymmetrical (its vertices just follow a mirrored pose).

## Consequences

- It runs on the Outfit Passes too, so clothes stay on a body that moved by up to 0.3 mm. Meshes the game doesn't let scripts read (KKS's clothes, SVS's clothes and nails) are baked by Unity at the game's pose and aren't mirrored; the Core's Symmetry still snaps the Body Pass ones.
- It runs only when the export doesn't keep the current pose (`current_pose`), which is the game's to keep.
- The head tongue's six vertices that the game made 1 to 5 mm off stay as they are.
- The probe stays in the adapters as a developer request, for checking this after a game update.
- In Blender, the glTF importer's rounding and the upper eyeline's shadow still kept X Mirror from some KK and KKS vertices; the importer puts both right ([ADR 0049](0049-the-importer-snaps-mirror-partners-and-lifts-the-upper-eyeline.md)).
