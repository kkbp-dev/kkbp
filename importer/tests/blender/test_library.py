"""Every Template Description against library.blend: each template, node, socket and group it
names must exist (docs/design/material-template.md, "Template Descriptions")."""

import bpy
import pytest

from conftest import submodule

library = submodule("library")
templates = submodule("templates")


@pytest.fixture(scope="module")
def blend():
    """The library's materials and node groups, read straight from the file into an empty one."""
    bpy.ops.wm.read_homefile(use_empty=True)
    with bpy.data.libraries.load(str(library.LIBRARY), link=False) as (source, target):
        target.materials = list(source.materials)
        target.node_groups = list(source.node_groups)
    materials = {m.name: m for m in target.materials}
    groups = {g.name: g for g in target.node_groups}
    yield materials, groups


@pytest.fixture(autouse=True)
def empty_scene():
    """The library stays loaded for the whole module, so the scene isn't reset between tests."""
    yield


def _inputs(group):
    return [i.name for i in group.interface.items_tree if i.item_type == "SOCKET" and i.in_out == "INPUT"]


def _outputs(group):
    return [i.name for i in group.interface.items_tree if i.item_type == "SOCKET" and i.in_out == "OUTPUT"]


def _socket(node, name):
    if node.type == "VALUE":
        return node.outputs.get(name)
    return node.inputs.get(name)


@pytest.mark.parametrize("name", sorted(library.TEMPLATES))
def test_every_description_matches_the_library(blend, name):
    materials, groups = blend
    template = library.TEMPLATES[name]
    assert name in materials, f"library.blend has no template {name}"
    nodes = materials[name].node_tree.nodes
    at = lambda path: templates.node_at(materials[name], path)  # noqa: E731
    for slot, node_name in template.textures.items():
        assert at(node_name) is not None and at(node_name).type == "TEX_IMAGE", f"{name}: {slot} -> {node_name}"
    for param, (node_name, socket) in template.params.items():
        assert at(node_name) is not None, f"{name}: param {param} names node {node_name}"
        assert _socket(at(node_name), socket) is not None, f"{name}: {node_name} has no socket {socket}"
    for path in template.copies:
        assert at(path) is not None and at(path).type == "GROUP", f"{name}: copies {path}"
    assert list(template.copies) == sorted(template.copies, key=lambda p: p.count("/")), "outermost first"
    for slot, path in template.positions.items():
        assert slot in template.textures and at(path).type == "GROUP", f"{name}: position {slot} -> {path}"
        assert set(library.POSITION_SOCKETS.values()) <= set(_inputs(at(path).node_tree))
    if template.shader:
        assert nodes[template.shader].type == "GROUP"
        shader_inputs = _inputs(nodes[template.shader].node_tree)
        for variant, group_name in template.variants.items():
            assert group_name in groups, f"{name}: variant {variant} names group {group_name}"
            missing = [s for s in shader_inputs if s not in _inputs(groups[group_name])
                       and s != "Disable permalight mask" and s not in template.variant_drops]
            assert not missing, f"{name}: swapping to {group_name} would drop {missing}"
            for param, (node_name, socket) in template.variant_params.get(variant, {}).items():
                assert node_name == template.shader and socket in _inputs(groups[group_name]), \
                    f"{name}: {variant} param {param} -> {socket}"
    for group_name in template.groups:
        assert group_name in groups, f"{name} needs group {group_name}"
    patterns = template.patterns
    if patterns and patterns.nodes:
        for node_name in patterns.nodes:
            assert node_name in nodes and nodes[node_name].type == "TEX_IMAGE"
    if patterns and patterns.chain:
        chain, sockets = patterns.chain, patterns.chain.sockets
        uv, pick = groups[chain.uv_group], groups[chain.pick_group]
        assert set(chain.pattern_params.values()) | {sockets["frame"]} <= set(_inputs(uv))
        assert sockets["vector"] in _outputs(uv)
        assert {sockets[k] for k in ("choice", "index", "color", "alpha", "previous_color", "previous_alpha")} \
            <= set(_inputs(pick))
        assert {sockets["picked_color"], sockets["picked_alpha"]} <= set(_outputs(pick))
        output = nodes[chain.output]
        assert output.inputs.get(sockets["output_color"]) and output.inputs.get(sockets["output_alpha"])


def test_every_template_and_group_carries_the_template_version(blend):
    materials, groups = blend
    assert set(materials) == set(library.TEMPLATES), "library.blend holds exactly the described templates"
    for datablock in list(materials.values()) + list(groups.values()):
        assert datablock.get(library.VERSION_PROP) == library.TEMPLATE_VERSION, datablock.name


def test_every_extra_is_in_the_library():
    with bpy.data.libraries.load(str(library.LIBRARY), link=False) as (source, target):
        names = {kind: set(getattr(source, kind)) for kind in ("images", "node_groups")}
    for name, (kind, datablock) in library.EXTRAS.items():
        assert datablock in names[kind], f"library.blend has no {kind} {datablock} ({name})"
