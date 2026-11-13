"""Template Sets: which Material Template each material gets (docs/design/material-template.md).

A set is a list of rows, keyed on (Material Role, Blend Mode); the first row that matches a material
picks its template, parameter values and render method. A set may extend another: a row with the
same key as a parent's row takes its place, a row with a new key comes before all the parent's
rows, and `replace` swaps template names in the parent's rows it keeps. A material that lacks a slot its template `requires` gets the
set's `fallback`, as the legacy importer gave unbaked materials its Transparent template.

The Game Profile names its set (`TEMPLATE_SET`).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace as dc_replace
from types import MappingProxyType
from typing import Iterable, Mapping

from .descriptions import TEMPLATES, Template

_EMPTY: Mapping = MappingProxyType({})


@dataclass(frozen=True)
class Row:
    template: str
    role: str | None = None  # Material Role; None matches any, including none
    blend_mode: str | None = None  # None matches any
    params: Mapping[str, float] = _EMPTY
    render_method: str | None = None  # DITHERED or BLENDED; None keeps the template's
    transparent_shadow: bool | None = None

    @property
    def key(self):
        return (self.role, self.blend_mode)

    def matches(self, role: str | None, blend_mode: str) -> bool:
        return (self.role is None or self.role == role) and (self.blend_mode is None or self.blend_mode == blend_mode)


@dataclass(frozen=True)
class TemplateSet:
    name: str
    rows: tuple[Row, ...]
    fallback: str | None = None
    extends: str | None = None
    replace: Mapping[str, str] = field(default=_EMPTY)  # parent's template name -> this set's
    defaults: Mapping[str, float] = field(default=_EMPTY)  # param values every row starts from


_BLENDED = {"render_method": "BLENDED", "transparent_shadow": True}

SETS: Mapping[str, TemplateSet] = MappingProxyType({s.name: s for s in (
    TemplateSet(
        "KK",
        fallback="Transparent",
        defaults={"force_visibility": 2},
        rows=(
            Row("KK Tears", role="tears", render_method="BLENDED"),
            Row("Gag", role="gag_eyes", render_method="BLENDED"),
            Row("KK Eye", role="eye_l", **_BLENDED),
            Row("KK Eye", role="eye_r", **_BLENDED),
            Row("KK Light Dark", role="face", params={"force_visibility": 0}),
            Row("KK Light Dark", role="eye_white", **_BLENDED),
            Row("KK Light Dark", blend_mode="alpha", **_BLENDED),
            Row("KK Light Dark", blend_mode="glasses", render_method="BLENDED"),
            Row("KK Light Dark"),
        ),
    ),
    # SVS draws everything dithered but the tears, the pupils and the eyelashes (dithering leaves noise in
    # their soft edges, issue 40), and the face like everything else.
    TemplateSet(
        "SVS",
        extends="KK",
        replace={"KK Light Dark": "SVS Light Dark", "KK Eye": "SVS Light Dark"},
        rows=(
            Row("Gag", role="gag_eyes", render_method="DITHERED"),
            Row("SVS Light Dark", role="eye_l", **_BLENDED),
            Row("SVS Light Dark", role="eye_r", **_BLENDED),
            Row("SVS Light Dark", role="eyelash", **_BLENDED),
            Row("SVS Light Dark", role="face"),
            Row("SVS Light Dark", role="eye_white", render_method="DITHERED"),
            Row("SVS Light Dark", blend_mode="alpha", render_method="DITHERED"),
            Row("SVS Light Dark", blend_mode="glasses", render_method="DITHERED"),
        ),
    ),
)})


class TemplateSetError(LookupError):
    pass


def resolve(name: str) -> TemplateSet:
    """The set `name` with its parents' rows folded in, as one flat set."""
    if name not in SETS:
        raise TemplateSetError(f"there is no Template Set {name}")
    s = SETS[name]
    if s.extends is None:
        return s
    parent = resolve(s.extends)
    own = {r.key: r for r in s.rows}
    parent_keys = {r.key for r in parent.rows}
    rows = tuple(r for r in s.rows if r.key not in parent_keys)
    rows += tuple(own.get(r.key) or dc_replace(r, template=s.replace.get(r.template, r.template))
                  for r in parent.rows)
    return TemplateSet(name=s.name, rows=rows,
                       fallback=s.fallback or s.replace.get(parent.fallback, parent.fallback),
                       defaults={**parent.defaults, **s.defaults})


def choose(set_name: str, role: str | None, blend_mode: str, slots: Iterable[str]) -> tuple[Template, Row, dict]:
    """The template, row and parameter values for a material with this role, Blend Mode and the
    texture slots it has. Falls back to the set's fallback when the template's `requires` are missing."""
    s = resolve(set_name)
    present = set(slots)
    for row in s.rows:
        if row.matches(role, blend_mode):
            template = TEMPLATES[row.template]
            if not set(template.requires) <= present and s.fallback:
                row = Row(s.fallback, role=row.role, blend_mode=row.blend_mode)
                return TEMPLATES[s.fallback], row, {}
            values = {k: v for k, v in {**s.defaults, **row.params}.items() if k in template.params}
            return template, row, values
    if s.fallback:
        return TEMPLATES[s.fallback], Row(s.fallback), {}
    raise TemplateSetError(f"Template Set {set_name} has no row for role {role}, Blend Mode {blend_mode}")
