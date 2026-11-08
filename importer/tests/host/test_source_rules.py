"""Rules about the add-on's source that are checked by reading it."""

import ast
import re
import sys

from conftest import ADDON

# Packages that never import bpy, so host tests (and bundle/) can import them directly.
PURE = (ADDON / "bundle", ADDON / "profiles", ADDON / "library")


def _sources(folder):
    return sorted(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)


def test_pure_packages_import_only_the_standard_library_and_themselves():
    for path in [p for folder in PURE for p in _sources(folder)]:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                assert top in sys.stdlib_module_names or top == "__future__", \
                    f"{path.relative_to(ADDON)}:{node.lineno} imports {name}"


def test_blender_version_is_checked_only_in_compat():
    """docs/design/blender-compat-and-testing.md: bpy.app.version appears only in compat/.
    (bpy.app.version_string, for messages, is fine anywhere.)"""
    pattern = re.compile(r"\bbpy\.app\.version\b")
    for path in _sources(ADDON):
        if "compat" in path.relative_to(ADDON).parts:
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not pattern.search(line), f"{path.relative_to(ADDON)}:{number} checks the Blender version"


def test_built_in_code_never_reads_ctx_game():
    """docs/design/game-profile.md: built-in Steps and Hooks never check ctx.game. Game
    differences come from Game lists and the bundle's Roles, Groups and Names."""
    for path in _sources(ADDON):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Attribute) and node.attr == "game" and \
                    isinstance(node.value, ast.Name) and node.value.id == "ctx":
                raise AssertionError(f"{path.relative_to(ADDON)}:{node.lineno} reads ctx.game")


def test_the_atlas_uses_pillow_and_never_bpy():
    """D28: the atlas's layout and compositing run without Blender, so pytest tests them."""
    for path in _sources(ADDON / "atlas"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 else []
            for name in names:
                top = name.split(".")[0]
                assert top in sys.stdlib_module_names or top in ("__future__", "PIL"), \
                    f"{path.relative_to(ADDON)}:{node.lineno} imports {name}"


def test_shading_uses_numpy_and_never_bpy():
    """D42: the edit colours' maths runs without Blender, so pytest tests it."""
    for path in _sources(ADDON / "shading"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module] if isinstance(node, ast.ImportFrom) and node.level == 0 else []
            for name in names:
                top = name.split(".")[0]
                assert top in sys.stdlib_module_names or top in ("__future__", "numpy"), \
                    f"{path.relative_to(ADDON)}:{node.lineno} imports {name}"


def _api_list(name):
    """A tuple or list of strings assigned to `name` in kkbp/api.py, read without importing it (bpy)."""
    tree = ast.parse((ADDON / "api.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == name for t in n.targets))
    return [e.value for e in node.value.elts]


def test_the_hook_interface_doc_names_the_whole_public_api():
    """docs/hook-interface.md is the hook interface: every public name is in it."""
    doc = (ADDON.parents[1] / "docs" / "hook-interface.md").read_text(encoding="utf-8")
    for name in _api_list("__all__"):
        assert f"kkbp.{name}" in doc or f"`{name}" in doc, f"docs/hook-interface.md doesn't mention kkbp.{name}"
    for name in _api_list("TEMPLATE_FUNCTIONS"):
        assert f"templates.{name}(" in doc, f"docs/hook-interface.md doesn't describe kkbp.templates.{name}"
    version = re.search(r'HOOK_API_VERSION = "([0-9.]+)"', (ADDON / "pipeline" / "hooks.py").read_text(encoding="utf-8"))
    assert f"# Hook interface {version.group(1)}" in doc
