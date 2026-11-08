"""Template Descriptions and Template Sets, checked against each other, the contract's sets and the
Game Profiles. tests/blender/test_library.py checks them against library.blend itself."""

import pytest

import library
import profiles
from bundle import _contract

RENDER_METHODS = ("DITHERED", "BLENDED")


def _role_slots():
    roles = set(_contract.TEXTURE_ROLES)
    return roles | {f"{r}.{v}" for r in roles for v in _contract.TEXTURE_VARIANTS}


def _raw_slots():
    return {slot for game in profiles.games() for slot in profiles.get(game).raw_textures.values()}


@pytest.mark.parametrize("template", [t for t in library.TEMPLATES.values() if t.name not in library.EDIT_TEMPLATES],
                         ids=lambda t: t.name)
def test_descriptions_name_known_slots(template):
    known = _role_slots() | _raw_slots() | {"permalight_mask"}
    assert set(template.textures) <= known, set(template.textures) - known
    assert set(template.requires) <= set(template.textures)
    if template.patterns:
        assert template.patterns.slot in known
        assert template.patterns.choice in template.params
        assert bool(template.patterns.nodes) != bool(template.patterns.chain), "fixed nodes or a chain, not both"
        if template.patterns.chain:
            assert template.patterns.chain.frame in template.params
    if template.variants:
        assert template.shader
    assert set(template.variant_params) <= set(template.variants)
    assert not template.variant_drops or template.variants


@pytest.mark.parametrize("name", library.SETS)
def test_sets_name_known_templates_roles_and_blend_modes(name):
    s = library.resolve(name)
    assert s.fallback in library.TEMPLATES
    for row in s.rows:
        template = library.TEMPLATES[row.template]
        assert row.role is None or row.role in _contract.MATERIAL_ROLES
        assert row.blend_mode is None or row.blend_mode in _contract.BLEND_MODES
        assert row.render_method is None or row.render_method in RENDER_METHODS
        assert set(row.params) <= set(template.params), (row, set(row.params) - set(template.params))
    assert s.rows[-1].key == (None, None), "the last row catches every material"


@pytest.mark.parametrize("game", _contract.GAMES)
def test_every_profile_names_a_set_and_its_slots_and_values_exist(game):
    p = profiles.get(game)
    s = library.resolve(p.template_set)
    templates = [library.TEMPLATES[r.template] for r in s.rows]
    slots = {slot for t in templates for slot in t.textures} | {t.patterns.slot for t in templates if t.patterns}
    assert set(p.raw_textures.values()) <= slots, set(p.raw_textures.values()) - slots
    pattern_params = {k for t in templates if t.patterns and t.patterns.chain for k in t.patterns.chain.pattern_params}
    assert set(p.pattern_values.values()) <= pattern_params
    for raw in p.pattern_values:
        name, _, component = raw.partition(".")
        assert name.startswith("_") and component in ("", "x", "y", "z", "w")


def _pick(set_name, role, blend, slots=("main.light", "main.dark")):
    template, row, values = library.choose(set_name, role, blend, slots)
    return template.name, row.render_method, values


def test_kk_choices():
    assert _pick("KK", "face", "opaque") == ("KK Light Dark", None, {"force_visibility": 0})
    assert _pick("KK", "body", "opaque") == ("KK Light Dark", None, {"force_visibility": 2})
    assert _pick("KK", None, "cutout") == ("KK Light Dark", None, {"force_visibility": 2})
    assert _pick("KK", "eyebrow", "alpha") == ("KK Light Dark", "BLENDED", {"force_visibility": 2})
    assert _pick("KK", "eye_l", "alpha") == ("KK Eye", "BLENDED", {"force_visibility": 2})
    assert _pick("KK", "eye_white", "cutout")[1] == "BLENDED"
    assert _pick("KK", "tears", "glasses", ()) == ("KK Tears", "BLENDED", {})
    assert _pick("KK", "gag_eyes", "cutout", ()) == ("Gag", "BLENDED", {})


def test_a_material_without_its_baked_texture_falls_back_to_transparent():
    assert _pick("KK", None, "cutout", ("main",)) == ("Transparent", None, {})
    assert _pick("SVS", "eye_l", "alpha", ())[0] == "Transparent"


def test_svs_extends_kk_and_overrides_what_differs():
    assert _pick("SVS", "face", "opaque") == ("SVS Light Dark", None, {"force_visibility": 2})
    assert _pick("SVS", None, "cutout") == ("SVS Light Dark", None, {"force_visibility": 2})
    assert _pick("SVS", "eyebrow", "alpha") == ("SVS Light Dark", "DITHERED", {"force_visibility": 2})
    assert _pick("SVS", "eye_r", "alpha")[:2] == ("SVS Light Dark", "DITHERED")
    assert _pick("SVS", "tears", "alpha", ()) == ("KK Tears", "BLENDED", {})  # inherited from KK
    assert _pick("SVS", "gag_eyes", "cutout", ()) == ("Gag", "DITHERED", {})


def test_slot_names():
    assert library.slot("main") == "main"
    assert library.slot("main", "light") == "main.light"
    assert library.slot(None) is None


def _edit_slots():
    # main.dark is made from main; color_mask.plain takes color_mask for the plain-mask shaders.
    return {slot for game in profiles.games() for slot in profiles.get(game).edit.textures} | \
        {"main.dark", "color_mask.plain"}


@pytest.mark.parametrize("name", library.EDIT_TEMPLATES)
def test_edit_templates_name_edit_slots(name):
    template = library.TEMPLATES[name]
    assert set(template.textures) <= _edit_slots(), set(template.textures) - _edit_slots()
    assert template.copies and template.copies[0] == "textures"
    assert set(template.positions) <= set(template.textures)
    assert {"toon_shading", "use_normals"} <= set(template.params), "every edit template bakes"


def _params(params, param, how):
    """As tools/edit_material.py: item and skin set the light and dark pair; the others set the
    param, or both of the pair when the template has one."""
    if how in ("item", "skin") or param not in params:
        return [f"{param}.light", f"{param}.dark"]
    return [param]


@pytest.mark.parametrize("game", profiles.games())
def test_edit_tables_name_known_templates_slots_and_params(game):
    edit = profiles.get(game).edit
    assert set(edit.templates.values()) <= set(library.EDIT_TEMPLATES)
    assert set(edit.templates) - {None} <= set(_contract.MATERIAL_ROLES)
    assert edit.not_editable_blend_modes <= set(_contract.BLEND_MODES)
    assert edit.saturated <= set(edit.textures)
    if edit.templates:
        assert edit.saturated_roles <= set(edit.templates) - {None}
    for slot, sources in edit.textures.items():
        for s in sources:
            assert s.raw or s.key in _contract.TEXTURE_ROLES, f"{slot}: {s}"
    for template, colors in edit.colors.items():
        params = library.TEMPLATES[template].params
        for c in colors:
            for p in _params(params, c.param, c.how):
                assert p in params, f"{template}: {p}"
    every = {p for name in library.EDIT_TEMPLATES for p in library.TEMPLATES[name].params}
    for terms, values in edit.values:
        for name in values:
            assert name in every or f"{name}.light" in every, f"{terms}: {name}"
        for term in terms:
            kind, _, value = term.partition(":")
            if kind == "role":
                assert value in _contract.MATERIAL_ROLES
            if kind in ("missing", "has"):
                assert value in _edit_slots()
