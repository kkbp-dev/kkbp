# The Rigify Hook aims the hands and makes palms on every skeleton

ADR 0022 put every KK-only part of the Rigify set-up behind one test, whether the skeleton has the joint-correction bones, to reproduce the legacy rigs. SVS lacks some of those bones, so its rig got none of the hand set-up. Issues 24 and 26 reported the result: the hand controls sat turned on the wrist and the fingers didn't work.

Measured on the SVS Golden Sample (2026-11-14), three things were wrong, none of them a matter of joint corrections:

- The wrist bone pointed straight up, 10 cm long. It has no child bone to aim it, so the Core Import left it at its default. KK's wrist is aimed across the hand by the code behind the gate. The legacy "SVS-only hand IK widget" turn was a workaround for this.
- Each finger's last bone, and the thumb's, pointed straight up too, for the same reason: SVS has no fingertip bone (KK has `cf_j_index04_L` and so on).
- The thumbs' rolls were Blender's defaults, so a thumb bent downwards like a finger, about 120° off the axis KK's thumb bends about.

SVS's fingers were skinned correctly all along: the weights are on `cf_s_index01_L` and so on, which follow the finger joints.

So the hand set-up no longer waits for the joint-correction bones:

- **Wrist:** aimed level across the hand, two thirds along its vertices, on every skeleton (the same code as KK's).
- **Palms:** the palm bones, their vertex groups cut from the wrist's, and the `super_palm` control, on every skeleton.
- **Fingers without the joint-correction bones:** the joints stay where the game has them. The last bone carries on the way the second points, as far as the fingertip's vertices reach. The thumb's three bones are rolled to bend level, towards the palm, as KK's do. KK's fixed rolls and its head positions taken from the vertex groups stay behind the gate: they were tuned on KK's hand.
- The SVS-only hand IK widget turn is gone, since the wrist it compensated for is aimed.

## Considered Options

- **Run all of KK's finger code on SVS**: it moves each joint to a fraction of its vertex group's bounds and sets rolls tuned on KK's hand. SVS's joints are already where the game bends them, so this could only move them off.
- **A gate per part, each on the bones it needs**: what the plan proposed. The wrist, palms and fingers need only bones every supported skeleton has (they have Bone Roles), so a test for them would never be false. The elbow, knee, shoulder and nipple parts keep ADR 0022's test, which names the bones they use.
- **Aim the hands and make palms everywhere (chosen)**.

## Consequences

- The KK and KKS rigs are unchanged (the rig fingerprint matches).
- SVS rigs change: the wrist, hand IK and finger controls lie along the hand, there are palm controls, and vertices of the wrist group near the fingers move to the palm groups. The rest pose is the same.
- `names.game_finger_group` writes the `cf_s_` finger bones' names: they have no Bone Role, and the Hook reads their vertex groups to find the fingertips.
- Nobody has posed an SVS hand in the viewport for this yet; the tests check the bones' directions and that a finger control bends its own finger.
