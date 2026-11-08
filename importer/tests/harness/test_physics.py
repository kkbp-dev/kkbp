"""Tests for physics.py. Run with: python3 -m unittest discover importer/tests/harness"""

import unittest

import compare
import physics

ARMATURE = "/objects/Armature {character}/armature/bones"
METARIG = "Metarig {character}"
RIG = "/objects/Rig {character}/armature/bones"


def bone(id, parent, group="deform"):
    return {"id": id, "parent": parent, "group": group}


SKELETON = {"bones": [
    bone("cf_j_root", None),
    bone("cf_j_hips", "cf_j_root"),
    bone("cf_j_waist01", "cf_j_hips"),
    bone("cf_j_sk_00_00", "cf_j_waist01", "skirt"),
    bone("cf_j_sk_00_01", "cf_j_sk_00_00", "skirt"),
    bone("a_n_skirt_acc", "cf_j_sk_00_01", "helper"),
    bone("cf_j_siri_L", "cf_j_waist01"),
    bone("cf_s_siri_L", "cf_j_siri_L"),
    bone("k_f_siriL_00", "cf_s_siri_L", "helper"),
    bone("cf_j_bust01_L", "cf_j_hips", "breast"),
    bone("cf_J_hairB_00", "cf_j_hips", "hair"),
]}
METARIG_BONES = {"Hips": {}, "cf_j_waist01": {}, "cf_j_sk_00_00": {}, "cf_j_sk_00_01": {}, "cf_j_siri_L": {},
                 "cf_j_bust01_L": {}, "Left arm": {}, "Left Buttock handle": {}, "Breasts handle": {}}
SUMMARY = {"objects": {METARIG: {"armature": {"bones": METARIG_BONES}}}}


class PhysicsBonesTest(unittest.TestCase):
    def test_groups_buttocks_and_descendants(self):
        self.assertEqual(physics.physics_bones(SKELETON), {
            "cf_j_sk_00_00", "cf_j_sk_00_01", "a_n_skirt_acc", "cf_j_siri_L", "cf_s_siri_L", "k_f_siriL_00",
            "cf_j_bust01_L", "cf_J_hairB_00"})


class ToleranceTest(unittest.TestCase):
    def setUp(self):
        self.tolerance = physics.tolerance_for(SKELETON, SUMMARY)

    def test_physics_bone_heads_and_tails_get_the_physics_tolerance(self):
        for path in (f"{ARMATURE}/cf_j_sk_00_01/head", f"{ARMATURE}/k_f_siriL_00/tail",
                     f"/objects/{METARIG}/armature/bones/cf_J_hairB_00/head"):
            self.assertEqual(self.tolerance(path), physics.PHYSICS_TOLERANCE, path)

    def test_other_bones_and_other_values_keep_the_default(self):
        for path in (f"{ARMATURE}/cf_j_waist01/head", f"{ARMATURE}/cf_j_sk_00_01/parent",
                     "/objects/Body {character}/location", f"{ARMATURE}/cf_j_hips/tail"):
            self.assertEqual(self.tolerance(path), compare.DEFAULT_TOLERANCE, path)

    def test_the_rigify_handles_placed_from_physics_bones(self):
        for obj in (METARIG, "Rig {character}"):
            for bone in ("Breasts handle", "Left Breast handle", "Buttocks", "Buttocks handle", "Left Buttock handle"):
                path = f"/objects/{obj}/armature/bones/{bone}/head"
                self.assertEqual(self.tolerance(path), physics.PHYSICS_TOLERANCE, path)
        self.assertEqual(self.tolerance(f"{RIG}/MCH-Left Buttock handle/tail"), physics.PHYSICS_TOLERANCE)
        # Right side: the test skeleton has no cf_j_bust01_R or cf_j_siri_R.
        self.assertEqual(self.tolerance(f"{RIG}/Right Breast handle/head"), compare.DEFAULT_TOLERANCE)

    def test_rig_bones_and_widgets_made_from_physics_bones(self):
        for path in (f"{RIG}/DEF-cf_j_sk_00_01/head", f"{RIG}/ORG-cf_j_sk_00_00/tail", f"{RIG}/cf_j_sk_00_01/head",
                     "/objects/WGT-RIG-Armature {character}_cf_j_sk_00_01/location",
                     "/objects/WidgetButtockLeft/location", "/objects/WidgetBreasts/location"):
            self.assertEqual(self.tolerance(path), physics.PHYSICS_TOLERANCE, path)
        for path in (f"{RIG}/DEF-Left arm/head", f"{RIG}/MCH-cf_j_waist01/head",
                     "/objects/WGT-RIG-Armature {character}_Left arm_fk/location", "/objects/WidgetHips/location"):
            self.assertEqual(self.tolerance(path), compare.DEFAULT_TOLERANCE, path)


class DifferencesWithPhysicsTest(unittest.TestCase):
    def summary(self, skirt, waist):
        return {"objects": {"Armature {character}": {"armature": {"bones": {
            "cf_j_sk_00_01": {"head": skirt}, "cf_j_waist01": {"head": waist}}}}}}

    def check(self, skirt, waist):
        expected = self.summary([0.0, 0.0, 1.0], [0.0, 0.0, 0.9])
        return compare.differences(expected, self.summary(skirt, waist),
                                   tolerance=physics.tolerance_for(SKELETON, expected))

    def test_a_physics_bone_2_cm_off_matches(self):
        self.assertEqual(self.check([0.02, 0.0, 1.0], [0.0, 0.0, 0.9]), [])

    def test_a_physics_bone_4_cm_off_differs(self):
        self.assertEqual(len(self.check([0.04, 0.0, 1.0], [0.0, 0.0, 0.9])), 1)

    def test_any_other_bone_2_mm_off_differs(self):
        self.assertEqual(len(self.check([0.0, 0.0, 1.0], [0.002, 0.0, 0.9])), 1)


if __name__ == "__main__":
    unittest.main()
