# Import Pipeline and Hooks

How the importer turns an [Export Bundle](export-bundle.md) into a Character in Blender, and where custom scripts plug in. Terms are defined in [CONTEXT.md](../../CONTEXT.md).

Status: agreed design, not yet implemented. `ctx.character` is defined in [character.md](character.md).

## Steps

- A Step is a plain Python function `step(ctx)`. Steps are not Blender operators.
- The pipeline runs one flat, ordered list of Steps, declared in a single module. The reading order is the running order. There are no phases.
- The Step functions live in topic modules (mesh, armature, materials).
- A Step's Game list is written next to it in that list, so the one module shows what runs, in what order, and for which Games:

```python
STEPS = [
    Step(rename_uv_maps),
    Step(create_gag_and_tear_shapekeys, games=["KK", "KKS"]),
    ...
]
```
- One Blender operator sits at the top, for the UI only.
- Steps never read `scene.kkbp` and never scan `bpy.data` for the Character. Everything comes through `ctx`.
- Timing is done by the pipeline, not inside Steps.

### Steps per Game

- Each Step declares a list of Games it applies to.
- **An empty list means the Step runs on every Game.** A non-empty list means it runs only on the Games in that list.
- This replaces the `if is_kk` branches in today's Step lists. To be revisited in candidate 4 (Game Profile).

## Hooks

- Hooks run only **after the Core Import has finished**. There are no hook points between phases, and Hooks cannot replace built-in Steps.
- Today's post-operations become built-in Hooks on that same hook point: the Cycles/Eevee/Principled shader conversions, Rigify, SFW, separate meshes, outlines and face cards.
- Two import options that are part of the Core Import today also become built-in Hooks at the end of the import:
  - **Fix body seams** (today's `fix_seams` option and the `remove_body_seams` Step), which merges by distance on the body materials;
  - **Separate meshes**, with the **Separation type** as its choice option ("One object per outfit" or "Separate all clothing", today's `separate_clothes`). Like convert shaders, it has a choice option rather than an on/off switch.
- A Hook owns its own asset file if it needs one (Rigify widgets, the face-card rig). User Hooks can bring their own `.blend` too, for example to replace the Material Templates after the import.
- Registration: built-ins, add-ons and folder scripts all use one decorator, `kkbp.hook` (it calls the internal `register_hook`). A folder script is a `.py` file with one or more decorated functions, and loading the file registers them.
- An extension's module name is `bl_ext.<repository>.kkbp` and differs between systems, so there is no `import kkbp`. The hooks-folder loader puts the public API into each script's namespace as `kkbp` before running it:

```python
# A script in the hooks folder: `kkbp` is already defined.
@kkbp.hook(name="Fix eyebrow color", requires_api="2.0",
           options=[kkbp.Option("tint", float, default=0.5, label="Tint")])
def after_import(ctx):
    ...
```

- Another add-on finds KKBP among the enabled add-ons by its id and uses the same API. It registers its Hooks once KKBP is enabled, and removes them with `kkbp.unregister_hooks(__name__)` when it is disabled:

```python
import sys
import bpy

def find_kkbp():
    """KKBP's public API, or None if KKBP isn't enabled."""
    for name in bpy.context.preferences.addons.keys():
        if name.rpartition(".")[2] == "kkbp":
            return sys.modules[name].api
    return None
```

### Order and switching

- Built-in Hooks run first, in a fixed order: fix body seams → shader conversion → separate meshes → outlines → face cards → SFW → Rigify → delete default scene. Fixing seams runs first because it changes the body mesh that later Hooks work on.
- User Hooks run after them, in a list in Preferences that the user can reorder and switch on or off.
- Each built-in Hook gets one automatic on/off Import Option (`fix_seams`, `use_rigify`, `use_outlines`, `sfw_mode`). The pipeline checks the switch, so Hooks don't return early themselves.
- The shader variants (today's B/C/D/E dropdown) are one "convert shaders" Hook with a choice option.

### Hooks folder

- It is only the path set in Preferences. There is no default folder.
- The panel lists which scripts were loaded.
- The folder is loaded when the add-on starts, from a **Reload hooks** button, and again just before each import.
- Each reload rebuilds the options panel. Scene values for options whose names haven't changed are kept.

### What a Hook can rely on and change

- Every Hook starts in Object Mode with nothing selected. The pipeline puts Blender back into Object Mode afterwards, whatever the Hook left.
- `ctx.options` and `ctx.bundle` are read-only.
- A Hook changes the scene and reports through `ctx.log`. It returns nothing and cannot turn other Hooks on or off.

### Hook interface version

- The interface itself, version 2.0, is documented for Hook writers in [../hook-interface.md](../hook-interface.md).

- The hook interface has its own `major.minor` version, separate from the add-on version. A Hook may declare the version it needs. If that doesn't match, it is skipped with a warning.
- The versioned interface covers the `ctx` fields, the `register_hook` signature, the guaranteed starting state, the Bundle's interface and the shape of `ctx.character`.
- Any breaking change to these needs a major bump. Adding something is a minor bump.
- A Schema Version major bump in the Export Bundle therefore also forces a hook interface major bump.

## Context (`ctx`)

- `ctx.bundle`: the opened Export Bundle, read-only.
- `ctx.character`: the Character being imported (see [character.md](character.md)).
- `ctx.options`: the Import Options in effect.
- `ctx.game`: the bundle's Game.
- `ctx.log`: logging and user-facing reports.
- Steps also get `ctx.profile`, the bundle's Game Profile ([game-profile.md](game-profile.md)); Hooks don't.

## Import Options

- Each Step or Hook declares its own options, for example `use_rigify: bool = True`.
- That one declaration produces the panel control, the Preferences default and `ctx.options.<name>`.
- This replaces today's three copies (`KKPanel.py`, `preferences.py`, `load_user_defaults`). Candidate 9 is folded into this one.
- Types: bool, int, float, choice and text. Each has a default, a label and an optional description.
- Defaults live in Preferences. Current values live on the scene, so a `.blend` remembers how it was imported.
- The scene's values are a property group generated from the declarations, rebuilt when they change. A new scene starts from the Preferences defaults, which the panel's **Save as Defaults** sets from the current scene. Only the values set on the scene are passed to `import_bundle`; the rest come from Preferences.

## Failure

- If a built-in Step fails, the import stops. The error names the Step, and the partly built scene is left in place. The whole import is a single undo step.
- If a Hook fails, it is logged and reported as a warning, the remaining Hooks still run, and the import counts as succeeded.

## Running without the UI

- `kkbp.import_bundle(path, options) -> ImportResult`, which lists the Steps run, timings, warnings and Hook outcomes.
- The panel operator, `auto_import`, `bulklaunch` and the test harness all call it.
- While an import runs, Blender's progress counter replaces the mouse cursor with a number from 0 to 100 that goes up as each Step and Hook finishes (skipped ones count too). The import is one blocking operator call, so the window doesn't redraw and a progress bar couldn't update (issue 66).
- After an import, the panel shows one short summary: done or failed (naming the failed Step), how many warnings, and any Hooks that failed or were skipped, with their reasons. Per-Step timings and the full log go to the KKBP log: `log.txt` in the bundle's Cache (`kkbp_cache/log/log.txt`), replaced by each import of that bundle. Nothing is written into the `.blend`. If the bundle folder can't be written, the log goes to the console only, with a warning.
- Hooks run in automated imports the same way as from the button. Callers and tests can pass `hooks=[]` or a chosen list to override that, so the harness can test the Core Import alone and then each Hook on its own.
