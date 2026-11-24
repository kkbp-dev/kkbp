# Hook interface 2.2

How to write a Hook: a script that KKBP runs on each Character it imports, after the Core Import has rebuilt it. This is version **2.2** of the hook interface (`kkbp.HOOK_API_VERSION`). The design behind it is in [design/import-pipeline.md](design/import-pipeline.md#hooks); terms are defined in [CONTEXT.md](../CONTEXT.md).

## A first Hook

Put a `.py` file in a folder and choose that folder as the hooks folder in KKBP's Preferences. KKBP loads it when the add-on starts, from **Reload hooks**, and again before each import. The script doesn't import anything to get KKBP: `kkbp` is already defined.

This one adds a camera that frames the Character's face, upper body or whole body. Like any Blender script, it imports `bpy` for the rest:

```python
import bpy
from mathutils import Vector

# For each framing: the Bone Role to aim at, and how tall a slice of the Character fills the frame, in metres
FRAMINGS = {"face": ("head", 0.45), "bust": ("neck", 0.75), "full": ("hips", 2.0)}


@kkbp.hook(name="Portrait camera", requires_api="2.1", options=[
    kkbp.Option("portrait_camera_framing", str, "bust", "Framing",
                choices=["face", ("bust", "Bust"), ("full", "Full body", "From head to toe")]),
    kkbp.Option("portrait_camera_lens", float, 85.0, "Focal length", min=20.0, max=200.0,
                description="The camera's focal length, in millimetres"),
])
def portrait_camera(ctx):
    ch = ctx.character
    role, height = FRAMINGS[ctx.options.portrait_camera_framing]
    bone = ctx.bundle.skeleton.by_role(role)  # the bundle's bone with that Bone Role, in any Game
    armature = ch.control  # the Rigify rig, or the armature when there is none
    name = ch.bone(bone.id) if bone is not None else None  # that bone's name in it
    if name is None:
        ctx.log.warning(f"{ch.name} has no {role} bone, so no camera was added")
        return
    target = armature.matrix_world @ armature.pose.bones[name].head

    camera = bpy.data.objects.new(f"{ch.name} camera", bpy.data.cameras.new(f"{ch.name} camera"))
    camera.data.lens = ctx.options.portrait_camera_lens
    camera.data.sensor_fit = "VERTICAL"
    # In front of the Character, which faces -Y, as far away as it takes to fit `height` in the frame
    distance = height * camera.data.lens / camera.data.sensor_height
    camera.location = target + Vector((0.0, -distance, 0.0))
    aim = camera.constraints.new("TRACK_TO")  # keeps the bone in the middle of the frame when it's posed
    aim.target, aim.subtarget = armature, name
    aim.track_axis, aim.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    ch.collection.objects.link(camera)
    if bpy.context.scene.camera is None:
        bpy.context.scene.camera = camera
    ctx.log.info(f"Added {camera.name}, {distance:.2f} m from {bone.name} ({ctx.game})")
```

The Hook appears in Preferences, where it can be switched off and moved up or down among the user Hooks, and its options appear in the import panel. Along the way it shows:

- **Import Options:** each `kkbp.Option` becomes a control in the import panel and a value in `ctx.options`. Their names start with the Hook's own prefix, because every Step and Hook shares one set of names ([Import Options](#import-options)).
- **The bundle:** `ctx.bundle` holds the game's data. The Hook finds the bone by its Bone Role rather than by name, so it works on every Game.
- **The Character:** `ctx.character` finds the Character's rig and Collection by their tags, so it keeps working after the user renames them. `ch.bone` gets from the bundle's bone to the rig's, with Rigify's rig or without it.
- **The log:** `ctx.log` writes to the KKBP log. A warning also counts in the import's summary.

## Registering

`kkbp.hook(name, requires_api=None, options=())` registers the decorated function `fn(ctx)` as a Hook.

- `name`: shown in the panel and the log. A Hook with the same name from the same script replaces the earlier one.
- `requires_api`: the hook interface version the Hook was written for, `"major.minor"`. A Hook is skipped, with a warning, when the major version differs or its minor version is newer than KKBP's. Without it, the Hook always runs.
- `options`: the Hook's Import Options, as `kkbp.Option` declarations.

A script can register several Hooks. A script that raises while loading registers none, and the panel shows why.

### From another add-on

KKBP is an extension whose module name differs between systems (`bl_ext.<repository>.kkbp`), so another add-on looks it up instead of importing it, registers its Hooks once KKBP is enabled, and removes them when it is disabled:

```python
import sys
import bpy

def find_kkbp():
    """KKBP's public API, or None if KKBP isn't enabled."""
    for name in bpy.context.preferences.addons.keys():
        if name.rpartition(".")[2] == "kkbp":
            return sys.modules[name].api
    return None

def register():
    kkbp = find_kkbp()
    if kkbp is not None:
        kkbp.hook(name="My add-on's fix")(my_fix)

def unregister():
    kkbp = find_kkbp()
    if kkbp is not None:
        kkbp.unregister_hooks(__name__)
```

`kkbp.unregister_hooks(source)` removes every Hook registered from module `source`.

## Import Options

`kkbp.Option(name, type, default, label, description="", choices=None, min=None, max=None)` declares one option. That one declaration gives the panel control, the Preferences default and `ctx.options.<name>`.

- `name`: lower-case letters, digits and underscores. Names are shared by every Step and Hook, so a Hook whose option name is already declared isn't loaded; prefix yours.
- `type`: `bool`, `int`, `float` or `str`. A `str` with `choices` is a choice; each choice is an id, `(id, label)` or `(id, label, description)`.
- `min` and `max`: only for `int` and `float`.

A bad declaration raises `kkbp.OptionError`.

## What a Hook gets: `ctx`

`ctx` is a `kkbp.ImportContext`, read-only:

| Field | What it is |
|---|---|
| `ctx.character` | The `kkbp.Character` being imported |
| `ctx.bundle` | The opened Export Bundle, a `kkbp.Bundle`, read-only |
| `ctx.options` | The Import Options in effect, read-only: `ctx.options.<name>`, `ctx.options["name"]`, `"name" in ctx.options` |
| `ctx.game` | The bundle's Game: `"KK"`, `"KKS"` or `"SVS"` |
| `ctx.log` | `info(message)`, `warning(message)` and `error(message)`: lines in the KKBP log; warnings also count in the import's summary |

A Hook doesn't get the Game Profile; what a Hook needs to know about the Character comes from the bundle's roles and groups, through Character and Bundle.

## What a Hook can rely on

- The Core Import has finished: every Part is built, tagged and in the Character's Collection.
- The built-in Hooks that are switched on have run, in their fixed order: Convert shaders, Separate meshes, Outlines, Face cards, SFW, Rigify, Separate Eyes, Delete default scene. User Hooks run after them, in the order set in Preferences.
- Each Hook starts in Object Mode with nothing selected. Afterwards KKBP puts Blender back into Object Mode, whatever the Hook left.
- If a Hook raises, the error goes to the KKBP log as a warning, the remaining Hooks still run, and the import still succeeds.
- A Hook changes the scene and reports through `ctx.log`. It returns nothing, and it can't switch other Hooks on or off.

## Character

`ctx.character` finds the Character's Blender objects, materials and images by the tags the import put on them, never by name, so it keeps working after the user renames things. It looks everything up again on each access, so it is safe across undo; don't keep Blender objects from one access to the next.

| | |
|---|---|
| `ch.key`, `ch.name`, `ch.game` | The Character Key, the Character's name and its Game |
| `ch.body`, `ch.armature`, `ch.rig`, `ch.tears`, `ch.gag_eyes` | The one Part with that role, or None. More than one raises `kkbp.CharacterError`, naming them |
| `ch.control` | `ch.rig` if Rigify made one, else `ch.armature`: what to pose and animate |
| `ch.bone(id)` | The name of the bone in `ch.control` that follows the bundle's bone `id`, or None if it has none. Without Rigify it is the bone named `id`; in Rigify's rig, its `ORG-` copy, which keeps the bone's rest pose and follows the pose, or the bone itself where Rigify copied it unchanged (hair, accessories) |
| `ch.hairs`, `ch.outfits`, `ch.alt_outfits` | Lists of Parts |
| `ch.outfit(index)` | Every Part of Outfit `index` |
| `ch.parts(roles=None, outfit=None)` | Parts, filtered by Part Role (a name or a list) and Outfit |
| `ch.add_part(obj, role, outfit=None)` | Makes a new object a Part. `role` is a Part Role; `outfit` is required for `outfit`, `alt_outfit` and `low_poly` |
| `ch.collection` | The Character's Collection. It is there for tidiness: membership is the tag, not the Collection |
| `ch.material(id)`, `ch.materials(roles=None, parts=None)` | Materials by bundle Id, or filtered by Material Role and by the Part Roles that use them |
| `ch.image(id)` | An image the import loaded, by the name it gave it |
| `ch.bundle()` | Reopens the Export Bundle the Character came from |
| `kkbp.Character.of(obj)`, `kkbp.Character.all(scene)` | The Character an object belongs to, and every Character in a scene |

Part Roles: `body`, `hair`, `outfit`, `alt_outfit`, `tears`, `gag_eyes`, `armature`, `rig`, `face_card`, `eyes`, `eyebrows`, `low_poly` (the Low poly Hook's copies of the clothes and hair, which carry their Outfit). The tongue is part of Body: find its faces by the `tongue` Material Role. The armature's bones are named by bundle Id, except that the Rigify Hook gives the rig and its metarig readable names (`Left arm`, `Head`); `ch.bone(id)` finds a bone either way.

## Bundle

`ctx.bundle` is the Export Bundle as read and checked, with nothing from Blender in it. Its fields follow the Export Bundle contract (`contract/`, and [design/export-bundle.md](design/export-bundle.md)); the meanings of roles, groups and Blend Modes are the contract's.

| | |
|---|---|
| `bundle.game`, `bundle.manifest`, `bundle.character` | The Game, the Manifest (Schema Version, Exporter, Export Options, Passes) and the Character's name and Game Extensions |
| `bundle.skeleton` | Its `bones` (each with `id`, `name`, `parent`, `role`, `group` and rest pose), `bone(id)`, `by_role(role)` and `in_group(group)` |
| `bundle.materials`, `bundle.material(id)`, `bundle.materials_with_role(role)` | Materials, each with `id`, `name`, `shader`, `role`, `blend_mode`, `colors`, `floats`, `vectors` (keyed by the game's Raw Property) and `textures`, with `texture(role, variant=None)` |
| `bundle.passes`, `bundle.mesh(id)`, `bundle.pass_of(mesh_id)` | The Body Pass and Outfit Passes and their meshes |
| `bundle.expressions`, `bundle.physics` | Expressions with their effects, and physics |
| `bundle.extension(key)` | The Character's Game Extension `key`, or None for other Games |
| `bundle.cache_dir(kind)` | A folder of the bundle's Cache, `kkbp_cache/<kind>/`, for files a Hook makes. Deleting the Cache is always safe |
| `bundle.warnings` | What was found odd but not wrong |

`kkbp.open_bundle(path)` opens a bundle outside an import; it raises `kkbp.BundleError`, whose `problems` lists everything wrong.

## Changing the scene

- **Modes:** use `kkbp.editing(objects, mode="EDIT")`, a context manager that puts one object or a list of them into a mode and afterwards restores the mode, the active object and the selection, even if the block raises:

  ```python
  with kkbp.editing(ctx.character.armature, "EDIT"):
      bones = ctx.character.armature.data.edit_bones
      ...
  ```

- **Materials:** the imported materials are copies of KKBP's Material Templates. Reach their nodes through `kkbp.templates` rather than by node name, which may change between KKBP versions:

  | | |
  |---|---|
  | `templates.params(material)` | The names of the template's parameters |
  | `templates.param(material, name)` | The socket for parameter `name`; set its `default_value`. An unknown name raises `kkbp.TemplateError` |
  | `templates.slots(material)` | The template's texture slots |
  | `templates.texture(material, role, variant=None)` | The image node for a Texture Role and Variant (such as `"main", "light"`), or a raw slot name, or None |
  | `templates.swap(material, variant)` | Puts the template's variant (such as `cycles`) in place of its shader; returns the inputs the variant lacks |
  | `templates.variant(material)` | The variant `swap` put in, or None |
  | `templates.apply(ch, blender_material, bundle_material)` | Rebuilds a material from its template and the bundle's values; returns the new material |

  What an expression changes on a material (`hidden`, and the pattern choice of the eyes and gag eyes) is driven on a custom property of each object that uses the material, not on the socket, so the materials aren't re-evaluated on every frame of an animation. `param(material, "hidden")` is then the material's own value: setting it to 1 still hides the material, but it doesn't read 1 while an expression hides it.

- Prefer Blender's data API to operators. A Hook that uses operators sets the active object and selection itself.

## Importing from a script

`kkbp.import_bundle(path, options=None, hooks=None)` imports a bundle without the UI and returns a `kkbp.ImportResult`: `ok`, `character_key`, `character_name`, `game`, `failed_step` and `error`, the `steps` and `hooks` that ran (`kkbp.StepOutcome` and `kkbp.HookOutcome`, each with a `name`, `status` and `reason`), `warnings` and `log_path`. `options` overrides Import Options by name; `hooks` overrides which Hooks run (`[]` for none).

## Versions

- The hook interface has its own `major.minor` version, separate from KKBP's. Everything on this page is the interface: the names in `kkbp`, `ctx`, the starting state, Character, Bundle and `kkbp.templates`. Anything else in KKBP's modules is internal and may change in any release.
- Adding to the interface raises the minor version. Changing or removing anything raises the major version, and so does a major Schema Version change in the Export Bundle contract, because `ctx.bundle` follows it.
- A Hook that declares `requires_api="2.0"` runs on every 2.x, and one that declares `"2.1"` on 2.1 and later.
- 2.0 removed the `tongue` Part Role and `ch.tongue`: the tongue is part of Body ([ADR 0039](adr/0039-the-tongue-is-part-of-body.md)). A 1.x Hook is skipped; one that used neither runs again once it declares 2.0.
- 2.1 added `ch.bone(id)`.
- 2.2 added the `low_poly` Part Role.
