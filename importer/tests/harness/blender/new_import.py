"""Import one bundle with the new importer and write its scene summary.

Runs inside Blender, started by run.py:

    blender --background --factory-startup --python-exit-code 1 --python new_import.py -- \
        --bundle DIR --pillow WHEEL --out FILE [--hooks none|builtin|NAME,...] [--options JSON] \
        [--save-blend FILE]

`--hooks none` (the default) runs the Core Import alone; `builtin` runs every built-in Hook in its
fixed order; otherwise the named Hooks run. `--options` overrides Import Options by name.

The add-on must already be in the isolated profile's `user_default` extension repository (run.py
copies it there). Pillow is installed into that profile from WHEEL, as a user would offline.
"""

import argparse
import importlib
import json
import os
import sys
import traceback

import addon_utils
import bpy

sys.path.insert(0, os.path.dirname(__file__))
import scene_summary  # noqa: E402

MODULE = "bl_ext.user_default.kkbp"


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--pillow", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--hooks", default="none")
    parser.add_argument("--options", default="{}")
    parser.add_argument("--save-blend")
    args = parser.parse_args(argv)

    bpy.ops.wm.read_homefile(use_empty=True)
    if addon_utils.enable(MODULE, default_set=True, handle_error=_raise) is None:
        raise SystemExit(f"Could not enable {MODULE}")
    pillow = importlib.import_module(f"{MODULE}.pillow")
    if not pillow.available():
        pillow.use_wheel(args.pillow)
        if not pillow.install_from_manifest():
            raise SystemExit("Blender didn't install the Pillow wheel")
    kkbp = importlib.import_module(MODULE)

    result = kkbp.api.import_bundle(args.bundle, options=json.loads(args.options), hooks=_hooks(args.hooks))
    summary = scene_summary.summarize(result.character_name)
    summary["run"] = {
        "blender": bpy.app.version_string,
        "importer": _version(),
        "result": "ok" if result.ok else f"failed in {result.failed_step}: {result.error}",
        "steps": {s.name: s.status for s in result.steps},
        "hooks": {h.name: h.status if h.status != "failed" else f"failed: {h.reason}" for h in result.hooks},
        "seconds": round(result.seconds, 1),
        "log_warnings": result.warnings,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=1, sort_keys=True)
    if args.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=args.save_blend)
    if not result.ok:
        raise SystemExit(f"Import failed in Step {result.failed_step}: {result.error}")


def _hooks(text):
    if text == "none":
        return []
    if text == "builtin":  # the ones registered so far, in their fixed order
        steps = importlib.import_module(f"{MODULE}.pipeline.steps")
        registry = importlib.import_module(f"{MODULE}.pipeline.hooks")
        return [h.name for h in registry.builtin_in_order(steps.BUILTIN_HOOKS)]
    return [name.strip() for name in text.split(",") if name.strip()]


def _version():
    mod = sys.modules[MODULE]
    with open(os.path.join(os.path.dirname(mod.__file__), "blender_manifest.toml"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("version"):
                return line.split("=", 1)[1].strip().strip('"')
    return None


def _raise(ex):
    raise ex


try:
    main()
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    sys.exit(1)
