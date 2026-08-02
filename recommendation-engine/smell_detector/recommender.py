"""Deterministic, smell-specific refactoring candidate generation and ranking."""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

PACKAGE = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+$")
ABSTRACTION_SUFFIXES = ("Policy", "Port", "Gateway", "Contract", "Interface", "Provider")

RANKING_WEIGHTS = {
    "expected_smell_reduction": 0.30,
    "cohesion": 0.20,
    "reference_manageability": 0.10,
    "low_behavior_risk": 0.10,
    "low_package_cycle_risk": 0.10,
    "low_module_cycle_risk": 0.05,
    "automation_feasibility": 0.10,
    "test_coverage": 0.05,
}


def rounded(value: float) -> float:
    return round(value + 0.0, 6)


def stable_id(prefix: str, key: tuple[Any, ...]) -> str:
    canonical = "|".join(
        ",".join(sorted(value)) if isinstance(value, (list, tuple, set)) else str(value)
        for value in key
    )
    return f"{prefix}::{hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]}"


def component_of(class_name: str) -> str:
    return class_name.removeprefix("com.dsarp.shop.").split(".", 1)[0]


@dataclass(frozen=True)
class RecommendationResult:
    candidates: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
    warnings: list[str]


class Recommender:
    def generate(self, findings, metrics, component_edges, clusters, classes, class_edges):
        class_by_name = {row["fully_qualified_class_name"]: row for row in classes}
        metric_by_component = {row["component"]: row for row in metrics}
        candidates = []
        warnings = []
        for finding in sorted(findings, key=lambda row: row["finding_id"]):
            if finding["smell_type"] == "GOD_COMPONENT":
                candidates.extend(self._god_candidates(
                    finding, metric_by_component, clusters, class_by_name, class_edges))
            elif finding["smell_type"] == "UNSTABLE_DEPENDENCY":
                candidates.extend(self._unstable_candidates(
                    finding, metric_by_component, component_edges, class_by_name, class_edges))
            else:
                warnings.append(f"Unsupported smell type {finding['smell_type']} for {finding['finding_id']}")
        candidates = self._deduplicate(candidates)
        candidates.sort(key=lambda row: (-row["ranking_score"], row["candidate_id"]))
        recommendations = [dict(row) for row in candidates if not row["rejection_reasons"]]
        for rank, recommendation in enumerate(recommendations, start=1):
            recommendation["candidate_rank"] = rank
            recommendation["recommendation_id"] = stable_id("REC", self._dedup_key(recommendation))
            recommendation.pop("candidate_id", None)
            recommendation.pop("ranking_score", None)
            recommendation.pop("ranking_features", None)
        for rank, candidate in enumerate(candidates, start=1):
            candidate["candidate_rank"] = rank
        return RecommendationResult(candidates, recommendations, sorted(set(warnings)))

    def _god_candidates(self, finding, metrics, clusters, class_by_name, class_edges):
        component = finding["primary_component"]
        component_clusters = sorted(
            (row for row in clusters if row["component"] == component),
            key=lambda row: row["cluster_id"])
        result = []
        for cluster in component_clusters:
            members = sorted(cluster["member_classes"])
            if not members:
                continue
            source_packages = sorted({class_by_name[name]["package"] for name in members})
            destination = self._destination(cluster, component)
            member_set = set(members)
            incoming = sorted({(edge["source_class"], edge["target_class"])
                               for edge in class_edges if edge["target_class"] in member_set
                               and edge["source_class"] not in member_set})
            outgoing = sorted({(edge["source_class"], edge["target_class"])
                               for edge in class_edges if edge["source_class"] in member_set
                               and edge["target_class"] not in member_set})
            facade_symbols = sorted({target for source, target in incoming
                                     if component_of(source) != component
                                     and class_by_name[target]["public_type_count"] > 0})
            external_incoming = [(source, target) for source, target in incoming
                                 if component_of(source) != component]
            package_cycle = self._would_create_cycle(class_edges, member_set, destination)
            module_cycle = False  # package relocation remains in the existing Maven module
            base = self._god_candidate(
                finding, metrics[component], cluster, source_packages, destination,
                members, incoming, outgoing, package_cycle, module_cycle,
                preserve_facade=False, facade_symbols=[], maven_module=class_by_name[members[0]]["maven_module"])
            result.append(base)
            if len(external_incoming) >= 2 and facade_symbols:
                result.append(self._god_candidate(
                    finding, metrics[component], cluster, source_packages, destination,
                    members, incoming, outgoing, package_cycle, module_cycle,
                    preserve_facade=True, facade_symbols=facade_symbols,
                    maven_module=class_by_name[members[0]]["maven_module"]))
        return result

    def _god_candidate(self, finding, metric, cluster, source_packages, destination,
                       members, incoming, outgoing, package_cycle, module_cycle,
                       preserve_facade, facade_symbols, maven_module):
        group_share = len(members) / metric["production_class_count"]
        cohesion = rounded(0.5 * cluster["cohesion_score"] + 0.5 * cluster["confidence"])
        reference_count = len(incoming) + len(outgoing)
        manageability = 1.0 / (1.0 + reference_count / max(1, len(members)))
        behavior_risk_value = min(1.0, 0.20 + reference_count / 100.0 + (0.05 if preserve_facade else 0.10))
        automation = 0.92 if not preserve_facade else 0.82
        features = {
            "expected_smell_reduction": rounded(min(1.0, group_share * 2.0)),
            "cohesion": cohesion,
            "reference_manageability": rounded(manageability),
            "low_behavior_risk": rounded(1.0 - behavior_risk_value),
            "low_package_cycle_risk": 0.0 if package_cycle else 1.0,
            "low_module_cycle_risk": 0.0 if module_cycle else 1.0,
            "automation_feasibility": automation,
            "test_coverage": 0.5,
        }
        score = rounded(sum(RANKING_WEIGHTS[key] * features[key] for key in RANKING_WEIGHTS))
        kind = "PRESERVE_FACADE" if preserve_facade else "MOVE_RESPONSIBILITY_GROUP"
        target_symbol = cluster["cluster_id"]
        rejection = []
        if package_cycle:
            rejection.append("Move would create a package-component dependency cycle.")
        if module_cycle:
            rejection.append("Move would create a Maven module cycle.")
        if not PACKAGE.fullmatch(destination):
            rejection.append("Generated destination package is not a valid Java package.")
        key = (finding["finding_id"], kind, tuple(members), destination, target_symbol)
        related = sorted({value for edge in incoming + outgoing for value in edge if value not in set(members)})
        return {
            "candidate_id": stable_id("CAND", key),
            "recommendation_id": stable_id("REC", key),
            "finding_id": finding["finding_id"],
            "smell_type": finding["smell_type"],
            "candidate_rank": 0,
            "detection_confidence": finding["detection_confidence"],
            "refactoring_confidence": rounded(0.55 * cluster["confidence"] + 0.45 * automation),
            "source_component": finding["primary_component"],
            "target_component": destination.removeprefix("com.dsarp.shop.").split(".", 1)[0],
            "source_package": source_packages[0] if len(source_packages) == 1 else source_packages,
            "target_package": destination,
            "source_symbols": members,
            "related_symbols": related,
            "refactoring_kind": kind,
            "parameters": {
                "cluster_id": cluster["cluster_id"],
                "move_group_as_unit": True,
                "preserve_facade": preserve_facade,
                "facade_symbols": facade_symbols,
                "target_symbol": target_symbol,
                "keep_maven_module": maven_module,
            },
            "evidence": {
                "dominant_subpackage": cluster["dominant_subpackage"],
                "dominant_name_tokens": cluster["dominant_name_tokens"],
                "cluster_cohesion_score": cluster["cohesion_score"],
                "cluster_confidence": cluster["confidence"],
                "internal_edge_count": cluster["internal_edge_count"],
                "incoming_reference_count": len(incoming),
                "outgoing_reference_count": len(outgoing),
                "external_incoming_reference_count": len([e for e in incoming if component_of(e[0]) != finding["primary_component"]]),
            },
            "rationale": (
                f"Move the measured {cluster['dominant_subpackage']} responsibility cluster as one unit "
                f"to {destination}; the candidate contains {len(members)} classes and is distinct by "
                f"cluster {cluster['cluster_id']}." +
                (" Preserve externally referenced entry types as delegating facades to limit migration."
                 if preserve_facade else " Update resolved callers directly without renaming the whole component.")),
            "expected_metric_effect": {
                "source_class_count_delta": -len(members),
                "target_class_count_delta": len(members),
                "source_responsibility_cluster_count_delta": -1,
                "god_component_score_direction": "decrease",
            },
            "expected_dependency_changes": {
                "class_references_requiring_update": reference_count,
                "incoming_references": [list(edge) for edge in incoming],
                "outgoing_references_preserved": [list(edge) for edge in outgoing],
                "facade_delegations_added": facade_symbols if preserve_facade else [],
            },
            "preconditions": [
                "All source symbols still exist at the analyzed commit.",
                "The responsibility group passes its existing tests before relocation.",
                "A reviewed dry-run must show no unexpected type-attribution changes.",
            ],
            "postconditions": [
                f"All group implementation types are declared under {destination}.",
                "No duplicate source types remain in the original package.",
                "The benchmark build and tests pass with behavior unchanged.",
            ],
            "behavior_risk": risk_label(behavior_risk_value),
            "architecture_risk": "HIGH" if package_cycle or module_cycle else ("LOW" if preserve_facade else "MEDIUM"),
            "estimated_files_changed": len(members) + len({source for source, _ in incoming}),
            "automatable": not rejection,
            "automation_notes": "Package/type moves and import updates are suitable for a reviewed semantic recipe; facade delegation requires a custom Java recipe." if preserve_facade else "Package/type moves and resolved import updates are suitable for a reviewed semantic recipe.",
            "validation_commands": [
                "benchmark/mvnw -f benchmark/pom.xml clean verify",
                "java -jar architecture-analyzer/target/architecture-analyzer-1.0.0.jar analyze --project benchmark --output analysis/after --strict",
            ],
            "rejection_reasons": rejection,
            "ranking_score": score,
            "ranking_features": features,
        }

    def _unstable_candidates(self, finding, metrics, component_edges, class_by_name, class_edges):
        source = finding["primary_component"]
        target = finding["related_component"]
        exact = sorted({(edge["source_class"], edge["target_class"])
                        for edge in class_edges
                        if component_of(edge["source_class"]) == source
                        and component_of(edge["target_class"]) == target})
        by_target = defaultdict(list)
        for edge in exact:
            by_target[edge[1]].append(edge)
        result = []
        for target_symbol, references in sorted(by_target.items()):
            source_symbols = sorted({edge[0] for edge in references})
            looks_abstract = target_symbol.endswith(ABSTRACTION_SUFFIXES)
            simple = target_symbol.rsplit(".", 1)[-1]
            domain = token_prefix(simple) or target
            destination = f"com.dsarp.shop.contracts.{domain}"
            kind = "INTRODUCE_STABLE_ABSTRACTION" if looks_abstract else "CHANGE_DEPENDENCY"
            rejection = [] if looks_abstract else [
                "Target type is not identifiable as an abstraction from validated analyzer data; manual design review required."
            ]
            source_modules = {class_by_name[name]["maven_module"] for name in source_symbols}
            target_module = class_by_name[target_symbol]["maven_module"]
            module_cycle = target_module not in source_modules and self._module_cycle(
                class_edges, class_by_name, source_modules, target_module)
            if module_cycle:
                rejection.append("Relocating the abstraction would create a Maven module cycle.")
            migration = len(references)
            features = {
                "expected_smell_reduction": 1.0 if looks_abstract else 0.4,
                "cohesion": 1.0,
                "reference_manageability": rounded(1.0 / (1.0 + migration / max(1, len(source_symbols)))),
                "low_behavior_risk": 0.85 if looks_abstract else 0.5,
                "low_package_cycle_risk": 1.0,
                "low_module_cycle_risk": 0.0 if module_cycle else 1.0,
                "automation_feasibility": 0.85 if looks_abstract else 0.2,
                "test_coverage": 0.5,
            }
            score = rounded(sum(RANKING_WEIGHTS[key] * features[key] for key in RANKING_WEIGHTS))
            key = (finding["finding_id"], kind, tuple(source_symbols), destination, target_symbol)
            result.append({
                "candidate_id": stable_id("CAND", key), "recommendation_id": stable_id("REC", key),
                "finding_id": finding["finding_id"], "smell_type": finding["smell_type"], "candidate_rank": 0,
                "detection_confidence": finding["detection_confidence"],
                "refactoring_confidence": 0.85 if looks_abstract and not module_cycle else 0.35,
                "source_component": source, "target_component": "contracts",
                "source_package": sorted({class_by_name[name]["package"] for name in source_symbols}),
                "target_package": destination, "source_symbols": source_symbols,
                "related_symbols": [target_symbol], "refactoring_kind": kind,
                "parameters": {"target_symbol": target_symbol, "relocate_existing_type": looks_abstract,
                               "copy_interface": False, "composition_wiring_changes_required": True},
                "evidence": {"exact_class_references": [list(edge) for edge in references],
                             "target_looks_abstract": looks_abstract, "reference_count": migration},
                "rationale": f"Relocate the existing {simple} contract to {destination} and update only the exact resolved dependency edge; never copy the type.",
                "expected_metric_effect": {"unstable_dependency_edge_removed": f"{source} -> {target}"},
                "expected_dependency_changes": {"remove": [f"{source} -> {target}"],
                                                "add": [f"{source} -> contracts", f"{target} -> contracts"]},
                "preconditions": ["Confirm the target is an abstraction.", "Confirm implementation ownership and composition wiring."],
                "postconditions": ["Exactly one abstraction type exists.", "Both source and implementation depend on the stable contract."],
                "behavior_risk": "LOW" if looks_abstract else "HIGH",
                "architecture_risk": "HIGH" if module_cycle else "LOW",
                "estimated_files_changed": len(source_symbols) + 2, "automatable": not rejection,
                "automation_notes": "Semantic type relocation and import updates are automatable after design review." if looks_abstract else "Requires manual abstraction design review.",
                "validation_commands": ["benchmark/mvnw -f benchmark/pom.xml clean verify"],
                "rejection_reasons": rejection, "ranking_score": score, "ranking_features": features,
            })
        return result

    def _destination(self, cluster, source_component):
        evidence = sanitize(cluster["dominant_subpackage"])
        if not evidence or evidence == "root" or evidence == source_component:
            evidence = sanitize(next(iter(cluster["dominant_name_tokens"]), "responsibility"))
        return f"com.dsarp.shop.{evidence}"

    def _would_create_cycle(self, class_edges, moved, destination):
        target_component = destination.removeprefix("com.dsarp.shop.").split(".", 1)[0]
        graph = defaultdict(set)
        for edge in class_edges:
            source = target_component if edge["source_class"] in moved else component_of(edge["source_class"])
            target = target_component if edge["target_class"] in moved else component_of(edge["target_class"])
            if source != target:
                graph[source].add(target)
        return has_cycle(graph)

    def _module_cycle(self, class_edges, class_by_name, source_modules, target_module):
        graph = defaultdict(set)
        for edge in class_edges:
            left = class_by_name[edge["source_class"]]["maven_module"]
            right = class_by_name[edge["target_class"]]["maven_module"]
            if left != right:
                graph[left].add(right)
        return any(path_exists(graph, target_module, source) for source in source_modules)

    def _dedup_key(self, row):
        return (row["finding_id"], row["refactoring_kind"], tuple(sorted(row["source_symbols"])),
                row["target_package"], row["parameters"].get("target_symbol", ""))

    def _deduplicate(self, candidates):
        result = {}
        for candidate in candidates:
            key = self._dedup_key(candidate)
            previous = result.get(key)
            if previous is None or candidate["ranking_score"] > previous["ranking_score"]:
                result[key] = candidate
        return list(result.values())


def sanitize(value: str) -> str:
    cleaned = "".join(character.lower() if character.isalnum() or character == "_" else "_"
                      for character in value)
    if not cleaned or cleaned[0].isdigit():
        cleaned = "responsibility_" + cleaned
    return cleaned


def token_prefix(name: str) -> str:
    characters = []
    for index, character in enumerate(name):
        if index and character.isupper():
            break
        characters.append(character.lower())
    return sanitize("".join(characters))


def risk_label(value: float) -> str:
    return "LOW" if value < 0.35 else ("MEDIUM" if value < 0.65 else "HIGH")


def class_module(members, class_by_name):
    modules = sorted({class_by_name[name]["maven_module"] for name in members if name in class_by_name})
    return modules[0] if len(modules) == 1 else modules


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


def path_exists(graph, source, target):
    pending, seen = [source], set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current not in seen:
            seen.add(current)
            pending.extend(sorted(graph.get(current, ()), reverse=True))
    return False
