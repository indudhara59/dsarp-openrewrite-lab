"""Ground-truth evaluation with explicitly frozen matching rules."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any


MATCHING_RULES = {
    "detection_exact": "Normalized smell type and affected component set are equal.",
    "detection_partial": "Normalized smell type is equal and affected component sets overlap but are not equal.",
    "false_positive": "A detected finding has no exact or partial ground-truth match.",
    "false_negative": "A ground-truth smell has no exact or partial detected finding.",
    "recommendation_exact": "Finding matches, expected destination package matches, expected responsibility/type matches, and the operation directly implements the intended boundary.",
    "recommendation_partial": "Finding and destination match but expected representative symbols or responsibility evidence are incomplete.",
    "semantic_alternative": "The intended destination and responsibility match, with a behavior-preserving alternative such as retaining a delegating facade.",
    "incorrect": "The recommendation does not match an expected destination/responsibility for its finding.",
    "unsafe": "The recommendation matches semantically but has a rejection reason or HIGH architecture risk.",
    "unautomatable_valid": "The recommendation is exact/partial/alternative but is explicitly non-automatable.",
    "symbol_overlap": "Set overlap of normalized simple names from recommendation source_symbols against all explicit ground-truth affected_symbols.",
    "package_overlap": "Set overlap of recommendation target_package values against normalized expected destination packages.",
}


def canonical_smell(value: str) -> str:
    return value.lower().replace("_", " ").strip()


def simple_name(value: str) -> str:
    return value.rsplit(".", 1)[-1]


def components_for_finding(finding: dict[str, Any]) -> set[str]:
    values = {finding["primary_component"]}
    if finding.get("related_component"):
        values.add(finding["related_component"])
    return values


def safe_divide(numerator: float, denominator: float) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def prf(tp: int, fp: int, fn: int) -> dict[str, float | int]:
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    return {"true_positives": tp, "false_positives": fp, "false_negatives": fn,
            "precision": precision, "recall": recall, "f1": f1}


@dataclass(frozen=True)
class EvaluationResult:
    detection: dict[str, Any]
    recommendation: dict[str, Any]


class Evaluator:
    def evaluate(self, ground_truth, findings, recommendations, metrics):
        detection, match_by_finding = self._detection(ground_truth, findings, metrics)
        recommendation = self._recommendations(
            ground_truth, findings, recommendations, match_by_finding)
        return EvaluationResult(detection, recommendation)

    def _detection(self, truth, findings, metrics):
        unmatched_truth = {row["smell_id"]: row for row in truth}
        matches, unmatched_findings = [], []
        finding_to_truth = {}
        for finding in sorted(findings, key=lambda row: row["rank"]):
            best = None
            for expected in unmatched_truth.values():
                if canonical_smell(finding["smell_type"]) != canonical_smell(expected["smell_type"]):
                    continue
                detected_components = components_for_finding(finding)
                expected_components = set(expected["affected_components"])
                if detected_components == expected_components:
                    best = (expected, "exact match")
                    break
                if detected_components & expected_components and best is None:
                    best = (expected, "partial match")
            if best:
                expected, quality = best
                unmatched_truth.pop(expected["smell_id"])
                finding_to_truth[finding["finding_id"]] = expected["smell_id"]
                matches.append({"finding_id": finding["finding_id"], "smell_id": expected["smell_id"],
                                "quality": quality, "rank": finding["rank"],
                                "detected_components": sorted(components_for_finding(finding)),
                                "expected_components": sorted(expected["affected_components"])})
            else:
                unmatched_findings.append({"finding_id": finding["finding_id"],
                                           "smell_type": finding["smell_type"], "rank": finding["rank"]})
        expected_count = len(truth)
        ranks = {row["smell_id"]: 0 for row in truth}
        for match in matches:
            ranks[match["smell_id"]] = match["rank"]
        ranking = {
            "top_1_accuracy": safe_divide(sum(1 for rank in ranks.values() if 0 < rank <= 1), expected_count),
            "top_3_accuracy": safe_divide(sum(1 for rank in ranks.values() if 0 < rank <= 3), expected_count),
            "mean_reciprocal_rank": safe_divide(sum(1.0 / rank for rank in ranks.values() if rank), expected_count),
            "rank_by_expected_smell": ranks,
        }
        missed = []
        metric_by_component = {row["component"]: row for row in metrics}
        for expected in sorted(unmatched_truth.values(), key=lambda row: row["smell_id"]):
            reason = "No finding of the expected type and component identity was emitted."
            measured = {}
            if canonical_smell(expected["smell_type"]) == "unstable dependency" and len(expected["affected_components"]) == 2:
                source, target = expected["affected_components"]
                if source in metric_by_component and target in metric_by_component:
                    source_i = metric_by_component[source]["instability"]
                    target_i = metric_by_component[target]["instability"]
                    difference = round(target_i - source_i, 6)
                    measured = {"source_component": source, "target_component": target,
                                "source_instability": source_i, "target_instability": target_i,
                                "instability_difference": difference,
                                "configured_margin": 0.20,
                                "condition_satisfied": source_i + 0.20 < target_i}
                    reason = (f"Measured instability difference {difference:.6f} did not satisfy the unchanged "
                              f"condition I(source) + 0.20 < I(target).")
            missed.append({"smell_id": expected["smell_id"], "smell_type": expected["smell_type"],
                           "expected_components": expected["affected_components"],
                           "measured_reason": reason, "measured_values": measured})
        counts = prf(len(matches), len(unmatched_findings), len(missed))
        detected_packages = {package for row in findings for package in row["affected_packages"]}
        expected_packages = {package for row in truth for package in row["affected_packages"]}
        by_type = []
        types = sorted({canonical_smell(row["smell_type"]) for row in truth + findings})
        for smell_type in types:
            expected_ids = {row["smell_id"] for row in truth if canonical_smell(row["smell_type"]) == smell_type}
            detected_ids = {row["finding_id"] for row in findings if canonical_smell(row["smell_type"]) == smell_type}
            tp = sum(1 for row in matches if row["smell_id"] in expected_ids)
            fp = sum(1 for row in unmatched_findings if row["finding_id"] in detected_ids)
            fn = sum(1 for row in missed if row["smell_id"] in expected_ids)
            by_type.append({"smell_type": smell_type, **prf(tp, fp, fn)})
        return {
            "schema_version": "1.0", "matching_rules": MATCHING_RULES,
            "overall": counts, "by_smell_type": by_type,
            "ranking_metrics": ranking, "matched_findings": matches,
            "unmatched_findings": unmatched_findings, "missed_ground_truth_smells": missed,
            "detected_vs_expected_packages": overlap_metrics(detected_packages, expected_packages),
        }, finding_to_truth

    def _recommendations(self, truth, findings, recommendations, finding_to_truth):
        expected_units = expected_recommendation_units(truth)
        units_by_smell = defaultdict(list)
        for unit in expected_units:
            units_by_smell[unit["smell_id"]].append(unit)
        evaluated = []
        for recommendation in sorted(recommendations, key=lambda row: row["candidate_rank"]):
            smell_id = finding_to_truth.get(recommendation["finding_id"])
            units = units_by_smell.get(smell_id, [])
            target_package = recommendation["target_package"]
            symbols = {simple_name(value) for value in recommendation["source_symbols"] + recommendation["related_symbols"]}
            matching = [unit for unit in units if unit["target_package"] == target_package]
            matched_unit = matching[0] if matching else None
            if matched_unit and matched_unit["expected_symbol"] in symbols:
                quality = ("semantically valid alternative" if recommendation["refactoring_kind"] == "PRESERVE_FACADE"
                           else "exact match")
            elif matched_unit:
                quality = "partial match"
            else:
                quality = "incorrect recommendation"
            unsafe = bool(recommendation["rejection_reasons"]) or recommendation["architecture_risk"] == "HIGH"
            if unsafe and quality != "incorrect recommendation":
                quality = "unsafe recommendation"
            elif not recommendation["automatable"] and quality not in ("incorrect recommendation", "unsafe recommendation"):
                quality = "unautomatable but valid recommendation"
            evaluated.append({"recommendation_id": recommendation["recommendation_id"],
                              "candidate_rank": recommendation["candidate_rank"],
                              "finding_id": recommendation["finding_id"], "smell_id": smell_id,
                              "classification": quality, "target_package": target_package,
                              "expected_unit": matched_unit, "source_symbol_count": len(recommendation["source_symbols"])})
        category_counts = {category: sum(1 for row in evaluated if row["classification"] == category)
                           for category in ("exact match", "partial match", "semantically valid alternative",
                                            "incorrect recommendation", "unsafe recommendation",
                                            "unautomatable but valid recommendation")}
        expected_symbols = {simple_name(symbol) for row in truth for symbol in row["affected_symbols"]}
        recommended_symbols = {simple_name(symbol) for row in recommendations for symbol in row["source_symbols"]}
        expected_packages = {unit["target_package"] for unit in expected_units}
        recommended_packages = {row["target_package"] for row in recommendations}
        symbol_overlap = overlap_metrics(recommended_symbols, expected_symbols)
        package_overlap = overlap_metrics(recommended_packages, expected_packages)
        covered_units = {(row["smell_id"], row["expected_unit"]["unit_id"])
                         for row in evaluated if row["expected_unit"] and row["classification"] not in
                         ("incorrect recommendation", "unsafe recommendation")}
        unmatched_units = [unit for unit in expected_units if (unit["smell_id"], unit["unit_id"]) not in covered_units]
        valid = {"exact match", "partial match", "semantically valid alternative", "unautomatable but valid recommendation"}
        return {
            "schema_version": "1.0", "matching_rules": MATCHING_RULES,
            "summary": {"recommendation_count": len(recommendations), **category_counts,
                        "top_1_valid_accuracy": 1.0 if evaluated and evaluated[0]["classification"] in valid else 0.0,
                        "top_3_valid_accuracy": safe_divide(sum(1 for row in evaluated[:3] if row["classification"] in valid), min(3, len(evaluated)))},
            "recommendation_symbol_overlap": symbol_overlap,
            "recommendation_package_overlap": package_overlap,
            "evaluated_recommendations": evaluated,
            "expected_recommendation_units": expected_units,
            "unmatched_expected_units": unmatched_units,
        }


def expected_recommendation_units(truth):
    units = []
    for smell in truth:
        destinations = smell["expected_destinations"]
        groups = smell["expected_responsibility_groups"]
        symbols = smell["affected_symbols"]
        if canonical_smell(smell["smell_type"]) == "god component":
            for index, destination in enumerate(destinations):
                units.append({"unit_id": groups[index], "smell_id": smell["smell_id"],
                              "target_package": destination, "expected_symbol": simple_name(symbols[index]),
                              "responsibility_group": groups[index]})
        else:
            for destination in destinations:
                parts = destination.rsplit(".", 1)
                package = parts[0] if parts[-1][:1].isupper() else destination
                symbol = parts[-1] if parts[-1][:1].isupper() else simple_name(symbols[0])
                units.append({"unit_id": symbol, "smell_id": smell["smell_id"],
                              "target_package": package, "expected_symbol": symbol,
                              "responsibility_group": "stable abstraction"})
    return units


def overlap_metrics(predicted: set[str], expected: set[str]):
    intersection = predicted & expected
    precision = safe_divide(len(intersection), len(predicted))
    recall = safe_divide(len(intersection), len(expected))
    return {"predicted_count": len(predicted), "expected_count": len(expected),
            "intersection_count": len(intersection), "precision": precision, "recall": recall,
            "f1": safe_divide(2 * precision * recall, precision + recall),
            "jaccard": safe_divide(len(intersection), len(predicted | expected)),
            "matched": sorted(intersection), "predicted_only": sorted(predicted - expected),
            "expected_only": sorted(expected - predicted)}
