"""Allowlisted input loading and deterministic baseline artifact writing."""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

INPUTS = {
    "classes": "classes.json",
    "class_dependencies": "class_dependencies.json",
    "component_dependencies": "component_dependencies.json",
    "component_metrics": "component_metrics.json",
    "responsibility_clusters": "responsibility_clusters.json",
    "metadata": "analyzer_metadata.json",
}


def load_inputs(input_directory: Path) -> tuple[dict[str, Any], dict[str, str]]:
    loaded: dict[str, Any] = {}
    hashes: dict[str, str] = {}
    for key, filename in INPUTS.items():
        path = input_directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required analyzer input missing: {path}")
        content = path.read_bytes()
        hashes[filename] = hashlib.sha256(content).hexdigest()
        loaded[key] = json.loads(content)
    return loaded, hashes


def write_outputs(output: Path, raw: dict[str, Any], hashes: dict[str, str], result) -> None:
    output.mkdir(parents=True, exist_ok=True)
    metrics = raw["component_metrics"]["component_metrics"]
    dependencies = raw["component_dependencies"]["component_dependencies"]
    clusters = raw["responsibility_clusters"]["responsibility_clusters"]
    write_json(output / "component_metrics.json", raw["component_metrics"])
    write_json(output / "component_dependencies.json", raw["component_dependencies"])
    write_json(output / "responsibility_clusters.json", raw["responsibility_clusters"])
    write_json(output / "smell_findings.json", {
        "schema_version": "1.0",
        "formula_versions": ["god-component-v1", "unstable-dependency-v1"],
        "findings": result.findings,
    })
    write_csv(output / "component_metrics.csv", metrics, [
        "component", "production_class_count", "production_loc", "package_count", "ca", "ce",
        "instability", "weighted_incoming_dependency_count", "weighted_outgoing_dependency_count",
        "fan_in", "fan_out", "internal_class_dependency_count", "internal_dependency_density",
        "percentage_total_production_classes", "percentage_total_production_loc", "degree_centrality",
    ])
    write_csv(output / "component_dependencies.csv", dependencies,
              ["source_component", "target_component", "weight"])
    write_finding_csv(output / "smell_findings.csv", result.findings)
    (output / "ranking_explanation.md").write_text(ranking_markdown(result), encoding="utf-8")
    (output / "analysis_report.md").write_text(report_markdown(result), encoding="utf-8")

    metadata = raw["metadata"]
    warnings = sorted(set(result.warnings + (
        [f"Semantic analyzer reported {metadata.get('unresolved_symbol_count')} unresolved symbols."]
        if metadata.get("unresolved_symbol_count", 0) else [])))
    write_json(output / "run_metadata.json", {
        "schema_version": "1.0",
        "detector_version": "1.0.0",
        "execution_timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "detected_at_commit": metadata.get("git_commit_sha", "unavailable"),
        "input_sha256": {key: hashes[key] for key in sorted(hashes)},
        "input_allowlist": [INPUTS[key] for key in INPUTS],
        "ground_truth_accessed": False,
        "formula_versions": ["god-component-v1", "unstable-dependency-v1"],
        "god_component_threshold": 0.60,
        "unstable_dependency_margin": 0.20,
        "deterministic_sort": "severity desc, confidence desc, finding_id asc",
        "warnings": warnings,
        "missing_data": [],
        "analyzer_unresolved_symbol_count": metadata.get("unresolved_symbol_count", 0),
    })


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in sorted(rows, key=lambda item: tuple(str(item.get(field, "")) for field in fields)):
            writer.writerow(row)


def write_finding_csv(path: Path, findings: list[dict[str, Any]]) -> None:
    fields = ["finding_id", "smell_type", "rank", "severity", "detection_confidence",
              "primary_component", "related_component", "affected_packages", "affected_symbols",
              "evidence", "metrics", "threshold", "formula_version", "explanation", "detected_at_commit"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for finding in findings:
            row = dict(finding)
            for field in ("affected_packages", "affected_symbols", "evidence", "metrics", "threshold"):
                row[field] = json.dumps(row[field], sort_keys=True, separators=(",", ":"))
            row["related_component"] = row["related_component"] or ""
            writer.writerow(row)


def ranking_markdown(result) -> str:
    lines = [
        "# Blind Smell Ranking Explanation", "",
        "Findings are ranked by severity descending, detection confidence descending, then stable finding ID.", "",
        "## God Component scoring", "",
        "The `god-component-v1` score uses eight normalized dimensions and a fixed threshold of `0.60`.", "",
        "| Candidate rank | Component | Score | Threshold | Cluster count | Class share | LOC share |", "|---:|---|---:|---:|---:|---:|---:|",
    ]
    for candidate in result.god_candidates:
        raw = candidate["raw_features"]
        lines.append(f"| {candidate['rank']} | {candidate['component']} | {candidate['final_score']:.6f} | "
                     f"{candidate['threshold']:.2f} | {raw['responsibility_cluster_count']:.0f} | "
                     f"{raw['class_share'] * 100:.6f}% | {raw['loc_share'] * 100:.6f}% |")
    lines.extend(["", "## Unstable Dependency scoring", "",
                  "An edge is eligible only when `I(source) + 0.20 < I(target)`. Severity combines excess instability margin, edge weight, source stability, and source-class coverage.", ""])
    return "\n".join(lines) + "\n"


def report_markdown(result) -> str:
    lines = ["# Blind Baseline Architecture Smell Analysis", "",
             "This report is generated from semantic analyzer outputs using deterministic formulas. It contains detection only and no refactoring recommendations.", "",
             "## Ranked findings", "",
             "| Rank | Finding | Type | Severity | Confidence | Explanation |", "|---:|---|---|---:|---:|---|"]
    for finding in result.findings:
        explanation = finding["explanation"].replace("|", "\\|")
        lines.append(f"| {finding['rank']} | `{finding['finding_id']}` | {finding['smell_type']} | "
                     f"{finding['severity']:.6f} | {finding['detection_confidence']:.6f} | {explanation} |")
    if not result.findings:
        lines.append("| — | — | — | — | — | No findings crossed the configured thresholds. |")
    lines.extend(["", "## Warnings and missing data", ""])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("No input warnings or missing required data were reported.")
    unstable = [row for row in result.findings if row["smell_type"] == "UNSTABLE_DEPENDENCY"]
    lines.extend(["", "## Unstable Dependency assessment", ""])
    if unstable:
        top = unstable[0]
        values = top["metrics"]
        lines.append(f"The highest-ranked detected edge is `{top['primary_component']} -> {top['related_component']}` "
                     f"with I(source)={values['source_instability']:.6f}, "
                     f"I(target)={values['target_instability']:.6f}, and difference "
                     f"{values['instability_difference']:.6f}.")
    elif result.unstable_edge_assessments:
        closest = result.unstable_edge_assessments[0]
        lines.append("No component edge satisfies `I(source) + 0.20 < I(target)`. "
                     f"The largest observed increase is `{closest['source_component']} -> "
                     f"{closest['target_component']}` with I(source)={closest['source_instability']:.6f}, "
                     f"I(target)={closest['target_instability']:.6f}, and difference "
                     f"{closest['instability_difference']:.6f}, below the required strict margin 0.20.")
    else:
        lines.append("No component dependency edges were available for assessment.")
    return "\n".join(lines) + "\n"
