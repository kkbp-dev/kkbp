# Joint corrections copy the games' own rules, as Studio applies them

Each game moves a set of correction bones every frame from the pose of the limbs: the elbow, knee, shoulder, hip and buttock bones, the twist bones of the arms and legs, and the bust. The legacy importer had hand-tuned constraints and drivers for some of them, on KK only, written for those bones turned to point straight up, and some poses looked wrong (issue 10). The games' code is now read and copied: KK's and KKS's `ExpressionBone.LateUpdate` (decompiled; KKS's is KK's, constant for constant) and SVS's `HumanIndirectCorrection` (read from `GameAssembly.dll`'s machine code). [docs/design/joint-corrections.md](../design/joint-corrections.md) has the rules.

- The rules are data in the Game Profiles (`CORRECTIONS` in `profiles/kk.py` and `profiles/svs.py`), in the game's own terms: Unity's axes, its Euler orders, degrees, and each bone's local transform in its parent's units. They name bones exactly: nothing in the bundle marks the correction bones, as [ADR 0022](0022-kk-rigify-extras-gated-on-their-bones.md) already says for the legacy set.
- `profiles/corrections.py` evaluates them in plain Python. The exporters' correction probe (`"probe_corrections"` in the auto-export request, `scripts/probe-corrections.sh`) records what each game's own correction does to its Sample Card in 801 poses; the host tests hold the rules to that, and all three Games match to float32 precision.
- A Core Import Step (`joint_corrections.py`; it had an Import Option `joint_corrections`, on by default, until issue 99 removed it and every import runs the Step) rebuilds the rules as hidden helper bones, constraints and drivers in a hidden `Joint corrections (MCH)` collection. Every driver is a simple expression, so the rig works with Python scripts off, and stays under Blender's 256-character limit by keeping each input and value in a register bone. The in-Blender tests hold the drivers to the rules.
- The drivers match Studio: they give each correction bone the rules' value for the current pose, not the change from the bundle's rest pose. KK only runs `ExpressionBone` in Studio; in the maker, where the bundle is captured, the correction bones are where the maker's animation put them. So in KK and KKS the correction bones move by up to about a centimetre and five degrees as soon as the Character is imported, to where Studio would put them for that pose.
- The games work in each parent's unscaled units, which the rest pose leaves out ([ADR 0008](0008-bone-rest-poses-carry-no-scale.md)), so Schema Version 1.1 adds each bone's `game_scale`. A 1.0 bundle's bones count as unscaled.
- The bones keep the directions [ADR 0017](0017-bone-tails-from-the-game-rotation.md) gives them: helper bones on the game's own axes read and write the game's values, whichever way a Blender bone points. The Rigify Hook no longer turns the correction bones upright.
- Hooks that change the skeleton take the corrections off and build them again on the result: SFW, around the bones it deletes, and Rigify, on the generated rig, because the legacy Rigify scripts count bone children and re-aim bones. The Step keeps the rules and the game's rest poses on the armature and tags the bones they name, so the Hooks need neither the Game Profile nor the bundle's Ids.

## Considered Options

- **Keep and tune the legacy drivers**: no new machinery, but they would still be guesses, and SVS would still have none.
- **Drive the change from the bundle's rest pose**: the imported Character would look exactly as exported until posed, but every pose would be off from Studio by the maker animation's difference, and Studio is where KK Characters are posed.
- **Python drivers calling the rules**: one short driver per channel, but they need auto-run scripts and the add-on, and are slow.
- **Bake the corrections into shape keys or an action**: they only work for the poses baked.

## Consequences

- Where the rules read a position, Blender's is used. The game shears a bone turning under a parent with an uneven scale (the KK Sample Card's forearms), and Blender bones, which carry no scale, turn rigidly; the hand correction can differ by a few millimetres at extreme wrist bends.
- A correction bone copies its target, so it can't be posed by hand while the corrections are on. Turning the Import Option off leaves them free.
- Left out: KK's breast colliders (`cf_d_hit_bust`, never exported) and SVS's skirt corrections (`HumanIndirectCorrection.Skirt`), which would fight the skirt's physics.
- A new Game, or a game update that changes the rules, needs the probe run again and the rules updated until the host tests pass.
