"""Running an import: the Core Import's Steps, then the Hooks."""

from __future__ import annotations

import time
import traceback
from pathlib import Path

import bpy

from .. import editing, mesh_loader, profiles, settings
from ..bundle import Bundle, BundleError, open_bundle
from ..character import Character
from . import hooks as hook_registry
from .context import ImportContext, ImportLog, StepContext
from .hooks import Hook
from .options import Options, OptionError, check_unique, resolve
from .result import HookOutcome, ImportResult, StepOutcome
from .step import Step
from .steps import BUILTIN_HOOKS, STEPS


def import_bundle(path, options: dict | None = None, hooks=None) -> ImportResult:
    """Imports the Export Bundle at `path` and returns what happened.

    `options` overrides Import Options by name; the rest come from Preferences, then each
    declaration's default. `hooks=None` reloads the hooks folder and runs the built-in Hooks and the
    user Hooks switched on in Preferences; a list (of Hooks, Hook keys or names) runs exactly those,
    and `[]` runs the Core Import alone.

    A Step that fails stops the import, and the result says which. Raises before anything is built
    if the bundle can't be opened (BundleError), Pillow is missing, an option is wrong (OptionError)
    or the glTF importer has changed (MeshLoaderError).
    """
    settings.require_pillow()
    problems = mesh_loader.problems()
    if problems:
        raise mesh_loader.MeshLoaderError("; ".join(problems))
    bundle = open_bundle(path)
    profile_for(bundle)
    if hooks is None:
        settings.reload_hooks()
        chosen = [(h, True) for h in hook_registry.builtin_in_order(BUILTIN_HOOKS)]
        chosen += hook_registry.user_in_order(settings.user_hook_order())
    else:
        chosen = [(_hook(h), True) for h in hooks]
    resolved = resolve(declared_options(STEPS, [h for h, _ in chosen] + hook_registry.registered()),
                       settings.option_defaults(), options)
    return run_pipeline(bundle, STEPS, chosen, resolved)


def profile_for(bundle: Bundle) -> profiles.Profile:
    """The bundle's Game Profile, or BundleError if this importer has none for its Game."""
    try:
        return profiles.get(bundle.game)
    except profiles.ProfileError as ex:
        raise BundleError(bundle.path, [str(ex)]) from None


def declared_options(steps: list[Step], hooks: list[Hook]):
    """Every option the Steps and Hooks declare, once each; OptionError on a name clash."""
    seen = {}
    owned = [(f"Step {s.name}", o) for s in steps for o in s.options]
    for h in hooks:
        if h.key not in seen:
            seen[h.key] = h
            owned += [(f"Hook {h.name}", o) for o in h.all_options]
    return [o for _, o in check_unique(owned).values()]


def _hook(h) -> Hook:
    if isinstance(h, Hook):
        return h
    found = hook_registry.find(h) if isinstance(h, str) else None
    if found is None:
        raise ValueError(f"there is no registered Hook {h!r}")
    return found


def run_pipeline(bundle: Bundle, steps: list[Step], hooks: list[tuple[Hook, bool]], options: Options,
                 scene=None) -> ImportResult:
    """Runs `steps`, then (if they all succeed) `hooks`, each a (Hook, switched on) pair."""
    started = time.perf_counter()
    scene = scene or bpy.context.scene
    log = ImportLog()
    for warning in bundle.warnings:
        log.warning(warning)
    character = Character.new(bundle.manifest.character_name, bundle.game, bundle.path)
    character.add_collection(scene.collection)
    ctx = ImportContext(bundle=bundle, character=character, options=options, game=bundle.game, log=log)
    step_ctx = StepContext(**vars(ctx), profile=profile_for(bundle))
    result = ImportResult(ok=True, character_key=character.key, character_name=character.name, game=bundle.game)
    log.info(f"Importing {character.name} ({bundle.game}, Schema Version {bundle.manifest.schema_version}) "
             f"from {bundle.path}")
    log.info(f"Import Options: {options.as_dict()}")

    editing.object_mode()
    for step in steps:
        if not step.runs_on(bundle.game):
            result.steps.append(StepOutcome(step.name, "skipped", reason=f"not for {bundle.game}"))
            continue
        log.source = step.name
        t = time.perf_counter()
        try:
            step.fn(step_ctx)
        except Exception as ex:
            seconds = time.perf_counter() - t
            log.error(f"failed:\n{traceback.format_exc().rstrip()}")
            result.steps.append(StepOutcome(step.name, "failed", seconds, _describe(ex)))
            result.ok, result.failed_step, result.error = False, step.name, _describe(ex)
            break
        seconds = time.perf_counter() - t
        result.steps.append(StepOutcome(step.name, "ran", seconds))
        log.source = "import"
        log.info(f"Step {step.name}: {seconds:.2f} s")

    if result.ok:
        for hook, switched_on in hooks:
            result.hooks.append(_run_hook(ctx, hook, switched_on))

    log.source = "import"
    result.seconds = time.perf_counter() - started
    log.info(result.summary()[0])
    result.warnings = list(log.warnings)
    result.log_path = _write_log(bundle, log, result)
    return result


def _run_hook(ctx, hook: Hook, switched_on: bool) -> HookOutcome:
    log = ctx.log
    if not switched_on:
        return HookOutcome(hook.name, "off", reason="switched off in Preferences")
    if hook.builtin and not hook.switched_on(ctx.options):
        return HookOutcome(hook.name, "off", reason=f"{hook.switch.name} is off")
    mismatch = hook_registry.api_mismatch(hook)
    if mismatch:
        log.warning(f"Hook {hook.name} was skipped: {mismatch}")
        return HookOutcome(hook.name, "skipped", reason=mismatch)
    log.source = f"hook {hook.name}"
    editing.reset_state()
    t = time.perf_counter()
    try:
        hook.fn(ctx)
        outcome = HookOutcome(hook.name, "ran", time.perf_counter() - t)
    except Exception as ex:
        log.error(f"failed:\n{traceback.format_exc().rstrip()}")
        log.source = "import"
        log.warning(f"Hook {hook.name} failed: {_describe(ex)}")
        outcome = HookOutcome(hook.name, "failed", time.perf_counter() - t, _describe(ex))
    finally:
        editing.object_mode()
    log.source = "import"
    log.info(f"Hook {hook.name}: {outcome.status}, {outcome.seconds:.2f} s")
    return outcome


def _describe(ex):
    return f"{type(ex).__name__}: {ex}"


def _write_log(bundle: Bundle, log: ImportLog, result: ImportResult) -> Path | None:
    """Writes the log to kkbp_cache/log/log.txt, replacing the last import's. If the bundle
    folder can't be written, the log stays on the console and the result gets a warning."""
    try:
        path = bundle.cache_dir("log") / "log.txt"
        path.write_text(log.text(), encoding="utf-8")
        return path
    except OSError as ex:
        message = f"The KKBP log couldn't be written into the bundle ({ex}); it is on the console only."
        log.warning(message)
        result.warnings.append(message)
        return None


__all__ = ["import_bundle", "run_pipeline", "declared_options", "OptionError"]
