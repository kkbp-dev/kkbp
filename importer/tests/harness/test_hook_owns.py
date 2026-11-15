import unittest

import hook_owns
from hook_owns import Difference


class HookOwnsTest(unittest.TestCase):
    def test_patterns(self):
        d = Difference(("objects", "Body {character}", "mesh", "vertices"), "changed", 10, 8)
        self.assertTrue(hook_owns._matches(("objects", "*", "mesh", "vertices"), d))
        self.assertTrue(hook_owns._matches(("objects", "Body {character}", "**"), d))
        self.assertFalse(hook_owns._matches(("objects", "*", "mesh"), d))
        self.assertFalse(hook_owns._matches(("materials", "**"), d))
        self.assertTrue(hook_owns._matches(lambda d: d.kind == "changed", d))

    def test_split_by_the_hooks_rules(self):
        run = hook_owns.Run("Test hook", {"use_test": True})
        hook_owns.OWNS["Test hook"] = (("objects", "*", "mesh", "vertices"),)
        try:
            owned = Difference(("objects", "Body {character}", "mesh", "vertices"), "changed", 10, 8)
            other = Difference(("materials", "cf_m_body", "images"), "changed", [], ["x"])
            self.assertEqual(hook_owns.split(run, [owned, other]), ([owned], [other]))
        finally:
            del hook_owns.OWNS["Test hook"]

    def test_variant_names(self):
        self.assertEqual(hook_owns.Run("Delete default scene").variant, "hook.delete_default_scene")
        self.assertEqual(hook_owns.Run("Convert shaders", choice="cycles").variant, "hook.convert_shaders.cycles")


if __name__ == "__main__":
    unittest.main()
