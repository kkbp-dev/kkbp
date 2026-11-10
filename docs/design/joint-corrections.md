# Joint corrections: what the games do

Research for issue 10. Nothing here is implemented yet; the open decisions are at the end.

Each game moves a set of "correction" bones every frame, after animation, from the pose of the limb bones. The importer's present drivers (`builtin/rigify/prepare.py`, `_joint_corrections`) are hand-tuned guesses at this. This note records the games' real rules.

## Where the code is

| Game | Class | How it was read |
|---|---|---|
| KK | `ExpressionBone.LateUpdate` in `Koikatu_Data/Managed/Assembly-CSharp.dll` | `ilspycmd -t ExpressionBone` |
| KKS | the same class in `KoikatsuSunshine_Data/Managed/Assembly-CSharp.dll` | decompiles to the same code as KK, constant for constant |
| SVS | `Character.HumanExpressionBone.LateUpdate` calls `Character.HumanIndirectCorrection.OnUpdate`, which runs eleven `Correction()` methods | IL2CPP: method addresses from `LibCpp2IL` (in `BepInEx/core`), then `objdump` of `GameAssembly.dll`, constants read from `.rdata` |

The SVS rules below are a hand reading of x64 disassembly. They have **not** been checked against the running game yet.

KK only gives a Character its `ExpressionBone` in Studio (`ChaControl.InitializeExpression`, called from Studio's `AddObjectFemale` and `AddObjectMale`). In the maker and the main game the correction bones are moved by the animations alone, so a KK bundle's rest pose holds the maker animation's values, not the rules'.

The KK rules are checked: the exporter's correction probe (`"probe_corrections"` in the auto-export request) ran 801 poses in the game on the KK Sample Card, and `profiles/corrections.py` with `profiles/kk.py` reproduces every corrected bone to float precision (positions within 1e-6, rotations within 0.06°).

Both games use `ConvertRotation` for Euler angles, in degrees. `e(order, bone)` below is `ConvertDegreeFromQuaternion(order, bone.localRotation)`; order `zyx` means the quaternion is `Rz * Ry * Rx`. Positions are `localPosition`, in the parent's unscaled units.

## KK and KKS

Left side shown; the right side mirrors the signs as noted. `sin` and `tan` take the value in radians exactly as written (degrees times a small factor).

| Part | Input | Output |
|---|---|---|
| Shoulder | `p` = `cf_j_forearm01` position in the frame of a point 0.3 above `cf_j_shoulder`; `a = abs(p.y)`, `b = abs(p.z)`, `d = max(0, 0.3 - a)` | `cf_d_shoulder02`: pos.x = `cf_j_arm00`.pos.x − d·0.03 − b·0.03 (right: +, +); pos.y = d·0.2; pos.z = −p.z·0.06; rotation (`yzx`): y = p.z·50 (right: −), z = −d·250 (right: +) |
| Upper arm twist | `x = e(zyx, cf_j_arm00).x` | `cf_d_arm01/02/03` rot.x = −x·0.6 / −x·0.5 / −x·0.125 |
| Elbow | `y = e(zxy, cf_j_forearm01).y` | `cf_s_elbo`: rot.y = −y·0.5; pos.x = sin(y·0.015)·0.022; pos.z = (−0.25 + sin((y−1)·0.006)·0.18)·0.1 (right: − sin). `cf_s_elboback`: rot.y = −y·0.5; pos.x = −tan(y·0.0039)·1.2; pos.z = (0.3 − sin(−y·0.009)·7.6 − tan(y·0.0022)·16)·0.1 (right: sin(y·0.009), + tan) |
| Wrist | `v` = `cf_j_middle01` position in a frame at `cf_j_hand` with `cf_j_forearm01`'s rotation; `t = radians(max(0, v.y)·100)` | `cf_d_hand`: pos.x = −(0.25 − sin(t)·15)·0.1 (right: −(−0.25 + sin(t)·15)·0.1); pos.y = sin(t)·1.5 |
| Wrist twist | the point (−0.01, 0.01, 0) of `cf_j_hand` (right: +0.01), in `cf_j_forearm01`'s frame, x dropped | `cf_d_wrist` Euler x = angle from up, signed by z |
| Forearm twist | `x = e(zyx, cf_j_hand).x` | `cf_d_forearm02` rot.x = x·0.45 |
| Hip | `v` = `cf_j_leg01` position in the frame of a point (∓0.083, 0.4, −0.008) from `cf_j_waist02`, times −10; `k = 8.849 − v.y`; `n` = how far the knee is above the hip in `cf_j_waist02`'s frame, ÷ `cf_n_height` scale.y, × 10, never below 0 | `cf_s_leg`: pos = ((1 + v.x·0.2 + (abs(v.z·1.1) − k)·0.06)·−0.1, (1 + k·0.4 + v.x·0.2 + n·0.6)·0.1, (−v.z·0.2 + v.x·0.05 − n·0.4)·0.1); rotation `zyx`(v.z·6 − v.x·2 − n·5, −v.x·12 − v.z·3, −v.x); scale (1 + abs(v.z)·0.2, 1 + n·0.4, 1 + abs(v.z)·0.3 + n·0.3). `cf_d_siri`: pos = ((−0.7 + v.x·0.01 − abs(v.x·0.02) − abs(v.z·0.005))·0.1, (k·0.01 + abs(v.z·0.02) + v.x·0.04)·0.1, (−k·0.03 − (v.z − n·3)·0.03 − abs(v.x)·0.02)·0.1); scale.x = 1 + abs(v.z)·0.02, scale.y = 1 + n·0.01. A rotation is computed for `cf_d_siri` and thrown away. |
| Thigh twist | `y = e(zyx, cf_j_thigh00).y` | `cf_d_thigh01/02/03` rot.y = −y·0.75 / −y·0.5 / −y·0.25 |
| Knee | `x = e(zyx, cf_j_leg01).x` | `cf_s_kneeB`: rot.x = −x·0.5, rot.z = x·0.1 (right: −); pos.y = (−x·0.048 + sin(x·0.01)·1.1)·0.1; pos.z = (−0.6 − sin(x·0.0115)·4 + tan(x·0.0032)·5)·0.1. `cf_d_kneeF`: rot.x = −x·0.5; pos.y = (sin(x·0.012)·1.8 − tan(x·0.00335)·4.5)·0.1; pos.z = (0.4 + x·0.0125 − tan(x·0.0032)·4.5)·0.1 |
| Calf twist | `y = e(zyx, cf_j_leg03).y` | `cf_d_leg02` rot.y = y·0.5 |
| Bust | `e = e(zyx, cf_j_spine03)` | `cf_d_bust00`: rotation `zyx`(−0.35·e); pos.y = (−0.081 + e.x·0.003)·0.1; pos.z = e.x·0.0004 |
| Bust colliders | `cf_j_bust02` position and scale | `cf_d_hit_bust`: collider only |
| Neck accessory point | `e = e(zyx, cf_j_head)` | `a_n_neck`: pos.x = e.z·0.0002; pos.z = (−0.08 − e.x·0.002)·0.1 |

Where one Euler component is set, the bone's other two components are kept. The right-side hip formulas mirror several signs; take them from the decompiled source, not from this table.

### Against the present drivers

- The twist chains use other factors (0.75/0.5/0.25 on the arm against the game's 0.6/0.5/0.125) and `cf_d_thigh01` has none.
- `cf_d_leg02` follows the knee; in the game it follows the ankle (`cf_j_leg03`), and `cf_d_leg03` isn't corrected at all.
- `cf_s_elbo`, `cf_s_elboback` and `cf_s_kneeB` have no rotation; the game turns each by half the joint angle.
- The elbow and knee offsets are linear or squared in the angle; the game's are sums of `sin` and `tan`.
- `cf_s_leg` gets no scale, `cf_d_siri` no scale and only two of three position axes, `cf_d_bust00` nothing.
- The shoulder, wrist and hip corrections read rotations; the game reads where the elbow, middle finger and knee are.
- `cf_s_waist02` has four constraints and a driver; the game never touches it.

## SVS

`TransformHelper` wraps a bone: `translateX/Y/Z` set one `localPosition` component (× 0.1 when the helper is "scaled"), `rotateX/Y/Z` set one component of `localEulerAngles` (Unity's own order), `Angle` is `e(yzx, bone)`. Only the leg and skirt helpers are scaled.

| Class | Reads | Writes |
|---|---|---|
| `ArmBase` | `h = Angle(cf_j_hand)`, `a = Angle(cf_j_arm00)` | `cf_d_forearm_wrist` rot.z = h.z, rot.y = h.y. `cf_d_arm01/02/03` rot.x = a.x·−0.8 / −0.5 / −0.2. `cf_d_forearm01/02/03` rot.x = h.x·0.2 / 0.5 / 0.8. `cf_j_shoulder02` rot.x = a.x·0.7, rot.y = a.y·0.7, rot.z = a.z·0.7 when a.z < 0 on the left (> 0 on the right), else 0 |
| `ForearmBase` | `y = Angle(cf_j_forearm01).y`; `over(n)` = how far y is past n degrees in the bending direction (left: y − n when y > n; right: y + n when y < −n; else 0) | `cf_d_elboback`: pos.x = y·0.0005 + over(60)·0.0005; rot.y = y·0.25; pos.z = 0.03 ± y·0.0006 ∓ over(60)·0.0003. `cf_d_elbo`: rot.y = y·0.2 + over(90)·0.6; pos.x = y·−0.0002 − over(90)·0.0003; pos.z = −0.025 ∓ y·0.00003 ± over(50)·0.0004. `cf_d_forearm00`: pos.z = ∓over(90)·0.00033; rot.y = over(90)·0.095 |
| `LegBase` | `k = Angle(cf_j_leg01).x`, `f = Angle(cf_j_leg03)`, `t = Angle(cf_j_thigh00).y`, `a = Angle(cf_d_thigh00).x`; `o = max(0, k − 90)` | `cf_d_leg00` rot.x = o·0.05; `cf_d_leg01` rot.x = −o·0.05, scale.x = 1 + o·0.002; `cf_d_thigh03` scale.x = 1 + o·0.004, pos.z = max(0, k − 60)·0.0025. `cf_d_kneeB`: pos.z = −0.3 − k·0.005 + o·0.01; pos.y = k·0.005 + o·0.005; scale.x = 1 − o·0.002; rot.x = k·0.25. `cf_d_kneeF`: pos.z = 0.322 − k·0.001 + o·0.001; pos.y = −k·0.003 + o·0.001; rot.x = k·0.6. `cf_d_leg03` rot = (f.x·0.1, f.y·0.9, f.z·0.1); `cf_d_leg02` rot.y = f.y·0.4. `cf_d_thigh01/02/03` rot.y = t·−0.8 / −0.5 / −0.2. When a < −80: `cf_d_thigh00` pos.z = (a + 80)·0.008, pos.y = −(a + 80)·0.003, scale.y = 1 − (a + 80)·0.0017. All positions here × 0.1 |
| `ThighBase` | `x, z` of `Angle(cf_j_thigh00)` | `cf_d_hipleg1`: pos.x = z·0.0003 ∓ 0.0845 (left −); pos.y = (−x ∓ z)·0.0007 + 0.0315; rot.x = x·0.66; rot.z = z·0.66. `cf_d_hipleg2`: pos.x = z·0.001 ∓ 0.041; pos.y = x·0.0014 − 0.0773 ∓ z·0.0005; pos.z = 0.0711 − x·0.00148 ± z·0.0013. Then runs `HipBase` |
| `HipBase` | `x, z` of `Angle(cf_j_thigh00)` | `cf_d_siri`: pos.x = ±(z·0.0002 − 0.053) (left +); pos.y = −0.03 ∓ z·0.0001 − x·0.0001; rot.z = z·0.25; rot.x = (x + 1)·0.45; pos.z = −0.01 − x·0.0001 ± z·0.0001, and when x < −80: −0.01 − (x + 80)·0.0003 − x·0.0001 ∓ z·0.0001 |
| `HipC` | `cf_d_siri_L` and `_R`: `Angle.x`, pos.y, pos.z | `cf_d_siri_C`: rot.x = (xL + xR)·0.4; pos.y = (yL + yR)·0.5; pos.z = (zL + zR + 0.0594)·0.25 − 0.01. `cf_d_ana`: pos.y = (yL + yR)·0.1 − 0.0924; pos.z = (zL + zR + 0.02)·0.2 − 0.0296 |
| `BreastRoot` | `e = Angle(cf_j_spine03)` | `cf_d_bust00`: rot = −0.3·e; pos.y = 0.01 − e.x·0.0003; pos.z = abs(e.x)·0.0005 when e.x > 0, else abs(e.x)·0.0003 |
| `Skirt` | `Angle` of both `cf_j_thigh00` | the eight `cf_d_sk_NN_01` skirt roots: rot.x from the thigh's x (front bones take only the forward swing, back bones only the backward one, side bones half), rot.y = the thigh's y, rot.z from the thighs' z; `cf_d_sk_07_01` and `_01_01` rise by (−80 − x)·0.002 past 80° |

Two things in this reading look like bugs in the game and are kept as read: the sign of z in `HipBase` pos.z flips when x passes −80, and `LegBase` reads the angle of `cf_d_thigh00`, which nothing but an animation would turn.

SVS has no shoulder, wrist or hip rule that reads a position: every input is an Euler angle of one bone.

## What the bundle lacks

- **Scale.** The games work in each parent's unscaled units; the bundle's rest pose has every scale baked into the positions ([ADR 0008](../adr/0008-bone-rest-poses-carry-no-scale.md)). In the KK Golden Sample the rest offset of `cf_d_kneeF` is 0.89 of what the formula gives, `cf_s_kneeB` 0.81, `cf_s_elbo` 0.87: the body sliders. To reproduce the offsets the importer needs each bone's scale in the game.
- **The rest pose isn't the zero pose.** The Pass is captured in the maker's pose: `cf_j_arm00` is turned 2.5°, `cf_j_leg01` 1° (5° in SVS), `cf_j_forearm01` −7° in SVS. The corrections in the bundle's rest pose are the rules' values at those angles, so a Blender driver must give the rule's value at the current pose minus its value at the rest pose.

## Replicating it in Blender

- **Drivers with simple expressions.** Every rule needs only arithmetic, `sin`, `tan`, `abs`, `min`, `max` and a conditional, which Blender evaluates without Python, so the rig works with auto-run scripts off and with the add-on disabled.
- **Reading the game's Euler angles.** A driver variable reads a bone's rotation relative to its own rest pose, in its own Blender axes; the game reads the rotation relative to the parent, rest rotation included. A hidden helper bone under the same parent, resting on the parent's game axes and copying the limb bone's rotation, gives exactly the game's local rotation, in any Euler order. This works whichever way the limb bone itself points, so the upright rule of [ADR 0017](../adr/0017-bone-tails-from-the-game-rotation.md) can stay.
- **Reading positions** (KK shoulder, wrist, hip): a helper bone at the game's reference point with a Copy Location constraint to the elbow, finger or knee.
- **Writing.** The correction bones are aimed bones, a fixed turn from the game's axes, so each game axis maps to one Blender channel. The Rigify Hook's `_reaim` goes away with the old drivers.
