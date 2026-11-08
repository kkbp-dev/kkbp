"""Run a Hook on a Character imported earlier (D30; the legacy "Convert for Rigify" button, for any
Hook). The Hook gets the same `ctx` as during an import, from the Character's bundle."""

from __future__ import annotations

from .. import editing, settings
from ..pipeline import hooks as registry
from ..pipeline.context import ImportContext, ImportLog
from ..pipeline.options import resolve
from ..pipeline.run import declared_options
from ..pipeline.steps import STEPS


def run_hook(ch, name: str, options: dict | None = None) -> ImportLog:
    """Runs Hook `name` (its switch on, if it has one) on the Character; raises what the Hook raises."""
    hook = registry.find(name)
    if hook is None:
        raise ValueError(f"there is no registered Hook {name!r}")
    given = dict(options or {})
    if hook.switch is not None and hook.switch.name not in given:
        given[hook.switch.name] = True if hook.switch.type is bool else next(
            c for c in hook.switch.choice_ids if c != "off")
    resolved = resolve(declared_options(STEPS, registry.registered()), settings.option_defaults(), given)
    log = ImportLog()
    log.source = f"hook {hook.name}"
    ctx = ImportContext(bundle=ch.bundle(), character=ch, options=resolved, game=ch.game, log=log)
    editing.reset_state()
    try:
        hook.fn(ctx)
    finally:
        editing.object_mode()
    return log
