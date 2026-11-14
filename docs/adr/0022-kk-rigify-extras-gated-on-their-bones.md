# The KK-only Rigify extras run when the skeleton has the joint-correction bones

The legacy Rigify set-up had parts only KK and KKS got: the joint-correction drivers and constraints the legacy armature Step added (copying the game's elbow, knee, shoulder, wrist, hip and butt corrections), the elbow, knee and wrist edits that use those bones, the palm bones and palm vertex groups, the finger rolls and the nipple widgets. One part only SVS got: a turned and smaller hand IK widget. Built-in Hooks never compare `ctx.game` ([game-profile.md](../design/game-profile.md)) and don't get the Game Profile, so the Rigify Hook decides with one test on the skeleton: the KK parts run when every bone the legacy joint-correction drivers and constraints name is in the bundle's skeleton, and the SVS part runs when one is missing. KK and KKS have all of them; SVS lacks seven (`cf_d_shoulder02`, `cf_d_wrist`, `cf_d_hand`, `cf_s_elboback`, `cf_s_leg`, `cf_s_kneeB` and their sides), so the result matches the legacy importer on all three golden samples.

## Considered Options

- **Each part runs when the bones it needs exist**: closer to the rule that Hooks look at data, not Games, but SVS would get a partial set of corrections and palm controls that nobody has checked, and the comparison with the baseline would gain differences no one has approved.
- **A Hook option for the KK parts**: lets a user switch them off, but its default would have to differ per Game, which a Hook can't know.
- **One test on the joint-correction bones (chosen)**: reproduces the legacy rigs, and the bone names it checks are the ones the drivers need anyway.

## Consequences

- The bone names the test checks are listed in the Rigify Hook with a note on why, like every other exact name it uses.
- A KK skeleton missing one of those bones (a mod, a future game update) loses all the KK parts, not just the ones that need that bone.
- Giving SVS its own corrections or palm controls later means a second set of bones to test for, not a Game check.
- [ADR 0045](0045-every-skeleton-gets-aimed-hands-and-palms.md) takes the wrist aiming and the palms out from behind this test, and removes the SVS-only hand IK widget turn.
