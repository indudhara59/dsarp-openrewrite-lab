"""Translate validated recommendations into a verified, non-executing OpenRewrite plan."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

CHANGE_PACKAGE = "org.openrewrite.java.ChangePackage"
COMPOSITE = "org.dsarp.architecture.RefactorBenchmarkArchitecture"
DOCS = {
    CHANGE_PACKAGE: "https://docs.openrewrite.org/recipes/java/changepackage",
    "org.openrewrite.java.ChangeType": "https://docs.openrewrite.org/recipes/java/changetype",
    "org.openrewrite.java.dependencies.ChangeDependency": "https://docs.openrewrite.org/recipes/java/dependencies/changedependency",
    "org.openrewrite.java.dependencies.AddDependency": "https://docs.openrewrite.org/recipes/java/dependencies/adddependency",
    "org.openrewrite.java.dependencies.RemoveDependency": "https://docs.openrewrite.org/recipes/java/dependencies/removedependency",
}
VERIFIED_OPTIONS = {
    CHANGE_PACKAGE: {"oldPackageName", "newPackageName", "recursive"},
    "org.openrewrite.java.ChangeType": {"oldFullyQualifiedTypeName", "newFullyQualifiedTypeName", "ignoreDefinition"},
    "org.openrewrite.java.dependencies.ChangeDependency": {
        "oldGroupId", "oldArtifactId", "newGroupId", "newArtifactId", "newVersion",
        "versionPattern", "overrideManagedVersion", "changeManagedDependency"},
    "org.openrewrite.java.dependencies.AddDependency": {
        "groupId", "artifactId", "version", "versionPattern", "onlyIfUsing", "classifier",
        "familyPattern", "extension", "configuration", "scope", "releasesOnly", "type",
        "optional", "acceptTransitive"},
    "org.openrewrite.java.dependencies.RemoveDependency": {
        "groupId", "artifactId", "unlessUsing", "configuration", "scope"},
}


def stable_id(recommendation_id: str) -> str:
    return "OP::" + hashlib.sha256(recommendation_id.encode()).hexdigest()[:16]


def load_inputs(root: Path):
    files = {
        "recommendations": ("analysis/recommendations/recommendations.json", "recommendations"),
        "evaluation": ("analysis/ground-truth-evaluation/recommendation_evaluation.json", None),
        "classes": ("analysis/raw/classes.json", "classes"),
        "edges": ("analysis/raw/class_dependencies.json", "class_dependencies"),
    }
    values, sources = {}, []
    for name, (relative, key) in files.items():
        path = root / relative
        content = path.read_bytes()
        data = json.loads(content)
        values[name] = data[key] if key else data
        sources.append({"path": relative, "sha256": hashlib.sha256(content).hexdigest()})
    return values, sources


class Planner:
    def create(self, root: Path):
        inputs, sources = load_inputs(root)
        classes = {row["fully_qualified_class_name"]: row for row in inputs["classes"]}
        edges = inputs["edges"]
        operations, unsupported = [], []
        selected_symbols = set()
        order = 30
        for recommendation in sorted(inputs["recommendations"], key=lambda row: row["candidate_rank"]):
            if recommendation["refactoring_kind"] == "MOVE_RESPONSIBILITY_GROUP":
                operation = self._package_move(recommendation, classes, edges, order)
                operations.append(operation)
                selected_symbols.update(recommendation["source_symbols"])
                order += 1
            elif recommendation["refactoring_kind"] == "PRESERVE_FACADE":
                operation = self._rejected_facade(recommendation, classes, order)
                operations.append(operation)
                unsupported.append({
                    "operation_id": operation["operation_id"],
                    "recommendation_id": recommendation["recommendation_id"],
                    "automation_class": "REJECTED_UNSAFE",
                    "reason": "Conflicts with the higher-ranked direct move for the same responsibility group; facade API/delegation shape is not specified.",
                    "required_resolution": "Choose either direct migration or define and validate an explicit facade contract before recipe authoring.",
                })
                order += 1
            else:
                operation = self._ambiguous(recommendation, classes, order)
                operations.append(operation)
                unsupported.append({"operation_id": operation["operation_id"],
                                    "recommendation_id": recommendation["recommendation_id"],
                                    "automation_class": operation["automation_class"],
                                    "reason": "; ".join(operation["preconditions"])})
                order += 1
        unsupported.append(self._stable_abstraction_gap(inputs, classes, edges))
        source_commit = git_commit(root)
        plan = {
            "plan_version": "1.0.0",
            "source_commit": source_commit,
            "source_analysis": sources,
            "composite_recipe_name": COMPOSITE,
            "operations": operations,
            "unsupported_operations": unsupported,
            "global_preconditions": [
                "The working tree matches source_commit and contains no unreviewed overlapping edits.",
                "The benchmark clean build and all tests pass.",
                "All seven source packages contain exactly the analyzed symbol sets.",
                "A successful OpenRewrite dry run is reviewed before any rewrite:run invocation.",
                "No operation crosses a Maven module boundary in this plan.",
            ],
            "global_postconditions": [
                "All moved source paths match their new package declarations.",
                "All imports, fully qualified references, declarations, and type attribution use the new packages.",
                "No unrelated responsibility under the original component moved.",
                "The benchmark build and tests pass and the semantic analyzer reports no unresolved symbols.",
                "The resulting component graph has no newly introduced cycle.",
            ],
            "validation_commands": [
                "benchmark/mvnw -f benchmark/pom.xml clean verify",
                f"benchmark/mvnw -f benchmark/pom.xml rewrite:dryRun -Drewrite.activeRecipes={COMPOSITE}",
                "java -jar architecture-analyzer/target/architecture-analyzer-1.0.0.jar analyze --project benchmark --output analysis/dry-run --strict",
                "python3 scripts/count_benchmark_size.py",
            ],
        }
        validate_plan(plan, classes, edges)
        return plan

    def _package_move(self, recommendation, classes, edges, order):
        symbols = sorted(recommendation["source_symbols"])
        old_package = recommendation["source_package"]
        new_package = recommendation["target_package"]
        incoming_names = sorted({edge["source_class"] for edge in edges
                                 if edge["target_class"] in symbols and edge["source_class"] not in symbols})
        expected_names = symbols + incoming_names
        expected_files = sorted({classes[name]["source_file"] for name in expected_names})
        removed, added = remapped_edges(edges, old_package, new_package, set(symbols))
        escaped_package = new_package.replace(".", "\\.")
        return {
            "operation_id": stable_id(recommendation["recommendation_id"]),
            "recommendation_id": recommendation["recommendation_id"],
            "execution_order": order,
            "automation_class": "DECLARATIVE_BUILT_IN",
            "recipe_name": CHANGE_PACKAGE,
            "verified_recipe_source": DOCS[CHANGE_PACKAGE],
            "options": {"oldPackageName": old_package, "newPackageName": new_package, "recursive": False},
            "affected_symbols": symbols,
            "affected_packages": [old_package, new_package],
            "expected_files": expected_files,
            "preconditions": [
                f"Exactly {len(symbols)} analyzed production types are declared directly in {old_package}.",
                "Every affected type remains in its current Maven module.",
                "The simulated package move introduces no component cycle.",
                "No unrelated subpackage is selected because recursive is false.",
            ],
            "postconditions": [
                f"All {len(symbols)} declarations and source paths reside under {new_package}.",
                "All resolved callers reference the new fully qualified type names.",
                f"No production declaration remains directly in {old_package}.",
            ],
            "expected_dependency_edges_added": added,
            "expected_dependency_edges_removed": removed,
            "risk": "MEDIUM",
            "rollback_description": "Revert this operation's dry-run diff or apply the inverse ChangePackage mapping before any subsequent operation.",
            "validation_commands": [
                "benchmark/mvnw -f benchmark/pom.xml clean verify",
                f"rg -n '^package {escaped_package};' benchmark/shop-business/src/main/java",
            ],
        }

    def _rejected_facade(self, recommendation, classes, order):
        symbols = sorted(recommendation["source_symbols"])
        files = sorted({classes[name]["source_file"] for name in symbols})
        return {
            "operation_id": stable_id(recommendation["recommendation_id"]),
            "recommendation_id": recommendation["recommendation_id"],
            "execution_order": order,
            "automation_class": "REJECTED_UNSAFE",
            "recipe_name": None,
            "verified_recipe_source": None,
            "options": {},
            "affected_symbols": symbols,
            "affected_packages": [recommendation["source_package"], recommendation["target_package"]],
            "expected_files": files,
            "preconditions": [
                "An explicit facade API and delegation contract must be selected.",
                "The conflicting direct move must be removed from the composite plan.",
            ],
            "postconditions": ["Not scheduled; no source change is permitted from this operation."],
            "expected_dependency_edges_added": [],
            "expected_dependency_edges_removed": [],
            "risk": "HIGH",
            "rollback_description": "No rollback needed because the operation is rejected and must not execute.",
            "validation_commands": ["Confirm this operation_id is absent from the executable recipe list."],
        }

    def _ambiguous(self, recommendation, classes, order):
        symbols = sorted(recommendation["source_symbols"])
        return {
            "operation_id": stable_id(recommendation["recommendation_id"]),
            "recommendation_id": recommendation["recommendation_id"],
            "execution_order": order, "automation_class": "MANUAL_REFACTORING",
            "recipe_name": None, "verified_recipe_source": None, "options": {},
            "affected_symbols": symbols,
            "affected_packages": [recommendation["source_package"], recommendation["target_package"]],
            "expected_files": sorted({classes[name]["source_file"] for name in symbols}),
            "preconditions": ["No verified, unambiguous recipe mapping was selected for this recommendation kind."],
            "postconditions": ["Manual design review records a precise transformation or rejects it."],
            "expected_dependency_edges_added": [], "expected_dependency_edges_removed": [],
            "risk": "HIGH", "rollback_description": "No automated changes are scheduled.",
            "validation_commands": ["benchmark/mvnw -f benchmark/pom.xml clean verify"],
        }

    def _stable_abstraction_gap(self, inputs, classes, edges):
        expected = [row for row in inputs["evaluation"].get("unmatched_expected_units", [])
                    if row.get("responsibility_group") == "stable abstraction"]
        target_symbol = "com.dsarp.shop.experimentalpromotions.api.DiscountPolicy"
        ordercore_sources = sorted({edge["source_class"] for edge in edges
                                    if edge["target_class"] == target_symbol
                                    and component(edge["source_class"]) == "ordercore"})
        implementations = sorted({edge["source_class"] for edge in edges
                                  if edge["target_class"] == target_symbol
                                  and component(edge["source_class"]) == "experimentalpromotions"})
        wiring = sorted({name for name, row in classes.items()
                         if row["top_level_component"] == "application"
                         and any(dep in implementations for dep in row["outgoing_class_dependencies"])})
        destination = expected[0]["target_package"] if expected else "com.dsarp.shop.contracts.promotion"
        return {
            "operation_id": "UNSUPPORTED::UD-001",
            "recommendation_id": None,
            "automation_class": "MANUAL_REFACTORING",
            "status": "NOT_SCHEDULED",
            "reason": "Blind detection missed the unstable dependency, so no validated accepted recommendation authorizes this transformation.",
            "investigated_mechanical_mapping": {
                "recipe_name": CHANGE_PACKAGE,
                "verified_recipe_source": DOCS[CHANGE_PACKAGE],
                "options": {"oldPackageName": "com.dsarp.shop.experimentalpromotions.api",
                            "newPackageName": destination, "recursive": False},
                "note": "The built-in mapping is mechanically applicable, but scheduling it would bypass the validated recommendation pipeline.",
            },
            "affected_symbols": [target_symbol],
            "ordercore_reference_sources": ordercore_sources,
            "experimental_implementation_sources": implementations,
            "application_wiring_sources": wiring,
            "required_dependency_outcome": [
                "ordercore -> contracts.promotion",
                "experimentalpromotions -> contracts.promotion",
                "remove ordercore -> experimentalpromotions",
                "exactly one DiscountPolicy declaration",
            ],
            "maven_module_assessment": "All affected types are currently in shop-business; no Maven dependency change is required for a package-only relocation.",
        }


def remapped_edges(edges, old_package, new_package, symbols):
    removed, added = set(), set()
    for edge in edges:
        source, target = edge["source_class"], edge["target_class"]
        if source not in symbols and target not in symbols:
            continue
        new_source = rename(source, old_package, new_package)
        new_target = rename(target, old_package, new_package)
        old_edge = f"{source} -> {target}"
        new_edge = f"{new_source} -> {new_target}"
        if old_edge != new_edge:
            removed.add(old_edge)
            added.add(new_edge)
    return sorted(removed), sorted(added)


def rename(name, old_package, new_package):
    return new_package + name[len(old_package):] if name.startswith(old_package + ".") else name


def component(name):
    return name.removeprefix("com.dsarp.shop.").split(".", 1)[0]


def git_commit(root):
    process = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True,
                             capture_output=True, check=False)
    return process.stdout.strip() if process.returncode == 0 else "unavailable"


def validate_plan(plan, classes, edges):
    operation_ids, recommendation_ids = set(), set()
    executable = []
    for operation in plan["operations"]:
        if operation["operation_id"] in operation_ids:
            raise ValueError("Duplicate operation ID " + operation["operation_id"])
        operation_ids.add(operation["operation_id"])
        recommendation_id = operation["recommendation_id"]
        if recommendation_id in recommendation_ids:
            raise ValueError("Recommendation classified more than once " + recommendation_id)
        recommendation_ids.add(recommendation_id)
        missing = set(operation["affected_symbols"]) - set(classes)
        if missing:
            raise ValueError(f"Unknown symbols for {operation['operation_id']}: {sorted(missing)}")
        if operation["recipe_name"]:
            if operation["recipe_name"] not in VERIFIED_OPTIONS:
                raise ValueError("Unverified recipe " + operation["recipe_name"])
            unknown_options = set(operation["options"]) - VERIFIED_OPTIONS[operation["recipe_name"]]
            if unknown_options:
                raise ValueError(f"Unverified options {unknown_options}")
        if operation["automation_class"] == "DECLARATIVE_BUILT_IN":
            executable.append(operation)
            old_package = operation["options"]["oldPackageName"]
            actual = sorted(name for name, row in classes.items() if row["package"] == old_package)
            if actual != operation["affected_symbols"]:
                raise ValueError(f"Source package mismatch for {old_package}")
    all_selected = [symbol for op in executable for symbol in op["affected_symbols"]]
    if len(all_selected) != len(set(all_selected)):
        raise ValueError("Conflicting executable operations affect the same symbol")
    mapping = {}
    for operation in executable:
        for symbol in operation["affected_symbols"]:
            mapping[symbol] = rename(symbol, operation["options"]["oldPackageName"],
                                     operation["options"]["newPackageName"])
    graph = defaultdict(set)
    for edge in edges:
        source = component(mapping.get(edge["source_class"], edge["source_class"]))
        target = component(mapping.get(edge["target_class"], edge["target_class"]))
        if source != target:
            graph[source].add(target)
    if has_cycle(graph):
        raise ValueError("Simulated executable plan creates a component cycle")


def has_cycle(graph):
    visiting, visited = set(), set()
    def visit(node):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in sorted(graph.get(node, ()))):
            return True
        visiting.remove(node)
        visited.add(node)
        return False
    return any(visit(node) for node in sorted(graph))
