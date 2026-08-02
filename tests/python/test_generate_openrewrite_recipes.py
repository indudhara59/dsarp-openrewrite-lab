from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "tools" / "generate_openrewrite_recipes.py"
SPEC = importlib.util.spec_from_file_location("recipe_generator", MODULE_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


def operation(
    operation_id: str = "OP::one",
    order: int = 10,
    automation_class: str = "DECLARATIVE_BUILT_IN",
) -> dict:
    return {
        "operation_id": operation_id,
        "recommendation_id": "REC::one",
        "execution_order": order,
        "automation_class": automation_class,
        "recipe_name": "org.openrewrite.java.ChangePackage",
        "verified_recipe_source": "https://docs.openrewrite.org/recipes/java/changepackage",
        "options": {
            "oldPackageName": "com.dsarp.shop.old",
            "newPackageName": "com.dsarp.shop.new",
            "recursive": False,
        },
        "affected_symbols": ["com.dsarp.shop.old.Example"],
        "affected_packages": ["com.dsarp.shop.old", "com.dsarp.shop.new"],
        "expected_files": ["src/main/java/com/dsarp/shop/old/Example.java"],
        "preconditions": [],
        "postconditions": [],
        "expected_dependency_edges_added": [],
        "expected_dependency_edges_removed": [],
        "risk": "LOW",
        "rollback_description": "Revert the reviewed diff.",
        "validation_commands": [],
    }


def plan(operations: list[dict] | None = None) -> dict:
    return {
        "plan_version": "1.0.0",
        "source_commit": "a" * 40,
        "source_analysis": [],
        "composite_recipe_name": "org.dsarp.architecture.RefactorBenchmarkArchitecture",
        "operations": [operation()] if operations is None else operations,
        "unsupported_operations": [],
        "global_preconditions": [],
        "global_postconditions": [],
        "validation_commands": [],
    }


class RecipeGeneratorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_plan(self, value: dict, strict: bool = False):
        path = self.directory / "plan.json"
        path.write_text(json.dumps(value), encoding="utf-8", newline="\n")
        return generator.generate(
            path,
            strict=strict,
            timestamp="2026-01-01T00:00:00Z",
        )

    def test_valid_change_package_generation(self):
        result = self.run_plan(plan())
        self.assertEqual(0, result.exit_code)
        document = yaml.safe_load(result.yaml_bytes)
        self.assertEqual(
            {"oldPackageName": "com.dsarp.shop.old", "newPackageName": "com.dsarp.shop.new", "recursive": False},
            document["recipeList"][0]["org.openrewrite.java.ChangePackage"],
        )

    def test_multiple_operations_are_ordered(self):
        later = operation("OP::later", 20)
        earlier = operation("OP::earlier", 10)
        earlier["options"]["oldPackageName"] = "com.dsarp.shop.first"
        result = self.run_plan(plan([later, earlier]))
        recipes = yaml.safe_load(result.yaml_bytes)["recipeList"]
        self.assertEqual(
            "com.dsarp.shop.first",
            recipes[0]["org.openrewrite.java.ChangePackage"]["oldPackageName"],
        )

    def test_deterministic_output(self):
        first = self.run_plan(plan()).yaml_bytes
        second = self.run_plan(plan()).yaml_bytes
        self.assertEqual(first, second)

    def test_malformed_json(self):
        path = self.directory / "bad.json"
        path.write_text("{", encoding="utf-8")
        result = generator.generate(path, strict=False)
        self.assertNotEqual(0, result.exit_code)
        self.assertIn("malformed JSON", result.report["validation_errors"][0])

    def test_schema_violation(self):
        value = plan()
        value["unexpected"] = True
        result = self.run_plan(value)
        self.assertNotEqual(0, result.exit_code)
        self.assertTrue(result.report["validation_errors"])

    def test_missing_parameters(self):
        value = plan()
        del value["operations"][0]["options"]["newPackageName"]
        result = self.run_plan(value)
        self.assertIn("missing parameters", " ".join(result.report["validation_errors"]))

    def test_unknown_parameters(self):
        value = plan()
        value["operations"][0]["options"]["rationale"] = "move it"
        result = self.run_plan(value)
        self.assertIn("unknown parameters", " ".join(result.report["validation_errors"]))

    def test_unknown_recipe(self):
        value = plan()
        value["operations"][0]["recipe_name"] = "org.example.Unknown"
        result = self.run_plan(value)
        self.assertIn("unknown recipe mapping", " ".join(result.report["validation_errors"]))

    def test_duplicate_operations(self):
        result = self.run_plan(plan([operation(), operation()]))
        self.assertIn("duplicate operation ID", " ".join(result.report["validation_errors"]))

    def test_conflicting_moves(self):
        first = operation("OP::one")
        second = operation("OP::two")
        second["options"]["newPackageName"] = "com.dsarp.shop.other"
        result = self.run_plan(plan([first, second]))
        self.assertIn("conflicting package moves", " ".join(result.report["validation_errors"]))

    def test_invalid_java_package(self):
        value = plan()
        value["operations"][0]["options"]["newPackageName"] = "com.dsarp.shop.Bad-Package"
        result = self.run_plan(value)
        self.assertIn("invalid Java package", " ".join(result.report["validation_errors"]))

    def test_invalid_recipe_fqn(self):
        value = plan()
        value["operations"][0]["recipe_name"] = "not a recipe"
        result = self.run_plan(value)
        self.assertIn("invalid recipe FQN", " ".join(result.report["validation_errors"]))

    def test_manual_operation_exclusion(self):
        item = operation(automation_class="MANUAL_REFACTORING")
        item["recipe_name"] = None
        item["verified_recipe_source"] = None
        item["options"] = {}
        result = self.run_plan(plan([item]))
        self.assertEqual([], yaml.safe_load(result.yaml_bytes)["recipeList"])
        self.assertEqual(["OP::one"], result.report["skipped_operation_ids"])

    def test_unsafe_operation_exclusion(self):
        item = operation(automation_class="REJECTED_UNSAFE")
        item["recipe_name"] = None
        item["verified_recipe_source"] = None
        item["options"] = {}
        result = self.run_plan(plan([item]))
        self.assertEqual([], yaml.safe_load(result.yaml_bytes)["recipeList"])

    def test_custom_recipe_reference_with_artifact(self):
        (self.directory / "recipe.jar").write_bytes(b"test artifact")
        item = operation(automation_class="CUSTOM_IMPERATIVE_RECIPE")
        item["recipe_name"] = "org.dsarp.recipe.CustomMove"
        item["verified_recipe_source"] = "recipe.jar"
        item["options"] = {}
        result = self.run_plan(plan([item]), strict=True)
        self.assertEqual(0, result.exit_code)
        self.assertEqual(
            ["org.dsarp.recipe.CustomMove"], yaml.safe_load(result.yaml_bytes)["recipeList"]
        )

    def test_custom_recipe_without_artifact_fails_strict(self):
        item = operation(automation_class="CUSTOM_IMPERATIVE_RECIPE")
        item["recipe_name"] = "org.dsarp.recipe.CustomMove"
        item["verified_recipe_source"] = "missing.jar"
        item["options"] = {}
        result = self.run_plan(plan([item]), strict=True)
        self.assertNotEqual(0, result.exit_code)
        self.assertIsNone(result.yaml_bytes)

    def test_manual_operation_fails_strict(self):
        item = operation(automation_class="MANUAL_REFACTORING")
        item["recipe_name"] = None
        item["verified_recipe_source"] = None
        item["options"] = {}
        result = self.run_plan(plan([item]), strict=True)
        self.assertNotEqual(0, result.exit_code)
        self.assertEqual("FAILED", result.report["strict_mode_result"])

    def test_free_form_text_cannot_inject_yaml(self):
        value = plan()
        value["operations"][0]["rollback_description"] = "!!python/object/apply:os.system ['id']"
        result = self.run_plan(value)
        self.assertNotIn(b"python/object", result.yaml_bytes)
        yaml.safe_load(result.yaml_bytes)

    def test_empty_plan(self):
        result = self.run_plan(plan([]), strict=True)
        self.assertEqual(0, result.exit_code)
        self.assertEqual([], yaml.safe_load(result.yaml_bytes)["recipeList"])

    def test_output_digest_generation(self):
        result = self.run_plan(plan())
        self.assertEqual(generator.sha256(result.yaml_bytes), result.report["output_digest"])
        self.assertEqual(64, len(result.report["output_digest"]))


if __name__ == "__main__":
    unittest.main()
