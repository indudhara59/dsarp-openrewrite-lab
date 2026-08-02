from __future__ import annotations

import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smell_detector.recipe_plan import Planner, VERIFIED_OPTIONS


ROOT = Path(__file__).resolve().parents[2]


class RecipePlanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = Planner().create(ROOT)
        cls.classes = {row["fully_qualified_class_name"]: row for row in
                       json.loads((ROOT / "analysis/raw/classes.json").read_text())["classes"]}

    def test_every_recommendation_has_exactly_one_classification(self):
        recommendations = json.loads((ROOT / "analysis/recommendations/recommendations.json").read_text())["recommendations"]
        ids = [operation["recommendation_id"] for operation in self.plan["operations"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), {row["recommendation_id"] for row in recommendations})
        counts = Counter(operation["automation_class"] for operation in self.plan["operations"])
        self.assertEqual(counts, {"DECLARATIVE_BUILT_IN": 7, "REJECTED_UNSAFE": 5})

    def test_symbols_packages_and_expected_files_exist(self):
        for operation in self.plan["operations"]:
            self.assertLessEqual(set(operation["affected_symbols"]), set(self.classes))
            for source_file in operation["expected_files"]:
                self.assertTrue((ROOT / "benchmark" / source_file).is_file(), source_file)
            if operation["automation_class"] == "DECLARATIVE_BUILT_IN":
                old_package = operation["options"]["oldPackageName"]
                actual = {name for name, row in self.classes.items() if row["package"] == old_package}
                self.assertEqual(actual, set(operation["affected_symbols"]))

    def test_recipe_names_and_options_are_verified(self):
        for operation in self.plan["operations"]:
            recipe = operation["recipe_name"]
            if recipe:
                self.assertIn(recipe, VERIFIED_OPTIONS)
                self.assertLessEqual(set(operation["options"]), VERIFIED_OPTIONS[recipe])
                self.assertTrue(operation["verified_recipe_source"].startswith("https://docs.openrewrite.org/"))

    def test_executable_operations_do_not_overlap(self):
        seen = set()
        mappings = set()
        for operation in self.plan["operations"]:
            if operation["automation_class"] != "DECLARATIVE_BUILT_IN":
                continue
            self.assertTrue(seen.isdisjoint(operation["affected_symbols"]))
            seen.update(operation["affected_symbols"])
            mapping = (operation["options"]["oldPackageName"], operation["options"]["newPackageName"])
            self.assertNotIn(mapping, mappings)
            mappings.add(mapping)

    def test_stable_abstraction_is_investigated_but_not_scheduled(self):
        gap = next(row for row in self.plan["unsupported_operations"]
                   if row["operation_id"] == "UNSUPPORTED::UD-001")
        self.assertIsNone(gap["recommendation_id"])
        self.assertEqual(gap["automation_class"], "MANUAL_REFACTORING")
        self.assertEqual(len(gap["ordercore_reference_sources"]), 12)
        self.assertGreaterEqual(len(gap["experimental_implementation_sources"]), 1)
        self.assertIn("remove ordercore -> experimentalpromotions", gap["required_dependency_outcome"])

    def test_generated_json_is_valid_and_composite_name_matches(self):
        generated = json.loads((ROOT / "analysis/recipe-plan/recipe_plan.json").read_text())
        unsupported = json.loads((ROOT / "analysis/recipe-plan/unsupported_operations.json").read_text())
        self.assertEqual(generated["composite_recipe_name"],
                         "org.dsarp.architecture.RefactorBenchmarkArchitecture")
        self.assertEqual(generated, self.plan)
        self.assertEqual(unsupported["unsupported_operations"], self.plan["unsupported_operations"])


if __name__ == "__main__":
    unittest.main()
