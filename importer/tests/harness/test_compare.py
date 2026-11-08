"""Tests for compare.py. Run with: python3 -m unittest discover importer/tests/harness"""

import unittest

import compare


class DifferencesTest(unittest.TestCase):
    def test_equal_summaries_have_no_differences(self):
        summary = {"objects": {"Body": {"mesh": {"vertices": 10, "shape_keys": ["a", "b"]}}}}
        self.assertEqual(compare.differences(summary, summary), [])

    def test_positions_within_tolerance_match(self):
        self.assertEqual(compare.differences({"head": [0.0, 1.0, 2.0]}, {"head": [0.0004, 1.0, 2.0]}), [])

    def test_positions_outside_tolerance_differ(self):
        self.assertEqual(
            compare.differences({"head": [0.0, 1.0, 2.0]}, {"head": [0.01, 1.0, 2.0]}),
            ["/head: [0.0, 1.0, 2.0] != [0.01, 1.0, 2.0]"],
        )

    def test_counts_must_match_exactly(self):
        self.assertEqual(compare.differences({"vertices": 10}, {"vertices": 11}), ["/vertices: 10 != 11"])

    def test_missing_and_unexpected_keys(self):
        self.assertEqual(
            compare.differences({"objects": {"Body": {}}}, {"objects": {"Hair": {}}}),
            ["/objects/Body: missing", "/objects/Hair: unexpected"],
        )

    def test_string_lists_report_missing_and_unexpected_items(self):
        self.assertEqual(
            compare.differences({"shape_keys": ["smile", "blink"]}, {"shape_keys": ["smile", "wink"]}),
            ["/shape_keys: missing ['blink'], unexpected ['wink']"],
        )

    def test_string_list_order_matters(self):
        self.assertEqual(
            compare.differences({"shape_keys": ["a", "b"]}, {"shape_keys": ["b", "a"]}),
            ["/shape_keys: same items, different order"],
        )

    def test_booleans_are_not_numbers(self):
        self.assertEqual(compare.differences({"deform": True}, {"deform": False}), ["/deform: True != False"])

    def test_run_details_are_ignored(self):
        self.assertEqual(compare.differences({"run": {"blender": "5.2.2"}}, {"run": {"blender": "5.3.0"}}), [])

    def test_limit(self):
        expected = {str(i): i for i in range(10)}
        actual = {str(i): i + 1 for i in range(10)}
        self.assertEqual(len(compare.differences(expected, actual, limit=3)), 3)


if __name__ == "__main__":
    unittest.main()
