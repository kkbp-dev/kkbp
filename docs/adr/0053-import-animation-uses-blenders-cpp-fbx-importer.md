# Import Animation uses Blender's C++ FBX importer

Import Animation reads the game's FBX animation with Blender's FBX importer, then retargets it onto the Rigify rig (D34). It called `bpy.ops.import_scene.fbx`, the Python importer, which Blender 5.3's File > Import menu lists as "FBX (.fbx) (Legacy)". That importer builds an armature by making it the view layer's active object and switching modes with `bpy.ops.object.mode_set`. `mode_set` acts on the context's active object, not the view layer's. So if Import Animation runs under a context override that names another object, such as a script's `temp_override(active_object=rig)`, the switch back to Object Mode never reaches the new armature. It stays in Edit Mode with edit bones and no pose bones, and the importer raises `KeyError: 'bpy_prop_collection[key]: key "p_cf_body_bone" not found'`. Blender 5.2.2 and 5.3.0 do the same; their importers differ by one line elsewhere. The FBX files and the options KKBP passed play no part. A click in the Tools panel has no such override, which is why only scripted calls hit this.

Now:

1. **`compat.import_fbx` calls `bpy.ops.wm.fbx_import`**, Blender's C++ importer, which builds the armature through the data API and needs no mode switch. Both harness builds have it with the same options. On the game's walk (`f_aruki_00_01_01`) and beachball (`beachball_01`) clips it gives the same 580 bones, the same frame range and the same rest and posed world matrices as the Python importer, to the printed precision (0.000°, 0.0000 m), on both builds.
2. **It sets every option the importer has** (`compat.FBX_OPTIONS`), as the Mesh Loader does for glTF, and `test_the_fbx_importer_gets_every_option_it_has` fails when a Blender update adds one. `anim_offset` stays 1, so a clip's time 0 is frame 1, as before.
3. **A failed import removes what it made** (`compat.remove_imported`): its objects, their data and actions, after returning those objects to Object Mode. Before, a failure left the half-built armature in Edit Mode, and Import Animation's `poll()` then refused to run until the user left Edit Mode. The C++ importer gives its action a fake user, which the removal counts.

## Considered Options

- **Keep the Python importer and drop the caller's override**: a nested `temp_override` can't remove a key the outer one set, and setting `active_object=None` makes the importer's own `mode_set` fail.
- **Refuse to run under an override**: the operator can't tell an override from the screen's own context, and scripts and Hooks that call tools under overrides are normal.
