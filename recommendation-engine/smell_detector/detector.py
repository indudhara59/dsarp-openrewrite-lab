"""Pure deterministic scoring over semantic analyzer output tables."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

GOD_WEIGHTS = {
    "class_share": 0.19,
    "loc_share": 0.19,
    "normalized_ca": 0.14,
    "normalized_ce": 0.14,
    "centrality": 0.10,
    "responsibility_diversity": 0.10,
    "responsibility_cluster_count": 0.09,
    "internal_dependency_concentration": 0.05,
}
GOD_THRESHOLD = 0.60
SDP_MARGIN = 0.20


def rounded(value: float) -> float:
    return round(value + 0.0, 6)


def normalize(values: dict[str, float]) -> dict[str, float]:
    maximum = max(values.values(), default=0.0)
    if maximum == 0:
        return {key: 0.0 for key in sorted(values)}
    return {key: rounded(values[key] / maximum) for key in sorted(values)}


def component_of(class_name: str) -> str:
    prefix = "com.dsarp.shop."
    remainder = class_name[len(prefix):]
    return remainder.split(".", 1)[0]


@dataclass(frozen=True)
class DetectionResult:
    findings: list[dict[str, Any]]
    god_candidates: list[dict[str, Any]]
    unstable_edge_assessments: list[dict[str, Any]]
    warnings: list[str]


class Detector:
    """Scores components and edges without external or generative decisions."""

    def detect(
        self,
        classes: list[dict[str, Any]],
        class_dependencies: list[dict[str, Any]],
        component_dependencies: list[dict[str, Any]],
        component_metrics: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
        commit_sha: str,
        input_warnings: list[str],
    ) -> DetectionResult:
        metrics = {row["component"]: row for row in component_metrics}
        classes_by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in classes:
            classes_by_component[row["top_level_component"]].append(row)
        clusters_by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in clusters:
            clusters_by_component[row["component"]].append(row)

        candidates = self._god_candidates(metrics, classes_by_component, clusters_by_component)
        findings = [self._god_finding(candidate, commit_sha) for candidate in candidates
                    if candidate["final_score"] >= GOD_THRESHOLD]
        unstable_findings, unstable_assessments = self._unstable_findings(
            metrics, classes_by_component, class_dependencies,
            component_dependencies, commit_sha)
        findings.extend(unstable_findings)
        findings.sort(key=lambda row: (-row["severity"], -row["detection_confidence"], row["finding_id"]))
        for rank, finding in enumerate(findings, start=1):
            finding["rank"] = rank
        warnings = sorted(set(input_warnings))
        return DetectionResult(findings, candidates, unstable_assessments, warnings)

    def _god_candidates(self, metrics, classes_by_component, clusters_by_component):
        raw: dict[str, dict[str, float]] = {}
        for component in sorted(metrics):
            metric = metrics[component]
            component_clusters = clusters_by_component.get(component, [])
            internal = metric["internal_class_dependency_count"]
            outgoing = metric["weighted_outgoing_dependency_count"]
            raw[component] = {
                "class_share": metric["percentage_total_production_classes"] / 100.0,
                "loc_share": metric["percentage_total_production_loc"] / 100.0,
                "normalized_ca": float(metric["ca"]),
                "normalized_ce": float(metric["ce"]),
                "centrality": float(metric["degree_centrality"]),
                "responsibility_diversity": float(len({row["dominant_subpackage"] for row in component_clusters})),
                "responsibility_cluster_count": float(len(component_clusters)),
                "internal_dependency_concentration": (
                    internal / (internal + outgoing) if internal + outgoing else 0.0),
            }
        normalized_by_feature = {
            feature: normalize({component: values[feature] for component, values in raw.items()})
            for feature in GOD_WEIGHTS
        }
        candidates = []
        for component in sorted(metrics):
            normalized = {feature: normalized_by_feature[feature][component] for feature in GOD_WEIGHTS}
            score = rounded(sum(GOD_WEIGHTS[name] * normalized[name] for name in GOD_WEIGHTS))
            support_classes = sorted(
                classes_by_component.get(component, []),
                key=lambda row: (-len(row["outgoing_class_dependencies"]), -row["loc"],
                                 row["fully_qualified_class_name"]),
            )[:12]
            candidates.append({
                "component": component,
                "raw_features": {key: rounded(value) for key, value in raw[component].items()},
                "normalized_features": normalized,
                "final_score": score,
                "threshold": GOD_THRESHOLD,
                "confidence": rounded(min(1.0, 0.75 + max(0.0, score - GOD_THRESHOLD) * 0.625)),
                "supporting_classes": [row["fully_qualified_class_name"] for row in support_classes],
                "supporting_responsibility_clusters": sorted(
                    row["cluster_id"] for row in clusters_by_component.get(component, [])),
                "packages": sorted({row["package"] for row in classes_by_component.get(component, [])}),
            })
        candidates.sort(key=lambda row: (-row["final_score"], row["component"]))
        for rank, candidate in enumerate(candidates, start=1):
            candidate["rank"] = rank
        return candidates

    def _god_finding(self, candidate, commit_sha):
        component = candidate["component"]
        raw = candidate["raw_features"]
        explanation = (
            f"{component} scored {candidate['final_score']:.6f} against the {GOD_THRESHOLD:.2f} threshold; "
            f"it contains {raw['class_share'] * 100:.6f}% of classes and "
            f"{raw['loc_share'] * 100:.6f}% of LOC, with Ca={raw['normalized_ca']:.0f}, "
            f"Ce={raw['normalized_ce']:.0f}, centrality={raw['centrality']:.6f}, and "
            f"{raw['responsibility_cluster_count']:.0f} measured responsibility clusters."
        )
        return {
            "finding_id": f"GC::{component}",
            "smell_type": "GOD_COMPONENT",
            "rank": 0,
            "severity": rounded(candidate["final_score"] * 100.0),
            "detection_confidence": candidate["confidence"],
            "primary_component": component,
            "related_component": None,
            "affected_packages": candidate["packages"],
            "affected_symbols": candidate["supporting_classes"],
            "evidence": {
                "supporting_classes": candidate["supporting_classes"],
                "supporting_responsibility_clusters": candidate["supporting_responsibility_clusters"],
                "raw_features": candidate["raw_features"],
                "normalized_features": candidate["normalized_features"],
            },
            "metrics": {"god_component_score": candidate["final_score"]},
            "threshold": {"score_at_least": GOD_THRESHOLD},
            "formula_version": "god-component-v1",
            "explanation": explanation,
            "detected_at_commit": commit_sha,
        }

    def _unstable_findings(self, metrics, classes_by_component, class_dependencies,
                           component_dependencies, commit_sha):
        class_edges: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)
        for edge in class_dependencies:
            source = edge["source_class"]
            target = edge["target_class"]
            class_edges[(component_of(source), component_of(target))].append((source, target))
        maximum_weight = max((edge["weight"] for edge in component_dependencies), default=0)
        findings = []
        assessments = []
        seen = set()
        for edge in sorted(component_dependencies,
                           key=lambda row: (row["source_component"], row["target_component"])):
            source = edge["source_component"]
            target = edge["target_component"]
            identity = (source, target)
            if identity in seen:
                continue
            seen.add(identity)
            source_i = metrics[source]["instability"]
            target_i = metrics[target]["instability"]
            difference = rounded(target_i - source_i)
            assessments.append({
                "source_component": source,
                "target_component": target,
                "source_instability": source_i,
                "target_instability": target_i,
                "instability_difference": difference,
                "required_difference": SDP_MARGIN,
                "qualifies": source_i + SDP_MARGIN < target_i,
            })
            if not source_i + SDP_MARGIN < target_i:
                continue
            supporting = sorted(set(class_edges.get(identity, [])))
            source_classes = sorted({pair[0] for pair in supporting})
            target_classes = sorted({pair[1] for pair in supporting})
            excess = rounded(difference - SDP_MARGIN)
            normalized_excess = min(1.0, excess / (1.0 - SDP_MARGIN))
            weight_signal = edge["weight"] / maximum_weight if maximum_weight else 0.0
            source_stability = 1.0 - source_i
            source_coverage = len(source_classes) / metrics[source]["production_class_count"]
            severity = rounded(100.0 * (
                0.45 * normalized_excess + 0.25 * weight_signal
                + 0.20 * source_stability + 0.10 * source_coverage))
            confidence = rounded(min(1.0, 0.60 + 0.20 * weight_signal + 0.20 * source_coverage))
            findings.append({
                "finding_id": f"UD::{source}::{target}",
                "smell_type": "UNSTABLE_DEPENDENCY",
                "rank": 0,
                "severity": severity,
                "detection_confidence": confidence,
                "primary_component": source,
                "related_component": target,
                "affected_packages": sorted({
                    row["package"] for name in (source, target)
                    for row in classes_by_component.get(name, [])}),
                "affected_symbols": sorted(set(source_classes + target_classes)),
                "evidence": {
                    "number_of_class_level_references": len(supporting),
                    "source_classes": source_classes,
                    "target_classes": target_classes,
                    "component_edge_weight": edge["weight"],
                },
                "metrics": {
                    "source_instability": source_i,
                    "target_instability": target_i,
                    "instability_difference": difference,
                    "threshold_margin": SDP_MARGIN,
                    "margin_beyond_threshold": excess,
                    "source_centrality": metrics[source]["degree_centrality"],
                    "target_centrality": metrics[target]["degree_centrality"],
                    "normalized_edge_weight": rounded(weight_signal),
                    "source_stability": rounded(source_stability),
                    "source_class_coverage": rounded(source_coverage),
                },
                "threshold": {"condition": "I(source) + 0.20 < I(target)", "margin": SDP_MARGIN},
                "formula_version": "unstable-dependency-v1",
                "explanation": (
                    f"{source} (I={source_i:.6f}) depends on {target} (I={target_i:.6f}); "
                    f"the difference {difference:.6f} exceeds the required margin {SDP_MARGIN:.2f} "
                    f"and is supported by {len(supporting)} resolved class-level references."
                ),
                "detected_at_commit": commit_sha,
            })
        assessments.sort(key=lambda row: (-row["instability_difference"],
                                          row["source_component"], row["target_component"]))
        return findings, assessments
