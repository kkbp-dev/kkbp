# Built-in Hooks and tools

The Phase 5 Hooks that run after the Core Import and the tools used after an import. Terms are in [CONTEXT.md](../../CONTEXT.md); the Hook mechanics are in [import-pipeline.md](import-pipeline.md).

Status: implemented in Phase 5 (decisions D14 to D47 in the [roadmap](README.md#phase-5-hooks-and-tools-needs-phase-4)). This file holds the inventories they refer to: every legacy piece and what happens to it, and every legacy name lookup and what replaces it.

## Hooks

| Order | Hook (name in `BUILTIN_HOOKS`) | Switch option | Default | Asset file |
|---|---|---|---|---|
| 1 | Fix body seams | `fix_seams` (bool) | on | none |
| 2 | Convert shaders | `convert_shaders` (choice): `off` "Eevee (no change)", `eevee_mod`, `cycles`, `cycles_classic`, `principled` | `off` | none: the variants are in `library.blend` |
| 3 | Separate meshes | `separation_type` (choice): `off` "One object per outfit", `by_material` "Separate all clothing" | `off` | none |
| 4 | Outlines | `use_outlines` (bool) | on | `outlines.blend` |
| 5 | Face cards | `use_face_cards` (bool) | on | `face_cards.blend` |
| 6 | SFW | `sfw_mode` (bool) | off | none |
| 7 | Rigify | `use_rigify` (bool) | on | `rigify.blend` |
| 8 | Separate Eyes | `separate_eyes` (bool) | off | none |
| 9 | Delete default scene | `delete_default_scene` (bool) | on | none |

The defaults are the legacy panel's. The legacy importer always added face cards, so their switch defaults to on.

## Legacy pieces

Ported means the behaviour comes over, rewritten onto `ctx`, the data API and the bundle's tags. Replaced means something else in the new importer does the job. Dropped means nothing does, for the reason given. Added means legacy had no such piece.

### `importing/postoperations.py`

| Piece | Verdict | Why / where |
|---|---|---|
| `hide_unused_objects`: Outfit, Alts and tears/gag Collections | Replaced | Core Step `arrange_collections` (Phase 4) |
| `hide_unused_objects`: hide the KK armature when Rigify is on | Ported | Rigify Hook hides the metarig on every Game |
| `hide_unused_objects`: hide the rigged tongue | Dropped | One visible tongue, in Body ([ADR 0020](../adr/0020-one-tongue-with-mouth-keys-and-bones.md), [ADR 0039](../adr/0039-the-tongue-is-part-of-body.md)) |
| `hide_unused_objects`: exclude the Hitboxes Collection | Dropped | Hit boxes are never exported |
| `hide_unused_objects`: exclude Bone Widgets | Ported | Rigify Hook |
| `apply_cycles` | Ported | Convert shaders, `cycles` and `cycles_classic` (below) |
| `apply_cycles`: `ignore_list` of `KK Eyebrows (mayuge) <name>` and the like | Dropped | Dead code: no material has those names, so nothing was ever skipped |
| `apply_cycles`: re-assigning the eyeline faces to `cf_m_eyeline_00_up` | Dropped | Each eyeline material has its own vertices now (approved Phase 4 difference) |
| `apply_eeveemod` | Ported | Convert shaders, `eevee_mod` |
| `apply_principled` | Replaced | A `.Principled` variant group swapped in like the others, instead of deleting every node but the light image |
| `apply_rigify`: enable Rigify and `save_userpref` | Ported, changed | Enabled for the session only; preferences are never saved |
| `apply_rigify`: `rigbefore`, `rigify_generate`, `rigafter` | Ported | Rigify Hook |
| `apply_rigify`: pivot point and face select mode | Ported | Rigify Hook, as legacy |
| `apply_sfw` | Ported | SFW Hook |
| `separate_meshes` | Ported | Separate meshes, `by_material` |
| `mark_body_freestyle_faces` | Dropped | Its call was already commented out |
| `apply_outlines`, `add_outlines_to_body`, `add_outlines_to_hair_clothes` | Ported | Outlines Hook |
| `import_face_cards` | Ported | Face cards Hook |
| `apply_viewport_colors` | Replaced | Core Step `set_viewport_colors`; the Outlines Hook gives its own materials a black viewport colour |
| `c.clean_orphaned_data()` | Dropped | It also purged the user's own orphan data; the importer removes only what it made |
| `set_viewport_shading('SOLID')` | Dropped | UI state an import shouldn't change, and there is no screen in the harness |

### `importing/importbuttons.py`

| Piece | Verdict | Why / where |
|---|---|---|
| Delete `Camera`, `Light` and `Cube` when they are the file's only objects | Ported | Delete default scene Hook: they go when every other object belongs to an imported Character, since it runs after the Core Import |

### `importing/modifymesh.py` and `importing/modifyarmature.py`

| Piece | Verdict | Why / where |
|---|---|---|
| `remove_body_seams` | Ported | Fix body seams |
| `create_eye_controller_bone` (Rigify only) | Ported | Rigify Hook, from Bone and Material Roles |
| `create_joint_drivers` (KK and KKS, Rigify only) | Replaced | The joint corrections Step copies the games' own rules on every Game, Rigify or not, and the Rigify Hook rebuilds them on the generated rig (D64, ADR 0038) |
| `rename_bones_for_clarity` | Ported, changed | Only the Rigify Hook renames, from a Bone Role table (D23); the Core keeps Ids (D9) |
| `modify_finger_bone_orientations` | Replaced | Core Step `orient_fingers_and_legs` (Phase 4) |

### `extras/rigifyscripts/`

| Piece | Verdict | Why / where |
|---|---|---|
| `rigify_before.main`: reserved-name and duplicate-name fixes | Ported | Rigify Hook (accessory bones can still be called `root`, `torso` or `head`) |
| optional features: skirt, rigged tongue, Better Penetration, head mod, male | Ported | From Bone Groups and the tongue bones' vertex groups on Body; see the name table |
| widgets: `createWidget`, `createEyeWidget`, `createEyesWidget`, `arrangeTripleWidgetSet` | Ported | Rigify Hook; the fixed widget meshes come from `rigify.blend` |
| eye, chest and butt bones, tracking bones, handle bones | Ported | Rigify Hook |
| `fix_bone_orientations`, `connectAndParentBones` | Ported | Rigify Hook, after it re-aims its bones (ADR 0017) |
| KK-only joint-correction bone edits, `relink_constraints` | Ported | Gated (D24) |
| The legacy drivers' axis swaps and `invert_y/z` | Dropped | Those drivers are gone (ADR 0038) |
| palm vertex groups, `finalizeFingerBones` rolls, `super_palm` (KK only) | Ported | Rolls gated (D24); palms on every skeleton, and SVS's fingertips and thumbs aimed (ADR 0045) |
| nipple widgets (KK only) | Ported | Gated (D24) |
| `finalizeRiggedTongueSideBones` and the tongue rig | Ported | Rigs the single tongue, in Body (ADR 0020, ADR 0039) |
| skirt rig (`getSkirtBoneName` indexes) | Ported | Found by the game's indexed names, `cf_d_sk_top` and `cf_d_sk_00_00` to `cf_j_sk_07_05`, all 48 or no skirt rig (`names.skirt_bone`) |
| layer setup (`RigifyLayer`, `BoneManagerLayer`, Charamaker, Toes, Face MCH) | Ported, changed | Rig collections built from the Core's (D7); the name-based splits D7 dropped stay dropped |
| a `Custom` collection for the user's own bones | Added | Rigify Hook: empty and hidden, to the right of NSFW in the Rig Layers panel (issue #7) |
| `rigify_after.main`: rename Metarig/Rig, move meshes and UV-warp modifiers to the rig | Ported | Rigify Hook, through Character (the rig gets Part Role `rig`) |
| `rigify_after`: copy bone `id`s to generated bones | Ported | Bones keep their Id in their `id` property |
| `rigify_after`: SVS-only hand IK widget rotation | Removed | The wrist it compensated for is aimed (ADR 0045) |
| `rigify_after`: hair/accessory bones of later Outfits in their own collections | Ported | `join_armatures` tags each bone with its Outfit, `kkbp_outfit` (D29) |
| `rigify_after`: IK stretch off | Ported | Rigify Hook |
| `rigify_after`: emotion grid (mouth, eye and custom key controllers and their drivers) | Ported | `finish/emotions.py`, from the Expression Names present; at a missing eye key the grid stops, as legacy's error stopped it, with a warning naming the key (ADR 0043) |
| `rigify_after`: feet on the ground, `origin_set` | Ported | The lowest visible vertex goes on the floor, not 4 cm under the ankle ([ADR 0027](../adr/0027-rigify-stands-the-lowest-vertex-on-the-floor.md)); the bones move as edit bones, without `origin_set` |
| `commons.fixJapChars`, `getContainedJapCharacters`, `loadJsonDictionaryFile` | Dropped | Bone names are ASCII Ids ([ADR 0005](../adr/0005-ids-per-kind-from-adapter-keys.md)) |
| `commons` constraint, driver and bone helpers | Replaced | `constraints.py`, `drivers.py`, `bones.py`, `bone_collections.py` and `meshes.py` in the Rigify Hook, with keyword arguments (ADR 0043) |
| `extras/rigifywrapper.py` ("Convert for Rigify" on an imported Character) | Replaced | The Run Hook tool runs any Hook on an imported Character (D30) |

### Tools

| Piece | Verdict | Why / where |
|---|---|---|
| `extras/editmaterial.py`: edit, reset, cancel, save | Ported | `tools/edit_material.py`, through `ch.bundle()`, the templates module and the profile's `EDIT` tables (D38–D41); the Backup material is dropped, Cancel replaces it (D44) |
| `editmaterial.create_darktex`, `saturate_texture` (numpy, threads) | Ported | `kkbp/shading/`, whole-array numpy with no `bpy` or threads (D42); the dark texture compares red with max(green, blue) as the shader does, where legacy's numpy compared it with green |
| `exporting/bakematerials.py` | Ported | `tools/bake.py`, Save's light and dark passes in a scene of its own; writes into the Cache (`kkbp_cache/baked/`). Its normal pass is dropped: the bundle's normal maps are already standard (D44) |
| `exporting/exportprep.py` | Ported | Export prep tool, by Bone Role and Group |
| `exporting/material_combiner/` (about 3,000 lines) | Replaced | KKBP's own atlas: a layout and compositing part with no `bpy` (Pillow, pytest) and a thin Blender part |
| `material_combiner/get_pillow.py` | Replaced | Phase 3's `pillow.py` |
| `extras/catsscripts/armature_manual.MergeWeights` | Ported | Merge Weights operator, data API; in operator search, not on the panel |
| `extras/catsscripts/common.py` (2,292 lines) | Dropped | Only Merge Weights used it |
| `extras/matcombsetup.py`, `matcombswitch.py` | Dropped | Glue for the removed material_combiner UI |
| `importanimation.py` (+ IK snap), Koikatsu FBX | Ported | Import Animation with KKBP's own retargeting by Bone Role (D34) |
| `importanimation.py`, Mixamo FBX | Dropped | D34 |
| `createanimationlibrary.py` | Dropped | D34 |
| `extras/animationlibrary/*.json` (Rokoko and ARP retargeting lists) | Replaced | The mapping comes from Bone Roles (D34) |
| `linkshapekeys.py` | Ported | Separate Eyes Hook: new Parts with Part Roles `eyes` and `eyebrows`, in an `Eyes and Eyebrows` Collection (D35, D60) |
| `linkhair.py` | Ported | `tools/link_hair.py`, on the edit templates' params; it puts every hair material into edit first (D45) |
| `bulklaunch.py`, `auto_import.py` | Ported | Bulk import: one background Blender per bundle folder through `kkbp.import_bundle` (D36) |
| `toggle_console` (animation tools) | Dropped | Windows-only console window |

## Legacy name lookups

Every legacy lookup by a bone, material, object, node, socket or image name, and what replaces it. "Role" is a Bone or Material Role, "Group" a Bone Group, "template" a Template Description lookup through `templates`.

### Objects and materials (every Hook and tool)

| Legacy | Replacement |
|---|---|
| `c.get_body()`, `get_hairs()`, `get_outfits()`, `get_alts()`, `get_armature()`, `get_rig()`, `get_tongue()`, `get_gags()`, `get_tears()` | `ch.body`, `ch.hairs`, `ch.outfits`, `ch.alt_outfits`, `ch.armature`, `ch.rig`, `ch.body` (the tongue is in Body), `ch.gag_eyes`, `ch.tears` |
| `'Body ' + c.get_name()`, `"Tongue (rigged) " + name` | `ch.body` for both |
| `c.get_material_names('cf_O_face')`, `('o_body_a')` | materials with Role `face`, `body` |
| `'KK cf_m_eyeline_down'`, `'KK cf_m_eyeline_00_up'`, `'KK cf_m_mayuge_00'` | Roles `eyeline_lower`, `eyeline_upper`, `eyebrow` |
| `'KK cf_m_hitomi_00_cf_Ohitomi_L02'` / `_R02`, `'KK cf_m_sirome_00'` | Roles `eye_l`, `eye_r`, `eye_white` |
| `'KK cf_m_face_00'` / `'SVS cf_m_head_00'`, `'KK cf_m_body'` / `'SVS cf_m_body_00'` | Roles `face`, `body` |
| `material.get('glasses')` | Blend Mode `glasses` from the bundle |
| `cf_O_eyeline` `up` / `kage` / `down` (face cards) | Roles `eyeline_upper` (else `eyelash`, SVS), `eyeline_shadow`, `eyeline_lower` |
| `cf_Ohitomi_L02`, `_R02`, `cf_Ohitomi_L`/`_R` + `sirome` (face cards) | Roles `eye_l`, `eye_r`, `eye_white` |
| `material.name.endswith('cf_m_body')`, `('cf_m_face_00')` (Eevee Mod) | Roles `body`, `face` |
| `body.active_material_index = 1` (Eevee Mod normal reset) | faces of Role `face` and `body` |
| `'Tex ' + name + ' ' + character` groups (edit material) | the template's `copies`, named after the edit material ([ADR 0025](../adr/0025-edit-materials-copy-their-texture-group.md)) |
| `remap_dict` (`cf_m_face_00` → `KK Face`, …, `o_tang` → `KK General`) | the profile's `EDIT["templates"]`, by Material Role (D38) |

### Nodes, sockets and images

| Legacy | Replacement |
|---|---|
| `nodes['shader']`, `nodes.get('shader')` | `templates.swap`; the template's `shader` |
| `nodes['_light.png']`, `['_dark.png']`, `['_NMP_CNV.png']`, `['_AM.png']`, `['_AMB.png']`, `['perma']` | `templates.texture(m, "main", "light")`, `("main", "dark")`, `("normal")`, `("alpha_mask")`, slot `alpha_mask_bottom`, slot `permalight_mask` |
| `inputs['Light image']` / `['Light texture']`, `['Dark image']` / `['Dark texture']` | new params `light`, `dark` |
| `inputs['Light image alpha']` / `['Light txture Alpha']` | param `light_alpha` |
| `inputs[0]` (force visibility) | param `force_visibility` |
| `inputs['Enable fresnel']`, `['Disable permalight mask']`, `['Permalight mask']`, `inputs[7]` (SDF) | new per-variant params `fresnel`, `disable_permalight_mask`, `permalight_mask`, `sdf` (D18) |
| `bpy.data.node_groups['.Cycles']` and the other variants | `templates.swap(m, variant)` |
| `images['Template: Black']` | `templates` (already kept in `library.blend`) |
| `images['Template: BlackWithAlpha']`, `['Template: Placeholder']`, `['KK OutlineMask.png']`, `['SVS OutlineMask.png']` | `outlines.blend`, through the Outlines Hook's asset description |
| `image.name != 'Template: Placeholder'` (has an image?) | the slot holds an image tagged with the Character Key |
| face card nodes `up`, `kage`, `down`, `_light.png` | role-named nodes in `face_cards.blend`, through its asset description |
| face card `Eye_White_Alpha` | `tex.eye_white_mask`, with KK's or SVS's mask by the eye white's template ([ADR 0037](../adr/0037-svs-face-cards-use-the-eyelash-and-their-own-eye-white-mask.md)) |
| `.Combine colors` `mix`, `.Tex*` `shade` (bake) | the edit templates' params `toon_shading` (the combine node's own input, so the shared group isn't changed) and `use_normals` |
| `Lut_TimeDay.png` | `library.blend`, with the edit templates (extra `lut`) |
| edit image nodes `_ST_CT.png`, `_CM.png`, `_PM1.png`, … in `.Tex *` groups | edit slots `main`, `color_mask`, `pattern_mask1`, … by path (`textures/_CM.png`) in the edit templates' descriptions |
| `set_uv_type` on `eyeshadowuv`, `nippleuv`, `underuv`, `hairuv` | set once in the edit templates' groups (`importer/tools/library/groups/`) |
| `.Eye Textures positioning` `eye_scale`, `Group`, `Group.001` (from the character JSON) | the eye templates' `positions`, from the texture offsets and scales (D41) |

### Bones (Rigify Hook, SFW Hook, export prep)

Bones with a Bone Role are found by it. Bones without one are found by Bone Group and the bone tree where that is enough, and otherwise by exact name, listed in the Hook with a note on why.

The SFW Hook runs before the Rigify Hook and removes the `nsfw` Group's bones and its own list of nipple and breast bones (`cf_s_bust02`, `cf_j_bnip02root`, `cf_j_bnip02`, `cf_s_bnip01`, `cf_s_bnip025`). The Rigify Hook names some of those (`SFW_REMOVES` in `metarig/types.py`) and builds the rig without their controls when they are gone; any other named bone that is missing fails the Hook (issue 55).

| Legacy name | Replacement |
|---|---|
| `Center` (`cf_n_height`) | Role `body_root` |
| `Hips`, `Spine`, `Chest`, `Upper Chest`, `Neck`, `Head` | Roles `hips`, `spine`, `chest`, `upper_chest`, `neck`, `head` |
| `Left shoulder`, `Left arm`, `Left elbow`, `Left wrist` (and Right) | Roles `left_shoulder`, `left_upper_arm`, `left_lower_arm`, `left_hand` |
| `Left leg`, `Left knee`, `Left ankle`, `Left toe` | Roles `left_upper_leg`, `left_lower_leg`, `left_foot`, `left_toes` |
| `Thumb0_L`…`Thumb2_L`, `IndexFinger1_L`…`LittleFinger3_L` | the 30 finger Roles |
| `Left Eye`, `Right Eye` (`cf_J_hitomi_tx_L`; SVS's renamed `EyeTargetL`) | Roles `left_eye`, `right_eye` |
| `cf_pv_hand_L`, `cf_pv_foot_L`, `cf_pv_elbo_L`, `cf_pv_knee_L` | Roles `left_hand_ik`, `left_foot_ik`, `left_elbow_pole`, `left_knee_pole` |
| `cf_j_tang_01`…`_05`, `cf_j_tang_L_03`…`_05` | Role `tongue_root` and its subtree: the chain is the single-child path, side bones by the sign of x |
| `cf_d_sk_top`, `cf_d_sk_0N_00`, `cf_j_sk_0N_0M` | Group `skirt` and the tree: the chain roots ordered by angle around `hips` |
| `cf_J_Va…na_*`, `cf_j_kokan`, `cf_j_ana`, `cf_d_/cf_s_` forms | Group `nsfw`; Better Penetration found by its root's name (`cf_J_Vagina_root`) |
| `cf_d_bust00`, `cf_j_bust01_L`…`03`, `cf_s_bust01_L`…`03` | Roles `left_breast`, `right_breast` for `cf_j_bust01`; the rest by name |
| `cf_j_bnip02root_L`, `cf_j_bnip02_L`, `cf_s_bnip01_L`, `cf_s_bnip025_L` | by name: the `breast` Group also holds the bust, and no Role marks a nipple |
| `cf_j_siri_L`, `cf_s_siri_L`, `cf_d_siri_L` (butt) | by name: no Role or Group marks them |
| `cf_j_waist01` (`Pelvis`), `cf_j_waist02`, `cf_s_waist01`, `cf_s_waist02` | by name: no Role |
| `cf_s_index01_L`…`cf_s_little03_L`, `cf_s_thumb01_L`…`03` (SVS's finger weights) | by name (`names.game_finger_group`): no Role; their vertex groups give the fingertips (ADR 0045) |
| joint-correction set: `cf_d_shoulder02`, `cf_d_arm01`…`03`, `cf_d_forearm02`, `cf_d_wrist`, `cf_d_hand`, `cf_s_elbo`, `cf_s_elboback`, `cf_s_forearm01`, `cf_d_siri`, `cf_d_thigh02`, `03`, `cf_s_leg`, `cf_d_kneeF`, `cf_s_kneeB`, `cf_s_leg01`, `cf_d_leg02`, `03`, `cf_s_waist02` (each side) | by name: they are what the game's own correction components move, and no Role or Group marks them |
| `cf_s_shoulder02`, `cf_s_arm01`…`03`, `cf_s_forearm01`, `02`, `cf_s_wrist`, `cf_s_hand`, `cf_s_thigh01`…`03`, `cf_s_leg01`…`03`, `cf_s_head`, `cf_s_neck`, `cf_s_spine01`…`03`, `cf_s_waist01` (Rigify deform bones) | by name |
| `cf_J_FaceUp_ty`, `cf_J_FaceBase` (head height, head mod) | by name |
| `a_n_heel_L` (heel) | by name (Group `helper`) |
| `cf_hit_head`, `cf_J_Mayu_R` (eye controller) | Roles `left_eye`, `right_eye`, `head` and Group `eyebrow` (hit boxes are never exported) |
| `Eyesx`, `Eye Controller` | made by the Rigify Hook |
| `MasterFootIK.L`, `ToeRotator.L`, `HeelIK.L`, `cf_pv_root_upper` | Dropped: no legacy armature had them |
| `p_cf_body_bone`, `cf_j_root` (export prep, Koikatsu) | the bones between the skeleton root and `body_root` |

### Shape keys

| Legacy | Replacement |
|---|---|
| `Mouth Big A`, `Mouth Small I`, … (emotion grid), `Eye Closed`, `Eye Happy, Closed`, … | Expression Names, as legacy |
| `vagina.open` (SFW) | the game name, as legacy |
