"""Tests for the rig fingerprint's host side: its names (blender/fingerprint_names.py) and the
comparison `run.py fingerprint` makes. Run with: python3 -m unittest discover importer/tests/harness"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "blender"))
import compare  # noqa: E402
import fingerprint_names  # noqa: E402
import run  # noqa: E402


class CleanerTest(unittest.TestCase):
    def test_replaces_the_names_given_and_the_metarig_id(self):
        clean = fingerprint_names.Cleaner()
        clean.replacements["Haruno Chika"] = "{character}"
        clean.replacements["abc123"] = "{rig_id}"
        self.assertEqual(clean("Rig Haruno Chika abc123 Metarig_ID:a1B2c3D4e5F6g7H8"),
                         "Rig {character} {rig_id} Metarig_ID:{random}")

    def test_leaves_other_values_alone(self):
        clean = fingerprint_names.Cleaner()
        self.assertEqual(clean(3), 3)
        self.assertIsNone(clean(None))


class SortedSetsTest(unittest.TestCase):
    def test_sorts_the_items_of_a_set_of_names(self):
        self.assertEqual(fingerprint_names.sorted_sets("if is_selected({'neck', 'head'}):"),
                         "if is_selected({'head', 'neck'}):")

    def test_two_orders_of_the_same_set_agree(self):
        a = "x = {'Left arm_fk', 'Left wrist_fk', 'Left arm_parent'} or {'b', 'a'}"
        b = "x = {'Left arm_parent', 'Left arm_fk', 'Left wrist_fk'} or {'a', 'b'}"
        self.assertEqual(fingerprint_names.sorted_sets(a), fingerprint_names.sorted_sets(b))

    def test_leaves_dicts_and_code_alone(self):
        line = "d = {'a': 1, 'b': 2}; f({x})"
        self.assertEqual(fingerprint_names.sorted_sets(line), line)


class ComparisonTest(unittest.TestCase):
    def differences(self, expected, actual):
        return compare.differences(expected, actual, tolerance=run.FINGERPRINT_TOLERANCE)

    def test_a_value_rounded_the_other_way_matches(self):
        self.assertEqual(self.differences({"head": [0.12345]}, {"head": [0.12346]}), [])

    def test_a_changed_setting_differs(self):
        self.assertEqual(self.differences({"influence": 1.0}, {"influence": 0.9999}),
                         ["/influence: 1.0 != 0.9999"])

    def test_a_changed_expression_differs(self):
        self.assertEqual(self.differences({"expression": "max(0,z)"}, {"expression": "max(0,-z)"}),
                         ["/expression: 'max(0,z)' != 'max(0,-z)'"])

    def test_constraint_order_matters(self):
        self.assertEqual(self.differences({"constraints": [{"name": "a"}, {"name": "b"}]},
                                          {"constraints": [{"name": "b"}, {"name": "a"}]}),
                         ["/constraints[0]/name: 'a' != 'b'", "/constraints[1]/name: 'b' != 'a'"])


if __name__ == "__main__":
    unittest.main()
