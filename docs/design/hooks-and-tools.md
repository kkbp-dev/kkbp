# Built-in Hooks and tools

The Hooks that run after the Core Import, and the tools used on an imported Character. Terms are in [CONTEXT.md](../../CONTEXT.md); how Hooks are registered, ordered and switched is in [import-pipeline.md](import-pipeline.md). The decisions cited as D14 to D47 are in [README.md](README.md#hooks-and-tools).

## Hooks

The built-in Hooks are modules in `importer/kkbp/builtin/`. They run in the order of `BUILTIN_HOOKS` (`pipeline/steps.py`), each when its switch option says so.

| Order | Hook (name in `BUILTIN_HOOKS`) | Options | Default | Asset file |
|---|---|---|---|---|
| 1 | Fix body seams | `fix_seams` (bool) | on | none |
| 2 | Convert shaders | `convert_shaders` (choice): `off` "Eevee", `eevee_mod`, `cycles`, `cycles_classic`, `principled` | `off` | none: the variants are in `library.blend` |
| 3 | Separate meshes | `separation_type` (choice): `off` "One object per outfit", `by_material` "Separate all clothing" | `off` | none |
| 4 | Outlines | `use_outlines` (bool) | on | `outlines.blend` |
| 5 | Face cards | `use_face_cards` (bool) | on | `face_cards.blend` |
| 6 | SFW | `sfw_mode` (bool) | off | none |
| 7 | Rigify | `use_rigify` (bool) | on | `rigify.blend` |
| 8 | Separate Eyes | `separate_eyes` (bool) | off | none |
| 9 | Delete default scene | `delete_default_scene` (bool) | on | none |

Fix body seams comes first because it changes the body mesh the later Hooks work on. SFW comes before Rigify so the rig is built without the bones it deletes. Separate Eyes comes after Rigify so the new Parts are made on the finished rig. Delete default scene runs last, once every object the other Hooks add is in the file.

### Fix body seams (`seams.py`)

Merges the Body vertices of Material Roles `face` and `body` that sit on top of each other, keeping each face corner's custom normal (D16).

### Convert shaders (`shaders.py`)

Swaps the materials of the body, hair, clothes and alternate clothes to another shader variant with `templates.swap` (D18). The tears and gag eyes keep their own templates.

- `eevee_mod`: the eyebrows, eyes, upper eyeline and eye whites keep the Eevee shader and are always lit; the face and body normals are reset so no seam shows at the neck.
- `cycles` and `cycles_classic`: the eyelines and eyebrows draw without shadows, and the eyelines move forward a little so they don't sink into the face.
- `principled`: a `.Principled` variant group, a very simple material.

### Separate meshes (`separate.py`)

With `by_material`, splits each `outfit` Part into one Part per material, named by material Id (D17).

### Outlines (`outlines.py`)

Gives the body, hair and clothes a Solidify modifier and a black outline material for each of their materials (D19). The face outline mask is chosen by the face material's template, and Body's modifier has no thickness where the mask hides the outline (D57). The outline materials get a black viewport colour. The Hook skips itself for the Cycles and Principled shader variants, which draw outlines badly.

### Face cards (`face_cards.py`)

Adds 2D eye and mouth cards in front of the face, in a Collection that starts hidden, with Part Role `face_card` (D20). Each image node tries its Material Roles in order, and a node none of them fills is unlinked (D63).

### SFW (`sfw.py`)

Deletes the vertices and bones of Bone Group `nsfw` and, by exact name, the nipple and breast bones listed under "Bones found by name" (D21).

### Rigify (`rigify/`)

Turns the armature into a hidden metarig (still `ch.armature`), generates a Rigify rig with Part Role `rig`, and moves the meshes onto it (D22). Rigify is enabled for the session only; preferences are never saved. The code is a `RigBuild` handed to the phases of `metarig/` and `finish/`, with every name in `names.py` ([ADR 0043](../adr/0043-rigify-rewritten-and-checked-by-a-rig-fingerprint.md)).

- **Names.** The Role bones are renamed to readable names (`Left arm`, `Hips`) from a Bone Role table before generating (D23). Accessory bones called `root`, `torso` or `head`, and duplicate names, are renamed so they don't clash with Rigify's own. Every generated bone keeps its bundle Id in its `id` property.
- **Optional parts** are made when the skeleton has their bones: the skirt, the tongue, Better Penetration, the head and the male parts.
- **Bones.** The Hook re-aims the bones its rig needs ([ADR 0017](../adr/0017-bone-tails-from-the-game-rotation.md)), then connects and parents them. It adds eye, chest and butt bones, tracking bones and handle bones.
- **Eyes.** The eye controller and the Left and Right Eye vertex groups come from Bone and Material Roles (D25).
- **Hands.** The wrists are aimed and the palms made on every skeleton; SVS's fingertips and thumbs are aimed from their vertex groups ([ADR 0045](../adr/0045-every-skeleton-gets-aimed-hands-and-palms.md)). Finger rolls, the edits to the joint-correction bones and the nipple widgets run only when the skeleton has every joint-correction bone they name (D24, [ADR 0022](../adr/0022-kk-rigify-extras-gated-on-their-bones.md)).
- **Joint corrections.** The Core Import's joint corrections are put back on the generated rig ([ADR 0038](../adr/0038-joint-corrections-copy-the-games-rules.md)).
- **Tongue.** The single tongue is rigged on Body ([ADR 0020](../adr/0020-one-tongue-with-mouth-keys-and-bones.md), [ADR 0039](../adr/0039-the-tongue-is-part-of-body.md)).
- **Skirt.** Found by the game's indexed names, `cf_d_sk_top` and `cf_d_sk_00_00` to `cf_j_sk_07_05` (`names.skirt_bone`): all 48, or there is no skirt rig.
- **Teeth bones** (`metarig/teeth.py`, issues 42 and 99; every rig gets them). The faces with the `teeth` Material Role are split into an upper and a lower row by connected piece. Each row gets the controls `Teeth <row> L2`, `L1`, `C`, `R1`, `R2` (ends, halfway, middle) in the `Face (MCH)` collection. Under each mouth bone the teeth are weighted to, a control has a hidden bone that copies it and takes those weights, so the teeth follow the mouth bones exactly as they would without the controls.
- **Widgets.** Each Character gets its own widgets; the fixed widget meshes come from `rigify.blend`. The Bone Widgets collection becomes a hidden Junk collection that also holds the metarig.
- **Bone collections.** The rig's collections are built from the Core's (D7). Hair and accessory bones of later Outfits go in their own collections, from the Outfit tag `join_armatures` gives each bone (`kkbp_outfit`, D29). An empty, hidden `Custom` collection sits to the right of NSFW in the Rig Layers panel, for bones the user adds (issue 7).
- **Emotion grid** (`finish/emotions.py`). Mouth, eye and custom key controllers and their drivers, built from the Expression Names present. A key Body lacks is left out and named in the log, and the rest of the grid is made (issue 64). The mouth circle's first keys also go by `Mouth A`, `I`, `U`, `E`, `O`; where Body lacks the second keys of A, I and O, `Mouth Smiling`, `Mouth Hate, Closed` and `Mouth Serious` stand in (for SVS); a first key with no second stays at full instead of fading out.
- **Feet on the floor.** The lowest visible vertex goes on the floor ([ADR 0027](../adr/0027-rigify-stands-the-lowest-vertex-on-the-floor.md)); the bones move as edit bones.
- IK stretch is off.

With SFW on, the rig has no crotch, anus or nipple controls: the Rigify Hook names the bones SFW removes (`SFW_REMOVES` in `metarig/types.py`) and builds the rig without their controls when they are gone. Any other named bone that is missing fails the Hook (issue 55).

A change to the Hook is checked with the rig fingerprint (`run.py fingerprint`, in the [harness README](../../importer/tests/harness/README.md)).

### Separate Eyes (`separate_eyes.py`)

Moves the eye and eyebrow materials out of Body into new Parts with Part Roles `eyes` and `eyebrows`, in an `Eyes and Eyebrows <name>` Collection, parented to Body with their shape keys driven from Body's (D35, D60). The eyes Part takes the pupils, eye whites and eye lines: KK's and KKS's eyelines, and SVS's eyelash and eyelid materials. The Rigify eye UV-warp modifiers move with them. When it separates something, it also turns on the Cryptomatte Object and Material passes of every view layer of the scene, which the compositor needs to pick the Parts out (issue 102); it never turns them off.

### Delete default scene (`default_scene.py`)

Deletes Blender's startup cube, camera and light when every other object in the file belongs to an imported Character (D47).

## Tools

The tools are modules in `importer/kkbp/tools/`, with their operators in `ui/tools.py`. Each one finds its Character from the active object, goes through Character, `ch.bundle()` and the templates module, and writes generated files into the Cache (D26).

| Tool | Module | What it does |
|---|---|---|
| Edit Material, with Cancel, Reset and Save | `edit_material.py`, `bake.py`, `kkbp/shading/` | Swaps a material for an editable one that rebuilds the game's colouring from the bundle's textures and colours, through the profile's `EDIT` tables (D37 to D41). Save bakes light and dark with Eevee, in a scene of its own, into the original Light Dark material (D44). The dark-texture and saturation maths is whole-array numpy with no `bpy` (D42). Not available for SVS (D46) |
| Link Hair | `link_hair.py` | Puts every hair material of the object into edit and copies the active one's light and dark settings to them (D45) |
| Export Prep | `export_prep/` | Readies a Character without a rig for another program: one module per target (VRM, VRChat, Unreal, Koikatsu, no change), built by Bone Role; simplification by Bone Group; an atlas (D28) |
| The atlas | `kkbp/atlas/` | Export Prep's atlas: a layout and compositing part with no `bpy` (Pillow, tested with pytest) and a thin Blender part |
| Merge Weights | `merge_weights.py` | Gives the selected bones' weights to their parents and deletes the bones. In operator search, not on the panel |
| Import Animation, Snap IKs | `animation.py` | Puts a Koikatsu `.fbx` animation on the Rigify rig with KKBP's own retargeting, mapped by Bone Role (D34). Snap IKs snaps the IK controls to the FK pose |
| Run Hook | `run_hook.py` | Runs any Hook on an imported Character, for example Rigify on one imported without it (D30) |
| Bulk Import | `bulk_import.py`, `bulk_import_script.py` | Imports every bundle folder in a folder, one background Blender each, through `kkbp.import_bundle`, and saves `<folder>.blend` (or `Error - <folder>.blend`) beside it (D36) |

The importer removes only what it made: it never purges the user's orphan data, and it leaves viewport shading and other UI state alone.

## How Hooks and tools find things

Nothing is found by an object, material, node, socket or image name.

### Objects and materials

| What | How it is found |
|---|---|
| The body, hair, clothes, alternate clothes, armature, rig, gag eyes, tears | `ch.body`, `ch.hairs`, `ch.outfits`, `ch.alt_outfits`, `ch.armature`, `ch.rig`, `ch.gag_eyes`, `ch.tears` |
| The tongue | Body's faces with Material Role `tongue` |
| Face and body materials | Material Roles `face`, `body` |
| Eyelines and eyebrows | Material Roles `eyeline_upper` (else `eyelash`, SVS), `eyeline_shadow`, `eyeline_lower`, `eyebrow` |
| Eyes and eye whites | Material Roles `eye_l`, `eye_r`, `eye_white` |
| Glasses | Blend Mode `glasses` from the bundle |
| An edit material's texture group | the template's `copies`, named after the edit material ([ADR 0025](../adr/0025-edit-materials-copy-their-texture-group.md)) |
| Which edit template a material takes | the profile's `EDIT["templates"]`, by Material Role (D38) |

### Nodes, sockets and images

| What | How it is found |
|---|---|
| A material's shader variant | `templates.variant(m)`, changed with `templates.swap(m, variant)` |
| The light, dark, normal and alpha mask images | `templates.texture(m, "main", "light")`, `("main", "dark")`, `("normal")`, `("alpha_mask")`; slots `alpha_mask_bottom`, `permalight_mask` |
| Shader inputs | template params: `light`, `dark`, `light_alpha`, `force_visibility`, and per variant `fresnel`, `disable_permalight_mask`, `permalight_mask`, `sdf` (D18) |
| Whether a slot has an image | the slot holds an image tagged with the Character Key |
| The Outlines Hook's images (blank images, outline masks) | `outlines.blend`, through the Hook's asset description |
| The face cards' nodes and the eye white mask | role-named nodes in `face_cards.blend`, through its asset description; `tex.eye_white_mask` takes KK's or SVS's mask by the eye white's template ([ADR 0037](../adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)) |
| The bake's switches | the edit templates' params `toon_shading` and `use_normals` |
| The colour grade LUT (`Lut_TimeDay.png`) | `library.blend`, with the edit templates (extra `lut`) |
| An edit template's image slots | edit slots `main`, `color_mask`, `pattern_mask1`, … in the edit templates' descriptions |
| Pupil and highlight positions | the eye templates' `positions`, from the texture offsets and scales (D41) |

### Bones

Bones with a Bone Role are found by it. Bones without one are found by Bone Group and the bone tree where that is enough, and otherwise by exact name.

| Bones | How they are found |
|---|---|
| The body root (`cf_n_height`) | Role `body_root` |
| Hips, spine, chest, upper chest, neck, head | Roles `hips`, `spine`, `chest`, `upper_chest`, `neck`, `head` |
| Shoulders, arms, hands | Roles `left_shoulder`, `left_upper_arm`, `left_lower_arm`, `left_hand` (and right) |
| Legs, feet, toes | Roles `left_upper_leg`, `left_lower_leg`, `left_foot`, `left_toes` (and right) |
| Fingers | the 30 finger Roles |
| Eyes | Roles `left_eye`, `right_eye` |
| IK targets and poles | Roles `left_hand_ik`, `left_foot_ik`, `left_elbow_pole`, `left_knee_pole` (and right) |
| Tongue | Role `tongue_root` and its subtree: the chain is the single-child path, side bones by the sign of x |
| NSFW bones | Group `nsfw`; Better Penetration by its root's name (`cf_J_Vagina_root`) |
| Breasts | Roles `left_breast`, `right_breast` for `cf_j_bust01`; the rest by name |
| Eyebrows (for the eye controller) | Group `eyebrow`, with Roles `left_eye`, `right_eye` and `head` |
| The bones above the body root (Export Prep, Koikatsu target) | the bones between the skeleton root and `body_root` |

### Bones found by name

These have no Role, and no Group that marks only them. Each is written in the Hook that needs it (the Rigify Hook's `names.py`, the SFW Hook's own list) with a note saying why. They are an allowed exception to the rule above.

| Bones | Used by | Why by name |
|---|---|---|
| `cf_s_bust02`, `cf_j_bnip02root`, `cf_j_bnip02`, `cf_s_bnip01`, `cf_s_bnip025` (each side) | SFW, Rigify | The `breast` Group also holds the bust, and no Role marks a nipple |
| `cf_d_bust00`, `cf_j_bust02`, `03`, `cf_s_bust01`…`03` | Rigify | Only `cf_j_bust01` has a Role |
| `cf_j_siri`, `cf_s_siri`, `cf_d_siri` (butt) | Rigify | No Role or Group marks them |
| `cf_j_waist01`, `cf_j_waist02`, `cf_s_waist01`, `cf_s_waist02` | Rigify | No Role |
| `cf_d_sk_top`, `cf_d_sk_0N_00`, `cf_j_sk_0N_0M` (skirt) | Rigify | The rig needs each chain's place around the hips, which the game's index gives |
| `cf_s_index01`…`cf_s_little03`, `cf_s_thumb01`…`03` (SVS's finger weights, `names.game_finger_group`) | Rigify | No Role; their vertex groups give the fingertips (ADR 0045) |
| The joint-correction set: `cf_d_shoulder02`, `cf_d_arm01`…`03`, `cf_d_forearm02`, `cf_d_wrist`, `cf_d_hand`, `cf_s_elbo`, `cf_s_elboback`, `cf_s_forearm01`, `cf_d_siri`, `cf_d_thigh02`, `03`, `cf_s_leg`, `cf_d_kneeF`, `cf_s_kneeB`, `cf_s_leg01`, `cf_d_leg02`, `03`, `cf_s_waist02` (each side) | Rigify | They are what the game's own correction components move, and no Role or Group marks them |
| The deform bones: `cf_s_shoulder02`, `cf_s_arm01`…`03`, `cf_s_forearm01`, `02`, `cf_s_wrist`, `cf_s_hand`, `cf_s_thigh01`…`03`, `cf_s_leg01`…`03`, `cf_s_head`, `cf_s_neck`, `cf_s_spine01`…`03`, `cf_s_waist01` | Rigify | No Role |
| `cf_J_FaceUp_ty`, `cf_J_FaceBase` (head height, head mod) | Rigify | No Role |
| `a_n_heel` (heel) | Rigify | Group `helper` holds many others |
| `Eyesx`, `Eye Controller` | Rigify | Made by the Hook itself |

### Shape keys

Shape keys are found by Expression Name (`Eye Closed`, `Mouth Big A`), which is a display name matched by pattern position ([ADR 0004](../adr/0004-expression-names-are-display-names.md)). The SFW Hook removes `vagina.open` by its game name.
