"""The Rigify Hook's names and source rules, checked without Blender. names.py imports nothing, so it
is loaded from its file; the package's __init__ needs bpy."""

import ast
import importlib.util

from conftest import ADDON

RIGIFY = ADDON / "builtin" / "rigify"


def _names():
    spec = importlib.util.spec_from_file_location("rigify_names", RIGIFY / "names.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sources():
    return sorted(p for p in RIGIFY.rglob("*.py") if "__pycache__" not in p.parts)


def test_right_name_mirrors_each_kind_of_left_name():
    names = _names()
    assert names.right_name("Left arm") == "Right arm"
    assert names.right_name("Thumb0_L") == "Thumb0_R"
    assert names.right_name("Arm.L") == "Arm.R"
    assert names.right_name("Head") == "Head"


def test_skirt_bones_are_named_by_chain_and_place():
    names = _names()
    assert names.skirt_bone(True, 3) == "cf_d_sk_03_00"
    assert names.skirt_bone(False, 7, 5) == "cf_j_sk_07_05"
    assert names.skirt_deform_bone(0, 2) == "DEF-cf_j_sk_00_02"


def test_the_name_tables_cannot_be_changed():
    """Changing one changed it for the next Character imported in the session: before the rewrite
    a KK Character after a KKS one lost its Better Penetration bones' NSFW collection."""
    names = _names()
    mutable = [k for k, v in vars(names).items() if not k.startswith("_") and isinstance(v, (list, dict, set))]
    assert mutable == []


def test_no_blanket_except():
    """A missing bone or key is tested for and logged, not swallowed."""
    for path in _sources():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.ExceptHandler):
                caught = ast.unparse(node.type) if node.type else "everything"
                assert caught not in ("everything", "Exception", "BaseException"), \
                    f"{path.relative_to(ADDON)}:{node.lineno} catches {caught}"


def test_nothing_is_found_by_name_in_bpy_data():
    """The Hook reaches meshes and widgets through the Character, not bpy.data, which holds other
    Characters' too."""
    for path in _sources():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Subscript) and ast.unparse(node.value) in ("bpy.data.objects", "bpy.data.collections"):
                raise AssertionError(f"{path.relative_to(ADDON)}:{node.lineno} looks up {ast.unparse(node)}")
