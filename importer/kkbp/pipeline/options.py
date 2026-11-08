"""Import Options (docs/design/import-pipeline.md, "Import Options").

A Step or Hook declares each of its options once, as an Option. That one declaration gives the
panel control, the Preferences default and `ctx.options.<name>`. Names are flat and unique across
every Step and Hook.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping

_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_RESERVED = {"name", "rna_type"}  # Blender's own property group fields
TYPES = (bool, int, float, str)


class OptionError(ValueError):
    """An option declaration or value is wrong."""


@dataclass(frozen=True)
class Option:
    """One Import Option. `type` is bool, int, float or str; a str with `choices` is a choice.

    `choices` are ids, or (id, label) or (id, label, description) tuples.
    """

    name: str
    type: type
    default: Any
    label: str
    description: str = ""
    choices: tuple | None = None
    min: float | None = None
    max: float | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not _NAME.match(self.name):
            raise OptionError(f"option name {self.name!r} should be lower-case letters, digits and underscores")
        if self.name in _RESERVED:
            raise OptionError(f"option name {self.name!r} is taken by Blender")
        if self.type not in TYPES:
            raise OptionError(f"option {self.name}: type should be bool, int, float or str")
        if self.choices is not None:
            if self.type is not str:
                raise OptionError(f"option {self.name}: only a str option can have choices")
            items = tuple(_choice(self.name, c) for c in self.choices)
            if not items or len({c[0] for c in items}) != len(items):
                raise OptionError(f"option {self.name}: choices should be non-empty and unique")
            object.__setattr__(self, "choices", items)
        if (self.min is not None or self.max is not None) and self.type not in (int, float):
            raise OptionError(f"option {self.name}: only int and float options have min and max")
        object.__setattr__(self, "default", self.check(self.default))

    @property
    def kind(self) -> str:
        """bool, int, float, choice or text."""
        if self.choices is not None:
            return "choice"
        return {bool: "bool", int: "int", float: "float", str: "text"}[self.type]

    @property
    def choice_ids(self) -> tuple[str, ...]:
        return tuple(c[0] for c in self.choices or ())

    def check(self, value):
        """`value` as this option's type, or OptionError."""
        ok = (isinstance(value, bool) if self.type is bool
              else isinstance(value, int) and not isinstance(value, bool) if self.type is int
              else isinstance(value, (int, float)) and not isinstance(value, bool) if self.type is float
              else isinstance(value, str))
        if not ok:
            raise OptionError(f"option {self.name} should be {self.kind}, not {value!r}")
        if self.type is float:
            value = float(value)
        if self.choices is not None and value not in self.choice_ids:
            raise OptionError(f"option {self.name} should be one of {', '.join(self.choice_ids)}, not {value!r}")
        if self.min is not None and value < self.min or self.max is not None and value > self.max:
            raise OptionError(f"option {self.name} should be between {self.min} and {self.max}, not {value!r}")
        return value


def _choice(name, c):
    if isinstance(c, str):
        return (c, c.replace("_", " ").capitalize(), "")
    if isinstance(c, tuple) and 2 <= len(c) <= 3 and all(isinstance(x, str) for x in c):
        return (c[0], c[1], c[2] if len(c) == 3 else "")
    raise OptionError(f"option {name}: a choice is an id, or (id, label[, description])")


class Options:
    """The Import Options in effect: read-only, as attributes (`ctx.options.fix_seams`) or items."""

    __slots__ = ("_values",)

    def __init__(self, values: Mapping[str, Any]):
        object.__setattr__(self, "_values", MappingProxyType(dict(values)))

    def __getattr__(self, name):
        try:
            return self._values[name]
        except KeyError:
            raise AttributeError(f"there is no Import Option {name!r}") from None

    def __getitem__(self, name):
        return self._values[name]

    def __contains__(self, name):
        return name in self._values

    def __iter__(self):
        return iter(self._values)

    def __setattr__(self, name, value):
        raise AttributeError("Import Options are read-only")

    def as_dict(self) -> dict[str, Any]:
        return dict(self._values)

    def __repr__(self):
        return f"Options({dict(self._values)!r})"


def check_unique(owned: Iterable[tuple[str, Option]]) -> dict[str, tuple[str, Option]]:
    """{option name: (owner, option)}, or OptionError naming both owners of a clashing name."""
    out: dict[str, tuple[str, Option]] = {}
    for owner, option in owned:
        if option.name in out:
            raise OptionError(f"option {option.name} is declared by both {out[option.name][0]} and {owner}")
        out[option.name] = (owner, option)
    return out


def resolve(declared: Iterable[Option], defaults: Mapping[str, Any] | None = None,
            given: Mapping[str, Any] | None = None) -> Options:
    """The options in effect: each declared default, then the Preferences `defaults`, then `given`.

    A name in `given` that nothing declares, or a value of the wrong type, raises OptionError. A
    stale Preferences default (a renamed option, a value of the old type) is ignored.
    """
    declared = {o.name: o for o in declared}
    unknown = sorted(set(given or {}) - set(declared))
    if unknown:
        raise OptionError(f"unknown Import Option{'s' if len(unknown) > 1 else ''}: {', '.join(unknown)}")
    values = {}
    for name, option in declared.items():
        value = option.default
        if defaults and name in defaults:
            try:
                value = option.check(defaults[name])
            except OptionError:
                pass
        if given and name in given:
            value = option.check(given[name])
        values[name] = value
    return Options(values)
