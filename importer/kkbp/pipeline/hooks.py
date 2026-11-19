"""Hook registration and the hooks folder (docs/design/import-pipeline.md, "Hooks").

Built-ins, other add-ons and folder scripts all register through `hook` (the public decorator),
which calls `register_hook`. A Hook is built-in when it is defined inside this add-on.
"""

from __future__ import annotations

import importlib.util
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .options import Option, OptionError

HOOK_API_VERSION = "2.1"
_ADDON = __package__.rpartition(".")[0]  # this add-on's package, such as bl_ext.user_default.kkbp
FOLDER_MODULE = "kkbp_user_hooks"  # folder scripts are loaded as kkbp_user_hooks.<file stem>


@dataclass(frozen=True)
class Hook:
    fn: Callable
    name: str
    source: str  # the module that registered it
    requires_api: str | None = None
    options: tuple[Option, ...] = ()
    switch: Option | None = None
    builtin: bool = False

    @property
    def key(self) -> str:
        """Unique per Hook: '<source>:<name>'. Preferences list user Hooks by key."""
        return f"{self.source}:{self.name}"

    @property
    def all_options(self) -> tuple[Option, ...]:
        return ((self.switch,) if self.switch else ()) + self.options

    def switched_on(self, options) -> bool:
        """For a built-in Hook: whether its switch (a bool, or a choice whose 'off' means off) is on."""
        if self.switch is None:
            return True
        value = options[self.switch.name]
        return value if self.switch.type is bool else value != "off"


_registry: dict[str, Hook] = {}


def register_hook(fn: Callable, *, name: str, requires_api: str | None = None, options=(), switch: Option | None = None,
                  source: str | None = None, builtin: bool | None = None) -> Hook:
    """Registers `fn(ctx)` as a Hook, replacing one with the same source and name."""
    source = source or fn.__module__
    if builtin is None:
        builtin = source == _ADDON or source.startswith(_ADDON + ".")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("a Hook needs a name")
    options = tuple(options)
    if not all(isinstance(o, Option) for o in options):
        raise TypeError(f"Hook {name}: options should be kkbp.Option declarations")
    if switch is not None:
        if not builtin:
            raise ValueError(f"Hook {name}: only built-in Hooks have a switch; users switch their own in Preferences")
        if not (switch.type is bool or "off" in switch.choice_ids):
            raise ValueError(f"Hook {name}: a switch is a bool, or a choice with an 'off' choice")
    if requires_api is not None:
        _parse_version(requires_api)
    hook = Hook(fn, name.strip(), source, requires_api, options, switch, builtin)
    _registry[hook.key] = hook
    return hook


def hook(name: str, requires_api: str | None = None, options=(), switch: Option | None = None):
    """Decorator that registers the function as a Hook run after the Core Import.

        @kkbp.hook(name="Fix eyebrow color", requires_api="2.0",
                   options=[kkbp.Option("tint", float, default=0.5, label="Tint")])
        def after_import(ctx):
            ...

    `switch` is for built-in Hooks only: the Import Option that turns the Hook on and off. Users
    switch their own Hooks in Preferences.
    """
    def decorate(fn):
        register_hook(fn, name=name, requires_api=requires_api, options=options, switch=switch)
        return fn
    return decorate


def unregister_hooks(source: str):
    """Removes every Hook registered from module `source` (an add-on calls this when it is disabled)."""
    for key in [k for k, h in _registry.items() if h.source == source or h.source.startswith(source + ".")]:
        del _registry[key]


def registered() -> list[Hook]:
    return list(_registry.values())


def find(key_or_name: str) -> Hook | None:
    if key_or_name in _registry:
        return _registry[key_or_name]
    matches = [h for h in _registry.values() if h.name == key_or_name]
    if len(matches) > 1:
        raise ValueError(f"several Hooks are named {key_or_name}; use one of {', '.join(h.key for h in matches)}")
    return matches[0] if matches else None


def builtin_in_order(order: list[str]) -> list[Hook]:
    """The built-in Hooks, in the fixed order of `order` (their names)."""
    by_name = {h.name: h for h in _registry.values() if h.builtin}
    missing = sorted(set(by_name) - set(order))
    if missing:
        raise RuntimeError(f"built-in Hooks missing from BUILTIN_HOOKS: {', '.join(missing)}")
    return [by_name[n] for n in order if n in by_name]


def user_in_order(preference_order: list[tuple[str, bool]]) -> list[tuple[Hook, bool]]:
    """The user Hooks with their on/off state: in the Preferences order, then new ones, switched on."""
    users = {h.key: h for h in _registry.values() if not h.builtin}
    out = [(users.pop(key), enabled) for key, enabled in preference_order if key in users]
    out += [(h, True) for h in users.values()]
    return out


def api_mismatch(hook: Hook) -> str | None:
    """Why this Hook can't run with this hook interface version, or None if it can."""
    if hook.requires_api is None:
        return None
    major, minor = _parse_version(hook.requires_api)
    have_major, have_minor = _parse_version(HOOK_API_VERSION)
    if major != have_major or minor > have_minor:
        return f"it needs hook interface {hook.requires_api}; this KKBP has {HOOK_API_VERSION}"
    return None


def _parse_version(text):
    try:
        major, minor = text.split(".")
        return int(major), int(minor)
    except (AttributeError, ValueError):
        raise ValueError(f"hook interface version {text!r} should be major.minor, such as '1.0'") from None


# --- the hooks folder -----------------------------------------------------------------

@dataclass
class LoadedScript:
    """One .py file from the hooks folder: the Hooks it registered, or why it didn't load."""

    path: Path
    hooks: list[str] = field(default_factory=list)
    error: str | None = None


def load_folder(folder: str | Path | None, api, taken: dict[str, str]) -> list[LoadedScript]:
    """Loads every .py file in `folder`, replacing every Hook loaded from a folder before.

    Each script gets the public API as `kkbp` before it runs. `taken` maps the option names the
    Steps and other Hooks already declare to their owner; a Hook whose option clashes isn't loaded.
    """
    unregister_hooks(FOLDER_MODULE)
    if not folder:
        return []
    folder = Path(folder).expanduser()
    if not folder.is_dir():
        return [LoadedScript(folder, error="the hooks folder doesn't exist")]
    taken = dict(taken)
    scripts = []
    for path in sorted(folder.glob("*.py")):
        module_name = f"{FOLDER_MODULE}.{_identifier(path.stem)}"
        script = LoadedScript(path)
        scripts.append(script)
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            module.kkbp = api
            spec.loader.exec_module(module)
        except Exception as ex:
            unregister_hooks(module_name)
            script.error = _last_line(ex)
            continue
        for h in [h for h in registered() if h.source == module_name]:
            clash = next((o.name for o in h.all_options if o.name in taken), None)
            if clash:
                del _registry[h.key]
                script.error = f"Hook {h.name} wasn't loaded: option {clash} is already declared by {taken[clash]}"
                continue
            taken.update({o.name: f"Hook {h.name}" for o in h.all_options})
            script.hooks.append(h.name)
    return scripts


def _identifier(stem):
    return "".join(c if c.isalnum() or c == "_" else "_" for c in stem) or "script"


def _last_line(ex):
    lines = traceback.format_exception_only(type(ex), ex)
    return lines[-1].strip() if lines else repr(ex)


def check_options(hooks: list[Hook], taken: dict[str, str]):
    """OptionError if a Hook declares an option name that `taken` (or another Hook) already has."""
    taken = dict(taken)
    for h in hooks:
        for o in h.all_options:
            if o.name in taken:
                raise OptionError(f"option {o.name} is declared by both {taken[o.name]} and Hook {h.name}")
            taken[o.name] = f"Hook {h.name}"
